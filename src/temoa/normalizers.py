"""
URL normalization for gleanings.

This module provides domain-specific normalization for gleaning titles and descriptions.
Each normalizer handles a specific URL pattern (e.g., GitHub, YouTube) and applies
appropriate transformations to make titles and descriptions more concise and searchable.

Usage:
    registry = NormalizerRegistry()
    title, description = registry.normalize(url, fetched_title, fetched_description)
"""

import re
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse


class URLNormalizer(ABC):
    """Base class for URL normalizers."""

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Check if this normalizer handles the URL."""
        pass

    @abstractmethod
    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """Normalize the title."""
        pass

    @abstractmethod
    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """Normalize the description."""
        pass


class GitHubNormalizer(URLNormalizer):
    """Normalize GitHub repository URLs."""

    def matches(self, url: str) -> bool:
        """Match github.com URLs."""
        return "github.com" in urlparse(url).netloc

    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """
        Preserve 'user/repo: Description' format, just clean it.

        Examples:
            "GitHub - user/repo: Description" -> "user/repo: Description"
            "user/repo: Description - user/repo" -> "user/repo: Description"
            "user/repo: Description" -> "user/repo: Description"
            None -> Extract "user/repo" from URL path
        """
        if fetched_title:
            title = fetched_title.strip()

            # Remove redundant "GitHub - " prefix
            if title.startswith("GitHub - "):
                title = title[9:]  # len("GitHub - ") = 9

            # Remove trailing " - user/repo" if present (redundant suffix)
            if " - " in title:
                parts = title.split(" - ")
                # Check if last part looks like user/repo (has a slash)
                if "/" in parts[-1] and len(parts) > 1:
                    # Only remove if it's at the end and looks like a repo path
                    title = " - ".join(parts[:-1])

            return title.strip()

        # Fallback: extract user/repo from URL
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return url

    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """
        Extract description, remove redundant repo name.

        Examples:
            "Description text. - user/repo" -> "Description text."
            "Description text. Contribute to user/repo..." -> "Description text."
        """
        if not fetched_description:
            return ""

        desc = fetched_description.strip()

        # Remove " - user/repo" suffix
        if " - " in desc:
            parts = desc.split(" - ")
            # Check if last part looks like user/repo
            if "/" in parts[-1]:
                desc = " - ".join(parts[:-1]).strip()

        # Remove "Contribute to user/repo..." suffix
        if "Contribute to " in desc:
            desc = desc.split("Contribute to ")[0].strip()

        # Remove emojis (Unicode ranges for emoji characters)
        # This pattern covers most common emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002500-\U00002BEF"  # chinese char
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+",
            flags=re.UNICODE
        )
        desc = emoji_pattern.sub("", desc)
        
        # Clean up extra whitespace created by emoji removal
        desc = re.sub(r'\s+', ' ', desc).strip()

        return desc


class DefaultNormalizer(URLNormalizer):
    """Pass-through normalizer for unknown domains."""

    def matches(self, url: str) -> bool:
        """Match everything (fallback)."""
        return True

    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """Return title as-is."""
        return fetched_title or url

    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """Return description as-is."""
        return fetched_description or ""


class NormalizerRegistry:
    """Registry of URL normalizers."""

    def __init__(self):
        self.normalizers = [
            GitHubNormalizer(),
            # YouTubeNormalizer(),  # Future
            # RedditNormalizer(),   # Future
            DefaultNormalizer(),  # Always last (fallback)
        ]

    def get_normalizer(self, url: str) -> URLNormalizer:
        """Get the appropriate normalizer for a URL."""
        for normalizer in self.normalizers:
            if normalizer.matches(url):
                return normalizer
        return self.normalizers[-1]  # DefaultNormalizer

    def normalize(
        self, url: str, title: Optional[str], description: Optional[str]
    ) -> tuple[str, str]:
        """
        Normalize title and description for a URL.

        Args:
            url: The URL to normalize
            title: The fetched title (or None)
            description: The fetched description (or None)

        Returns:
            (normalized_title, normalized_description)
        """
        normalizer = self.get_normalizer(url)
        norm_title = normalizer.normalize_title(url, title)
        norm_desc = normalizer.normalize_description(url, description)
        return norm_title, norm_desc
