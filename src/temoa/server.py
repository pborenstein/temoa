"""FastAPI server for Temoa semantic search"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import Config, ConfigError
from .synthesis import SynthesisClient, SynthesisError
from .gleanings import parse_frontmatter_status, GleaningStatusManager, scan_gleaning_files

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

# Initialize Synthesis client (loads model once at startup)
try:
    logger.info("Initializing Synthesis client (this may take 10-20 seconds)...")
    synthesis = SynthesisClient(
        synthesis_path=config.synthesis_path,
        vault_path=config.vault_path,
        model=config.default_model,
        storage_dir=config.storage_dir
    )
    logger.info("✓ Synthesis client ready")
except SynthesisError as e:
    logger.error(f"Failed to initialize Synthesis: {e}")
    raise

# Initialize Gleaning status manager
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


def filter_inactive_gleanings(results: list) -> list:
    """
    Filter out inactive gleanings from search results.

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
            # If status is inactive, skip this result
            elif status == "inactive":
                logger.debug(f"Filtered out inactive gleaning: {result.get('title', 'Unknown')}")
                continue

        except Exception as e:
            # If we can't read file, include it anyway (fail open)
            logger.warning(f"Error checking status for {file_path}: {e}")
            filtered.append(result)

    return filtered


# Create FastAPI app
app = FastAPI(
    title="Temoa",
    description="Local semantic search server for Obsidian vault",
    version="0.1.0",
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
        return HTMLResponse(content="""
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
</body>
</html>
        """)

    html_content = ui_path.read_text()
    return HTMLResponse(content=html_content)


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    limit: Optional[int] = Query(
        default=None,
        description="Maximum number of results",
        ge=1,
        le=100
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
        logger.info(f"Search: query='{q}', limit={limit}, model={model or 'default'}")

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

        # Perform search
        data = synthesis.search(query=q, limit=limit)

        # Filter out inactive gleanings
        original_count = len(data.get("results", []))
        data["results"] = filter_inactive_gleanings(data.get("results", []))
        filtered_count = len(data["results"])

        if filtered_count < original_count:
            logger.info(f"Filtered {original_count - filtered_count} inactive gleanings from results")

        # Update total count
        data["total"] = filtered_count

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
    threshold: float = Query(
        default=0.2,
        description="Similarity threshold (0.0-1.0)",
        ge=0.0,
        le=1.0
    ),
    top_k: int = Query(
        default=100,
        description="Number of documents to analyze",
        ge=10,
        le=500
    )
):
    """
    Temporal archaeology analysis - track interest evolution over time.

    Analyzes when interest in a topic peaked across your vault's history
    by examining document similarity scores and temporal patterns.

    Example:
        GET /archaeology?q=machine+learning&threshold=0.2

    Returns:
        {
            "query": "machine learning",
            "threshold": 0.2,
            "timeline": [...],
            "model": "all-MiniLM-L6-v2"
        }
    """
    try:
        logger.info(f"Archaeology: query='{q}', threshold={threshold}, top_k={top_k}")

        data = synthesis.archaeology(
            query=q,
            threshold=threshold,
            top_k=top_k
        )

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
async def stats():
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
        logger.debug("Retrieving vault stats")

        data = synthesis.get_stats()

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
        logger.info(f"Reindex requested (force={force})")

        result = synthesis.reindex(force=force)

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
        logger.info(f"Extraction requested (incremental={incremental}, auto_reindex={auto_reindex})")

        # Initialize extractor
        extractor = GleaningsExtractor(config.vault_path)

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
            rel_path = str(note_path.relative_to(config.vault_path))
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
                result["reindexed"] = True
                result["files_indexed"] = reindex_result.get("files_indexed", 0)
            except Exception as e:
                logger.warning(f"Auto-reindex failed: {e}")
                result["reindexed"] = False
                result["reindex_error"] = str(e)
        else:
            result["reindexed"] = False

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



