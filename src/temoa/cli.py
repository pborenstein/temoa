#!/usr/bin/env python3
"""
Temoa CLI - Command-line interface for Temoa semantic search server
"""
import json
import sys
from pathlib import Path
import click
import uvicorn


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Temoa - Local semantic search server for Obsidian vault.

    \b
    Quick Start:
      temoa index               # Build index (first time setup)
      temoa server              # Start the FastAPI server
      temoa search "query"      # Quick search from CLI
      temoa stats               # Show vault statistics

    \b
    Common Workflows:
      # First time setup
      temoa config              # Check configuration
      temoa index               # Build embedding index

      # Start server for mobile access
      temoa server

      # Extract new gleanings and update index
      temoa extract
      temoa reindex

      # Quick search from terminal
      temoa search "semantic search"
      temoa archaeology "tailscale"
    """
    pass


@main.command()
@click.option('--host', default=None, help='Server host (default: from config)')
@click.option('--port', default=None, type=int, help='Server port (default: from config)')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--log-level', default='info',
              type=click.Choice(['critical', 'error', 'warning', 'info', 'debug']),
              help='Logging level')
def server(host, port, reload, log_level):
    """Start the Temoa FastAPI server.

    This starts the HTTP server that provides the search API and web UI.
    The server will be accessible via http://HOST:PORT (default: 0.0.0.0:8080)

    Use Tailscale to access from mobile devices.
    """
    from .config import Config

    config = Config()

    # Override config with CLI options if provided
    server_host = host or config.server_host
    server_port = port or config.server_port

    click.echo(f"Starting Temoa server on {server_host}:{server_port}")
    click.echo(f"Web UI: http://{server_host}:{server_port}/")
    click.echo(f"API docs: http://{server_host}:{server_port}/docs")
    click.echo("")

    uvicorn.run(
        "temoa.server:app",
        host=server_host,
        port=server_port,
        reload=reload,
        log_level=log_level
    )


@main.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, type=int, help='Number of results (default: 10)')
@click.option('--model', '-m', default=None, help='Embedding model to use')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def search(query, limit, model, output_json):
    """Search the vault for similar content.

    \b
    Examples:
      temoa search "semantic search"
      temoa search "tailscale networking" --limit 5
      temoa search "AI tools" --json
    """
    from .config import Config
    from .synthesis import SynthesisClient

    config = Config()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=config.vault_path,
            model=model or config.default_model,
            storage_dir=config.storage_dir
        )

        result_data = client.search(query, limit=limit)
        results = result_data.get('results', [])

        if output_json:
            # Output as JSON for scripting
            click.echo(json.dumps(result_data, indent=2))
        else:
            # Human-readable output
            click.echo(f"\nSearch results for: {click.style(query, fg='cyan', bold=True)}\n")

            if not results:
                click.echo("No results found.")
                return

            for i, result in enumerate(results, 1):
                click.echo(f"{i}. {click.style(result.get('title', 'Untitled'), fg='green', bold=True)}")
                click.echo(f"   {result.get('relative_path', 'Unknown path')}")
                click.echo(f"   Similarity: {result.get('similarity_score', 0):.3f}")

                # Show description/snippet if available
                if result.get('description'):
                    desc = result['description'].strip()
                    click.echo(f"   {click.style(desc, dim=True)}")

                if result.get('tags'):
                    # Convert all tags to strings in case some are integers
                    tags_str = ', '.join(str(tag) for tag in result['tags'])
                    click.echo(f"   Tags: {tags_str}")
                click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('topic')
@click.option('--limit', '-n', default=20, type=int, help='Number of results (default: 20)')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def archaeology(topic, limit, output_json):
    """Analyze temporal patterns of interest in a topic.

    Shows when you were interested in a topic over time.

    \b
    Examples:
      temoa archaeology "machine learning"
      temoa archaeology "tailscale" --json
    """
    from .config import Config
    from .synthesis import SynthesisClient

    config = Config()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=config.vault_path,
            model=config.default_model,
            storage_dir=config.storage_dir
        )

        analysis = client.archaeology(topic, top_k=limit)

        if output_json:
            click.echo(json.dumps(analysis, indent=2))
        else:
            click.echo(f"\nTemporal analysis for: {click.style(topic, fg='cyan', bold=True)}\n")

            if 'results' in analysis and analysis['results']:
                click.echo(f"Found {len(analysis['results'])} relevant documents")

                if 'periods' in analysis:
                    click.echo(f"\nActive periods:")
                    for period in analysis['periods']:
                        click.echo(f"  • {period}")

                click.echo(f"\nTop results:")
                for i, result in enumerate(analysis['results'][:10], 1):
                    click.echo(f"{i}. {result['title']}")
                    click.echo(f"   Date: {result.get('date', 'Unknown')}")
                    click.echo(f"   Similarity: {result['similarity_score']:.3f}")
                    click.echo()
            else:
                click.echo("No results found.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def stats(output_json):
    """Show vault statistics.

    Displays information about indexed files, embeddings, and models.
    """
    from .config import Config
    from .synthesis import SynthesisClient

    config = Config()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=config.vault_path,
            model=config.default_model,
            storage_dir=config.storage_dir
        )

        statistics = client.get_stats()

        if output_json:
            click.echo(json.dumps(statistics, indent=2))
        else:
            click.echo("\nVault Statistics\n")
            click.echo(f"Vault path: {click.style(str(config.vault_path), fg='cyan')}")
            click.echo(f"Storage: {click.style(str(config.storage_dir), fg='cyan')}")

            # Check if embeddings exist
            total_files = statistics.get('total_files', 0)
            total_embeddings = statistics.get('num_embeddings', 0)  # Synthesis uses 'num_embeddings'
            has_error = 'error' in statistics

            if has_error or total_files == 0:
                click.echo(f"\n{click.style('⚠ No index found', fg='yellow', bold=True)}")
                click.echo("Run 'temoa index' to build the embedding index for your vault.")
            elif total_embeddings == 0 and total_files > 0:
                click.echo(f"\n{click.style('⚠ Index incomplete', fg='yellow', bold=True)}")
                click.echo(f"Files scanned: {click.style(str(total_files), fg='yellow')}")
                click.echo(f"Embeddings generated: {click.style('0', fg='red')}")
                click.echo("\nRun 'temoa index' to generate embeddings for your vault.")
            else:
                model_name = statistics.get('model_info', {}).get('model_name', 'Unknown')
                click.echo(f"Model: {click.style(model_name, fg='green')}")
                click.echo(f"Files indexed: {click.style(str(total_files), fg='yellow')}")
                click.echo(f"Embeddings: {click.style(str(total_embeddings), fg='green')}")

                # Show additional stats if available
                if 'avg_content_length' in statistics:
                    click.echo(f"Avg content length: {statistics['avg_content_length']:.0f} chars")
                if 'total_tags' in statistics:
                    click.echo(f"Total tags: {statistics['total_tags']}")
                if 'directories' in statistics:
                    click.echo(f"Directories: {statistics['directories']}")

            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
@click.option('--full', is_flag=True, help='Process all files (ignore state tracking)')
@click.option('--dry-run', is_flag=True, help='Show what would be extracted without writing files')
def extract(vault, full, dry_run):
    """Extract gleanings from daily notes.

    Parses daily notes looking for ## Gleanings sections and extracts
    individual gleaning entries to separate markdown files in L/Gleanings/.

    Uses incremental extraction by default (only processes new files).
    Use --full to re-process all files.
    """
    from .config import Config
    import subprocess

    config = Config()
    vault_path = Path(vault) if vault else config.vault_path

    # Build command for extraction script
    script = Path(__file__).parent.parent.parent / "scripts" / "extract_gleanings.py"

    cmd = [
        sys.executable,
        str(script),
        "--vault-path", str(vault_path)
    ]

    if full:
        cmd.append("--full")
    if dry_run:
        cmd.append("--dry-run")

    click.echo(f"Extracting gleanings from: {vault_path}")
    if dry_run:
        click.echo(click.style("DRY RUN - No files will be written", fg='yellow'))
    click.echo()

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        click.echo(f"Extraction failed: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: Extraction script not found at {script}", err=True)
        click.echo("Make sure you're running from the temoa project directory.", err=True)
        sys.exit(1)


@main.command()
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
@click.option('--json-file', required=True, type=click.Path(exists=True),
              help='Path to old gleanings JSON file')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without writing files')
def migrate(vault, json_file, dry_run):
    """Migrate gleanings from old-gleanings JSON format.

    Converts gleanings from the old JSON format to individual markdown files
    in L/Gleanings/, preserving all metadata (categories, tags, timestamps).
    """
    from .config import Config
    import subprocess

    config = Config()
    vault_path = Path(vault) if vault else config.vault_path

    # Build command for migration script
    script = Path(__file__).parent.parent.parent / "scripts" / "migrate_old_gleanings.py"

    cmd = [
        sys.executable,
        str(script),
        "--vault-path", str(vault_path),
        "--old-gleanings", json_file
    ]

    if dry_run:
        cmd.append("--dry-run")

    click.echo(f"Migrating gleanings to: {vault_path}")
    if dry_run:
        click.echo(click.style("DRY RUN - No files will be written", fg='yellow'))
    click.echo()

    try:
        result = subprocess.run(cmd, check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        click.echo(f"Migration failed: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: Migration script not found at {script}", err=True)
        click.echo("Make sure you're running from the temoa project directory.", err=True)
        sys.exit(1)


@main.command()
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
def index(vault):
    """Build the embedding index from scratch.

    This processes all files in the vault and creates embeddings.
    Run this once when you first set up Temoa, or after major vault changes.

    For incremental updates, use 'temoa reindex' instead.
    """
    from .config import Config
    from .synthesis import SynthesisClient

    config = Config()
    vault_path = Path(vault) if vault else config.vault_path

    click.echo(f"Building index for: {vault_path}")
    click.echo(click.style("This may take a few minutes for large vaults...", fg='yellow'))
    click.echo()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=config.storage_dir
        )

        with click.progressbar(length=100, label='Indexing') as bar:
            result = client.reindex(force=True)
            bar.update(100)

        click.echo(f"\n{click.style('✓', fg='green')} Index built successfully")
        click.echo(f"Files indexed: {result.get('files_indexed', 'Unknown')}")
        click.echo(f"Model: {result.get('model', 'Unknown')}")

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
@click.option('--force', is_flag=True, help='Force full rebuild of index')
def reindex(vault, force):
    """Re-index the vault embeddings.

    Updates the embedding index incrementally (only processes new/changed files).
    Use --force to rebuild everything from scratch.

    For first-time setup, use 'temoa index' instead.
    """
    from .config import Config
    from .synthesis import SynthesisClient

    config = Config()
    vault_path = Path(vault) if vault else config.vault_path

    click.echo(f"Re-indexing vault: {vault_path}")
    if force:
        click.echo(click.style("Force rebuild enabled", fg='yellow'))

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=config.storage_dir
        )

        with click.progressbar(length=100, label='Re-indexing') as bar:
            # Note: This is a simple progress indicator
            # Real progress would require Synthesis to support callbacks
            result = client.reindex(force=force)
            bar.update(100)

        click.echo(f"\n{click.style('✓', fg='green')} Re-indexing complete")
        click.echo(f"Files indexed: {result.get('files_indexed', 'Unknown')}")

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@main.group()
def gleaning():
    """Manage gleaning status (mark as active/inactive).

    \b
    Examples:
      temoa gleaning mark abc123def456 --status inactive --reason "broken link"
      temoa gleaning list --status inactive
      temoa gleaning show abc123def456
    """
    pass


@gleaning.command(name="mark")
@click.argument('gleaning_id')
@click.option('--status', type=click.Choice(['active', 'inactive']), required=True,
              help='Status to set for the gleaning')
@click.option('--reason', default=None, help='Optional reason for status change')
def gleaning_mark(gleaning_id, status, reason):
    """Mark a gleaning as active or inactive.

    \b
    Examples:
      temoa gleaning mark abc123def456 --status inactive --reason "broken link"
      temoa gleaning mark abc123def456 --status active
    """
    from .config import Config
    from .gleanings import GleaningStatusManager

    try:
        cfg = Config()
        manager = GleaningStatusManager(cfg.vault_path / ".temoa")

        record = manager.mark_status(gleaning_id, status, reason)

        click.echo(f"\n{click.style('✓', fg='green')} Gleaning {gleaning_id} marked as {click.style(status, fg='yellow')}")
        if reason:
            click.echo(f"  Reason: {reason}")
        click.echo(f"  Marked at: {record['marked_at']}")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gleaning.command(name="list")
@click.option('--status', type=click.Choice(['active', 'inactive', 'all']), default='all',
              help='Filter by status (default: all)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def gleaning_list(status, json_output):
    """List all gleanings from vault.

    \b
    Examples:
      temoa gleaning list
      temoa gleaning list --status inactive
      temoa gleaning list --status active --json-output
    """
    from .config import Config
    from .gleanings import GleaningStatusManager, scan_gleaning_files

    try:
        cfg = Config()
        manager = GleaningStatusManager(cfg.vault_path / ".temoa")

        # Scan gleaning files
        status_filter = None if status == 'all' else status
        gleanings = scan_gleaning_files(
            vault_path=cfg.vault_path,
            status_manager=manager,
            status_filter=status_filter
        )

        if json_output:
            click.echo(json.dumps(gleanings, indent=2))
            return

        if not gleanings:
            click.echo(f"\nNo gleanings found{' with status: ' + status if status != 'all' else ''}")
            click.echo()
            return

        click.echo(f"\nGleanings ({status}):\n")
        for gleaning in gleanings:
            gleaning_id = gleaning['gleaning_id']
            title = gleaning.get('title', 'Untitled')
            status_value = gleaning['status']
            created = gleaning.get('created', 'Unknown')
            url = gleaning.get('url', '')

            click.echo(f"{click.style(gleaning_id, fg='cyan')} - {title}")
            click.echo(f"  URL: {url}")
            click.echo(f"  Status: {click.style(status_value, fg='yellow')}")
            click.echo(f"  Created: {created}")

            # If marked inactive, check status file for reason
            if status_value == 'inactive':
                record = manager.get_gleaning_record(gleaning_id)
                if record and 'reason' in record:
                    click.echo(f"  Reason: {record['reason']}")

            click.echo()

        click.echo(f"Total: {len(gleanings)}")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gleaning.command(name="show")
@click.argument('gleaning_id')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def gleaning_show(gleaning_id, json_output):
    """Show details for a specific gleaning.

    \b
    Example:
      temoa gleaning show abc123def456
      temoa gleaning show abc123def456 --json-output
    """
    from .config import Config
    from .gleanings import GleaningStatusManager

    try:
        cfg = Config()
        manager = GleaningStatusManager(cfg.vault_path / ".temoa")

        record = manager.get_gleaning_record(gleaning_id)

        if not record:
            click.echo(f"\nGleaning {gleaning_id} not found (or has default status: active)")
            click.echo()
            return

        if json_output:
            click.echo(json.dumps(record, indent=2))
            return

        click.echo(f"\nGleaning: {click.style(gleaning_id, fg='cyan')}\n")
        click.echo(f"Status: {click.style(record['status'], fg='yellow')}")
        click.echo(f"Marked: {record.get('marked_at', 'Unknown')}")
        if 'reason' in record:
            click.echo(f"Reason: {record['reason']}")

        if 'history' in record and len(record['history']) > 1:
            click.echo("\nHistory:")
            for i, entry in enumerate(record['history'], 1):
                click.echo(f"  {i}. {entry['status']} at {entry['marked_at']}")
                if 'reason' in entry and entry['reason']:
                    click.echo(f"     Reason: {entry['reason']}")

        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@gleaning.command(name="maintain")
@click.option('--check-links/--no-check-links', default=True,
              help='Check if URLs are alive (default: true)')
@click.option('--add-descriptions/--no-add-descriptions', default=True,
              help='Fetch meta descriptions for missing ones (default: true)')
@click.option('--mark-dead-inactive/--no-mark-dead-inactive', default=True,
              help='Mark dead links as inactive (default: true)')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying them')
@click.option('--timeout', type=int, default=10, help='HTTP request timeout in seconds (default: 10)')
@click.option('--rate-limit', type=float, default=1.0, help='Seconds between requests (default: 1.0)')
def gleaning_maintain(check_links, add_descriptions, mark_dead_inactive, dry_run, timeout, rate_limit):
    """Maintain gleanings (check links, add descriptions).

    This command:
    - Checks if gleaning URLs are still alive
    - Fetches meta descriptions from live URLs if missing
    - Marks dead links as inactive
    - Updates frontmatter with new data

    \b
    Examples:
      temoa gleaning maintain --dry-run
      temoa gleaning maintain
      temoa gleaning maintain --no-mark-dead-inactive
      temoa gleaning maintain --rate-limit 2.0
    """
    from .config import Config

    # Import the maintainer from scripts
    scripts_path = Path(__file__).parent.parent.parent / "scripts"
    if str(scripts_path) not in sys.path:
        sys.path.insert(0, str(scripts_path))

    try:
        from maintain_gleanings import GleaningMaintainer
    except ImportError as e:
        click.echo(f"Error importing maintenance tool: {e}", err=True)
        sys.exit(1)

    try:
        cfg = Config()

        maintainer = GleaningMaintainer(
            vault_path=cfg.vault_path,
            timeout=timeout
        )

        maintainer.maintain_all(
            check_links=check_links,
            add_descriptions=add_descriptions,
            mark_dead_inactive=mark_dead_inactive,
            dry_run=dry_run,
            rate_limit=rate_limit
        )

    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def config():
    """Show current configuration.

    Displays the configuration being used by Temoa, including paths,
    server settings, and model information.
    """
    from .config import Config

    try:
        cfg = Config()

        click.echo("\nTemoa Configuration\n")
        click.echo(f"Config file: {click.style(str(cfg.config_path), fg='cyan')}")
        click.echo()
        click.echo("Paths:")
        click.echo(f"  Vault: {cfg.vault_path}")
        click.echo(f"  Index: {cfg.index_path}")
        click.echo(f"  Synthesis: {cfg.synthesis_path}")
        click.echo()
        click.echo("Server:")
        click.echo(f"  Host: {cfg.server_host}")
        click.echo(f"  Port: {cfg.server_port}")
        click.echo()
        click.echo("Search:")
        click.echo(f"  Default model: {cfg.default_model}")
        click.echo(f"  Default limit: {cfg.search_default_limit}")
        click.echo(f"  Max limit: {cfg.search_max_limit}")
        click.echo(f"  Timeout: {cfg.search_timeout}s")
        click.echo()

    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
