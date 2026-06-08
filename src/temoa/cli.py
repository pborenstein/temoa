#!/usr/bin/env python3
"""Temoa CLI - Command-line interface for Temoa semantic search server"""
import json
import logging
import sys
from pathlib import Path
import click
import uvicorn

from .__version__ import __version__

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logging.getLogger("temoa.synthesis").setLevel(logging.WARNING)
logging.getLogger("src.embeddings").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("nahuatl_frontmatter").setLevel(logging.ERROR)


@click.group()
@click.version_option(version=__version__)
def main():
    """Local semantic search server for Obsidian vaults.

    \b
    Setup:
      temoa index               # build embedding index (first run)
      temoa server              # start the search API

    \b
    Daily use:
      temoa search "query"      # search from the terminal
      temoa reindex             # pick up new and changed files
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
    """Start the search API server."""
    import socket
    from .config import Config

    config = Config()
    server_host = host or config.server_host
    server_port = port or config.server_port

    addresses = []
    try:
        import netifaces
        addresses.append("localhost")
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    ip = addr_info.get('addr')
                    if ip and ip != '127.0.0.1':
                        addresses.append(ip)
    except Exception:
        try:
            addrs = socket.getaddrinfo(socket.gethostname(), None)
            for addr in addrs:
                if addr[0] == socket.AF_INET:
                    ip = addr[4][0]
                    if ip != "127.0.0.1":
                        addresses.append(ip)
        except Exception:
            pass

    if not addresses:
        addresses = ["localhost"]

    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = '%(asctime)s %(levelprefix)s %(message)s'
    log_config["formatters"]["default"]["datefmt"] = '%Y-%m-%d %H:%M:%S'
    log_config["formatters"]["access"]["fmt"] = '%(asctime)s %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
    log_config["formatters"]["access"]["datefmt"] = '%Y-%m-%d %H:%M:%S'

    addr_str = " or ".join([f"http://{addr}:{server_port}/" for addr in addresses])
    click.echo(f"Temoa server starting at {addr_str}")

    uvicorn.run(
        "temoa.server:app",
        host=server_host,
        port=server_port,
        reload=reload,
        log_level=log_level,
        log_config=log_config
    )


@main.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, type=int, help='Number of results (default: 10)')
@click.option('--min-score', '-s', default=0.3, type=float, help='Minimum similarity score (0.0-1.0, default: 0.3)')
@click.option('--type', '-t', 'include_types', default=None, help='Include only these types (comma-separated, e.g. "gleaning,article")')
@click.option('--exclude-type', '-x', 'exclude_types', default=None, help='Exclude these types (comma-separated, e.g. "daily")')
@click.option('--hybrid', is_flag=True, default=None, help='Use hybrid search (BM25 + semantic)')
@click.option('--rerank/--no-rerank', default=True, help='Use cross-encoder re-ranking (default: enabled)')
@click.option('--expand/--no-expand', 'expand_query', default=False, help='Expand short queries with TF-IDF terms')
@click.option('--time-boost/--no-time-boost', 'time_boost', default=True, help='Boost recent documents')
@click.option('--bm25-only', is_flag=True, help='Use BM25 keyword search only')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--vault', default=None, type=click.Path(exists=True), help='Vault path (default: from config)')
def search(query, limit, min_score, include_types, exclude_types, hybrid, rerank, expand_query, time_boost, bm25_only, output_json, vault):
    """Search the vault by meaning.

    \b
    Examples:
      temoa search "semantic search"
      temoa search "tailscale networking" --hybrid
      temoa search "saved articles" --type gleaning
      temoa search "topic" --exclude-type daily
      temoa search "AI tools" --min-score 0.5
      temoa search "obsidian" --json
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir
    from .pipeline import default_pipeline, SearchContext

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
        vault_config = config.find_vault(vault)
        vault_model = vault_config.get('model') if vault_config else None
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir
        vault_model = None

    try:
        effective_model = vault_model or config.default_model

        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=effective_model,
            storage_dir=storage_dir
        )

        original_query = query
        expanded_query_str = None
        if expand_query and not bm25_only:
            from .query_expansion import QueryExpander
            expander = QueryExpander(max_expansion_terms=3)
            if expander.should_expand(query):
                initial_data = client.search(query, limit=5)
                query = expander.expand(query, initial_data.get('results', []), top_k=5)
                if query != original_query:
                    expanded_query_str = query

        if bm25_only:
            result_data = client.bm25_search(query, limit=limit)
            results = result_data.get('results', [])
        else:
            use_hybrid = hybrid if hybrid is not None else config.hybrid_search_enabled
            search_limit = limit * 3 if limit else 100

            if use_hybrid:
                result_data = client.hybrid_search(query, limit=search_limit)
            else:
                result_data = client.search(query, limit=search_limit)

            results = result_data.get('results', [])
            search_mode = "hybrid" if use_hybrid else "semantic"

            services = {}
            if time_boost:
                from .time_scoring import TimeAwareScorer
                time_decay_config = config._config.get("search", {}).get("time_decay", {})
                services["time_scorer"] = TimeAwareScorer(
                    half_life_days=time_decay_config.get("half_life_days", 90),
                    max_boost=time_decay_config.get("max_boost", 0.2),
                    enabled=True
                )
            if rerank:
                from .reranker import CrossEncoderReranker
                services["reranker"] = CrossEncoderReranker()

            include_types_list = [t.strip() for t in include_types.split(",")] if include_types else []
            exclude_types_list = [t.strip() for t in exclude_types.split(",")] if exclude_types else []

            ctx = SearchContext(
                query=query,
                original_query=original_query,
                vault_path=vault_path,
                vault_name=vault or "",
                limit=limit,
                search_mode=search_mode,
                params={
                    "min_score": min_score,
                    "rerank": rerank,
                    "time_boost": time_boost,
                    "include_types": include_types_list,
                    "exclude_types": exclude_types_list,
                },
                services=services,
            )
            ctx.results = results
            default_pipeline().run(ctx)
            results = ctx.results

            result_data['results'] = results
            result_data['total'] = len(results)
            result_data['query'] = original_query
            if expanded_query_str:
                result_data['expanded_query'] = expanded_query_str

        # Log to search_log.db
        import asyncio as _asyncio
        from .search_log import SearchLog as _SearchLog
        _log = _SearchLog(storage_dir / "search_log.db")
        _asyncio.run(_log.init())
        _asyncio.run(_log.log_search(
            query=original_query,
            vault=str(vault_path),
            mode=result_data.get("search_mode", search_mode if not bm25_only else "bm25"),
            limit=limit,
            rerank=rerank,
            expand_query=expand_query,
            results=results,
        ))

        if output_json:
            click.echo(json.dumps(result_data, indent=2))
        else:
            search_mode_str = result_data.get('search_mode', 'semantic')
            if expanded_query_str:
                click.echo(f"\nSearch results for: {click.style(original_query, fg='cyan', bold=True)}")
                click.echo(click.style(f"Expanded to: {expanded_query_str}", dim=True))
                click.echo()
            else:
                click.echo(f"\nSearch results for: {click.style(query, fg='cyan', bold=True)} ({search_mode_str})\n")

            if not results:
                click.echo("No results found.")
                return

            for i, result in enumerate(results, 1):
                click.echo(f"{i}. {click.style(result.get('title', 'Untitled'), fg='green', bold=True)}")
                click.echo(f"   {result.get('relative_path', 'Unknown path')}")

                sim_score = result.get('similarity_score')
                bm25_score = result.get('bm25_score')

                if sim_score is not None and bm25_score is not None:
                    click.echo(f"   Semantic: {sim_score:.3f} | BM25: {bm25_score:.3f}")
                elif bm25_score is not None:
                    click.echo(f"   BM25: {bm25_score:.3f}")
                elif sim_score is not None:
                    click.echo(f"   Similarity: {sim_score:.3f}")

                if result.get('description'):
                    click.echo(f"   {click.style(result['description'].strip(), dim=True)}")

                if result.get('tags'):
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
@click.option('--vault', default=None, type=click.Path(exists=True), help='Vault path (default: from config)')
def archaeology(topic, limit, output_json, vault):
    """Show when you were interested in a topic over time.

    \b
    Examples:
      temoa archaeology "machine learning"
      temoa archaeology "tailscale" --json
    """
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
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
                        click.echo(f"  * {period}")

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
@click.option('--vault', default=None, type=click.Path(exists=True), help='Vault path (default: from config)')
def stats(output_json, vault):
    """Show index statistics."""
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
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

            total_files = statistics.get('total_files', 0)
            total_embeddings = statistics.get('num_embeddings', 0)
            has_error = 'error' in statistics

            if has_error or total_files == 0:
                click.echo(f"\nNo index found")
                click.echo("Run 'temoa index' to build the embedding index for your vault.")
            elif total_embeddings == 0 and total_files > 0:
                click.echo(f"\nIndex incomplete")
                click.echo(f"Files scanned: {total_files}")
                click.echo(f"Embeddings generated: 0")
                click.echo("\nRun 'temoa index' to generate embeddings for your vault.")
            else:
                model_name = statistics.get('model_info', {}).get('model_name', 'Unknown')
                click.echo(f"Model: {click.style(model_name, fg='green')}")
                click.echo(f"Files indexed: {click.style(str(total_files), fg='yellow')}")
                click.echo(f"Embeddings: {click.style(str(total_embeddings), fg='green')}")

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
@click.option('--vault', default=None, type=click.Path(exists=True), help='Vault path (default: from config)')
@click.option('--force', is_flag=True, help='Force overwrite if storage mismatch (DANGER)')
@click.option('--model', '-m', default=None, help='Embedding model to use (default: from config)')
@click.option('--enable-chunking', is_flag=True, help='Enable adaptive chunking for large files')
@click.option('--chunk-size', default=2000, type=int, help='Target chunk size in characters (default: 2000)')
@click.option('--chunk-overlap', default=400, type=int, help='Overlapping characters between chunks (default: 400)')
@click.option('--chunk-threshold', default=4000, type=int, help='Minimum file size before chunking (default: 4000)')
def index(vault, force, model, enable_chunking, chunk_size, chunk_overlap, chunk_threshold):
    """Build the full embedding index (first-time setup)."""
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    if model:
        embedding_model = model
    else:
        vault_config = config.find_vault(str(vault_path))
        embedding_model = vault_config.get('model') if vault_config and 'model' in vault_config else config.default_model

    validate_storage_safe(storage_dir, vault_path, "index", force, model=embedding_model)

    click.echo(f"Building index for: {vault_path}")
    click.echo(f"Storage directory: {storage_dir}")
    click.echo(f"Model: {embedding_model}")
    click.echo(click.style("This may take a few minutes for large vaults...", fg='yellow'))
    click.echo()

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=embedding_model,
            storage_dir=storage_dir
        )

        if enable_chunking:
            click.echo(f"Chunking: size={chunk_size}, overlap={chunk_overlap}, threshold={chunk_threshold}")
            click.echo()

        with click.progressbar(length=100, label='Indexing') as bar:
            result = client.reindex(
                force=True,
                enable_chunking=enable_chunking,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunk_threshold=chunk_threshold
            )
            bar.update(100)

        click.echo(f"\nIndex built successfully")
        click.echo(f"Files indexed: {result.get('files_indexed', 'Unknown')}")
        if enable_chunking and result.get('total_chunks'):
            click.echo(f"Total files: {result.get('total_files', 'Unknown')}")
            click.echo(f"Total chunks: {result.get('total_chunks', 'Unknown')}")
        click.echo(f"Model: {result.get('model', 'Unknown')}")

    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--vault', default=None, type=click.Path(exists=True), help='Vault path (default: from config)')
@click.option('--force', is_flag=True, help='Force overwrite if storage mismatch (DANGER)')
@click.option('--model', '-m', default=None, help='Embedding model to use (default: from config)')
@click.option('--enable-chunking', is_flag=True, help='Enable adaptive chunking for large files')
@click.option('--chunk-size', default=2000, type=int, help='Target chunk size in characters (default: 2000)')
@click.option('--chunk-overlap', default=400, type=int, help='Overlapping characters between chunks (default: 400)')
@click.option('--chunk-threshold', default=4000, type=int, help='Minimum file size before chunking (default: 4000)')
@click.option('--log-format', is_flag=True, help='Output a single timestamped markdown line (for cron logs)')
def reindex(vault, force, model, enable_chunking, chunk_size, chunk_overlap, chunk_threshold, log_format):
    """Update the index incrementally (new and modified files only)."""
    from .config import Config
    from .synthesis import SynthesisClient
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    if model:
        embedding_model = model
    else:
        vault_config = config.find_vault(str(vault_path))
        embedding_model = vault_config.get('model') if vault_config and 'model' in vault_config else config.default_model

    validate_storage_safe(storage_dir, vault_path, "reindex", force, model=embedding_model)

    if not log_format:
        click.echo(f"Re-indexing vault: {vault_path}")
        click.echo(f"Storage directory: {storage_dir}")
        click.echo(f"Model: {embedding_model}")
        click.echo("Running incremental reindex (only changed files)...")
        if enable_chunking:
            click.echo(f"Chunking: size={chunk_size}, overlap={chunk_overlap}, threshold={chunk_threshold}")

    try:
        client = SynthesisClient(
            synthesis_path=config.synthesis_path,
            vault_path=vault_path,
            model=embedding_model,
            storage_dir=storage_dir
        )

        if log_format:
            result = client.reindex(
                force=False,
                enable_chunking=enable_chunking,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunk_threshold=chunk_threshold,
                show_progress=False
            )
        else:
            with click.progressbar(length=100, label='Re-indexing') as bar:
                result = client.reindex(
                    force=False,
                    enable_chunking=enable_chunking,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunk_threshold=chunk_threshold,
                    show_progress=True
                )
                bar.update(100)

        new_f = result.get('files_new', 0)
        mod_f = result.get('files_modified', 0)
        del_f = result.get('files_deleted', 0)

        if log_format:
            import datetime
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if 'files_new' in result:
                file_stats = f"+{new_f} new, ~{mod_f} modified, -{del_f} deleted"
            else:
                file_stats = f"{result.get('files_indexed', '?')} indexed"
            click.echo(f"## {ts} | reindex\n{file_stats}")
        else:
            click.echo(f"\nRe-indexing complete")
            if 'files_new' in result:
                click.echo(f"New files: {new_f}")
                click.echo(f"Modified files: {mod_f}")
                click.echo(f"Deleted files: {del_f}")
            else:
                click.echo(f"Files indexed: {result.get('files_indexed', 'Unknown')}")

    except Exception as e:
        if log_format:
            import datetime
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            click.echo(f"## {ts} | reindex | ERROR: {e}")
        else:
            click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


@main.command()
def config():
    """Show current configuration."""
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


@main.command()
def vaults():
    """List configured vaults and their models."""
    from .config import Config

    try:
        cfg = Config()
        vault_list = cfg.vaults

        if not vault_list:
            click.echo("No vaults configured.")
            return

        click.echo("\nConfigured vaults:\n")
        for v in vault_list:
            name = v.get('name', 'unnamed')
            path = v.get('path', 'unknown')
            model = v.get('model', cfg.default_model)
            click.echo(f"  {click.style(name, fg='green')}: {path} (model: {model})")
        click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("log")
@click.option("--vault", default=None, type=click.Path(exists=True), help="Vault path (default: from config)")
@click.option("--recent", "-n", default=20, type=int, help="Show N most recent searches (default: 20)")
@click.option("--stats", "show_stats", is_flag=True, help="Show aggregate stats instead of recent searches")
@click.option("--detail", is_flag=True, help="Show ranked result paths for each search")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def log(vault, recent, show_stats, detail, output_json):
    """Show the search query log.

    \b
    Examples:
      temoa log                        # recent searches
      temoa log --detail               # include ranked result paths
      temoa log --stats                # aggregate stats
      temoa log --recent 50 --json     # last 50 searches as JSON
    """
    import asyncio
    from .config import Config
    from .search_log import SearchLog
    from .storage import derive_storage_dir

    config = Config()

    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    log_path = storage_dir / "search_log.db"
    if not log_path.exists():
        click.echo(f"No search log found at {log_path}. Start the server and run some searches first.")
        return

    search_log = SearchLog(log_path)

    async def _run():
        await search_log.init()
        if show_stats:
            return await search_log.get_stats()
        return await search_log.recent(recent)

    try:
        data = asyncio.run(_run())

        if output_json:
            click.echo(json.dumps(data, indent=2))
            return

        if show_stats:
            click.echo("\nSearch Log Stats\n")
            click.echo(f"Total searches: {click.style(str(data['total_searches']), fg='yellow')}")
            dr = data.get("date_range", {})
            if dr.get("first"):
                click.echo(f"Date range:     {dr['first']} — {dr['last']}")
            if data.get("by_mode"):
                click.echo("\nBy mode:")
                for mode, count in data["by_mode"].items():
                    click.echo(f"  {mode}: {count}")
            if data.get("timing"):
                t = data["timing"]
                click.echo(f"\nAvg retrieval: {t.get('avg_retrieval_ms', '?')} ms")
                click.echo(f"Avg total:     {t.get('avg_total_ms', '?')} ms")
            click.echo()
        else:
            if not data:
                click.echo("No searches logged yet.")
                return
            click.echo(f"\nRecent searches ({len(data)}):\n")
            for row in data:
                from datetime import datetime, timezone
                raw_ts = row.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                    ts = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts = raw_ts[:19].replace("T", " ")
                q = row.get("query", "")
                mode = row.get("mode") or "?"
                n = row.get("result_count", 0)
                top = row.get("top_score")
                rt = row.get("retrieval_ms")
                score_str = f"  top={top:.3f}" if top is not None else ""
                rt_str = f"  {rt}ms" if rt is not None else ""
                click.echo(f"{ts}  {click.style(q, fg='cyan')}  [{mode}, {n} results{score_str}{rt_str}]")
                if detail and row.get("results"):
                    try:
                        result_list = json.loads(row["results"])
                        for i, r in enumerate(result_list, 1):
                            score = r.get("score")
                            score_fmt = f"{score:.3f}" if score is not None else "?"
                            click.echo(f"  {i:2d}. {click.style(score_fmt, dim=True)}  {r.get('path', '?')}")
                    except Exception:
                        pass
            click.echo()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
