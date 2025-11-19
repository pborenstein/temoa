"""FastAPI server for Temoa semantic search"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import Config, ConfigError
from .synthesis import SynthesisClient, SynthesisError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
        model=config.default_model
    )
    logger.info("✓ Synthesis client ready")
except SynthesisError as e:
    logger.error(f"Failed to initialize Synthesis: {e}")
    raise


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


