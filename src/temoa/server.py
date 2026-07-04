"""Temoa search server — pure JSON API, no UI."""
import logging
import math
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .__version__ import __version__
from .client_cache import ClientCache
from .config import Config, ConfigError
from .pipeline import SearchContext, default_pipeline
from .query_expansion import QueryExpander
from .rate_limiter import RateLimiter
from .reranker import CrossEncoderReranker
from .search_log import SearchLog
from .storage import derive_storage_dir, get_vault_metadata, validate_storage_safe
from .synthesis import SynthesisClient, SynthesisError
from .time_scoring import TimeAwareScorer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# --------------------------------------------------------------------------- #
# JSON safety
# --------------------------------------------------------------------------- #

def sanitize_unicode(obj):
    """Recursively replace Unicode surrogates and non-finite floats."""
    if isinstance(obj, str):
        return obj.encode("utf-8", errors="replace").decode("utf-8")
    elif isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    elif isinstance(obj, dict):
        return {k: sanitize_unicode(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_unicode(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_unicode(item) for item in obj)
    return obj


# --------------------------------------------------------------------------- #
# Rate limiting (module-level singleton)
# --------------------------------------------------------------------------- #

rate_limiter = RateLimiter()


def _check_rate_limit(request: Request, action: str, config: Config) -> None:
    rate_limits = config._config.get("rate_limits", {})
    defaults = {"search": 1000, "reindex": 5}
    max_req = rate_limits.get(f"{action}_per_hour", defaults.get(action, 100))
    ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check_limit(ip, action, max_requests=max_req):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {action}. Max {max_req}/hour.",
        )


# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Temoa server starting...")

    try:
        config = Config()
        logger.info("  ✓ Configuration loaded")

        cache_size = config._config.get("server", {}).get("client_cache_size", 3)
        client_cache = ClientCache(max_size=cache_size)
        logger.info(f"  ✓ Client cache initialized (max_size={cache_size})")

        # Pre-warm default vault
        logger.info("  ⏳ Pre-warming default vault (may take 10-20s)...")
        default_vault = config.get_default_vault()
        default_vault_path = Path(default_vault["path"]).expanduser().resolve()
        default_storage_dir = derive_storage_dir(
            default_vault_path, config.vault_path, config.storage_dir
        )
        client_cache.get(
            vault_path=default_vault_path,
            model=config.default_model,
            storage_dir=default_storage_dir,
        )
        logger.info("  ✓ Default vault client ready")

        logger.info("  ⏳ Loading cross-encoder model (may take 2-3s)...")
        reranker = CrossEncoderReranker()
        logger.info("  ✓ Cross-encoder reranker ready")

        query_expander = QueryExpander(max_expansion_terms=3)
        logger.info("  ✓ Query expander initialized")

        time_decay_cfg = config._config.get("search", {}).get("time_decay", {})
        time_scorer = TimeAwareScorer(
            half_life_days=time_decay_cfg.get("half_life_days", 90),
            max_boost=time_decay_cfg.get("max_boost", 0.2),
            enabled=time_decay_cfg.get("enabled", True),
        )
        logger.info("  ✓ Time-aware scorer initialized")

        search_log_path = default_storage_dir / "search_log.db"
        search_log = SearchLog(search_log_path)
        await search_log.init()
        logger.info("  ✓ Search log initialized")

        app.state.config = config
        app.state.client_cache = client_cache
        app.state.reranker = reranker
        app.state.query_expander = query_expander
        app.state.time_scorer = time_scorer
        app.state.search_log = search_log

        logger.info("=" * 60)
        logger.info("Temoa server ready")
        logger.info(f"  Vault:  {config.vault_path}")
        logger.info(f"  Model:  {config.default_model}")
        logger.info(f"  Server: http://{config.server_host}:{config.server_port}")
        logger.info("=" * 60)

    except (ConfigError, SynthesisError, IOError, OSError, ImportError, RuntimeError) as e:
        logger.error(f"Failed to initialize server: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
        raise

    yield

    logger.info("Temoa server shutting down...")


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

app = FastAPI(
    title="Temoa",
    description="Local semantic search for Obsidian vaults",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Vault helper
# --------------------------------------------------------------------------- #

def _get_client(request: Request, vault: Optional[str] = None) -> tuple[SynthesisClient, Path, str]:
    config: Config = request.app.state.config
    client_cache: ClientCache = request.app.state.client_cache

    vault_config = config.find_vault(vault) if vault else config.get_default_vault()
    if vault and vault_config is None:
        raise HTTPException(status_code=404, detail=f"Vault not found: {vault!r}")

    vault_path = Path(vault_config["path"]).expanduser().resolve()
    vault_name = vault_config["name"]
    vault_model = vault_config.get("model") or config.default_model
    storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)

    client = client_cache.get(
        vault_path=vault_path,
        model=vault_model,
        storage_dir=storage_dir,
    )
    return client, vault_path, vault_name


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #

@app.get("/health")
async def health(request: Request, vault: Optional[str] = None):
    config: Config = request.app.state.config
    try:
        synthesis, vault_path, vault_name = _get_client(request, vault)
        stats = synthesis.get_stats()
        return JSONResponse(content={
            "status": "healthy",
            "synthesis": "connected",
            "model": config.default_model,
            "vault": str(vault_path),
            "vault_name": vault_name,
            "files_indexed": stats.get("total_files") or stats.get("file_count", 0),
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "synthesis": "error",
            "error": str(e),
        })


@app.get("/vaults")
async def list_vaults(request: Request):
    config: Config = request.app.state.config
    vaults = []
    for vc in config.get_all_vaults():
        vault_path = Path(vc["path"]).expanduser().resolve()
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
        metadata = get_vault_metadata(storage_dir, config.default_model)
        vaults.append({
            "name": vc["name"],
            "path": str(vault_path),
            "is_default": vc.get("is_default", False),
            "indexed": metadata is not None,
            "file_count": metadata.get("file_count", 0) if metadata else 0,
        })
    return JSONResponse(content={
        "vaults": vaults,
        "default_vault": config.get_default_vault()["name"],
    })


@app.get("/config")
async def get_config(request: Request):
    config: Config = request.app.state.config
    vaults_config = {}
    for vc in config.get_all_vaults():
        vaults_config[vc["name"]] = {
            "name": vc["name"],
            "path": vc["path"],
            "enable_chunking": vc.get("enable_chunking", False),
            "chunk_size": vc.get("chunk_size", 2000),
            "chunk_overlap": vc.get("chunk_overlap", 400),
            "chunk_threshold": vc.get("chunk_threshold", 4000),
            "is_default": vc.get("is_default", False),
        }
    return JSONResponse(content={
        "vaults": vaults_config,
        "default_vault": config.get_default_vault()["name"],
        "default_model": config.default_model,
        "hybrid_enabled": config.hybrid_search_enabled,
        "version": __version__,
    })


@app.get("/models")
async def list_models(request: Request):
    try:
        synthesis, _, _ = _get_client(request)
        return JSONResponse(content={"models": synthesis.list_available_models()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def stats(request: Request, vault: Optional[str] = None):
    try:
        synthesis, vault_path, vault_name = _get_client(request, vault)
        data = synthesis.get_stats()
        data["vault"] = {"name": vault_name, "path": str(vault_path)}
        return JSONResponse(content=sanitize_unicode(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reindex")
async def reindex(
    request: Request,
    vault: Optional[str] = Query(default=None),
    force: bool = Query(default=True),
    enable_chunking: bool = Query(default=False),
    chunk_size: int = Query(default=2000),
    chunk_overlap: int = Query(default=400),
    chunk_threshold: int = Query(default=4000),
):
    config: Config = request.app.state.config
    client_cache: ClientCache = request.app.state.client_cache
    _check_rate_limit(request, "reindex", config)

    try:
        synthesis, vault_path, vault_name = _get_client(request, vault)
        logger.info(f"Reindex: vault={vault_name!r} force={force} chunking={enable_chunking}")

        result = synthesis.reindex(
            force=force,
            enable_chunking=enable_chunking,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_threshold=chunk_threshold,
        )

        # Re-inject vault_path into index.json (Synthesis overwrites it on full reindex)
        storage_dir = derive_storage_dir(vault_path, config.vault_path, config.storage_dir)
        validate_storage_safe(storage_dir, vault_path, "reindex", model=config.default_model)

        # Invalidate cache so next request loads fresh embeddings
        client_cache.invalidate(vault_path, config.default_model)

        result["vault"] = {"name": vault_name, "path": str(vault_path)}
        return JSONResponse(content=result)

    except SynthesisError as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected reindex error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    vault: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=100),
    min_score: float = Query(default=0.3, ge=0.0, le=1.0),
    include_types: Optional[str] = Query(default=None, description='JSON array: ["gleaning","article"]'),
    exclude_types: Optional[str] = Query(default=None, description='JSON array: ["daily"]'),
    include_props: Optional[str] = Query(default=None, description='JSON array: [{"prop":"type","value":"note"}]'),
    exclude_props: Optional[str] = Query(default=None),
    include_tags: Optional[str] = Query(default=None, description='JSON array: ["python","ai"]'),
    exclude_tags: Optional[str] = Query(default=None),
    include_paths: Optional[str] = Query(default=None),
    exclude_paths: Optional[str] = Query(default=None),
    include_files: Optional[str] = Query(default=None),
    exclude_files: Optional[str] = Query(default=None),
    hybrid: Optional[bool] = Query(default=None),
    rerank: bool = Query(default=True),
    expand_query: bool = Query(default=False),
    time_boost: bool = Query(default=True),
    harness: bool = Query(default=False, description="Include per-result score breakdown"),
    pipeline_debug: bool = Query(default=False),
):
    t_start = time.time()
    config: Config = request.app.state.config
    _check_rate_limit(request, "search", config)

    import json

    def _parse_json_list(raw: Optional[str]) -> list:
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            return []

    include_types_list = _parse_json_list(include_types)
    exclude_types_list = _parse_json_list(exclude_types)
    include_props_list = _parse_json_list(include_props)
    exclude_props_list = _parse_json_list(exclude_props)
    include_tags_list  = _parse_json_list(include_tags)
    exclude_tags_list  = _parse_json_list(exclude_tags)
    include_paths_list = _parse_json_list(include_paths)
    exclude_paths_list = _parse_json_list(exclude_paths)
    include_files_list = _parse_json_list(include_files)
    exclude_files_list = _parse_json_list(exclude_files)

    try:
        synthesis, vault_path, vault_name = _get_client(request, vault)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    use_hybrid = hybrid if hybrid is not None else config.hybrid_search_enabled
    effective_limit = limit or config.search_default_limit
    search_limit = effective_limit * 2  # over-fetch before filtering

    # Apply default query filter from config
    default_filter = config.default_query_filter
    original_query = q

    # --- Stage 0: Query expansion ---
    expanded_query = None
    if expand_query:
        expander: QueryExpander = request.app.state.query_expander
        if expander.should_expand(q):
            # seed expansion from a quick semantic fetch
            seed_data = synthesis.search(q, limit=20)
            seed_results = seed_data.get("results", [])
            expanded_q = expander.expand(q, seed_results)
            if expanded_q != q:
                expanded_query = expanded_q
                q = expanded_q
                logger.info(f"Query expanded: {original_query!r} → {q!r}")

    # --- Stage 0.5: Build file filter from include-only path/file params ---
    file_filter: Optional[list[str]] = None
    if include_paths_list or include_files_list:
        from .server_filters import build_file_filter
        file_filter = build_file_filter(
            vault_path, include_paths_list, include_files_list
        )
        if file_filter is not None and len(file_filter) == 0:
            # No files match the include filter — short-circuit
            return JSONResponse(content=sanitize_unicode({
                "query": original_query,
                "results": [],
                "total": 0,
                "vault": {"name": vault_name, "path": str(vault_path)},
                "filtered_count": {"total_removed": 0},
            }))

    # --- Stage 1+2: Retrieval (semantic or hybrid + chunk dedup) ---
    t0 = time.time()
    if use_hybrid:
        try:
            data = synthesis.hybrid_search(query=q, limit=search_limit, file_filter=file_filter)
        except SynthesisError as e:
            logger.warning(f"Hybrid search failed, falling back to semantic: {e}")
            data = synthesis.search(query=q, limit=search_limit, file_filter=file_filter)
            data["search_mode"] = "semantic (hybrid fallback)"
    else:
        data = synthesis.search(query=q, limit=search_limit, file_filter=file_filter)

    results = data.get("results", [])
    retrieval_elapsed = time.time() - t0
    logger.info(f"Retrieval: {len(results)} results in {retrieval_elapsed:.2f}s (hybrid={use_hybrid})")

    # --- Stages 3-7: post-retrieval pipeline ---
    ctx = SearchContext(
        query=q,
        original_query=original_query,
        vault_path=vault_path,
        vault_name=vault_name,
        limit=effective_limit,
        search_mode="hybrid" if use_hybrid else "semantic",
        params={
            "min_score": min_score,
            "rerank": rerank,
            "time_boost": time_boost,
            "pipeline_debug": pipeline_debug,
            "include_types": include_types_list,
            "exclude_types": exclude_types_list,
            "include_props": include_props_list,
            "exclude_props": exclude_props_list,
            "include_tags": include_tags_list,
            "exclude_tags": exclude_tags_list,
            "include_paths": include_paths_list,
            "exclude_paths": exclude_paths_list,
            "include_files": include_files_list,
            "exclude_files": exclude_files_list,
        },
        services={
            "reranker": request.app.state.reranker,
            "time_scorer": request.app.state.time_scorer,
        },
        results=results,
    )
    default_pipeline().run(ctx)

    # --- Assemble response ---
    response: dict = {
        "query": original_query,
        "results": ctx.results,
        "total": len(ctx.results),
        "model": data.get("model", config.default_model),
        "search_mode": data.get("search_mode", "hybrid" if use_hybrid else "semantic"),
        "vault": {"name": vault_name, "path": str(vault_path)},
        "min_score": min_score,
        "filtered_count": {
            "by_score": ctx.meta.get("score_removed", 0),
            "by_status": ctx.meta.get("status_removed", 0),
            "by_query_filter": ctx.meta.get("query_filter_removed", 0),
            "total_removed": sum([
                ctx.meta.get("score_removed", 0),
                ctx.meta.get("status_removed", 0),
                ctx.meta.get("query_filter_removed", 0),
            ]),
        },
    }
    if expanded_query:
        response["expanded_query"] = expanded_query

    if harness:
        for result in response["results"]:
            result["scores"] = {k: v for k, v in {
                "semantic": result.get("similarity_score"),
                "bm25": result.get("bm25_score"),
                "rrf": result.get("rrf_score"),
                "cross_encoder": result.get("cross_encoder_score"),
                "time_boost": result.get("time_boost", 0),
                "tag_boosted": result.get("tag_boosted", False),
            }.items() if v is not None}
        response["harness"] = {
            "mix": {"semantic_weight": 1.0, "bm25_weight": 1.0,
                    "tag_multiplier": 5.0, "time_weight": 1.0},
            "server": {"hybrid": use_hybrid, "rerank": rerank,
                       "expand_query": expand_query, "time_boost": time_boost},
        }

    if pipeline_debug:
        response["pipeline_debug"] = {
            "stages": ctx.stages_debug,
            "search_mode": response["search_mode"],
        }

    # Log to search_log.db (fire-and-forget within the async handler)
    search_log: SearchLog = request.app.state.search_log
    retrieval_ms_val = round((retrieval_elapsed) * 1000)
    total_ms_val = round((time.time() - t_start) * 1000)
    await search_log.log_search(
        query=original_query,
        vault=vault_name,
        mode=response["search_mode"],
        limit=effective_limit,
        rerank=rerank,
        expand_query=expand_query,
        retrieval_ms=retrieval_ms_val,
        total_ms=total_ms_val,
        results=ctx.results,
        pipeline_stages=ctx.stages_debug,
    )

    return JSONResponse(content=sanitize_unicode(response))
