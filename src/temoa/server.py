"""FastAPI server for Temoa semantic search"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .__version__ import __version__
from .config import Config, ConfigError
from .synthesis import SynthesisClient, SynthesisError
from .gleanings import parse_frontmatter_status, GleaningStatusManager, scan_gleaning_files
from .client_cache import ClientCache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import extraction functionality
# Add scripts directory to path so we can import extract_gleanings
scripts_path = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

try:
    from extract_gleanings import GleaningsExtractor
except ImportError as e:
    logger.warning(f"Could not import GleaningsExtractor: {e}")
    GleaningsExtractor = None

# Load configuration
try:
    config = Config()
    logger.info(f"Configuration loaded: {config}")
except ConfigError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize client cache for multi-vault support
cache_size = config._config.get("server", {}).get("client_cache_size", 3)
client_cache = ClientCache(max_size=cache_size)
logger.info(f"Client cache initialized (max_size={cache_size})")

# Pre-warm cache with default vault
try:
    logger.info("Pre-warming cache with default vault (this may take 10-20 seconds)...")
    default_vault = config.get_default_vault()
    default_vault_path = Path(default_vault["path"]).expanduser().resolve()

    from .storage import derive_storage_dir
    default_storage_dir = derive_storage_dir(
        default_vault_path,
        config.vault_path,
        config.storage_dir
    )

    client_cache.get(
        vault_path=default_vault_path,
        synthesis_path=config.synthesis_path,
        model=config.default_model,
        storage_dir=default_storage_dir
    )
    logger.info("✓ Default vault client ready")
except Exception as e:
    logger.error(f"Failed to pre-warm cache: {e}")
    raise

# Initialize Gleaning status manager (uses default vault)
gleaning_manager = GleaningStatusManager(config.vault_path / ".temoa")


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("=" * 60)
    logger.info("Temoa server starting")
    logger.info(f"  Vault: {config.vault_path}")
    logger.info(f"  Model: {config.default_model}")
    logger.info(f"  Synthesis: {config.synthesis_path}")
    logger.info(f"  Server: http://{config.server_host}:{config.server_port}")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Temoa server shutting down")


def get_client_for_vault(vault_identifier: Optional[str] = None) -> tuple[SynthesisClient, Path, str]:
    """
    Get SynthesisClient for specified vault.

    Args:
        vault_identifier: Vault name, path, or None (use default)

    Returns:
        (client, vault_path, vault_name) tuple

    Raises:
        HTTPException: If vault not found or invalid
    """
    try:
        # Find vault config
        if vault_identifier is None:
            # Use default vault
            vault_config = config.get_default_vault()
        else:
            # Look up by name or path
            vault_config = config.find_vault(vault_identifier)

        if vault_config is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vault not found: {vault_identifier}"
            )

        vault_path = Path(vault_config["path"]).expanduser().resolve()
        vault_name = vault_config["name"]

        # Derive storage dir using CLI logic
        from .storage import derive_storage_dir
        storage_dir = derive_storage_dir(
            vault_path,
            config.vault_path,
            config.storage_dir
        )

        # Get or create cached client
        client = client_cache.get(
            vault_path=vault_path,
            synthesis_path=config.synthesis_path,
            model=config.default_model,
            storage_dir=storage_dir
        )

        return client, vault_path, vault_name

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client for vault '{vault_identifier}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get client for vault: {str(e)}"
        )


def filter_inactive_gleanings(results: list) -> list:
    """
    Filter out inactive and hidden gleanings from search results.

    Args:
        results: List of search result dicts

    Returns:
        Filtered list with only active gleanings
    """
    filtered = []

    for result in results:
        # Get file path from result
        file_path = result.get("file_path")
        if not file_path:
            # If no file_path, include result (not a gleaning)
            filtered.append(result)
            continue

        try:
            # Read file to check status
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            status = parse_frontmatter_status(content)

            # If no status found or status is active, include result
            if status is None or status == "active":
                filtered.append(result)
            # If status is inactive or hidden, skip this result
            elif status in ("inactive", "hidden"):
                logger.debug(f"Filtered out {status} gleaning: {result.get('title', 'Unknown')}")
                continue

        except Exception as e:
            # If we can't read file, include it anyway (fail open)
            logger.warning(f"Error checking status for {file_path}: {e}")
            filtered.append(result)

    return filtered


def filter_by_type(
    results: list,
    include_types: list[str] | None = None,
    exclude_types: list[str] | None = None
) -> tuple[list, int]:
    """
    Filter results by type field in frontmatter.

    Args:
        results: Search results from Synthesis
        include_types: If set, only include results with these types (OR logic)
        exclude_types: If set, exclude results with these types (OR logic)

    Returns:
        (filtered_results, num_filtered_out)

    Logic:
        - If include_types: Keep only if ANY type matches
        - If exclude_types: Remove if ANY type matches
        - If both: Apply include first, then exclude
        - If neither: Return all results
        - Files with no type field are treated as empty list []
    """
    from .gleanings import parse_type_field

    if not include_types and not exclude_types:
        return results, 0

    filtered = []

    for result in results:
        # Try to get type from cached frontmatter in results first
        frontmatter_data = result.get("frontmatter")

        if frontmatter_data is not None:
            # Use cached frontmatter from Synthesis results (no file I/O!)
            types = parse_type_field(frontmatter_data)
        else:
            # Fallback: read file if no frontmatter in results
            # This shouldn't happen often since Synthesis includes frontmatter
            file_path = result.get("file_path")
            if not file_path:
                filtered.append(result)
                continue

            try:
                import frontmatter
                with open(file_path, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
                    types = parse_type_field(post.metadata)
            except Exception as e:
                logger.debug(f"Error reading frontmatter for {file_path}: {e}")
                types = []

        # Apply inclusive filter
        if include_types:
            if not types:
                # No type field - skip when using include filter
                continue
            if not any(t in include_types for t in types):
                # No matching types - skip
                continue

        # Apply exclusive filter
        if exclude_types:
            if any(t in exclude_types for t in types):
                # Has excluded type - skip
                logger.debug(f"Filtered out type {types}: {result.get('title', 'Unknown')}")
                continue

        filtered.append(result)

    num_filtered = len(results) - len(filtered)
    return filtered, num_filtered


# Create FastAPI app
app = FastAPI(
    title="Temoa",
    description="Local semantic search server for Obsidian vault",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve search UI"""
    ui_path = Path(__file__).parent / "ui" / "search.html"

    if not ui_path.exists():
        # Return basic HTML if UI file doesn't exist yet
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Temoa</title>
</head>
<body>
    <h1>🔍 Temoa</h1>
    <p>Semantic search server is running!</p>
    <p>UI coming soon. Try <a href="/docs">/docs</a> for API documentation.</p>
    <p>Version: {__version__}</p>
</body>
</html>
        """)

    html_content = ui_path.read_text()
    # Inject version into HTML
    html_content = html_content.replace("{{VERSION}}", __version__)
    return HTMLResponse(content=html_content)


@app.get("/manage", response_class=HTMLResponse)
async def manage():
    """Serve management UI"""
    ui_path = Path(__file__).parent / "ui" / "manage.html"

    if not ui_path.exists():
        # Return basic HTML if UI file doesn't exist yet
        return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Temoa Management</title>
</head>
<body>
    <h1>⚙︎ Temoa Management</h1>
    <p>Management UI coming soon.</p>
    <p><a href="/">Back to Search</a></p>
    <p>Version: {__version__}</p>
</body>
</html>
        """)

    html_content = ui_path.read_text()
    # Inject version into HTML
    html_content = html_content.replace("{{VERSION}}", __version__)
    return HTMLResponse(content=html_content)


@app.get("/favicon.svg")
async def favicon():
    """Serve favicon"""
    favicon_path = Path(__file__).parent / "ui" / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")


@app.get("/vaults")
async def list_vaults():
    """
    List available vaults with their status.

    Returns JSON with vault list and default vault.
    Each vault includes name, path, indexed status, and file count.
    """
    try:
        vaults = []

        for vault_config in config.get_all_vaults():
            vault_path = Path(vault_config["path"]).expanduser().resolve()

            # Derive storage dir
            from .storage import derive_storage_dir, get_vault_metadata
            storage_dir = derive_storage_dir(
                vault_path,
                config.vault_path,
                config.storage_dir
            )

            # Check if indexed
            metadata = get_vault_metadata(storage_dir)
            indexed = metadata is not None
            file_count = 0

            if indexed:
                # Try to get file count from metadata or stats
                try:
                    client, _, _ = get_client_for_vault(vault_config["name"])
                    stats = client.get_stats()
                    file_count = stats.get("total_files", 0)
                except Exception as e:
                    logger.warning(f"Could not get stats for vault {vault_config['name']}: {e}")

            vaults.append({
                "name": vault_config["name"],
                "path": str(vault_path),
                "is_default": vault_config.get("is_default", False),
                "indexed": indexed,
                "file_count": file_count
            })

        default_vault = config.get_default_vault()

        return JSONResponse(content={
            "vaults": vaults,
            "default_vault": default_vault["name"]
        })

    except Exception as e:
        logger.error(f"Error listing vaults: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list vaults: {str(e)}"
        )


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    ),
    limit: Optional[int] = Query(
        default=None,
        description="Maximum number of results",
        ge=1,
        le=100
    ),
    min_score: Optional[float] = Query(
        default=0.3,
        description="Minimum similarity score (0.0-1.0, default 0.3)",
        ge=0.0,
        le=1.0
    ),
    include_types: Optional[str] = Query(
        default=None,
        description="Comma-separated list of types to include (e.g., 'gleaning,article')"
    ),
    exclude_types: Optional[str] = Query(
        default="daily",
        description="Comma-separated list of types to exclude (default: 'daily')"
    ),
    hybrid: Optional[bool] = Query(
        default=None,
        description="Use hybrid search (BM25 + semantic). Defaults to config setting."
    ),
    model: Optional[str] = Query(
        default=None,
        description="Embedding model to use (optional)"
    )
):
    """
    Semantic search across vault using Synthesis.

    Returns JSON with search results including obsidian:// URIs for opening
    files directly in Obsidian.

    Example:
        GET /search?q=semantic+search&limit=5

    Returns:
        {
            "query": "semantic search",
            "results": [
                {
                    "title": "...",
                    "relative_path": "...",
                    "similarity_score": 0.85,
                    "obsidian_uri": "obsidian://vault/...",
                    "wiki_link": "[[...]]",
                    "description": "...",
                    ...
                }
            ],
            "total": 5,
            "model": "all-MiniLM-L6-v2"
        }
    """
    # Apply default limit if not specified
    if limit is None:
        limit = config.search_default_limit

    # Enforce maximum limit
    if limit > config.search_max_limit:
        limit = config.search_max_limit

    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(vault)

        # Parse type filters
        include_type_list = None
        if include_types:
            include_type_list = [t.strip() for t in include_types.split(",") if t.strip()]

        exclude_type_list = None
        if exclude_types:
            exclude_type_list = [t.strip() for t in exclude_types.split(",") if t.strip()]

        # Determine whether to use hybrid search
        use_hybrid = hybrid if hybrid is not None else config.hybrid_search_enabled

        logger.info(f"Search: vault='{vault_name}', query='{q}', limit={limit}, min_score={min_score}, include_types={include_type_list}, exclude_types={exclude_type_list}, hybrid={use_hybrid}, model={model or 'default'}")

        # Note: model parameter not supported yet in current wrapper
        # Would require reinitializing Synthesis with different model
        if model and model != config.default_model:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Model selection not yet implemented",
                    "message": f"Currently only {config.default_model} is supported",
                    "current_model": config.default_model
                }
            )

        # Perform search (request more results to account for filtering)
        search_limit = limit * 2 if limit else 50

        # Choose search method
        if use_hybrid:
            try:
                data = synthesis.hybrid_search(query=q, limit=search_limit)
            except SynthesisError as e:
                # Fall back to semantic search if hybrid fails
                logger.warning(f"Hybrid search failed, falling back to semantic: {e}")
                data = synthesis.search(query=q, limit=search_limit)
                data["search_mode"] = "semantic (hybrid fallback)"
        else:
            data = synthesis.search(query=q, limit=search_limit)

        # Filter by similarity score (but not in hybrid mode)
        results = data.get("results", [])

        if use_hybrid:
            # In hybrid mode, RRF has already ranked results appropriately
            # Don't filter by similarity score since BM25-only results may not have one
            score_filtered = results
            score_removed = 0
        else:
            # In semantic-only mode, filter by similarity threshold
            score_filtered = [r for r in results if r.get("similarity_score", 0) >= min_score]
            score_removed = len(results) - len(score_filtered)
            if score_removed > 0:
                logger.info(f"Filtered {score_removed} results below min_score={min_score}")

        # Filter out inactive gleanings
        original_count = len(score_filtered)
        filtered_results = filter_inactive_gleanings(score_filtered)
        status_removed = original_count - len(filtered_results)

        if status_removed > 0:
            logger.info(f"Filtered {status_removed} inactive gleanings from results")

        # Filter by type
        filtered_results, type_removed = filter_by_type(
            filtered_results,
            include_types=include_type_list,
            exclude_types=exclude_type_list
        )

        if type_removed > 0:
            logger.info(f"Filtered {type_removed} results by type (include={include_type_list}, exclude={exclude_type_list})")

        # Apply final limit
        filtered_results = filtered_results[:limit] if limit else filtered_results

        # Update response
        data["results"] = filtered_results
        data["total"] = len(filtered_results)
        data["min_score"] = min_score
        data["filtered_count"] = {
            "by_score": score_removed,
            "by_status": status_removed,
            "by_type": type_removed,
            "total_removed": score_removed + status_removed + type_removed
        }

        # Add vault information to response
        data["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        return JSONResponse(content=data)

    except SynthesisError as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/archaeology")
async def archaeology(
    q: str = Query(..., description="Topic to analyze", min_length=1),
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    ),
    threshold: float = Query(
        default=0.2,
        description="Similarity threshold (0.0-1.0)",
        ge=0.0,
        le=1.0
    ),
    exclude_daily: bool = Query(
        default=False,
        description="Exclude daily notes from analysis"
    )
):
    """
    Temporal archaeology analysis - track interest evolution over time.

    Analyzes when interest in a topic peaked across your vault's history
    by examining document similarity scores and temporal patterns.

    The analysis uses top 50 most similar documents (hardcoded in Synthesis).

    Example:
        GET /archaeology?q=machine+learning&threshold=0.2

    Returns:
        {
            "query": "machine learning",
            "threshold": 0.2,
            "entries": [{"date": "2024-01-01", "content": "...", "similarity_score": 0.8}],
            "intensity_by_month": {"2024-01": 0.75},
            "activity_by_month": {"2024-01": 5},
            "peak_periods": [{"month": "2024-01", "intensity": 0.75}],
            "dormant_periods": ["2024-02"],
            "model": "all-mpnet-base-v2"
        }
    """
    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(vault)

        logger.info(f"Archaeology: vault='{vault_name}', query='{q}', threshold={threshold}, exclude_daily={exclude_daily}")

        data = synthesis.archaeology(
            query=q,
            threshold=threshold,
            exclude_daily=exclude_daily
        )

        # Add vault information to response
        data["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        return JSONResponse(content=data)

    except SynthesisError as e:
        logger.error(f"Archaeology error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Archaeology failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/stats")
async def stats(
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    )
):
    """
    Get statistics about indexed vault.

    Returns:
        {
            "file_count": 1234,
            "model_info": {...},
            "embedding_dim": 384,
            ...
        }
    """
    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(vault)

        logger.debug(f"Retrieving stats for vault: {vault_name}")

        data = synthesis.get_stats()

        # Add vault information to response
        data["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        return JSONResponse(content=data)

    except SynthesisError as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/health")
async def health():
    """
    Health check endpoint.

    Returns server status and Synthesis connectivity.
    """
    try:
        # Quick test that Synthesis is accessible
        stats = synthesis.get_stats()

        return JSONResponse(content={
            "status": "healthy",
            "synthesis": "connected",
            "model": config.default_model,
            "vault": str(config.vault_path),
            "files_indexed": stats.get("total_files") or stats.get("file_count", 0)
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "synthesis": "error",
                "error": str(e)
            }
        )


@app.post("/reindex")
async def reindex(
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    ),
    force: bool = Query(
        default=True,
        description="Force rebuild even if embeddings exist"
    )
):
    """
    Trigger re-indexing of the vault.

    This rebuilds embeddings for all files in the vault. Useful after:
    - Extracting new gleanings
    - Modifying existing notes
    - Adding files to vault

    Example:
        POST /reindex?force=true

    Returns:
        {
            "status": "success",
            "files_indexed": 516,
            "model": "all-MiniLM-L6-v2",
            "message": "Successfully reindexed 516 files"
        }
    """
    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(vault)

        logger.info(f"Reindex requested for vault '{vault_name}' (force={force})")

        result = synthesis.reindex(force=force)

        # Invalidate cache after reindex to ensure fresh data on next access
        client_cache.invalidate(vault_path, config.default_model)

        # Add vault information to response
        result["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        return JSONResponse(content=result)

    except SynthesisError as e:
        logger.error(f"Reindex error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Reindexing failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during reindex: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/extract")
async def extract_gleanings(
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    ),
    incremental: bool = Query(
        default=True,
        description="Incremental mode (only new files) or full re-extraction"
    ),
    auto_reindex: bool = Query(
        default=True,
        description="Automatically re-index after extraction"
    )
):
    """
    Extract gleanings from daily notes.

    This scans daily notes for gleanings (links with descriptions) and creates
    individual gleaning notes in L/Gleanings/.

    Example:
        POST /extract?incremental=true&auto_reindex=true

    Returns:
        {
            "status": "success",
            "total_gleanings": 10,
            "new_gleanings": 5,
            "duplicates_skipped": 5,
            "files_processed": 3,
            "reindexed": true
        }
    """
    if GleaningsExtractor is None:
        raise HTTPException(
            status_code=500,
            detail="Gleaning extraction not available (import failed)"
        )

    try:
        # Get client for specified vault (for reindex later)
        synthesis, vault_path, vault_name = get_client_for_vault(vault)

        logger.info(f"Extraction requested for vault '{vault_name}' (incremental={incremental}, auto_reindex={auto_reindex})")

        # Initialize extractor
        extractor = GleaningsExtractor(vault_path)

        # Find notes to process
        daily_notes = extractor.find_daily_notes(incremental=incremental)

        if not incremental:
            # Clear state for full re-extraction
            extractor.state = {
                "version": "1.0",
                "created_at": extractor.state["created_at"],
                "last_run": None,
                "extracted_gleanings": {},
                "processed_files": []
            }

        output_dir = config.vault_path / "L" / "Gleanings"
        total_gleanings = 0
        new_gleanings = 0
        duplicate_gleanings = 0

        for note_path in daily_notes:
            gleanings = extractor.extract_from_note(note_path)

            for gleaning in gleanings:
                total_gleanings += 1

                # Check for duplicates
                if gleaning.gleaning_id in extractor.state["extracted_gleanings"]:
                    duplicate_gleanings += 1
                    logger.debug(f"Duplicate gleaning: {gleaning.title[:60]}...")
                    continue

                # Create gleaning note
                extractor.create_gleaning_note(gleaning, output_dir, dry_run=False)
                new_gleanings += 1

                # Update state
                extractor.state["extracted_gleanings"][gleaning.gleaning_id] = gleaning.to_dict()

            # Mark file as processed
            rel_path = str(note_path.relative_to(vault_path))
            if rel_path not in extractor.state["processed_files"]:
                extractor.state["processed_files"].append(rel_path)

        # Save state
        extractor._save_state()

        logger.info(
            f"Extraction complete: {new_gleanings} new, "
            f"{duplicate_gleanings} duplicates, "
            f"{len(daily_notes)} files processed"
        )

        result = {
            "status": "success",
            "total_gleanings": total_gleanings,
            "new_gleanings": new_gleanings,
            "duplicates_skipped": duplicate_gleanings,
            "files_processed": len(daily_notes),
            "message": f"Extracted {new_gleanings} new gleanings from {len(daily_notes)} files"
        }

        # Auto-reindex if requested and new gleanings were created
        if auto_reindex and new_gleanings > 0:
            logger.info("Auto-reindexing after extraction...")
            try:
                reindex_result = synthesis.reindex(force=True)
                # Invalidate cache after reindex
                client_cache.invalidate(vault_path, config.default_model)
                result["reindexed"] = True
                result["files_indexed"] = reindex_result.get("files_indexed", 0)
            except Exception as e:
                logger.warning(f"Auto-reindex failed: {e}")
                result["reindexed"] = False
                result["reindex_error"] = str(e)
        else:
            result["reindexed"] = False

        # Add vault information to response
        result["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        return JSONResponse(content=result)

    except FileNotFoundError as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during extraction: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(e)}"
        )


@app.post("/gleanings/{gleaning_id}/status")
async def mark_gleaning_status(
    gleaning_id: str,
    status: str = Query(..., regex="^(active|inactive)$", description="Status to set"),
    reason: Optional[str] = Query(None, description="Optional reason for status change")
):
    """
    Mark a gleaning as active or inactive.

    This doesn't modify the source daily note (which is the source of truth),
    but marks the extracted gleaning file so it can be excluded from searches.

    Example:
        POST /gleanings/abc123def456/status?status=inactive&reason=broken%20link

    Returns:
        {
            "gleaning_id": "abc123def456",
            "status": "inactive",
            "marked_at": "2025-11-20T15:30:00Z",
            "reason": "broken link"
        }
    """
    try:
        logger.info(f"Marking gleaning {gleaning_id} as {status}")

        record = gleaning_manager.mark_status(gleaning_id, status, reason)

        return JSONResponse(content={
            "gleaning_id": gleaning_id,
            **record
        })

    except Exception as e:
        logger.error(f"Error marking gleaning status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark gleaning status: {str(e)}"
        )


@app.get("/gleanings")
async def list_gleanings(
    status: Optional[str] = Query(
        None,
        regex="^(active|inactive)$",
        description="Filter by status (omit for all)"
    )
):
    """
    List all gleanings from the vault by scanning L/Gleanings/ directory.

    Example:
        GET /gleanings
        GET /gleanings?status=inactive
        GET /gleanings?status=active

    Returns:
        {
            "gleanings": [
                {
                    "gleaning_id": "abc123def456",
                    "title": "Example Title",
                    "url": "https://example.com",
                    "status": "inactive",
                    "created": "2025-11-20",
                    "file_path": "L/Gleanings/abc123def456.md"
                },
                ...
            ],
            "total": 5,
            "filter": "inactive"
        }
    """
    try:
        gleanings_list = scan_gleaning_files(
            vault_path=config.vault_path,
            status_manager=gleaning_manager,
            status_filter=status
        )

        return JSONResponse(content={
            "gleanings": gleanings_list,
            "total": len(gleanings_list),
            "filter": status or "all"
        })

    except Exception as e:
        logger.error(f"Error listing gleanings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list gleanings: {str(e)}"
        )


@app.get("/gleanings/{gleaning_id}")
async def get_gleaning(gleaning_id: str):
    """
    Get status details for a specific gleaning.

    Example:
        GET /gleanings/abc123def456

    Returns:
        {
            "gleaning_id": "abc123def456",
            "status": "inactive",
            "marked_at": "2025-11-20T15:30:00Z",
            "reason": "broken link",
            "history": [...]
        }
    """
    try:
        record = gleaning_manager.get_gleaning_record(gleaning_id)

        if not record:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Gleaning not found or has default status (active)",
                    "gleaning_id": gleaning_id
                }
            )

        return JSONResponse(content={
            "gleaning_id": gleaning_id,
            **record
        })

    except Exception as e:
        logger.error(f"Error getting gleaning: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get gleaning: {str(e)}"
        )



