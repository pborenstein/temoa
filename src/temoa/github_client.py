"""
GitHub API client for enriching repository gleanings.

Fetches repository metadata (description, language, stars, topics, etc.) and
README excerpts to provide rich context for GitHub gleanings.
"""

import re
import time
from typing import Optional
from urllib.parse import urlparse

import requests


class GitHubClient:
    """Client for fetching GitHub repository metadata via REST API."""

    def __init__(self, token: Optional[str] = None, rate_limit_delay: float = 2.0):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub personal access token (optional, but recommended for rate limits)
            rate_limit_delay: Seconds to wait between API calls (default: 2.0)
        """
        self.token = token
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self.base_url = "https://api.github.com"
        self.session = requests.Session()

        # Set up headers
        self.session.headers.update({
            "User-Agent": "Temoa-GitHub-Enricher/0.1",
            "Accept": "application/vnd.github.v3+json"
        })

        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def parse_repo_url(self, url: str) -> Optional[tuple[str, str]]:
        """
        Parse owner and repo name from GitHub URL.

        Handles various URL formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo/tree/main
        - https://github.com/owner/repo/blob/main/file.md
        - https://github.com/owner/repo/issues/42
        - https://github.com/owner/repo/pull/123

        Args:
            url: GitHub URL

        Returns:
            Tuple of (owner, repo) or None if not a valid GitHub repo URL
        """
        parsed = urlparse(url)

        # Check if it's a GitHub URL
        if parsed.netloc not in ["github.com", "www.github.com"]:
            return None

        # Extract path components
        path = parsed.path.strip("/")
        parts = path.split("/")

        # Need at least owner/repo
        if len(parts) < 2:
            return None

        owner, repo = parts[0], parts[1]

        # Validate owner and repo (basic check for reasonable names)
        if not owner or not repo:
            return None

        return (owner, repo)

    def get_repo_metadata(self, owner: str, repo: str) -> Optional[dict]:
        """
        Fetch repository metadata from GitHub API.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name

        Returns:
            Dict with metadata fields or None if request failed

        Raises:
            requests.HTTPError: For 401 (unauthorized) errors
        """
        self._rate_limit()

        url = f"{self.base_url}/repos/{owner}/{repo}"

        try:
            response = self.session.get(url, timeout=10)

            # Handle specific error cases
            if response.status_code == 401:
                raise requests.HTTPError("GitHub API: Unauthorized (check GITHUB_TOKEN)")

            if response.status_code == 403:
                # Rate limit exceeded
                if "X-RateLimit-Remaining" in response.headers:
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    reset_time = response.headers.get("X-RateLimit-Reset")
                    raise requests.HTTPError(
                        f"GitHub API rate limit exceeded. "
                        f"Remaining: {remaining}, Reset at: {reset_time}"
                    )
                raise requests.HTTPError("GitHub API: Forbidden (rate limit or permissions)")

            if response.status_code == 404:
                # Repo not found (deleted, private, or doesn't exist)
                return None

            response.raise_for_status()
            data = response.json()

            # Extract relevant fields
            return {
                "owner": data.get("owner", {}).get("login"),
                "repo": data.get("name"),
                "description": data.get("description", ""),
                "language": data.get("language"),
                "stars": data.get("stargazers_count", 0),
                "topics": data.get("topics", []),
                "archived": data.get("archived", False),
                "last_push": data.get("pushed_at"),
                "url": data.get("html_url")
            }

        except requests.Timeout:
            print(f"Warning: Timeout fetching {owner}/{repo}")
            return None
        except requests.RequestException as e:
            if isinstance(e, requests.HTTPError) and "Unauthorized" in str(e):
                raise  # Re-raise auth errors
            if isinstance(e, requests.HTTPError) and "rate limit" in str(e).lower():
                raise  # Re-raise rate limit errors
            print(f"Warning: Error fetching {owner}/{repo}: {e}")
            return None

    def get_readme_excerpt(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch README and extract first meaningful paragraph.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            First paragraph (max 500 chars) or None if README not available
        """
        self._rate_limit()

        url = f"{self.base_url}/repos/{owner}/{repo}/readme"

        try:
            response = self.session.get(
                url,
                headers={"Accept": "application/vnd.github.v3.raw"},
                timeout=10
            )

            if response.status_code == 404:
                # No README
                return None

            response.raise_for_status()
            readme_text = response.text

            # Extract first meaningful paragraph
            excerpt = self._extract_first_paragraph(readme_text)

            # Truncate to 500 chars, try to break at sentence boundary
            if excerpt and len(excerpt) > 500:
                excerpt = excerpt[:500]
                # Try to break at sentence
                last_period = excerpt.rfind(". ")
                if last_period > 300:  # Only if we have a reasonable amount of text
                    excerpt = excerpt[:last_period + 1]

            return excerpt

        except requests.RequestException:
            # README fetch failed, not critical
            return None

    def _extract_first_paragraph(self, markdown: str) -> Optional[str]:
        """
        Extract first meaningful paragraph from markdown README.

        Skips:
        - YAML frontmatter
        - HTML comments
        - Badges/images
        - Headers
        - Empty lines

        Args:
            markdown: Raw markdown content

        Returns:
            First paragraph with >50 chars, or None
        """
        lines = markdown.split("\n")

        in_frontmatter = False
        in_code_block = False
        paragraph_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip YAML frontmatter
            if stripped == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue

            # Skip code blocks
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Skip empty lines
            if not stripped:
                # Empty line might end a paragraph
                if paragraph_lines:
                    # Check if we have enough text
                    paragraph = " ".join(paragraph_lines)
                    if len(paragraph) > 50:
                        return paragraph
                    # Not enough, keep looking
                    paragraph_lines = []
                continue

            # Skip headers
            if stripped.startswith("#"):
                continue

            # Skip HTML comments
            if stripped.startswith("<!--") or "-->" in stripped:
                continue

            # Skip lines that are just badges/images
            if self._is_badge_or_image_line(stripped):
                continue

            # This looks like paragraph text
            paragraph_lines.append(stripped)

        # Check final paragraph
        if paragraph_lines:
            paragraph = " ".join(paragraph_lines)
            if len(paragraph) > 50:
                return paragraph

        return None

    def _is_badge_or_image_line(self, line: str) -> bool:
        """Check if line is primarily badges or images."""
        # Count markdown images/links
        image_count = line.count("![")
        link_count = line.count("](")

        # If more than 50% of line is brackets/parens, probably badges
        bracket_chars = line.count("[") + line.count("]") + line.count("(") + line.count(")")
        total_chars = len(line)

        if total_chars > 0 and bracket_chars / total_chars > 0.5:
            return True

        # If lots of images, probably a badge line
        if image_count > 2:
            return True

        return False

    def enrich_gleaning(self, url: str) -> Optional[dict]:
        """
        Fetch all enrichment data for a GitHub URL.

        Args:
            url: GitHub repository URL

        Returns:
            Dict with all enrichment fields, or None if not a valid GitHub repo

        Example return:
            {
                "owner": "fastapi",
                "repo": "fastapi",
                "description": "FastAPI framework, high performance...",
                "language": "Python",
                "stars": 12345,
                "topics": ["python", "fastapi", "api"],
                "archived": False,
                "last_push": "2025-01-15T12:34:56Z",
                "readme_excerpt": "FastAPI is a modern, fast web framework...",
                "url": "https://github.com/fastapi/fastapi"
            }
        """
        # Parse URL to get owner/repo
        parsed = self.parse_repo_url(url)
        if not parsed:
            print(f"Warning: Could not parse GitHub URL: {url}")
            return None

        owner, repo = parsed

        # Fetch repo metadata
        metadata = self.get_repo_metadata(owner, repo)
        if not metadata:
            return None

        # Fetch README excerpt (non-blocking, optional)
        readme_excerpt = self.get_readme_excerpt(owner, repo)
        if readme_excerpt:
            metadata["readme_excerpt"] = readme_excerpt

        return metadata
