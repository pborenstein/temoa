#!/usr/bin/env python3
"""
Add type: daily to all daily notes in Daily/ directory.

This script updates all daily note files to include 'type: daily' in their
frontmatter, ensuring they can be filtered using the new type filtering feature.

Usage:
    uv run scripts/add_type_to_daily_notes.py [--vault-path PATH] [--dry-run]
"""

import sys
from pathlib import Path
import frontmatter
import click


@click.command()
@click.option(
    "--vault-path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to vault (default: from config)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be changed without making changes",
)
def main(vault_path: Path | None, dry_run: bool):
    """Add type: daily to all daily notes."""

    # Load vault path from config if not provided
    if vault_path is None:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from temoa.config import Config
        config = Config()
        vault_path = config.vault_path

    vault_path = Path(vault_path)
    daily_dir = vault_path / "Daily"

    if not daily_dir.exists():
        click.echo(f"Error: Daily directory not found at {daily_dir}", err=True)
        sys.exit(1)

    click.echo(f"Scanning daily notes in: {daily_dir}")
    if dry_run:
        click.echo(click.style("DRY RUN MODE - No changes will be made", fg="yellow", bold=True))

    # Find all markdown files in Daily/
    md_files = list(daily_dir.glob("*.md"))
    click.echo(f"Found {len(md_files)} markdown files in Daily/")

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for md_file in md_files:
        try:
            # Read the file with frontmatter
            with open(md_file, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Check if type field already exists
            if "type" in post.metadata:
                existing_type = post.metadata["type"]

                # If it's already "daily", skip
                if existing_type == "daily":
                    skipped_count += 1
                    continue

                # If it's something else, show warning
                click.echo(
                    f"  {click.style('WARN', fg='yellow')}: {md_file.name} "
                    f"already has type: {existing_type} - skipping"
                )
                skipped_count += 1
                continue

            # Add type: daily
            post.metadata["type"] = "daily"

            if dry_run:
                click.echo(f"  {click.style('WOULD UPDATE', fg='blue')}: {md_file.name}")
                updated_count += 1
            else:
                # Write back to file
                with open(md_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(post))

                click.echo(f"  {click.style('UPDATED', fg='green')}: {md_file.name}")
                updated_count += 1

        except Exception as e:
            click.echo(
                f"  {click.style('ERROR', fg='red')}: {md_file.name} - {e}",
                err=True
            )
            error_count += 1

    # Summary
    click.echo()
    click.echo("Summary:")
    click.echo(f"  Updated: {updated_count}")
    click.echo(f"  Skipped: {skipped_count}")
    if error_count > 0:
        click.echo(f"  {click.style(f'Errors: {error_count}', fg='red')}")

    if dry_run and updated_count > 0:
        click.echo()
        click.echo("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
