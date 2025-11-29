#!/usr/bin/env python3
"""
Temoa CLI - Command-line interface for Temoa semantic search server
"""
import json
import logging
import sys
from pathlib import Path
import click
import uvicorn

from .__version__ import __version__

# Configure logging for CLI - quiet down noisy synthesis internals
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s"
)
# Only show warnings from synthesis/embeddings
logging.getLogger("temoa.synthesis").setLevel(logging.WARNING)
logging.getLogger("src.embeddings").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)


@click.group()
@click.version_option(version=__version__)
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
@click.option('--min-score', '-s', default=0.3, type=float, help='Minimum similarity score (0.0-1.0, default: 0.3)')
@click.option('--type', '-t', 'include_types', default=None, help='Include only these types (comma-separated, e.g., "gleaning,article")')
@click.option('--exclude-type', '-x', 'exclude_types', default='daily', help='Exclude these types (comma-separated, default: "daily")')
@click.option('--hybrid', is_flag=True, default=None, help='Use hybrid search (BM25 + semantic)')
@click.option('--bm25-only', is_flag=True, help='Use BM25 keyword search only (for debugging)')
@click.option('--model', '-m', default=None, help='Embedding model to use')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
def search(query, limit, min_score, include_types, exclude_types, hybrid, bm25_only, model, output_json, vault):
    """Search the vault for similar content.

    \b
    Examples:
      temoa search "semantic search"
      temoa search "tailscale networking" --limit 5
      temoa search "AI tools" --min-score 0.5
      temoa search "Joan Doe" --hybrid
      temoa search "Joan Doe" --bm25-only
      temoa search "obsidian" --json
      temoa search "topic" --type gleaning,article
      temoa search "topic" --exclude-type daily,note
      temoa search "topic" --type daily --exclude-type ""
      temoa search "query" --vault ~/vaults/other
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .server import filter_inactive_gleanings, filter_by_type
    from .storage import derive_storage_dir

    config = Config()

    # Determine vault and storage based on --vault flag
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    # Parse type filters
    include_type_list = None
    if include_types:
        include_type_list = [t.strip() for t in include_types.split(",") if t.strip()]

    # If include_types is specified, ignore exclude_types default (user is explicit about what they want)
    exclude_type_list = None
    if include_types:
        # User explicitly specified what to include, only apply exclude if they also specified it
        if exclude_types and exclude_types != 'daily':  # Don't use default when include is set
            exclude_type_list = [t.strip() for t in exclude_types.split(",") if t.strip()]
    elif exclude_types:
        # No include_types, use exclude_types (including default)
        exclude_type_list = [t.strip() for t in exclude_types.split(",") if t.strip()]

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=model or config.default_model,
            storage_dir=storage_dir
        )

        # Determine search mode
        if bm25_only:
            # BM25 only for debugging
            result_data = client.bm25_search(query, limit=limit)
            results = result_data.get('results', [])
        else:
            # Hybrid or semantic
            use_hybrid = hybrid if hybrid is not None else config.hybrid_search_enabled

            # Request more results to account for filtering
            search_limit = limit * 3 if limit else 100

            # Choose search method
            if use_hybrid:
                result_data = client.hybrid_search(query, limit=search_limit)
            else:
                result_data = client.search(query, limit=search_limit)

            results = result_data.get('results', [])

            # Filter by minimum similarity score (but not in hybrid mode)
            score_removed = 0
            if use_hybrid:
                # In hybrid mode, RRF has already ranked results appropriately
                # Don't filter by similarity score since BM25-only results may not have one
                filtered_results = results
            else:
                # In semantic-only mode, filter by similarity threshold
                filtered_results = [r for r in results if r.get('similarity_score', 0) >= min_score]
                score_removed = len(results) - len(filtered_results)

            # Filter out inactive gleanings
            status_count = len(filtered_results)
            filtered_results = filter_inactive_gleanings(filtered_results)
            status_removed = status_count - len(filtered_results)

            # Filter by type
            filtered_results, type_removed = filter_by_type(
                filtered_results,
                include_types=include_type_list,
                exclude_types=exclude_type_list
            )

            # Apply final limit
            filtered_results = filtered_results[:limit]

            # Update result data
            result_data['results'] = filtered_results
            result_data['total'] = len(filtered_results)
            result_data['min_score'] = min_score
            result_data['filtered_count'] = {
                'by_score': score_removed,
                'by_status': status_removed,
                'by_type': type_removed,
                'total_removed': score_removed + status_removed + type_removed
            }

            results = filtered_results

        if output_json:
            # Output as JSON for scripting
            click.echo(json.dumps(result_data, indent=2))
        else:
            # Human-readable output
            search_mode = result_data.get('search_mode', 'semantic')
            mode_str = f" ({search_mode})" if search_mode else ""
            click.echo(f"\nSearch results for: {click.style(query, fg='cyan', bold=True)}{mode_str}\n")

            # Show applied filters
            if include_type_list or exclude_type_list:
                filters_applied = []
                if include_type_list:
                    filters_applied.append(f"types: {', '.join(include_type_list)}")
                if exclude_type_list:
                    filters_applied.append(f"excluding: {', '.join(exclude_type_list)}")

                if filters_applied:
                    click.echo(click.style(f"Filters: {', '.join(filters_applied)}", dim=True))

            # Show filtered count
            if 'filtered_count' in result_data:
                fc = result_data['filtered_count']
                total = fc.get('total_removed', 0)
                if total > 0:
                    parts = []
                    if fc.get('by_score', 0) > 0:
                        parts.append(f"{fc['by_score']} by score")
                    if fc.get('by_status', 0) > 0:
                        parts.append(f"{fc['by_status']} by status")
                    if fc.get('by_type', 0) > 0:
                        parts.append(f"{fc['by_type']} by type")

                    click.echo(click.style(f"Filtered: {', '.join(parts)} ({total} total)", dim=True))
                    click.echo()

            if not results:
                click.echo("No results found.")
                return

            for i, result in enumerate(results, 1):
                click.echo(f"{i}. {click.style(result.get('title', 'Untitled'), fg='green', bold=True)}")
                click.echo(f"   {result.get('relative_path', 'Unknown path')}")

                # Show both scores if available
                sim_score = result.get('similarity_score')
                bm25_score = result.get('bm25_score')

                if sim_score is not None and bm25_score is not None:
                    # Hybrid result - show both
                    click.echo(f"   Semantic: {sim_score:.3f} | BM25: {bm25_score:.3f}")
                elif bm25_score is not None:
                    # BM25 only
                    click.echo(f"   BM25: {bm25_score:.3f}")
                elif sim_score is not None:
                    # Semantic only
                    click.echo(f"   Similarity: {sim_score:.3f}")

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
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
def archaeology(topic, limit, output_json, vault):
    """Analyze temporal patterns of interest in a topic.

    Shows when you were interested in a topic over time.

    \b
    Examples:
      temoa archaeology "machine learning"
      temoa archaeology "tailscale" --json
      temoa archaeology "topic" --vault ~/vaults/other
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir

    config = Config()

    # Determine vault and storage based on --vault flag
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=storage_dir
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
@click.option('--vault', default=None, type=click.Path(exists=True),
              help='Vault path (default: from config)')
def stats(output_json, vault):
    """Show vault statistics.

    Displays information about indexed files, embeddings, and models.
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir

    config = Config()

    # Determine vault and storage based on --vault flag
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=storage_dir
        )

        statistics = client.get_stats()

        if output_json:
            click.echo(json.dumps(statistics, indent=2))
        else:
            click.echo("\nVault Statistics\n")
            click.echo(f"Vault path: {click.style(str(vault_path), fg='cyan')}")
            click.echo(f"Storage: {click.style(str(storage_dir), fg='cyan')}")

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

    # Build command for extraction script (now in src/temoa/scripts/)
    script = Path(__file__).parent / "scripts" / "extract_gleanings.py"

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
@click.option('--force', is_flag=True,
              help='Force overwrite if storage mismatch (DANGER)')
def index(vault, force):
    """Build the embedding index from scratch.

    This processes all files in the vault and creates embeddings.
    Run this once when you first set up Temoa, or after major vault changes.

    For incremental updates, use 'temoa reindex' instead.
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    # Determine vault and storage based on --vault flag
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    # Validate storage is safe before proceeding
    validate_storage_safe(storage_dir, vault_path, "index", force)

    click.echo(f"Building index for: {vault_path}")
    click.echo(f"Storage directory: {storage_dir}")
    click.echo(click.style("This may take a few minutes for large vaults...", fg='yellow'))
    click.echo()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=storage_dir
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
@click.option('--force', is_flag=True,
              help='Force overwrite if storage mismatch (DANGER)')
def reindex(vault, force):
    """Re-index the vault incrementally (only new/modified files).

    Detects changes since last index and only processes:
    - New files
    - Modified files (based on modification time)
    - Deleted files (removes from index)

    Much faster than full rebuild for daily use (~6 seconds vs ~154 seconds).
    Falls back to full rebuild if no previous index exists.

    For first-time setup or full rebuild, use 'temoa index' instead.
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    # Determine vault and storage based on --vault flag
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    # Validate storage is safe before proceeding
    validate_storage_safe(storage_dir, vault_path, "reindex", force)

    click.echo(f"Re-indexing vault: {vault_path}")
    click.echo(f"Storage directory: {storage_dir}")
    click.echo("Running incremental reindex (only changed files)...")

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=config.default_model,
            storage_dir=storage_dir
        )

        with click.progressbar(length=100, label='Re-indexing') as bar:
            # Note: This is a simple progress indicator
            # Real progress would require Synthesis to support callbacks
            result = client.reindex(force=False)
            bar.update(100)

        click.echo(f"\n{click.style('✓', fg='green')} Re-indexing complete")

        # Show detailed stats for incremental reindex
        if 'files_new' in result:
            click.echo(f"New files: {result.get('files_new', 0)}")
            click.echo(f"Modified files: {result.get('files_modified', 0)}")
            click.echo(f"Deleted files: {result.get('files_deleted', 0)}")
        else:
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
@click.option('--status', type=click.Choice(['active', 'inactive', 'hidden']), required=True,
              help='Status to set for the gleaning')
@click.option('--reason', default=None, help='Optional reason for status change')
def gleaning_mark(gleaning_id, status, reason):
    """Mark a gleaning as active, inactive, or hidden.

    \b
    Status meanings:
      active   - Normal gleaning, included in search results
      inactive - Dead link, excluded from search, auto-restores if link comes back
      hidden   - Manually hidden, never checked by maintenance tool

    \b
    Examples:
      temoa gleaning mark abc123def456 --status inactive --reason "broken link"
      temoa gleaning mark abc123def456 --status hidden --reason "duplicate"
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
@click.option('--status', type=click.Choice(['active', 'inactive', 'hidden', 'all']), default='all',
              help='Filter by status (default: all)')
@click.option('--json-output', is_flag=True, help='Output as JSON')
def gleaning_list(status, json_output):
    """List all gleanings from vault.

    \b
    Examples:
      temoa gleaning list
      temoa gleaning list --status inactive
      temoa gleaning list --status hidden
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

            # If marked inactive or hidden, check status file for reason
            if status_value in ('inactive', 'hidden'):
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
    try:
        from .scripts.maintain_gleanings import GleaningMaintainer
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
