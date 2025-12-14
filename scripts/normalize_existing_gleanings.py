#!/usr/bin/env python3
"""
Normalize existing gleaning files.

Updates title and description in frontmatter for GitHub URLs and other
domains that benefit from normalization.

Usage:
    python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/amoxtli [--dry-run]
"""

import argparse
import sys
from pathlib import Path

import frontmatter

# Add src to path so we can import normalizers
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from temoa.normalizers import NormalizerRegistry


def normalize_gleanings(vault_path: Path, dry_run: bool = False):
    """Normalize existing gleaning files."""

    gleanings_dir = vault_path / "L" / "Gleanings"
    if not gleanings_dir.exists():
        print(f"Error: {gleanings_dir} does not exist")
        return

    registry = NormalizerRegistry()

    stats = {
        "total": 0,
        "normalized": 0,
        "unchanged": 0,
        "errors": 0,
    }

    for gleaning_file in sorted(gleanings_dir.glob("*.md")):
        stats["total"] += 1

        try:
            # Read frontmatter
            post = frontmatter.load(gleaning_file)

            url = post.metadata.get("url")
            old_title = post.metadata.get("title")
            old_desc = post.metadata.get("description", "")

            if not url:
                print(f"Warning: No URL: {gleaning_file.name}")
                stats["unchanged"] += 1
                continue

            # Normalize
            new_title, new_desc = registry.normalize(url, old_title, old_desc)

            # Check if changed
            if new_title == old_title and new_desc == old_desc:
                stats["unchanged"] += 1
                continue

            # Show changes
            changed = []
            if new_title != old_title:
                changed.append("title")
                print(f"\n{gleaning_file.name}")
                print(f"  Title: {old_title}")
                print(f"      -> {new_title}")

            if new_desc != old_desc:
                changed.append("desc")
                if not changed or changed[0] != "title":
                    print(f"\n{gleaning_file.name}")
                print(f"  Desc: {old_desc[:60]}...")
                print(f"     -> {new_desc[:60]}...")

            stats["normalized"] += 1

            if not dry_run:
                # Update frontmatter
                post.metadata["title"] = new_title
                post.metadata["description"] = new_desc

                # Write back
                with open(gleaning_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(post))

        except Exception as e:
            print(f"\nError processing {gleaning_file.name}: {e}")
            stats["errors"] += 1

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total: {stats['total']}")
    print(f"  Normalized: {stats['normalized']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors: {stats['errors']}")

    if dry_run:
        print("\nDRY RUN - No files were modified")


def main():
    parser = argparse.ArgumentParser(
        description="Normalize existing gleaning files"
    )
    parser.add_argument(
        "--vault-path",
        type=Path,
        required=True,
        help="Path to vault"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )

    args = parser.parse_args()
    
    vault_path = Path(args.vault_path).expanduser()
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    normalize_gleanings(vault_path, args.dry_run)


if __name__ == "__main__":
    main()
