#!/usr/bin/env python3
"""
Historical Gleanings Migration Script

Migrates gleanings from old-gleanings/gleanings_state.json to new L/Gleanings/ format.

Usage:
    python scripts/migrate_old_gleanings.py --vault-path /path/to/vault --old-gleanings /path/to/gleanings_state.json [--dry-run]
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


class OldGleaningMigrator:
    """Migrates gleanings from old format to new format."""

    def __init__(self, vault_path: Path, old_gleanings_file: Path):
        self.vault_path = Path(vault_path)
        self.old_gleanings_file = Path(old_gleanings_file)
        self.state_file = self.vault_path / ".temoa" / "extraction_state.json"
        self.state = self._load_state()

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

    def load_old_gleanings(self) -> Dict:
        """Load old gleanings from JSON file."""
        with open(self.old_gleanings_file, 'r') as f:
            data = json.load(f)
        return data.get("gleanings", {})

    def convert_to_markdown(self, gleaning_id: str, gleaning: Dict) -> str:
        """Convert old gleaning format to new markdown format."""
        title = gleaning.get("title", "Untitled")
        url = gleaning.get("url", "")
        description = gleaning.get("description", "")
        date = gleaning.get("date", "")
        domain = gleaning.get("domain", "")
        tags = gleaning.get("tags", [])
        category = gleaning.get("category", "")
        timestamp = gleaning.get("timestamp", "")

        # Build frontmatter
        frontmatter = f"""---
url: {url}
domain: {domain}
date: {date}
gleaning_id: {gleaning_id}
tags: [gleaning{', ' + ', '.join(tags) if tags else ''}]
"""
        if category:
            frontmatter += f"category: {category}\n"
        if timestamp:
            frontmatter += f"timestamp: {timestamp}\n"

        frontmatter += "migrated_from: old-gleanings\n---\n"

        # Build content
        content = f"""
# {title}

{description if description else '(No description)'}

## Link

[{title}]({url})
"""

        if category:
            content += f"\n## Category\n\n{category}\n"

        if tags:
            content += f"\n## Tags\n\n{', '.join(tags)}\n"

        content += f"""
## Metadata

- **Date**: {date}
- **Time**: {timestamp if timestamp else 'N/A'}
- **Domain**: {domain}
- **Original ID**: `{gleaning_id}`
- **Migrated**: {datetime.now().strftime('%Y-%m-%d')}
"""

        return frontmatter + content

    def migrate_all(self, dry_run: bool = False):
        """Migrate all old gleanings to new format."""
        output_dir = self.vault_path / "L" / "Gleanings"

        print(f"Old gleanings file: {self.old_gleanings_file}")
        print(f"Vault path: {self.vault_path}")
        print(f"Output directory: {output_dir.relative_to(self.vault_path) if output_dir.is_relative_to(self.vault_path) else output_dir}")
        print(f"Dry run: {dry_run}")
        print()

        # Load old gleanings
        old_gleanings = self.load_old_gleanings()
        print(f"Found {len(old_gleanings)} gleanings in old format")
        print()

        migrated = 0
        skipped_duplicates = 0
        errors = 0

        for gleaning_id, gleaning in old_gleanings.items():
            try:
                # Check if already migrated
                if gleaning_id in self.state["extracted_gleanings"]:
                    skipped_duplicates += 1
                    continue

                # Convert to markdown
                markdown_content = self.convert_to_markdown(gleaning_id, gleaning)

                # Create file
                output_file = output_dir / f"{gleaning_id}.md"

                if dry_run:
                    if migrated < 5:  # Show first 5 as preview
                        print(f"[DRY RUN] Would create: {output_file.relative_to(self.vault_path) if output_file.is_relative_to(self.vault_path) else output_file.name}")
                        print(f"  Title: {gleaning.get('title', 'Untitled')[:60]}...")
                        print(f"  Date: {gleaning.get('date', 'N/A')}")
                        print()
                else:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)

                    # Update state
                    self.state["extracted_gleanings"][gleaning_id] = {
                        "id": gleaning_id,
                        "title": gleaning.get("title", ""),
                        "url": gleaning.get("url", ""),
                        "description": gleaning.get("description", ""),
                        "date": gleaning.get("date", ""),
                        "domain": gleaning.get("domain", ""),
                        "source_file": "old-gleanings",
                        "extracted_at": datetime.now().isoformat(),
                        "migrated": True
                    }

                    if (migrated + 1) % 50 == 0:
                        print(f"Migrated {migrated + 1} gleanings...")

                migrated += 1

            except Exception as e:
                print(f"ERROR migrating {gleaning_id}: {e}")
                errors += 1

        # Save state
        if not dry_run:
            self._save_state()

        # Summary
        print()
        print("=" * 60)
        print(f"Migration {'preview' if dry_run else 'complete'}!")
        print(f"Gleanings {'would be migrated' if dry_run else 'migrated'}: {migrated}")
        print(f"Duplicates skipped: {skipped_duplicates}")
        print(f"Errors: {errors}")
        print(f"Total in old format: {len(old_gleanings)}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Migrate old gleanings to new format")
    parser.add_argument(
        "--vault-path",
        type=Path,
        required=True,
        help="Path to Obsidian vault"
    )
    parser.add_argument(
        "--old-gleanings",
        type=Path,
        required=True,
        help="Path to old gleanings_state.json file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be migrated without creating files"
    )

    args = parser.parse_args()

    migrator = OldGleaningMigrator(args.vault_path, args.old_gleanings)
    migrator.migrate_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
