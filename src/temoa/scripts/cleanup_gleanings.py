"""
Clean up gleanings: remove problematic unicode and fix YAML formatting.

This script:
1. Removes emojis, zero-width chars, RTL marks from all text fields
2. Normalizes smart quotes and dashes to ASCII
3. Converts JSON topic arrays to proper YAML lists
4. Cleans text in markdown body (headings, links)

Usage:
    # Dry run (preview changes)
    python cleanup_gleanings.py --vault-path ~/Obsidian/amoxtli --dry-run

    # Run cleanup
    python cleanup_gleanings.py --vault-path ~/Obsidian/amoxtli

    # Clean specific files only
    python cleanup_gleanings.py --vault-path ~/Obsidian/amoxtli --files file1.md file2.md
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from text_cleaner import clean_text


class GleaningCleaner:
    """Clean gleanings to remove problematic unicode and fix YAML."""

    def __init__(self, vault_path: Path, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.gleanings_dir = self.vault_path / "L" / "Gleanings"
        self.dry_run = dry_run
        self.stats = {
            "processed": 0,
            "modified": 0,
            "text_cleaned": 0,
            "topics_fixed": 0,
            "body_cleaned": 0,
            "errors": 0
        }

    def parse_frontmatter(self, content: str) -> Tuple[Dict, str, str]:
        """
        Parse frontmatter from markdown content.

        Args:
            content: File content

        Returns:
            Tuple of (frontmatter_dict, frontmatter_text, body_text)
        """
        # Check if file starts with frontmatter
        if not content.startswith("---\n"):
            return {}, "", content

        # Find end of frontmatter
        parts = content.split("---\n", 2)
        if len(parts) < 3:
            return {}, "", content

        frontmatter_text = parts[1]
        body = parts[2]

        # Parse YAML
        try:
            frontmatter_dict = yaml.safe_load(frontmatter_text)
            if frontmatter_dict is None:
                frontmatter_dict = {}
        except yaml.YAMLError as e:
            print(f"Warning: YAML parse error: {e}")
            return {}, frontmatter_text, body

        return frontmatter_dict, frontmatter_text, body

    def clean_frontmatter_text_fields(self, fm: Dict) -> Tuple[Dict, bool]:
        """
        Clean text fields in frontmatter.

        Args:
            fm: Frontmatter dictionary

        Returns:
            Tuple of (cleaned_frontmatter, was_modified)
        """
        modified = False
        text_fields = ["title", "description", "github_description", "github_readme_excerpt"]

        for field in text_fields:
            if field in fm and isinstance(fm[field], str):
                original = fm[field]
                cleaned = clean_text(original)
                if cleaned != original:
                    fm[field] = cleaned
                    modified = True

        return fm, modified

    def fix_github_topics(self, fm: Dict, fm_text: str) -> Tuple[Dict, bool]:
        """
        Convert JSON topic arrays to proper YAML lists.

        Converts:
            github_topics: ["topic1", "topic2"]
        To:
            github_topics:
              - topic1
              - topic2

        Args:
            fm: Frontmatter dictionary
            fm_text: Original frontmatter text (to check format)

        Returns:
            Tuple of (fixed_frontmatter, was_modified)
        """
        if "github_topics" not in fm:
            return fm, False

        # Check if original frontmatter has JSON-style topics (flow style with brackets)
        has_json_format = re.search(r'github_topics:\s*\[', fm_text)

        topics = fm["github_topics"]

        # If it's in JSON format in the source, mark as needing fix
        # (YAML will rewrite it in block style)
        if has_json_format and isinstance(topics, list):
            return fm, True

        # Check if it's a JSON string (shouldn't happen, but handle it)
        if isinstance(topics, str):
            try:
                # Try to parse as JSON
                topics_list = json.loads(topics)
                if isinstance(topics_list, list):
                    fm["github_topics"] = topics_list
                    return fm, True
            except json.JSONDecodeError:
                pass

        # Already a list, check if topics need text cleaning
        if isinstance(topics, list):
            # Clean each topic string
            modified = False
            cleaned_topics = []
            for topic in topics:
                if isinstance(topic, str):
                    cleaned = clean_text(topic)
                    cleaned_topics.append(cleaned)
                    if cleaned != topic:
                        modified = True
                else:
                    cleaned_topics.append(topic)

            if modified:
                fm["github_topics"] = cleaned_topics
                return fm, True

        return fm, False

    def clean_body_text(self, body: str) -> Tuple[str, bool]:
        """
        Clean text in markdown body.

        Cleans:
        - Headings (# text)
        - Link text ([text](url))

        Args:
            body: Markdown body text

        Returns:
            Tuple of (cleaned_body, was_modified)
        """
        original = body
        modified = False

        # Clean headings
        def clean_heading(match):
            nonlocal modified
            prefix = match.group(1)
            heading_text = match.group(2)
            cleaned = clean_text(heading_text)
            if cleaned != heading_text:
                modified = True
            return f"{prefix}{cleaned}"

        body = re.sub(r'^(#{1,6}\s+)(.+)$', clean_heading, body, flags=re.MULTILINE)

        # Clean link text
        def clean_link(match):
            nonlocal modified
            link_text = match.group(1)
            url = match.group(2)
            cleaned = clean_text(link_text)
            if cleaned != link_text:
                modified = True
            return f"[{cleaned}]({url})"

        body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', clean_link, body)

        return body, modified

    def clean_file(self, file_path: Path) -> bool:
        """
        Clean a single gleaning file.

        Args:
            file_path: Path to gleaning file

        Returns:
            True if file was modified, False otherwise
        """
        try:
            # Read file
            content = file_path.read_text(encoding='utf-8')

            # Parse frontmatter and body
            fm_dict, fm_text, body = self.parse_frontmatter(content)

            if not fm_dict:
                print(f"  Warning: No frontmatter found in {file_path.name}")
                return False

            # Track if anything changed
            file_modified = False

            # Clean text fields
            fm_dict, text_modified = self.clean_frontmatter_text_fields(fm_dict)
            if text_modified:
                file_modified = True
                self.stats["text_cleaned"] += 1

            # Fix github_topics format
            fm_dict, topics_modified = self.fix_github_topics(fm_dict, fm_text)
            if topics_modified:
                file_modified = True
                self.stats["topics_fixed"] += 1

            # Clean body text
            body, body_modified = self.clean_body_text(body)
            if body_modified:
                file_modified = True
                self.stats["body_cleaned"] += 1

            # Write back if modified
            if file_modified:
                if not self.dry_run:
                    # Serialize frontmatter properly
                    new_fm_text = yaml.dump(fm_dict,
                                           default_flow_style=False,
                                           allow_unicode=True,
                                           sort_keys=False)
                    new_content = f"---\n{new_fm_text}---\n{body}"
                    file_path.write_text(new_content, encoding='utf-8')

                self.stats["modified"] += 1
                return True

            return False

        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            self.stats["errors"] += 1
            return False

    def run(self, file_list: List[str] = None):
        """
        Run cleanup on gleanings.

        Args:
            file_list: Optional list of specific files to clean
        """
        if not self.gleanings_dir.exists():
            print(f"Error: Gleanings directory not found: {self.gleanings_dir}")
            return

        # Get files to process
        if file_list:
            files = [self.gleanings_dir / f for f in file_list]
        else:
            files = sorted(self.gleanings_dir.glob("*.md"))

        total = len(files)
        print(f"Processing {total} gleanings...")
        print(f"Dry run: {self.dry_run}")
        print()

        # Process files
        for i, file_path in enumerate(files, 1):
            self.stats["processed"] += 1

            modified = self.clean_file(file_path)

            # Show progress every 50 files
            if i % 50 == 0:
                print(f"  [{i}/{total}] Processed {i} files, {self.stats['modified']} modified")

            # Show modified files
            if modified:
                print(f"  ✓ Modified: {file_path.name}")

        # Final stats
        print()
        print("=" * 60)
        print("Cleanup complete!")
        print(f"Processed: {self.stats['processed']}")
        print(f"Modified: {self.stats['modified']}")
        print(f"  Text cleaned: {self.stats['text_cleaned']}")
        print(f"  Topics fixed: {self.stats['topics_fixed']}")
        print(f"  Body cleaned: {self.stats['body_cleaned']}")
        print(f"Errors: {self.stats['errors']}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Clean up gleanings: remove problematic unicode and fix YAML"
    )
    parser.add_argument(
        "--vault-path",
        type=str,
        required=True,
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific files to clean (filenames only, e.g., abc123.md)"
    )

    args = parser.parse_args()

    cleaner = GleaningCleaner(
        vault_path=Path(args.vault_path),
        dry_run=args.dry_run
    )

    cleaner.run(file_list=args.files)


if __name__ == "__main__":
    main()
