#!/usr/bin/env python3
"""
Gleaning Maintenance Tool

Maintains gleanings by:
- Checking if URLs are alive (dead link detection)
- Fetching meta descriptions from live URLs
- Marking dead links as inactive
- Updating frontmatter with descriptions

Usage:
    python scripts/maintain_gleanings.py --vault-path /path/to/vault [options]
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Add src to path so we can import gleanings module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from temoa.gleanings import GleaningStatusManager
from temoa.github_client import GitHubClient


class GleaningMaintainer:
    """Maintains gleanings by checking links and adding descriptions."""

    def __init__(
        self,
        vault_path: Path,
        timeout: int = 10,
        user_agent: str = "Mozilla/5.0 (compatible; Temoa/1.0; +https://github.com/pborenstein/temoa)",
        github_token: Optional[str] = None
    ):
        self.vault_path = Path(vault_path).expanduser()
        self.gleanings_dir = self.vault_path / "L" / "Gleanings"
        self.status_manager = GleaningStatusManager(self.vault_path / ".temoa")
        self.timeout = timeout
        self.user_agent = user_agent

        # Initialize GitHub client if token provided
        self.github_client = GitHubClient(token=github_token) if github_token else None

        # Statistics
        self.stats = {
            "total": 0,
            "checked": 0,
            "alive": 0,
            "dead": 0,
            "errors": 0,
            "descriptions_added": 0,
            "descriptions_skipped": 0,
            "marked_inactive": 0,
            "reasons_added": 0,
            "restored_active": 0,
            "skipped_hidden": 0,
            "github_enriched": 0,
            "github_skipped": 0,
            "github_errors": 0
        }

    def check_url(self, url: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if a URL is alive.

        Returns:
            (is_alive, error_message, status_code)
        """
        try:
            headers = {"User-Agent": self.user_agent}

            # Try HEAD first (faster)
            response = requests.head(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            # Some servers don't support HEAD, try GET
            if response.status_code == 405:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )

            if response.status_code < 400:
                return True, None, response.status_code
            else:
                return False, f"HTTP {response.status_code}", response.status_code

        except requests.exceptions.Timeout:
            return False, "Timeout", None
        except requests.exceptions.ConnectionError:
            return False, "Connection failed", None
        except requests.exceptions.TooManyRedirects:
            return False, "Too many redirects", None
        except Exception as e:
            return False, f"Error: {str(e)}", None

    def fetch_meta_description(self, url: str) -> Optional[str]:
        """
        Fetch meta description from a URL.

        Returns:
            Meta description string or None if not found
        """
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Try meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                desc = meta_desc.get('content').strip()
                if desc:
                    return desc

            # Try og:description
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc and og_desc.get('content'):
                desc = og_desc.get('content').strip()
                if desc:
                    return desc

            return None

        except Exception as e:
            print(f"    Error fetching meta description: {e}")
            return None

    def enrich_github_gleaning(
        self,
        file_path: Path,
        url: str,
        frontmatter_dict: Dict,
        dry_run: bool = False
    ) -> Dict[str, str]:
        """
        Enrich a GitHub gleaning with repository metadata.

        Args:
            file_path: Path to gleaning file
            url: GitHub repository URL
            frontmatter_dict: Current frontmatter
            dry_run: If True, don't actually write changes

        Returns:
            Dict of frontmatter updates to apply
        """
        updates = {}

        # Check if already enriched (has github_stars field)
        if "github_stars" in frontmatter_dict:
            print(f"    ⊘ Already enriched (skipping)")
            self.stats["github_skipped"] += 1
            return updates

        # Check if it's a GitHub URL
        if "github.com" not in url.lower():
            return updates

        try:
            print(f"    → Enriching with GitHub API...")

            # Fetch enrichment data
            enrichment = self.github_client.enrich_gleaning(url)

            if not enrichment:
                print(f"    ✗ Could not fetch GitHub metadata")
                self.stats["github_errors"] += 1
                return updates

            # Format title as "user/repo: Description"
            owner = enrichment.get("owner")
            repo = enrichment.get("repo")
            description = enrichment.get("description", "")

            if owner and repo:
                new_title = f"{owner}/{repo}"
                if description:
                    new_title = f"{new_title}: {description}"
                updates["title"] = new_title

            # Update description if we have one
            if description:
                updates["description"] = description

            # Add GitHub metadata fields
            if enrichment.get("language"):
                updates["github_language"] = enrichment["language"]

            updates["github_stars"] = str(enrichment.get("stars", 0))

            # Topics as list (will be formatted as YAML list in update_frontmatter)
            topics = enrichment.get("topics", [])
            if topics:
                # Store as JSON string for now, we'll handle YAML list formatting in update_frontmatter
                updates["github_topics"] = json.dumps(topics)

            updates["github_archived"] = str(enrichment.get("archived", False)).lower()

            if enrichment.get("last_push"):
                updates["github_last_push"] = enrichment["last_push"]

            if enrichment.get("readme_excerpt"):
                updates["github_readme_excerpt"] = enrichment["readme_excerpt"]

            # Update markdown heading in body to match new title
            if not dry_run and "title" in updates:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find and replace the first markdown heading (# Title)
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('# ') and i > 0:  # Skip frontmatter, look in body
                        # Check if we're past the frontmatter
                        if lines[:i].count('---') >= 2:
                            lines[i] = f"# {new_title}"
                            content = '\n'.join(lines)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            break

            self.stats["github_enriched"] += 1
            print(f"    ✓ Enriched: {owner}/{repo}")
            print(f"      Language: {enrichment.get('language', 'N/A')}, "
                  f"Stars: {enrichment.get('stars', 0)}, "
                  f"Topics: {len(topics)}")

            return updates

        except Exception as e:
            print(f"    ✗ Error enriching GitHub gleaning: {e}")
            self.stats["github_errors"] += 1
            return {}

    def parse_frontmatter(self, content: str) -> Tuple[Dict, str, str]:
        """
        Parse frontmatter from markdown content.

        Returns:
            (frontmatter_dict, frontmatter_text, body_text)
        """
        if not content.startswith("---\n"):
            return {}, "", content

        end_idx = content.find("\n---\n", 4)
        if end_idx == -1:
            return {}, "", content

        frontmatter_text = content[4:end_idx]
        body_text = content[end_idx + 5:]  # Skip "\n---\n"

        # Parse frontmatter into dict
        frontmatter_dict = {}
        for line in frontmatter_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]

                frontmatter_dict[key] = value

        return frontmatter_dict, frontmatter_text, body_text

    def update_frontmatter(
        self,
        file_path: Path,
        updates: Dict[str, str],
        dry_run: bool = False
    ) -> bool:
        """
        Update frontmatter fields in a gleaning file.

        Args:
            file_path: Path to gleaning file
            updates: Dict of field:value to update
            dry_run: If True, don't actually write changes

        Returns:
            True if file was updated, False otherwise
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter_dict, frontmatter_text, body_text = self.parse_frontmatter(content)

        # Apply updates
        changed = False
        for key, value in updates.items():
            if key not in frontmatter_dict or frontmatter_dict[key] != value:
                frontmatter_dict[key] = value
                changed = True

        if not changed:
            return False

        if dry_run:
            return True

        # Rebuild frontmatter
        new_frontmatter_lines = []
        for key, value in frontmatter_dict.items():
            # Special handling for github_topics (YAML list)
            if key == "github_topics" and value:
                # Value is JSON string, convert to YAML list
                try:
                    topics_list = json.loads(value) if isinstance(value, str) else value
                    if topics_list:
                        topics_yaml = json.dumps(topics_list)  # JSON list format works as YAML list
                        new_frontmatter_lines.append(f"{key}: {topics_yaml}")
                    else:
                        new_frontmatter_lines.append(f"{key}: []")
                except (json.JSONDecodeError, TypeError):
                    new_frontmatter_lines.append(f"{key}: {value}")
            # Quote values that need it
            elif key in ("title", "description", "reason", "github_readme_excerpt") and value:
                quoted_value = json.dumps(value)
                new_frontmatter_lines.append(f"{key}: {quoted_value}")
            else:
                new_frontmatter_lines.append(f"{key}: {value}")

        new_frontmatter_text = "\n".join(new_frontmatter_lines)
        new_content = f"---\n{new_frontmatter_text}\n---\n{body_text}"

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def maintain_gleaning(
        self,
        file_path: Path,
        check_links: bool = True,
        add_descriptions: bool = True,
        mark_dead_inactive: bool = True,
        enrich_github: bool = False,
        dry_run: bool = False
    ) -> Dict:
        """
        Maintain a single gleaning file.

        Returns:
            Dict with maintenance results
        """
        result = {
            "file": file_path.name,
            "checked": False,
            "alive": None,
            "description_added": False,
            "marked_inactive": False,
            "error": None
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter_dict, _, _ = self.parse_frontmatter(content)

            url = frontmatter_dict.get("url")
            if not url:
                result["error"] = "No URL in frontmatter"
                return result

            gleaning_id = frontmatter_dict.get("gleaning_id", file_path.stem)
            description = frontmatter_dict.get("description", "")
            title = frontmatter_dict.get("title", "Untitled")
            current_status = frontmatter_dict.get("status", "active")

            # Skip hidden gleanings entirely
            if current_status == "hidden":
                print(f"  Skipping (hidden): {title}")
                self.stats["skipped_hidden"] += 1
                return result

            updates = {}

            # Check if already inactive but missing reason
            status_record = self.status_manager.get_gleaning_record(gleaning_id)
            already_inactive = current_status == "inactive"
            has_reason = status_record and "reason" in status_record and status_record["reason"]

            # Check if URL is alive
            if check_links:
                # If already inactive but no reason, check link to add reason
                if already_inactive and not has_reason:
                    print(f"  Checking (backfill reason): {title}")
                else:
                    print(f"  Checking: {title}")

                is_alive, error_msg, status_code = self.check_url(url)
                result["checked"] = True
                result["alive"] = is_alive

                if is_alive:
                    print(f"    ✓ Link alive ({status_code})")
                    self.stats["alive"] += 1

                    # If was marked inactive but link is now alive, restore to active
                    if already_inactive:
                        reason_text = f"Link restored (was inactive, now alive as of check)"
                        updates["status"] = "active"
                        updates["reason"] = reason_text
                        if not dry_run:
                            self.status_manager.mark_status(
                                gleaning_id,
                                "active",
                                reason_text
                            )
                        self.stats["restored_active"] += 1
                        print(f"    → Restored to active (link came back)")

                    # Fetch description if missing
                    if add_descriptions and not description:
                        print(f"    Fetching meta description...")
                        meta_desc = self.fetch_meta_description(url)

                        if meta_desc:
                            updates["description"] = meta_desc
                            result["description_added"] = True
                            self.stats["descriptions_added"] += 1
                            print(f"    ✓ Added description ({len(meta_desc)} chars)")
                        else:
                            self.stats["descriptions_skipped"] += 1
                            print(f"    ✗ No meta description found")
                    elif description:
                        self.stats["descriptions_skipped"] += 1

                else:
                    print(f"    ✗ Link dead: {error_msg}")
                    self.stats["dead"] += 1

                    # Mark as inactive (or add reason if already inactive)
                    if mark_dead_inactive:
                        reason_text = f"Dead link: {error_msg}"
                        if not dry_run:
                            # Always update status file to ensure reason is captured
                            self.status_manager.mark_status(
                                gleaning_id,
                                "inactive",
                                reason_text
                            )

                        if not already_inactive:
                            updates["status"] = "inactive"
                            updates["reason"] = reason_text
                            result["marked_inactive"] = True
                            self.stats["marked_inactive"] += 1
                            print(f"    → Marked as inactive")
                        elif not has_reason:
                            updates["reason"] = reason_text
                            result["marked_inactive"] = True
                            self.stats["reasons_added"] += 1
                            print(f"    → Added reason to existing inactive gleaning")

            # GitHub enrichment
            if enrich_github and self.github_client:
                github_updates = self.enrich_github_gleaning(
                    file_path,
                    url,
                    frontmatter_dict,
                    dry_run=dry_run
                )
                updates.update(github_updates)

            # Apply updates
            if updates:
                if self.update_frontmatter(file_path, updates, dry_run=dry_run):
                    if dry_run:
                        print(f"    [DRY RUN] Would update: {', '.join(updates.keys())}")
                    else:
                        print(f"    ✓ Updated: {', '.join(updates.keys())}")

            return result

        except Exception as e:
            result["error"] = str(e)
            self.stats["errors"] += 1
            print(f"    ✗ Error: {e}")
            return result

    def maintain_all(
        self,
        check_links: bool = True,
        add_descriptions: bool = True,
        mark_dead_inactive: bool = True,
        enrich_github: bool = False,
        dry_run: bool = False,
        rate_limit: float = 1.0
    ):
        """
        Maintain all gleanings.

        Args:
            check_links: Check if URLs are alive
            add_descriptions: Fetch meta descriptions for missing ones
            mark_dead_inactive: Mark dead links as inactive
            dry_run: Preview changes without applying them
            rate_limit: Seconds to wait between requests (be nice to servers)
        """
        if not self.gleanings_dir.exists():
            print(f"Error: Gleanings directory not found: {self.gleanings_dir}")
            return

        gleaning_files = list(self.gleanings_dir.glob("*.md"))
        self.stats["total"] = len(gleaning_files)

        # Estimate time
        estimated_time = self.stats["total"] * rate_limit
        est_minutes = int(estimated_time / 60)
        est_seconds = int(estimated_time % 60)

        print(f"\nMaintaining {self.stats['total']} gleanings")
        print(f"Options:")
        print(f"  Check links: {check_links}")
        print(f"  Add descriptions: {add_descriptions}")
        print(f"  Mark dead inactive: {mark_dead_inactive}")
        print(f"  Enrich GitHub: {enrich_github}")
        print(f"  Dry run: {dry_run}")
        print(f"  Rate limit: {rate_limit}s between requests")
        if check_links or add_descriptions or enrich_github:
            print(f"  Estimated time: {est_minutes}m {est_seconds}s")
        print()

        start_time = time.time()

        for idx, file_path in enumerate(gleaning_files, 1):
            # Calculate progress and ETA
            progress_pct = (idx / self.stats["total"]) * 100
            elapsed = time.time() - start_time
            if idx > 1:
                avg_time_per_gleaning = elapsed / (idx - 1)
                remaining = (self.stats["total"] - idx) * avg_time_per_gleaning
                eta_min = int(remaining / 60)
                eta_sec = int(remaining % 60)
                eta_str = f" | ETA: {eta_min}m {eta_sec}s"
            else:
                eta_str = ""

            print(f"[{idx}/{self.stats['total']} - {progress_pct:.1f}%{eta_str}]")

            self.maintain_gleaning(
                file_path,
                check_links=check_links,
                add_descriptions=add_descriptions,
                mark_dead_inactive=mark_dead_inactive,
                enrich_github=enrich_github,
                dry_run=dry_run
            )

            self.stats["checked"] += 1

            # Rate limiting (be nice to servers)
            if check_links or add_descriptions:
                time.sleep(rate_limit)

        # Print summary
        print()
        print("=" * 60)
        print("Maintenance complete!")
        print(f"Total gleanings: {self.stats['total']}")
        print(f"Checked: {self.stats['checked']}")
        print(f"  Alive: {self.stats['alive']}")
        print(f"  Dead: {self.stats['dead']}")
        print(f"  Errors: {self.stats['errors']}")
        print(f"Descriptions added: {self.stats['descriptions_added']}")
        print(f"Descriptions skipped: {self.stats['descriptions_skipped']}")
        print(f"Marked inactive: {self.stats['marked_inactive']}")
        print(f"Restored to active: {self.stats['restored_active']}")
        print(f"Reasons added (backfill): {self.stats['reasons_added']}")
        print(f"Skipped (hidden): {self.stats['skipped_hidden']}")
        if enrich_github:
            print(f"GitHub enriched: {self.stats['github_enriched']}")
            print(f"GitHub skipped (already enriched): {self.stats['github_skipped']}")
            print(f"GitHub errors: {self.stats['github_errors']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Maintain gleanings (check links, add descriptions)")
    parser.add_argument(
        "--vault-path",
        type=Path,
        required=True,
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        default=True,
        help="Check if URLs are alive (default: true)"
    )
    parser.add_argument(
        "--no-check-links",
        dest="check_links",
        action="store_false",
        help="Skip link checking"
    )
    parser.add_argument(
        "--add-descriptions",
        action="store_true",
        default=True,
        help="Fetch meta descriptions for missing ones (default: true)"
    )
    parser.add_argument(
        "--no-add-descriptions",
        dest="add_descriptions",
        action="store_false",
        help="Skip adding descriptions"
    )
    parser.add_argument(
        "--mark-dead-inactive",
        action="store_true",
        default=True,
        help="Mark dead links as inactive (default: true)"
    )
    parser.add_argument(
        "--no-mark-dead-inactive",
        dest="mark_dead_inactive",
        action="store_false",
        help="Don't mark dead links as inactive"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="HTTP request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Seconds to wait between requests (default: 1.0)"
    )
    parser.add_argument(
        "--enrich-github",
        action="store_true",
        help="Enrich GitHub repos with API metadata (requires --github-token)"
    )
    parser.add_argument(
        "--github-token",
        help="GitHub API token (or set GITHUB_TOKEN environment variable)"
    )

    args = parser.parse_args()

    # Validate GitHub enrichment requirements
    if args.enrich_github and not args.github_token:
        import os
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            print("Error: --enrich-github requires --github-token or GITHUB_TOKEN environment variable", file=sys.stderr)
            return 1
        args.github_token = github_token

    try:
        maintainer = GleaningMaintainer(
            vault_path=args.vault_path,
            timeout=args.timeout,
            github_token=args.github_token if args.enrich_github else None
        )

        maintainer.maintain_all(
            check_links=args.check_links,
            add_descriptions=args.add_descriptions,
            mark_dead_inactive=args.mark_dead_inactive,
            enrich_github=args.enrich_github,
            dry_run=args.dry_run,
            rate_limit=args.rate_limit
        )

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
