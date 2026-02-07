"""FastAPI server for Temoa semantic search"""
import logging
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .__version__ import __version__
from .config import Config, ConfigError
from .synthesis import SynthesisClient, SynthesisError
from .gleanings import GleaningStatusManager, scan_gleaning_files
from .client_cache import ClientCache
from .reranker import CrossEncoderReranker
from .query_expansion import QueryExpander
from .time_scoring import TimeAwareScorer
from .rate_limiter import RateLimiter
from .vault_graph import VaultGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import extraction functionality
try:
    from .scripts.extract_gleanings import GleaningsExtractor
except ImportError as e:
    logger.warning(f"Could not import GleaningsExtractor: {e}")
    GleaningsExtractor = None


def sanitize_unicode(obj):
    """
    Recursively sanitize Unicode surrogates in strings.

    Replaces invalid surrogate pairs with replacement character.
    This prevents UnicodeEncodeError when serializing to JSON.
    """
    if isinstance(obj, str):
        # Replace surrogates with Unicode replacement character
        return obj.encode('utf-8', errors='replace').decode('utf-8')
    elif isinstance(obj, dict):
        return {k: sanitize_unicode(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_unicode(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_unicode(item) for item in obj)
    else:
        return obj


# Pipeline debugging helper functions
def format_result_preview(results, max_results=20):
    """
    Format results for pipeline debugging (path + key scores).

    Args:
        results: List of search results
        max_results: Maximum number of results to include

    Returns:
        List of preview dicts with path and score info
    """
    previews = []
    for result in results[:max_results]:
        preview = {
            "relative_path": result.get("relative_path", ""),
            "title": result.get("title", ""),
        }
        # Add available scores
        if "similarity_score" in result:
            preview["similarity_score"] = round(result["similarity_score"], 4)
        if "bm25_score" in result:
            preview["bm25_score"] = round(result["bm25_score"], 2)
        if "rrf_score" in result:
            preview["rrf_score"] = round(result["rrf_score"], 4)
        if "cross_encoder_score" in result:
            preview["cross_encoder_score"] = round(result["cross_encoder_score"], 4)
        if "time_boost" in result:
            preview["time_boost"] = round(result["time_boost"], 4)
        if "tag_boosted" in result:
            preview["tag_boosted"] = result["tag_boosted"]
        if "tags_matched" in result:
            preview["tags_matched"] = result["tags_matched"]

        previews.append(preview)

    return previews


def calculate_rank_changes(before, after):
    """
    Calculate rank changes between two result orderings.

    Args:
        before: List of results before transformation
        after: List of results after transformation

    Returns:
        List of dicts with rank change info
    """
    # Build path->rank maps
    before_ranks = {r.get("relative_path"): idx for idx, r in enumerate(before)}
    after_ranks = {r.get("relative_path"): idx for idx, r in enumerate(after)}

    # Calculate changes for results that appear in both
    changes = []
    for path in after_ranks:
        if path in before_ranks:
            before_rank = before_ranks[path]
            after_rank = after_ranks[path]
            delta = before_rank - after_rank  # Positive = moved up

            if delta != 0:
                changes.append({
                    "relative_path": path,
                    "title": after[after_rank].get("title", ""),
                    "before_rank": before_rank + 1,  # 1-indexed for display
                    "after_rank": after_rank + 1,
                    "delta": delta
                })

    # Sort by magnitude of change
    changes.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return changes


def capture_stage_state(stage_num, stage_name, results, metadata, start_time):
    """
    Capture state snapshot for a pipeline stage.

    Args:
        stage_num: Stage number (0-7)
        stage_name: Human-readable stage name
        results: Current result list
        metadata: Stage-specific metadata (counts, settings, etc.)
        start_time: Time when stage started (from time.time())

    Returns:
        Dict with stage state
    """
    import time

    return {
        "stage_num": stage_num,
        "stage_name": stage_name,
        "result_count": len(results),
        "results_preview": format_result_preview(results, max_results=20),
        "metadata": metadata,
        "timing_ms": round((time.time() - start_time) * 1000, 1)
    }


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.

    Initializes all server dependencies in proper order and stores them in app.state
    for access by endpoint handlers.
    """
    # Startup - Initialize all dependencies
    logger.info("=" * 60)
    logger.info("Temoa server starting...")

    try:
        # Load configuration
        config = Config()
        logger.info(f"  ✓ Configuration loaded")

        # Initialize client cache for multi-vault support
        cache_size = config._config.get("server", {}).get("client_cache_size", 3)
        client_cache = ClientCache(max_size=cache_size)
        logger.info(f"  ✓ Client cache initialized (max_size={cache_size})")

        # Pre-warm cache with default vault
        logger.info("  ⏳ Pre-warming cache with default vault (this may take 10-20 seconds)...")
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
        logger.info("  ✓ Default vault client ready")

        # Initialize Gleaning status manager (uses default vault)
        gleaning_manager = GleaningStatusManager(config.vault_path / ".temoa")
        logger.info("  ✓ Gleaning manager initialized")

        # Initialize cross-encoder reranker for search quality improvement
        logger.info("  ⏳ Loading cross-encoder model (this may take 2-3 seconds)...")
        reranker = CrossEncoderReranker()
        logger.info("  ✓ Cross-encoder reranker ready")

        # Initialize query expander for short query handling
        query_expander = QueryExpander(max_expansion_terms=3)
        logger.info("  ✓ Query expander initialized")

        # Initialize time-aware scorer for recency boost
        time_decay_config = config._config.get("search", {}).get("time_decay", {})
        time_scorer = TimeAwareScorer(
            half_life_days=time_decay_config.get("half_life_days", 90),
            max_boost=time_decay_config.get("max_boost", 0.2),
            enabled=time_decay_config.get("enabled", True)
        )
        logger.info("  ✓ Time-aware scorer initialized")

        # Initialize vault graph cache (lazy loading per vault)
        vault_graphs = {}
        logger.info("  ✓ Vault graph cache initialized (lazy loading)")

        # Store in app.state for access by endpoints
        app.state.config = config
        app.state.client_cache = client_cache
        app.state.gleaning_manager = gleaning_manager
        app.state.reranker = reranker
        app.state.query_expander = query_expander
        app.state.time_scorer = time_scorer
        app.state.vault_graphs = vault_graphs

        logger.info("=" * 60)
        logger.info(f"Temoa server ready")
        logger.info(f"  Vault: {config.vault_path}")
        logger.info(f"  Model: {config.default_model}")
        logger.info(f"  Synthesis: {config.synthesis_path}")
        logger.info(f"  Server: http://{config.server_host}:{config.server_port}")
        logger.info("=" * 60)

    except (ConfigError, SynthesisError, IOError, OSError, ImportError, RuntimeError) as e:
        # Expected initialization failures - log and re-raise
        logger.error(f"Failed to initialize server: {e}")
        raise
    except Exception as e:
        # Unexpected initialization error - log with traceback and re-raise
        logger.error(f"Unexpected error during server initialization: {e}", exc_info=True)
        raise

    yield

    # Shutdown - Clean up resources
    logger.info("Temoa server shutting down...")
    # Add cleanup here if needed (e.g., closing connections, saving state)
    logger.info("✓ Server shutdown complete")


def get_client_for_vault(request, vault_identifier: Optional[str] = None) -> tuple[SynthesisClient, Path, str]:
    """
    Get SynthesisClient for specified vault.

    Args:
        request: FastAPI Request object (for accessing app.state)
        vault_identifier: Vault name, path, or None (use default)

    Returns:
        (client, vault_path, vault_name) tuple

    Raises:
        HTTPException: If vault not found or invalid
    """
    config = request.app.state.config
    client_cache = request.app.state.client_cache

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
        # Try to get status from cached frontmatter in results first (no file I/O!)
        frontmatter_data = result.get("frontmatter")

        if frontmatter_data is not None:
            # Use cached frontmatter from Synthesis results
            status = frontmatter_data.get("status", "active")

            # If status is inactive or hidden, skip this result
            if status in ("inactive", "hidden"):
                logger.debug(f"Filtered out {status} gleaning: {result.get('title', 'Unknown')}")
                continue

            # Status is active or not specified, include result
            filtered.append(result)
        else:
            # No frontmatter in results - this shouldn't happen often
            # since Synthesis includes frontmatter, but handle gracefully
            # by including the result (fail open)
            logger.debug(f"No frontmatter in result for {result.get('title', 'Unknown')}, including")
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
                from nahuatl_frontmatter import parse_file
                metadata, _ = parse_file(file_path)
                types = parse_type_field(metadata or {})
            except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError) as e:
                # Fail-open: include file even if frontmatter can't be read
                logger.debug(f"Error reading frontmatter for {file_path}: {e}")
                types = []
            except Exception as e:
                # Unexpected error - log as warning but still fail-open
                logger.warning(f"Unexpected error reading frontmatter for {file_path}: {e}")
                types = []

        # Infer type if not explicitly set:
        # - If gleaning_id exists → type: gleaning
        # - Otherwise → type: none
        if not types:
            if frontmatter_data and frontmatter_data.get("gleaning_id"):
                types = ["gleaning"]
            else:
                types = ["none"]

        # Apply inclusive filter
        if include_types:
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


def filter_by_properties(
    results: list,
    include_props: list[dict] | None = None,
    exclude_props: list[dict] | None = None
) -> tuple[list, int]:
    """
    Filter results by any frontmatter property.

    Args:
        results: Search results from Synthesis
        include_props: If set, only include results matching these properties
                      Format: [{"prop": "type", "value": "gleaning"}, ...]
        exclude_props: If set, exclude results matching these properties
                      Format: [{"prop": "status", "value": "archived"}, ...]

    Returns:
        (filtered_results, num_filtered_out)

    Logic:
        - If include_props: Keep only if ANY property matches
        - If exclude_props: Remove if ANY property matches
        - If both: Apply include first, then exclude
        - Property values compared as strings (case-sensitive)
    """
    if not include_props and not exclude_props:
        return results, 0

    filtered = []

    for result in results:
        frontmatter_data = result.get("frontmatter", {})

        # Apply inclusive filter
        if include_props:
            match_found = False
            for prop_filter in include_props:
                prop_name = prop_filter.get("prop")
                prop_value = prop_filter.get("value")
                if not prop_name or not prop_value:
                    continue

                # Get the property value from frontmatter
                fm_value = frontmatter_data.get(prop_name)
                if fm_value is None:
                    continue

                # Compare as strings
                if str(fm_value).lower() == str(prop_value).lower():
                    match_found = True
                    break

            if not match_found:
                continue

        # Apply exclusive filter
        if exclude_props:
            should_exclude = False
            for prop_filter in exclude_props:
                prop_name = prop_filter.get("prop")
                prop_value = prop_filter.get("value")
                if not prop_name or not prop_value:
                    continue

                fm_value = frontmatter_data.get(prop_name)
                if fm_value is None:
                    continue

                if str(fm_value).lower() == str(prop_value).lower():
                    should_exclude = True
                    logger.debug(f"Filtered out {prop_name}={fm_value}: {result.get('title', 'Unknown')}")
                    break

            if should_exclude:
                continue

        filtered.append(result)

    num_filtered = len(results) - len(filtered)
    return filtered, num_filtered


def filter_by_tags(
    results: list,
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None
) -> tuple[list, int]:
    """
    Filter results by tags in frontmatter or content.

    Args:
        results: Search results from Synthesis
        include_tags: If set, only include results with these tags (OR logic)
        exclude_tags: If set, exclude results with these tags (OR logic)

    Returns:
        (filtered_results, num_filtered_out)
    """
    if not include_tags and not exclude_tags:
        return results, 0

    filtered = []

    for result in results:
        # Get tags from frontmatter (already parsed by Synthesis)
        frontmatter_data = result.get("frontmatter", {})
        tags = frontmatter_data.get("tags", [])

        # Normalize tags (remove # prefix if present, lowercase)
        if isinstance(tags, str):
            tags = [tags]
        tags = [t.lstrip('#').lower() for t in tags] if tags else []

        # Apply inclusive filter
        if include_tags:
            normalized_include = [t.lstrip('#').lower() for t in include_tags]
            if not any(t in tags for t in normalized_include):
                continue

        # Apply exclusive filter
        if exclude_tags:
            normalized_exclude = [t.lstrip('#').lower() for t in exclude_tags]
            if any(t in tags for t in normalized_exclude):
                logger.debug(f"Filtered out tags {tags}: {result.get('title', 'Unknown')}")
                continue

        filtered.append(result)

    num_filtered = len(results) - len(filtered)
    return filtered, num_filtered


def filter_by_paths(
    results: list,
    include_paths: list[str] | None = None,
    exclude_paths: list[str] | None = None
) -> tuple[list, int]:
    """
    Filter results by file path patterns.

    Args:
        results: Search results from Synthesis
        include_paths: If set, only include results with paths containing these patterns
        exclude_paths: If set, exclude results with paths containing these patterns

    Returns:
        (filtered_results, num_filtered_out)
    """
    if not include_paths and not exclude_paths:
        return results, 0

    filtered = []

    for result in results:
        file_path = result.get("file_path", "")

        # Apply inclusive filter
        if include_paths:
            if not any(pattern in file_path for pattern in include_paths):
                continue

        # Apply exclusive filter
        if exclude_paths:
            if any(pattern in file_path for pattern in exclude_paths):
                logger.debug(f"Filtered out path {file_path}")
                continue

        filtered.append(result)

    num_filtered = len(results) - len(filtered)
    return filtered, num_filtered


def filter_by_files(
    results: list,
    include_files: list[str] | None = None,
    exclude_files: list[str] | None = None
) -> tuple[list, int]:
    """
    Filter results by filename patterns.

    Args:
        results: Search results from Synthesis
        include_files: If set, only include results with filenames containing these patterns
        exclude_files: If set, exclude results with filenames containing these patterns

    Returns:
        (filtered_results, num_filtered_out)
    """
    if not include_files and not exclude_files:
        return results, 0

    from pathlib import Path
    filtered = []

    for result in results:
        file_path = result.get("file_path", "")
        filename = Path(file_path).name

        # Apply inclusive filter
        if include_files:
            if not any(pattern in filename for pattern in include_files):
                continue

        # Apply exclusive filter
        if exclude_files:
            if any(pattern in filename for pattern in exclude_files):
                logger.debug(f"Filtered out file {filename}")
                continue

        filtered.append(result)

    num_filtered = len(results) - len(filtered)
    return filtered, num_filtered


def build_file_filter(
    synthesis,
    vault_path: Path,
    include_props: list[dict] | None = None,
    include_tags: list[str] | None = None,
    include_paths: list[str] | None = None,
    include_files: list[str] | None = None
) -> list[str] | None:
    """
    Build a file filter list from Query Filter parameters.

    This enables pre-filtering BEFORE semantic search, which dramatically
    improves performance for inclusive filters (e.g., [type:daily]).

    Without pre-filtering:
        - Search ALL 3,000 vault files (30+ seconds)
        - Filter to 50 matching files
        - Return 20 results

    With pre-filtering:
        - Determine 50 files match filter criteria (1-2 seconds)
        - Search ONLY those 50 files (2-3 seconds)
        - Return 20 results
        Total: 3-5 seconds (6-10x faster!)

    Args:
        synthesis: SynthesisClient instance with access to VaultReader
        vault_path: Path to vault root
        include_props: Property filters (e.g., [{"prop": "type", "value": "daily"}])
        include_tags: Tag filters (e.g., ["python", "ai"])
        include_paths: Path filters (e.g., ["Gleanings", "Projects"])
        include_files: Filename filters (e.g., ["README", "index"])

    Returns:
        List of relative file paths to search, or None if no filters applied
    """
    # Only build filter if we have INCLUSIVE filters
    # Exclusive filters are fast (search limited set → filter), no need to pre-filter
    if not any([include_props, include_tags, include_paths, include_files]):
        return None

    logger.info(f"Building file filter from Query Filter parameters...")
    filter_start = time.time()

    # Get all vault files via VaultReader
    vault_reader = synthesis.pipeline.reader
    all_files = vault_reader.discover_files()

    if not all_files:
        logger.warning("No vault files found, cannot build file filter")
        return None

    logger.info(f"Filtering {len(all_files)} vault files...")

    # Apply filters to build allowed file list
    file_filter = []

    for file_path in all_files:
        # Read file to get frontmatter and metadata
        # Note: VaultReader caches frontmatter, so this should be fast
        try:
            content = vault_reader.read_file(file_path)
            if not content:
                continue

            frontmatter = content.frontmatter or {}
            tags = content.tags or []
            relative_path = str(file_path.relative_to(vault_path))
            filename = file_path.name

            # Apply property filters
            if include_props:
                match_found = False
                for prop_filter in include_props:
                    prop_name = prop_filter.get("prop")
                    prop_value = prop_filter.get("value")
                    if not prop_name or not prop_value:
                        continue

                    fm_value = frontmatter.get(prop_name)
                    if fm_value is None:
                        continue

                    if str(fm_value).lower() == str(prop_value).lower():
                        match_found = True
                        break

                if not match_found:
                    continue

            # Apply tag filters
            if include_tags:
                if not tags:
                    continue
                tags_lower = [str(tag).lower() for tag in tags]
                if not any(tag.lower() in tags_lower for tag in include_tags):
                    continue

            # Apply path filters
            if include_paths:
                if not any(pattern in relative_path for pattern in include_paths):
                    continue

            # Apply file filters
            if include_files:
                if not any(pattern in filename for pattern in include_files):
                    continue

            # All filters passed, include this file
            file_filter.append(relative_path)

        except Exception as e:
            logger.debug(f"Error reading file {file_path} for filter: {e}")
            continue

    filter_duration = time.time() - filter_start
    logger.info(f"File filter built: {len(file_filter)} files (from {len(all_files)} total) in {filter_duration:.2f}s")

    # Return None if no files matched (let search handle empty results)
    if not file_filter:
        logger.warning("File filter matched 0 files")
        return []

    return file_filter


# Determine CORS allowed origins
# Priority: 1. Environment variable, 2. Config file, 3. Safe defaults
cors_origins_env = os.getenv("TEMOA_CORS_ORIGINS", "").strip()
if cors_origins_env:
    # Environment variable takes precedence (comma-separated list)
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Try to load config for CORS settings, but provide defaults if not available
    try:
        _early_config = Config()
        allowed_origins = _early_config._config.get("server", {}).get("cors_origins", None)
        server_port = _early_config._config.get("server", {}).get("port", 8080)
    except ConfigError:
        # Config not available (e.g., during testing) - use safe defaults
        allowed_origins = None
        server_port = 8080

    if not allowed_origins:
        # Default: localhost only with configured port
        allowed_origins = [
            f"http://localhost:{server_port}",
            f"http://127.0.0.1:{server_port}",
        ]

        # Add Tailscale IP if available
        tailscale_ip = os.getenv("TAILSCALE_IP", "").strip()
        if tailscale_ip:
            allowed_origins.append(f"http://{tailscale_ip}:{server_port}")
            logger.info(f"Added Tailscale IP to CORS origins: {tailscale_ip}")

# Warn if wildcard is used
if "*" in allowed_origins:
    logger.warning("⚠️  CORS wildcard (*) enabled - this is insecure for production!")
    logger.warning("   Set TEMOA_CORS_ORIGINS environment variable or server.cors_origins in config")

logger.info(f"CORS allowed origins: {allowed_origins}")

# Create FastAPI app
app = FastAPI(
    title="Temoa",
    description="Local semantic search server for Obsidian vault",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware with restrictive defaults
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter for DoS protection
rate_limiter = RateLimiter()


def get_rate_limit(endpoint: str) -> int:
    """
    Get rate limit for an endpoint from config or use defaults.

    Args:
        endpoint: Endpoint name (search, archaeology, reindex, extract)

    Returns:
        Rate limit (requests per hour)
    """
    defaults = {
        "search": 1000,
        "archaeology": 20,
        "reindex": 5,
        "extract": 10
    }

    try:
        # Try to get from _early_config if it was loaded
        if '_early_config' in globals():
            rate_limits = _early_config._config.get("rate_limits", {})
            return rate_limits.get(f"{endpoint}_per_hour", defaults[endpoint])
    except (NameError, AttributeError, KeyError):
        pass

    return defaults[endpoint]


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


@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest"""
    manifest_path = Path(__file__).parent / "ui" / "manifest.json"
    if manifest_path.exists():
        return FileResponse(manifest_path, media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest not found")


@app.get("/sw.js")
async def service_worker():
    """Serve service worker"""
    sw_path = Path(__file__).parent / "ui" / "sw.js"
    if sw_path.exists():
        return FileResponse(sw_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker not found")


@app.get("/icon-192.png")
async def icon_192():
    """Serve 192x192 PWA icon"""
    icon_path = Path(__file__).parent / "ui" / "icon-192.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/icon-512.png")
async def icon_512():
    """Serve 512x512 PWA icon"""
    icon_path = Path(__file__).parent / "ui" / "icon-512.png"
    if icon_path.exists():
        return FileResponse(icon_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Icon not found")


@app.get("/vaults")
async def list_vaults(request: Request):
    """
    List available vaults with their status.

    Returns JSON with vault list and default vault.
    Each vault includes name, path, indexed status, and file count.
    """
    config = request.app.state.config

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

            # Check if indexed (pass model to check model-specific subdirectory)
            metadata = get_vault_metadata(storage_dir, config.default_model)
            indexed = metadata is not None
            file_count = metadata.get("file_count", 0) if metadata else 0

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


@app.get("/config")
async def get_config(request: Request, vault: str = None):
    """
    Get vault configuration including chunking settings.

    Returns configuration for specified vault or default vault.
    Includes chunking settings, model, and other vault-specific config.
    """
    config = request.app.state.config

    try:
        # Build response with all vaults' configs
        vaults_config = {}
        for vc in config.get_all_vaults():
            vaults_config[vc["name"]] = {
                "name": vc["name"],
                "path": vc["path"],
                "enable_chunking": vc.get("enable_chunking", False),
                "chunk_size": vc.get("chunk_size", 2000),
                "chunk_overlap": vc.get("chunk_overlap", 400),
                "chunk_threshold": vc.get("chunk_threshold", 4000),
                "is_default": vc.get("is_default", False)
            }

        return JSONResponse(content={
            "vaults": vaults_config,
            "default_vault": config.get_default_vault()["name"],
            "default_model": config.default_model,
            "search": {
                "default_limit": config.search_default_limit,
                "max_limit": config.search_max_limit,
                "timeout": config.search_timeout,
                "hybrid_enabled": config.hybrid_search_enabled,
                "default_query_filter": config.default_query_filter
            }
        })

    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get config: {str(e)}"
        )


@app.get("/search")
async def search(
    request: Request,
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
    include_props: Optional[str] = Query(
        default=None,
        description="JSON array of property filters to include: [{\"prop\": \"name\", \"value\": \"val\"}]"
    ),
    exclude_props: Optional[str] = Query(
        default=None,
        description="JSON array of property filters to exclude: [{\"prop\": \"name\", \"value\": \"val\"}]"
    ),
    include_tags: Optional[str] = Query(
        default=None,
        description="JSON array of tags to include: [\"python\", \"ai\"]"
    ),
    exclude_tags: Optional[str] = Query(
        default=None,
        description="JSON array of tags to exclude: [\"draft\", \"wip\"]"
    ),
    include_paths: Optional[str] = Query(
        default=None,
        description="JSON array of path patterns to include: [\"Gleanings\", \"Projects\"]"
    ),
    exclude_paths: Optional[str] = Query(
        default=None,
        description="JSON array of path patterns to exclude: [\"Archive\", \"Templates\"]"
    ),
    include_files: Optional[str] = Query(
        default=None,
        description="JSON array of filename patterns to include: [\"README\", \"index\"]"
    ),
    exclude_files: Optional[str] = Query(
        default=None,
        description="JSON array of filename patterns to exclude: [\"draft\", \"temp\"]"
    ),
    hybrid: Optional[bool] = Query(
        default=None,
        description="Use hybrid search (BM25 + semantic). Defaults to config setting."
    ),
    model: Optional[str] = Query(
        default=None,
        description="Embedding model to use (optional)"
    ),
    rerank: bool = Query(
        default=True,
        description="Use cross-encoder re-ranking for better precision (~200ms)"
    ),
    expand_query: bool = Query(
        default=False,
        description="Expand short queries (<3 words) with TF-IDF terms"
    ),
    time_boost: bool = Query(
        default=True,
        description="Boost recent documents with time-decay scoring"
    ),
    harness: bool = Query(
        default=False,
        description="Return structured score data for harness/mixer experiments"
    ),
    pipeline_debug: bool = Query(
        default=False,
        description="Return pipeline state showing results at each search stage"
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
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    search_limit = get_rate_limit("search")

    if not rate_limiter.check_limit(client_ip, "search", max_requests=search_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Too many search requests. Maximum {search_limit} per hour. Try again later."
        )

    config = request.app.state.config

    # Apply default limit if not specified
    if limit is None:
        limit = config.search_default_limit

    # Enforce maximum limit
    if limit > config.search_max_limit:
        limit = config.search_max_limit

    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

        # Parse filter parameters from JSON
        import json

        include_props_list = []
        if include_props:
            try:
                include_props_list = json.loads(include_props)
            except json.JSONDecodeError:
                logger.warning(f"Invalid include_props JSON: {include_props}")

        exclude_props_list = []
        if exclude_props:
            try:
                exclude_props_list = json.loads(exclude_props)
            except json.JSONDecodeError:
                logger.warning(f"Invalid exclude_props JSON: {exclude_props}")

        include_tags_list = []
        if include_tags:
            try:
                include_tags_list = json.loads(include_tags)
            except json.JSONDecodeError:
                logger.warning(f"Invalid include_tags JSON: {include_tags}")

        exclude_tags_list = []
        if exclude_tags:
            try:
                exclude_tags_list = json.loads(exclude_tags)
            except json.JSONDecodeError:
                logger.warning(f"Invalid exclude_tags JSON: {exclude_tags}")

        include_paths_list = []
        if include_paths:
            try:
                include_paths_list = json.loads(include_paths)
            except json.JSONDecodeError:
                logger.warning(f"Invalid include_paths JSON: {include_paths}")

        exclude_paths_list = []
        if exclude_paths:
            try:
                exclude_paths_list = json.loads(exclude_paths)
            except json.JSONDecodeError:
                logger.warning(f"Invalid exclude_paths JSON: {exclude_paths}")

        include_files_list = []
        if include_files:
            try:
                include_files_list = json.loads(include_files)
            except json.JSONDecodeError:
                logger.warning(f"Invalid include_files JSON: {include_files}")

        exclude_files_list = []
        if exclude_files:
            try:
                exclude_files_list = json.loads(exclude_files)
            except json.JSONDecodeError:
                logger.warning(f"Invalid exclude_files JSON: {exclude_files}")

        # Determine whether to use hybrid search
        use_hybrid = hybrid if hybrid is not None else config.hybrid_search_enabled

        logger.info(f"Search: vault='{vault_name}', query='{q}', limit={limit}, min_score={min_score}, include_props={include_props_list}, exclude_props={exclude_props_list}, include_tags={include_tags_list}, exclude_tags={exclude_tags_list}, include_paths={include_paths_list}, exclude_paths={exclude_paths_list}, include_files={include_files_list}, exclude_files={exclude_files_list}, hybrid={use_hybrid}, expand={expand_query}, time_boost={time_boost}, rerank={rerank}, model={model or 'default'}")

        # Initialize pipeline state container (if debugging enabled)
        pipeline_state = None
        if pipeline_debug:
            import time
            pipeline_state = {
                "stages": [],
                "query": {
                    "original": q,
                    "expanded": None,
                    "vault": vault_name
                },
                "config": {
                    "hybrid": use_hybrid,
                    "rerank": rerank,
                    "expand_query": expand_query,
                    "time_boost": time_boost,
                    "limit": limit,
                    "min_score": min_score,
                    "include_props": include_props_list,
                    "exclude_props": exclude_props_list,
                    "include_tags": include_tags_list,
                    "exclude_tags": exclude_tags_list,
                    "include_paths": include_paths_list,
                    "exclude_paths": exclude_paths_list,
                    "include_files": include_files_list,
                    "exclude_files": exclude_files_list
                }
            }

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

        # Stage 0: Query expansion (if enabled and query is short)
        import time
        stage_start = time.time()
        original_query = q
        expanded_query = None
        expansion_terms = []

        if expand_query:
            query_expander = request.app.state.query_expander
            if query_expander.should_expand(q):
                try:
                    # Get initial results for expansion
                    logger.info(f"Query '{q}' is short, fetching initial results for expansion")
                    initial_data = synthesis.search(query=q, limit=5)
                    initial_results = initial_data.get("results", [])

                    if not initial_results:
                        logger.info(f"Query '{q}' needs expansion but initial search returned no results")

                    # Expand query
                    q = query_expander.expand(q, initial_results, top_k=5)
                    if q != original_query:
                        expanded_query = q
                        # Extract expansion terms (terms in expanded query not in original)
                        original_terms = set(original_query.lower().split())
                        expanded_terms = set(q.lower().split())
                        expansion_terms = list(expanded_terms - original_terms)
                        logger.info(f"Query expanded: '{original_query}' → '{q}'")
                    else:
                        logger.debug(f"Query expansion did not modify query: '{original_query}'")
                except SynthesisError as e:
                    logger.warning(f"Initial search for expansion failed: {e}, proceeding with original query")
                    # Continue with original query
                except (ValueError, IndexError, KeyError) as e:
                    # Expected failures in query expansion (empty results, TF-IDF errors, etc.)
                    logger.warning(f"Query expansion failed: {e}, proceeding with original query")
                    # Continue with original query
                except Exception as e:
                    # Unexpected error - log as error but still fail-open
                    logger.error(f"Unexpected error during query expansion: {e}", exc_info=True)
                    # Continue with original query

        # Capture Stage 0 state
        if pipeline_state is not None:
            pipeline_state["query"]["expanded"] = expanded_query
            stage_state = capture_stage_state(
                stage_num=0,
                stage_name="Query Expansion",
                results=[],  # No results yet
                metadata={
                    "original_query": original_query,
                    "expanded_query": expanded_query,
                    "expansion_terms": expansion_terms,
                    "applied": expanded_query is not None
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 0.5: Build file filter from Query Filter (if inclusive filters present)
        # This enables pre-filtering BEFORE semantic search for dramatic performance improvement
        file_filter = None
        file_filter_metadata = {
            "enabled": False,
            "file_count": 0,
            "total_files": 0,
            "build_time": 0
        }

        if include_props_list or include_tags_list or include_paths_list or include_files_list:
            try:
                file_filter = build_file_filter(
                    synthesis=synthesis,
                    vault_path=vault_path,
                    include_props=include_props_list,
                    include_tags=include_tags_list,
                    include_paths=include_paths_list,
                    include_files=include_files_list
                )

                if file_filter is not None:
                    file_filter_metadata["enabled"] = True
                    file_filter_metadata["file_count"] = len(file_filter)
                    # Note: total_files would require counting vault_files, skip for now

                    # CRITICAL: If file filter is empty (0 matches), return empty results immediately
                    if len(file_filter) == 0:
                        logger.info("File filter matched 0 files, returning empty results")
                        return JSONResponse(
                            content={
                                "query": q,
                                "results": [],
                                "total": 0,
                                "model": synthesis.model_name,
                                "search_mode": "hybrid" if use_hybrid else "semantic",
                                "message": "No files matched the filter criteria",
                                "file_filter": {
                                    "enabled": True,
                                    "file_count": 0,
                                    "filters_applied": {
                                        "include_props": include_props_list,
                                        "include_tags": include_tags_list,
                                        "include_paths": include_paths_list,
                                        "include_files": include_files_list
                                    }
                                }
                            }
                        )

            except Exception as e:
                # Fail-open: if file filter building fails, continue without it
                logger.warning(f"File filter building failed, proceeding without pre-filtering: {e}")
                file_filter = None

        # Stage 1: Primary retrieval (semantic + BM25 hybrid or semantic-only)
        # Stage 2: Chunk deduplication (happens inside hybrid_search)
        stage_start = time.time()
        search_limit = limit * 2 if limit else 50

        logger.info(f"Stage 1: Starting primary retrieval (limit={search_limit}, hybrid={use_hybrid}, file_filter={'enabled' if file_filter else 'disabled'})")

        # Choose search method
        if use_hybrid:
            try:
                data = synthesis.hybrid_search(query=q, limit=search_limit, file_filter=file_filter)
            except SynthesisError as e:
                # Fall back to semantic search if hybrid fails
                logger.warning(f"Hybrid search failed, falling back to semantic: {e}")
                data = synthesis.search(query=q, limit=search_limit, file_filter=file_filter)
                data["search_mode"] = "semantic (hybrid fallback)"
        else:
            data = synthesis.search(query=q, limit=search_limit, file_filter=file_filter)

        # Get results
        results = data.get("results", [])
        stage_duration = time.time() - stage_start
        logger.info(f"Stage 1: Completed primary retrieval in {stage_duration:.2f}s ({len(results)} results)")

        # Capture Stage 1 & 2 state (retrieval + dedup, combined since dedup happens inside hybrid_search)
        if pipeline_state is not None:
            stage_state = capture_stage_state(
                stage_num=1,
                stage_name="Primary Retrieval & Chunk Deduplication",
                results=results,
                metadata={
                    "search_mode": data.get("search_mode", "semantic" if not use_hybrid else "hybrid"),
                    "search_limit": search_limit,
                    "hybrid_enabled": use_hybrid,
                    "note": "Chunk deduplication happens inside hybrid_search (best chunk per file)"
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 3: Score filtering (but not in hybrid mode)
        stage_start = time.time()
        results_before_score_filter = results

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

        # Capture Stage 3 state
        if pipeline_state is not None:
            removed_items = []
            if score_removed > 0:
                # Get items that were filtered
                filtered_paths = {r.get("relative_path") for r in score_filtered}
                removed_items = [
                    {
                        "relative_path": r.get("relative_path"),
                        "similarity_score": round(r.get("similarity_score", 0), 4)
                    }
                    for r in results_before_score_filter
                    if r.get("relative_path") not in filtered_paths
                ][:20]  # Limit to 20

            stage_state = capture_stage_state(
                stage_num=3,
                stage_name="Score Filtering",
                results=score_filtered,
                metadata={
                    "before_count": len(results_before_score_filter),
                    "after_count": len(score_filtered),
                    "removed_count": score_removed,
                    "min_score_threshold": min_score,
                    "applied": not use_hybrid,  # Only in semantic mode
                    "removed_items": removed_items
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 4: Status filtering (inactive gleanings)
        stage_start = time.time()
        original_count = len(score_filtered)
        filtered_results = filter_inactive_gleanings(score_filtered)
        status_removed = original_count - len(filtered_results)

        if status_removed > 0:
            logger.info(f"Filtered {status_removed} inactive gleanings from results")

        # Capture Stage 4 state
        if pipeline_state is not None:
            removed_items = []
            if status_removed > 0:
                filtered_paths = {r.get("relative_path") for r in filtered_results}
                removed_items = [
                    {
                        "relative_path": r.get("relative_path"),
                        "status": r.get("status", "unknown")
                    }
                    for r in score_filtered
                    if r.get("relative_path") not in filtered_paths
                ][:20]

            stage_state = capture_stage_state(
                stage_num=4,
                stage_name="Status Filtering",
                results=filtered_results,
                metadata={
                    "before_count": original_count,
                    "after_count": len(filtered_results),
                    "removed_count": status_removed,
                    "removed_items": removed_items
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 5: Query Filter (properties, tags, paths, files)
        stage_start = time.time()
        results_before_filtering = filtered_results
        total_filtered = 0

        logger.info(f"Stage 5: Starting Query Filter with {len(filtered_results)} results")

        # Apply property filters
        if include_props_list or exclude_props_list:
            filter_start = time.time()
            logger.info(f"Applying property filters: include={include_props_list}, exclude={exclude_props_list}")
            filtered_results, props_removed = filter_by_properties(
                filtered_results,
                include_props=include_props_list,
                exclude_props=exclude_props_list
            )
            total_filtered += props_removed
            filter_duration = time.time() - filter_start
            logger.info(f"Filtered {props_removed} results by properties in {filter_duration:.2f}s")

        # Apply tag filters
        if include_tags_list or exclude_tags_list:
            filtered_results, tags_removed = filter_by_tags(
                filtered_results,
                include_tags=include_tags_list,
                exclude_tags=exclude_tags_list
            )
            total_filtered += tags_removed
            if tags_removed > 0:
                logger.info(f"Filtered {tags_removed} results by tags")

        # Apply path filters
        if include_paths_list or exclude_paths_list:
            filtered_results, paths_removed = filter_by_paths(
                filtered_results,
                include_paths=include_paths_list,
                exclude_paths=exclude_paths_list
            )
            total_filtered += paths_removed
            if paths_removed > 0:
                logger.info(f"Filtered {paths_removed} results by paths")

        # Apply file filters
        if include_files_list or exclude_files_list:
            filtered_results, files_removed = filter_by_files(
                filtered_results,
                include_files=include_files_list,
                exclude_files=exclude_files_list
            )
            total_filtered += files_removed
            if files_removed > 0:
                logger.info(f"Filtered {files_removed} results by files")

        # Capture Stage 5 state
        if pipeline_state is not None:
            removed_items = []
            if total_filtered > 0:
                filtered_paths = {r.get("relative_path") for r in filtered_results}
                removed_items = [
                    {
                        "relative_path": r.get("relative_path"),
                        "title": r.get("title", "Unknown")
                    }
                    for r in results_before_filtering
                    if r.get("relative_path") not in filtered_paths
                ][:20]

            stage_state = capture_stage_state(
                stage_num=5,
                stage_name="Query Filter",
                results=filtered_results,
                metadata={
                    "before_count": len(results_before_filtering),
                    "after_count": len(filtered_results),
                    "removed_count": total_filtered,
                    "include_props": include_props_list,
                    "exclude_props": exclude_props_list,
                    "include_tags": include_tags_list,
                    "exclude_tags": exclude_tags_list,
                    "include_paths": include_paths_list,
                    "exclude_paths": exclude_paths_list,
                    "include_files": include_files_list,
                    "exclude_files": exclude_files_list,
                    "removed_items": removed_items
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 6: Cross-encoder re-ranking (if enabled)
        stage_start = time.time()
        results_before_rerank = [dict(r) for r in filtered_results[:20]]  # Shallow copy top 20 for comparison

        if rerank and filtered_results:
            reranker = request.app.state.reranker
            # Re-rank with more candidates than final limit for better quality
            rerank_count = min(100, len(filtered_results))
            logger.info(f"Re-ranking top {rerank_count} results with cross-encoder")
            filtered_results = reranker.rerank(
                query=q,
                results=filtered_results,
                top_k=limit,
                rerank_top_n=rerank_count
            )

        # Capture Stage 6 state
        if pipeline_state is not None:
            rank_changes = []
            if rerank and results_before_rerank:
                rank_changes = calculate_rank_changes(results_before_rerank, filtered_results[:20])

            stage_state = capture_stage_state(
                stage_num=6,
                stage_name="Cross-Encoder Re-Ranking",
                results=filtered_results,
                metadata={
                    "applied": rerank and len(filtered_results) > 0,
                    "rerank_count": min(100, len(filtered_results)) if rerank else 0,
                    "rank_changes": rank_changes[:20],  # Top 20 changes
                    "total_rank_changes": len([c for c in rank_changes if c["delta"] != 0])
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Stage 7: Time-aware boost (after re-ranking)
        stage_start = time.time()
        results_before_time_boost = [dict(r) for r in filtered_results[:20]]  # Shallow copy for comparison

        if time_boost and filtered_results:
            time_scorer = request.app.state.time_scorer
            logger.info(f"Applying time-aware boost to {len(filtered_results)} results")
            filtered_results = time_scorer.apply_boost(filtered_results, vault_path)

        # Capture Stage 7 state
        if pipeline_state is not None:
            boosted_items = []
            if time_boost and results_before_time_boost:
                # Find items with time boost applied
                for idx, result in enumerate(filtered_results[:20]):
                    time_boost_val = result.get("time_boost", 0)
                    if time_boost_val > 0:
                        boosted_items.append({
                            "relative_path": result.get("relative_path"),
                            "time_boost": round(time_boost_val, 4),
                            "mtime": result.get("mtime", "")
                        })

            rank_changes = []
            if time_boost and results_before_time_boost:
                rank_changes = calculate_rank_changes(results_before_time_boost, filtered_results[:20])

            stage_state = capture_stage_state(
                stage_num=7,
                stage_name="Time-Aware Boost",
                results=filtered_results,
                metadata={
                    "applied": time_boost and len(filtered_results) > 0,
                    "boosted_count": len(boosted_items),
                    "boosted_items": boosted_items,
                    "rank_changes": rank_changes[:20],
                    "total_rank_changes": len([c for c in rank_changes if c["delta"] != 0])
                },
                start_time=stage_start
            )
            pipeline_state["stages"].append(stage_state)

        # Apply final limit (if not already applied by reranker)
        if not rerank:
            filtered_results = filtered_results[:limit] if limit else filtered_results

        # Update response
        data["results"] = filtered_results
        data["total"] = len(filtered_results)
        data["query"] = original_query  # Always show original query
        if expanded_query:
            data["expanded_query"] = expanded_query  # Show expansion if occurred
        data["min_score"] = min_score
        data["filtered_count"] = {
            "by_score": score_removed,
            "by_status": status_removed,
            "by_query_filter": total_filtered,
            "total_removed": score_removed + status_removed + total_filtered
        }

        # Add vault information to response
        data["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        # Add harness data when requested
        if harness:
            # Restructure each result to have a "scores" object
            for result in data["results"]:
                scores = {
                    "semantic": result.get("similarity_score"),
                    "bm25": result.get("bm25_score"),
                    "rrf": result.get("rrf_score"),
                    "cross_encoder": result.get("cross_encoder_score"),
                    "time_boost": result.get("time_boost", 0),
                    "tag_boosted": result.get("tag_boosted", False),
                }
                # Remove None values
                scores = {k: v for k, v in scores.items() if v is not None}
                result["scores"] = scores

            # Add harness metadata
            data["harness"] = {
                "mix": {
                    "semantic_weight": 1.0,
                    "bm25_weight": 1.0,
                    "tag_multiplier": 5.0,
                    "time_weight": 1.0,
                },
                "server": {
                    "hybrid": use_hybrid,
                    "rerank": rerank,
                    "expand_query": expand_query,
                },
            }

        # Add pipeline debug data when requested
        if pipeline_state is not None:
            # Calculate total pipeline time
            total_time_ms = sum(stage["timing_ms"] for stage in pipeline_state["stages"])
            pipeline_state["summary"] = {
                "total_time_ms": round(total_time_ms, 1),
                "initial_results": pipeline_state["stages"][1]["result_count"] if len(pipeline_state["stages"]) > 1 else 0,
                "final_results": len(filtered_results),
                "total_filtered": (pipeline_state["stages"][1]["result_count"] if len(pipeline_state["stages"]) > 1 else 0) - len(filtered_results),
                "stages_count": len(pipeline_state["stages"])
            }
            data["pipeline"] = pipeline_state

        # Sanitize Unicode surrogates before JSON encoding
        data = sanitize_unicode(data)

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
    request: Request,
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
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    archaeology_limit = get_rate_limit("archaeology")

    if not rate_limiter.check_limit(client_ip, "archaeology", max_requests=archaeology_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Too many archaeology requests. Maximum {archaeology_limit} per hour. Try again later."
        )

    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

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

        # Sanitize Unicode surrogates before JSON encoding
        data = sanitize_unicode(data)

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
    request: Request,
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
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

        logger.debug(f"Retrieving stats for vault: {vault_name}")

        data = synthesis.get_stats()

        # Add vault information to response
        data["vault"] = {
            "name": vault_name,
            "path": str(vault_path)
        }

        # Sanitize Unicode surrogates before JSON encoding
        data = sanitize_unicode(data)

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


@app.get("/graph/neighbors")
async def graph_neighbors(
    request: Request,
    note: str = Query(..., description="Note name or path to explore"),
    vault: Optional[str] = Query(default=None, description="Vault name"),
    hops: int = Query(default=2, ge=1, le=4, description="Maximum distance (1-4)")
):
    """
    Get notes linked to/from a note within N hops.

    Explores the wikilink graph around a note, showing:
    - Direct incoming links (notes that link TO this note)
    - Direct outgoing links (notes this note links TO)
    - Notes reachable within N hops (undirected)

    Returns:
        {
            "note": "normalized note name",
            "found": true/false,
            "incoming": ["note1", "note2", ...],
            "outgoing": ["note3", "note4", ...],
            "by_distance": {
                "1": ["direct neighbors"],
                "2": ["2-hop neighbors"],
                ...
            }
        }
    """
    config = request.app.state.config
    vault_graphs = request.app.state.vault_graphs

    try:
        # Resolve vault
        if vault is None:
            vault_config = config.get_default_vault()
        else:
            vault_config = config.find_vault(vault)

        if vault_config is None:
            raise HTTPException(status_code=404, detail=f"Vault not found: {vault}")

        vault_path = Path(vault_config["path"]).expanduser().resolve()
        vault_name = vault_config["name"]

        # Get or create graph for this vault (lazy loading with cache)
        if vault_name not in vault_graphs:
            storage_dir = vault_path / ".temoa"
            vault_graphs[vault_name] = VaultGraph(vault_path, storage_dir)

        graph = vault_graphs[vault_name]

        # ensure_loaded tries cache first, then builds from scratch
        if not graph.ensure_loaded():
            raise HTTPException(
                status_code=503,
                detail="Vault graph not available (obsidiantools may not be installed)"
            )

        result = graph.get_neighbors(note, max_hops=hops)
        result["vault"] = vault_name

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph neighbors error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/stats")
async def graph_stats(
    request: Request,
    vault: Optional[str] = Query(default=None, description="Vault name")
):
    """
    Get vault graph statistics.

    Returns:
        {
            "loaded": true/false,
            "node_count": 1234,
            "edge_count": 5678,
            "connected_components": 42,
            "largest_component_size": 1000,
            "isolated_notes": 200
        }
    """
    config = request.app.state.config
    vault_graphs = request.app.state.vault_graphs

    try:
        # Resolve vault
        if vault is None:
            vault_config = config.get_default_vault()
        else:
            vault_config = config.find_vault(vault)

        if vault_config is None:
            raise HTTPException(status_code=404, detail=f"Vault not found: {vault}")

        vault_path = Path(vault_config["path"]).expanduser().resolve()
        vault_name = vault_config["name"]

        # Get or create graph for this vault (lazy loading with cache)
        if vault_name not in vault_graphs:
            storage_dir = vault_path / ".temoa"
            vault_graphs[vault_name] = VaultGraph(vault_path, storage_dir)

        graph = vault_graphs[vault_name]
        graph.ensure_loaded()
        stats = graph.get_stats()
        stats["vault"] = vault_name

        return JSONResponse(content=stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/hubs")
async def graph_hubs(
    request: Request,
    vault: Optional[str] = Query(default=None, description="Vault name"),
    min_in: int = Query(default=2, ge=1, description="Minimum incoming links"),
    min_out: int = Query(default=2, ge=1, description="Minimum outgoing links"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum results")
):
    """
    Find well-connected hub notes.

    Hub notes have many incoming AND outgoing links, making them
    important connection points in the vault.

    Returns:
        {
            "hubs": [
                {"note": "name", "in_degree": 10, "out_degree": 5},
                ...
            ]
        }
    """
    config = request.app.state.config
    vault_graphs = request.app.state.vault_graphs

    try:
        # Resolve vault
        if vault is None:
            vault_config = config.get_default_vault()
        else:
            vault_config = config.find_vault(vault)

        if vault_config is None:
            raise HTTPException(status_code=404, detail=f"Vault not found: {vault}")

        vault_path = Path(vault_config["path"]).expanduser().resolve()
        vault_name = vault_config["name"]

        # Get or create graph for this vault (lazy loading with cache)
        if vault_name not in vault_graphs:
            storage_dir = vault_path / ".temoa"
            vault_graphs[vault_name] = VaultGraph(vault_path, storage_dir)

        graph = vault_graphs[vault_name]

        if not graph.ensure_loaded():
            raise HTTPException(
                status_code=503,
                detail="Vault graph not available"
            )

        hubs = graph.get_hub_notes(min_in=min_in, min_out=min_out, limit=limit)

        return JSONResponse(content={
            "vault": vault_name,
            "hubs": [
                {"note": name, "in_degree": in_deg, "out_degree": out_deg}
                for name, in_deg, out_deg in hubs
            ]
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph hubs error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health(request: Request, vault: Optional[str] = None):
    """
    Health check endpoint.

    Args:
        vault: Vault identifier (name or path). Defaults to config vault.

    Returns server status and Synthesis connectivity.
    """
    config = request.app.state.config

    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

        # Quick test that Synthesis is accessible
        stats = synthesis.get_stats()

        return JSONResponse(content={
            "status": "healthy",
            "synthesis": "connected",
            "model": config.default_model,
            "vault": str(vault_path),
            "vault_name": vault_name,
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
    request: Request,
    vault: Optional[str] = Query(
        default=None,
        description="Vault name or path (default: config vault)"
    ),
    force: bool = Query(
        default=True,
        description="Force rebuild even if embeddings exist"
    ),
    model: Optional[str] = Query(
        default=None,
        description="Embedding model to use (default: config model)"
    ),
    enable_chunking: bool = Query(
        default=False,
        description="Enable adaptive chunking for large files"
    ),
    chunk_size: int = Query(
        default=2000,
        description="Target size for each chunk in characters"
    ),
    chunk_overlap: int = Query(
        default=400,
        description="Number of overlapping characters between chunks"
    ),
    chunk_threshold: int = Query(
        default=4000,
        description="Minimum file size before chunking is applied"
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
        POST /reindex?force=true&enable_chunking=true&chunk_size=2000

    Note: The 'model' parameter is for future use. Changing models requires
    restarting the server with a different model in config.

    Returns:
        {
            "status": "success",
            "files_indexed": 516,
            "model": "all-MiniLM-L6-v2",
            "message": "Successfully reindexed 516 files"
        }
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    reindex_limit = get_rate_limit("reindex")

    if not rate_limiter.check_limit(client_ip, "reindex", max_requests=reindex_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Too many reindex requests. Maximum {reindex_limit} per hour. Try again later."
        )

    config = request.app.state.config
    client_cache = request.app.state.client_cache

    try:
        # Get client for specified vault
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

        # Note: Model parameter is reserved for future use. Currently, the model
        # is set at server startup from config and cannot be changed per-request.
        if model and model != config.default_model:
            logger.warning(
                f"Model parameter '{model}' ignored. "
                f"Using configured model '{config.default_model}'. "
                f"To change models, update config.json and restart server."
            )

        logger.info(f"Reindex requested for vault '{vault_name}' (force={force}, chunking={enable_chunking})")

        result = synthesis.reindex(
            force=force,
            enable_chunking=enable_chunking,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_threshold=chunk_threshold
        )

        # Invalidate cache after reindex to ensure fresh data on next access
        client_cache.invalidate(vault_path, config.default_model)

        # Rebuild vault graph in background (takes ~90s, not needed for search)
        vault_graphs = request.app.state.vault_graphs
        storage_dir = vault_path / ".temoa"

        def _rebuild_graph():
            try:
                graph = VaultGraph(vault_path, storage_dir)
                if graph.rebuild_and_cache():
                    vault_graphs[vault_name] = graph
                    logger.info(
                        f"Vault graph rebuilt: {graph._graph.number_of_nodes()} nodes, "
                        f"{graph._graph.number_of_edges()} edges"
                    )
                else:
                    logger.warning("Vault graph rebuild failed")
            except Exception as e:
                logger.warning(f"Vault graph rebuild failed: {e}")

        thread = threading.Thread(target=_rebuild_graph, daemon=True)
        thread.start()
        logger.info(f"Vault graph rebuild started in background for '{vault_name}'")
        result["graph_rebuild"] = "started in background"

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
    request: Request,
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
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    extract_limit = get_rate_limit("extract")

    if not rate_limiter.check_limit(client_ip, "extract", max_requests=extract_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Too many extract requests. Maximum {extract_limit} per hour. Try again later."
        )

    config = request.app.state.config
    client_cache = request.app.state.client_cache

    if GleaningsExtractor is None:
        raise HTTPException(
            status_code=500,
            detail="Gleaning extraction not available (import failed)"
        )

    try:
        # Get client for specified vault (for reindex later)
        synthesis, vault_path, vault_name = get_client_for_vault(request, vault)

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
                "processed_files": {}  # Dict: {path: mtime}
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

            # Mark file as processed with its modification time
            rel_path = str(note_path.relative_to(vault_path))
            extractor.state["processed_files"][rel_path] = note_path.stat().st_mtime

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
            logger.info("Auto-reindexing after extraction (incremental)...")
            try:
                reindex_result = synthesis.reindex(force=False)
                # Invalidate cache after reindex
                client_cache.invalidate(vault_path, config.default_model)
                result["reindexed"] = True
                result["files_indexed"] = reindex_result.get("files_indexed", 0)
            except (SynthesisError, IOError, OSError) as e:
                # Expected failures during reindex - extraction still succeeded
                logger.warning(f"Auto-reindex failed: {e}")
                result["reindexed"] = False
                result["reindex_error"] = str(e)
            except Exception as e:
                # Unexpected error - log but don't fail extraction
                logger.error(f"Unexpected error during auto-reindex: {e}", exc_info=True)
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
    request: Request,
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
    gleaning_manager = request.app.state.gleaning_manager

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
    request: Request,
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
    config = request.app.state.config
    gleaning_manager = request.app.state.gleaning_manager

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
async def get_gleaning(request: Request, gleaning_id: str):
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
    gleaning_manager = request.app.state.gleaning_manager

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


@app.get("/gleaning/stats")
async def gleaning_stats(request: Request, vault: Optional[str] = None):
    """
    Get statistics about gleanings by status.

    Example:
        GET /gleaning/stats
        GET /gleaning/stats?vault=amoxtli

    Returns:
        {
            "active": 482,
            "inactive": 23,
            "hidden": 0,
            "total": 505
        }
    """
    try:
        _, vault_path, _ = get_client_for_vault(request, vault)
        gleaning_manager = request.app.state.gleaning_manager

        # Scan all gleanings and count by status
        all_gleanings = scan_gleaning_files(
            vault_path=vault_path,
            status_manager=gleaning_manager,
            status_filter=None
        )

        stats = {
            "active": 0,
            "inactive": 0,
            "hidden": 0,
            "total": len(all_gleanings)
        }

        for gleaning in all_gleanings:
            status = gleaning.get("status", "active")
            if status in stats:
                stats[status] += 1

        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Error getting gleaning stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get gleaning stats: {str(e)}"
        )


@app.get("/models")
async def list_models():
    """
    List available embedding models.

    Returns:
        {
            "models": [
                {
                    "name": "all-mpnet-base-v2",
                    "dimensions": 768,
                    "description": "High quality, larger embeddings"
                },
                {
                    "name": "all-MiniLM-L6-v2",
                    "dimensions": 384,
                    "description": "Fast, smaller embeddings (default)"
                },
                ...
            ]
        }
    """
    models = [
        {
            "name": "all-mpnet-base-v2",
            "dimensions": 768,
            "description": "High quality, larger embeddings"
        },
        {
            "name": "all-MiniLM-L6-v2",
            "dimensions": 384,
            "description": "Fast, smaller embeddings (default)",
            "default": True
        },
        {
            "name": "all-MiniLM-L12-v2",
            "dimensions": 384,
            "description": "Better quality than L6, still fast"
        },
        {
            "name": "paraphrase-albert-small-v2",
            "dimensions": 768,
            "description": "Optimized for paraphrase detection"
        },
        {
            "name": "multi-qa-mpnet-base-cos-v1",
            "dimensions": 768,
            "description": "Optimized for Q&A tasks"
        }
    ]

    return JSONResponse(content={"models": models})


@app.get("/stats/advanced")
async def advanced_stats(request: Request, vault: Optional[str] = None):
    """
    Get advanced vault statistics including chunking, tags, types, and index health.

    Example:
        GET /stats/advanced
        GET /stats/advanced?vault=amoxtli

    Returns:
        {
            "coverage": {
                "files_indexed": 2006,
                "chunks_created": 8755,
                "chunks_per_file": 4.4,
                "avg_file_size": 3200
            },
            "tags": {
                "total_tags": 234,
                "top_tags": [
                    {"tag": "python", "count": 234},
                    {"tag": "obsidian", "count": 189},
                    ...
                ]
            },
            "types": {
                "gleaning": 482,
                "article": 156,
                "tool": 89,
                "daily": 365
            },
            "index_health": {
                "status": "healthy",
                "last_indexed": "2025-12-31T10:30:00Z",
                "stale_files": 0
            }
        }
    """
    try:
        client, vault_path, _ = get_client_for_vault(request, vault)

        # Get basic stats from client
        basic_stats = client.get_stats()

        # Get metadata from storage for indexed_at timestamp and chunk counts
        from .storage import get_vault_metadata
        config = request.app.state.config
        vault_metadata = get_vault_metadata(client.storage_dir, config.default_model)

        # Read metadata.json to get accurate chunk counts and compute tag/type distributions
        metadata_file = client.storage_dir / config.default_model / "metadata.json"
        total_items = basic_stats.get("num_embeddings", 0)
        chunk_count = 0
        file_count = 0
        tag_freq = {}
        type_dist = {}

        if metadata_file.exists():
            import json
            with open(metadata_file) as f:
                metadata_list = json.load(f)

                # Process each item - only count non-chunks for tags/types to avoid duplication
                for item in metadata_list:
                    is_chunk = item.get("is_chunk", False)

                    if is_chunk:
                        chunk_count += 1
                    else:
                        file_count += 1

                        # Count tags (only for non-chunks)
                        for tag in item.get("tags", []):
                            if tag:  # Skip empty tags
                                tag_freq[tag] = tag_freq.get(tag, 0) + 1

                        # Count types (only for non-chunks)
                        frontmatter = item.get("frontmatter", {})
                        doc_type = frontmatter.get("type")
                        if doc_type:
                            # Handle case where type might be a list
                            if isinstance(doc_type, list):
                                doc_type = doc_type[0] if doc_type else None
                            if doc_type:
                                type_dist[doc_type] = type_dist.get(doc_type, 0) + 1

        # Use actual counts
        files_indexed = file_count if file_count > 0 else total_items
        chunks_created = total_items  # total embeddings = all chunks + non-chunked files

        coverage = {
            "files_indexed": files_indexed,
            "chunks_created": chunks_created,
            "chunks_per_file": round(chunks_created / files_indexed, 1) if files_indexed > 0 else 0,
            "avg_file_size": basic_stats.get("avg_file_size", 0)
        }

        # Get tag distribution (top 10)
        top_tags = sorted(tag_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        tags = {
            "total_tags": len(tag_freq),
            "top_tags": [{"tag": tag, "count": count} for tag, count in top_tags]
        }

        # Type distribution already computed above

        # Index health - use vault_metadata for indexed_at
        last_indexed = vault_metadata.get("indexed_at") if vault_metadata else None
        index_health = {
            "status": "healthy" if files_indexed > 0 else "unindexed",
            "last_indexed": last_indexed,
            "stale_files": basic_stats.get("stale_files", 0)
        }

        return JSONResponse(content={
            "coverage": coverage,
            "tags": tags,
            "types": type_dist,
            "index_health": index_health
        })

    except Exception as e:
        logger.error(f"Error getting advanced stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get advanced stats: {str(e)}"
        )



