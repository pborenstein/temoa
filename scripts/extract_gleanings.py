#!/usr/bin/env python3
"""
Gleanings Extraction Script

Extracts gleanings from daily notes and creates individual notes in L/Gleanings/.

Usage:
    python scripts/extract_gleanings.py --vault-path /path/to/vault [--dry-run]
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Add src to path so we can import gleanings module
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from temoa.gleanings import GleaningStatusManager, GleaningStatus


class Gleaning:
    """Represents a single gleaning."""

    def __init__(
        self,
        title: str,
        url: str,
        description: str,
        date: str,
        source_file: str,
        gleaning_id: Optional[str] = None,
        status: GleaningStatus = "active",
        reason: Optional[str] = None
    ):
        self.title = title
        self.url = url
        self.description = description
        self.date = date
        self.source_file = source_file
        self.domain = urlparse(url).netloc
        self.gleaning_id = gleaning_id or self._generate_id()
        self.status = status
        self.reason = reason

    def _generate_id(self) -> str:
        """Generate unique ID from URL."""
        return hashlib.md5(self.url.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.gleaning_id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "date": self.date,
            "domain": self.domain,
            "source_file": self.source_file,
            "extracted_at": datetime.now().isoformat()
        }

    def to_markdown(self) -> str:
        """Convert to markdown note format."""
        # Quote title for YAML safety (handles colons, quotes, etc.)
        quoted_title = json.dumps(self.title)

        # Quote description for YAML safety
        quoted_description = json.dumps(self.description) if self.description else '""'

        # Quote reason for YAML safety
        quoted_reason = json.dumps(self.reason) if self.reason else '""'

        # Build frontmatter
        frontmatter_lines = [
            f"title: {quoted_title}",
            f"url: {self.url}",
            f"domain: {self.domain}",
            f"created: {self.date}",
            f"source: {self.source_file}",
            f"gleaning_id: {self.gleaning_id}",
            f"status: {self.status}",
            f"type: gleaning",
            f"description: {quoted_description}"
        ]

        # Add reason only if inactive
        if self.status == "inactive" and self.reason:
            frontmatter_lines.append(f"reason: {quoted_reason}")

        frontmatter = "\n".join(frontmatter_lines)

        return f"""---
{frontmatter}
---

# {self.title}

{self.description}

## Link

[{self.title}]({self.url})

## Source

Gleaned from [[{Path(self.source_file).stem}]] on {self.date}
"""


class GleaningsExtractor:
    """Extracts gleanings from daily notes."""

    # Regex to match gleanings: - [Title](URL)  [HH:MM]
    # Format: - [Title](URL) optionally followed by timestamp
    # Description may be on next line starting with >
    GLEANING_LINK_PATTERN = re.compile(
        r'^-\s+\[([^\]]+)\]\(([^)]+)\)',
        re.MULTILINE
    )

    # Regex to find Gleanings section
    SECTION_PATTERN = re.compile(
        r'^##\s+Gleanings\s*$',
        re.MULTILINE
    )

    def __init__(self, vault_path: Path, state_file: Optional[Path] = None):
        self.vault_path = Path(vault_path).expanduser()

        # Validate vault path exists
        if not self.vault_path.exists():
            raise FileNotFoundError(
                f"Vault path does not exist: {self.vault_path}\n"
                f"Please check the path and try again."
            )

        if not self.vault_path.is_dir():
            raise NotADirectoryError(
                f"Vault path is not a directory: {self.vault_path}"
            )

        self.state_file = state_file or (self.vault_path / ".temoa" / "extraction_state.json")
        self.state = self._load_state()

        # Initialize status manager
        self.status_manager = GleaningStatusManager(self.vault_path / ".temoa")

    def _load_state(self) -> Dict:
        """Load extraction state."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "extracted_gleanings": {},
            "processed_files": []
        }

    def _save_state(self):
        """Save extraction state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_run"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def find_daily_notes(self, incremental: bool = True) -> List[Path]:
        """Find daily notes to process."""
        daily_notes = []

        # Search for daily notes (common patterns)
        patterns = [
            "Daily/**/*.md",
            "Journal/**/*.md",
            "daily/**/*.md",
            "journal/**/*.md"
        ]

        for pattern in patterns:
            for note in self.vault_path.glob(pattern):
                # Skip if already processed in incremental mode
                if incremental and str(note.relative_to(self.vault_path)) in self.state["processed_files"]:
                    continue
                daily_notes.append(note)

        return daily_notes

    def extract_from_note(self, note_path: Path) -> List[Gleaning]:
        """Extract gleanings from a single note."""
        gleanings = []

        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Gleanings section
        section_match = self.SECTION_PATTERN.search(content)
        if not section_match:
            return gleanings

        # Extract section after "## Gleanings"
        section_start = section_match.end()

        # Find next section (## Something) or end of file
        next_section = re.search(r'^##\s+', content[section_start:], re.MULTILINE)
        if next_section:
            section_end = section_start + next_section.start()
            section_content = content[section_start:section_end]
        else:
            section_content = content[section_start:]

        # Extract date from frontmatter or filename
        date = self._extract_date(note_path, content)

        # Split section into lines for easier processing
        lines = section_content.split('\n')

        # Find all gleanings in section
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.GLEANING_LINK_PATTERN.match(line)

            if match:
                title = match.group(1).strip()
                url = match.group(2).strip()

                # Check next line for description (starts with >)
                description = ""
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('>'):
                    # Extract description, removing leading > and whitespace
                    description = lines[i + 1].strip()[1:].strip()

                # Generate ID to check status and reason
                gleaning_id = hashlib.md5(url.encode()).hexdigest()[:12]
                status = self.status_manager.get_status(gleaning_id)

                # Get reason from status record if exists
                reason = None
                status_record = self.status_manager.get_gleaning_record(gleaning_id)
                if status_record and "reason" in status_record:
                    reason = status_record["reason"]

                gleaning = Gleaning(
                    title=title,
                    url=url,
                    description=description,
                    date=date,
                    source_file=str(note_path.relative_to(self.vault_path)),
                    gleaning_id=gleaning_id,
                    status=status,
                    reason=reason
                )

                gleanings.append(gleaning)

            i += 1

        return gleanings

    def _extract_date(self, note_path: Path, content: str) -> str:
        """Extract date from frontmatter or filename."""
        # Try frontmatter first
        frontmatter_match = re.search(r'^date:\s*(\d{4}-\d{2}-\d{2})', content, re.MULTILINE)
        if frontmatter_match:
            return frontmatter_match.group(1)

        # Try filename (YYYY-MM-DD pattern)
        filename_match = re.search(r'(\d{4}-\d{2}-\d{2})', note_path.stem)
        if filename_match:
            return filename_match.group(1)

        # Fallback to file modification time
        mtime = datetime.fromtimestamp(note_path.stat().st_mtime)
        return mtime.strftime('%Y-%m-%d')

    def create_gleaning_note(self, gleaning: Gleaning, output_dir: Path, dry_run: bool = False):
        """Create individual gleaning note."""
        output_file = output_dir / f"{gleaning.gleaning_id}.md"

        if dry_run:
            print(f"[DRY RUN] Would create: {output_file.relative_to(self.vault_path)}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(gleaning.to_markdown())

        print(f"Created: {output_file.relative_to(self.vault_path)}")

    def extract_all(self, incremental: bool = True, dry_run: bool = False):
        """Extract all gleanings from daily notes."""
        output_dir = self.vault_path / "L" / "Gleanings"

        # In full mode, clear existing state to start fresh
        if not incremental and not dry_run:
            print("Full mode: Clearing existing extraction state")
            self.state = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_run": None,
                "extracted_gleanings": {},
                "processed_files": []
            }
            print()

        print(f"Vault path: {self.vault_path}")
        print(f"Output directory: {output_dir.relative_to(self.vault_path)}")
        print(f"Mode: {'Incremental' if incremental else 'Full (starting fresh)'}")
        print(f"Dry run: {dry_run}")
        print()

        # Find notes to process
        daily_notes = self.find_daily_notes(incremental=incremental)
        print(f"Found {len(daily_notes)} daily notes to process")
        print()

        total_gleanings = 0
        new_gleanings = 0
        duplicate_gleanings = 0

        for note_path in daily_notes:
            gleanings = self.extract_from_note(note_path)

            if gleanings:
                print(f"Processing: {note_path.relative_to(self.vault_path)} ({len(gleanings)} gleanings)")

            for gleaning in gleanings:
                total_gleanings += 1

                # Check for duplicates (only in incremental mode or dry-run)
                if gleaning.gleaning_id in self.state["extracted_gleanings"]:
                    duplicate_gleanings += 1
                    print(f"  - DUPLICATE: {gleaning.title[:60]}... (ID: {gleaning.gleaning_id})")
                    continue

                # Create gleaning note
                self.create_gleaning_note(gleaning, output_dir, dry_run=dry_run)
                new_gleanings += 1

                # Update state
                if not dry_run:
                    self.state["extracted_gleanings"][gleaning.gleaning_id] = gleaning.to_dict()

            # Mark file as processed
            if not dry_run:
                rel_path = str(note_path.relative_to(self.vault_path))
                if rel_path not in self.state["processed_files"]:
                    self.state["processed_files"].append(rel_path)

        # Save state
        if not dry_run:
            self._save_state()

        # Summary
        print()
        print("=" * 60)
        print(f"Extraction {'preview' if dry_run else 'complete'}!")
        print(f"Total gleanings found: {total_gleanings}")
        print(f"New gleanings {'would be created' if dry_run else 'created'}: {new_gleanings}")
        print(f"Duplicates skipped: {duplicate_gleanings}")
        print(f"Files processed: {len(daily_notes)}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Extract gleanings from daily notes")
    parser.add_argument(
        "--vault-path",
        type=Path,
        required=True,
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Process all files (not just new ones)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be extracted without creating files"
    )

    args = parser.parse_args()

    try:
        extractor = GleaningsExtractor(args.vault_path)
        extractor.extract_all(incremental=not args.full, dry_run=args.dry_run)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=__import__('sys').stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=__import__('sys').stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
