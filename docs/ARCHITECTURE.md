# ARCHITECTURE.md - Temoa System Architecture

**Last Updated**: 2026-07-04
**Version**: 2.0.0
**Status**: Pure search engine — no UI, no gleanings, no graph

---

## High-Level Architecture

```
CLI (temoa search / temoa server)
            │
            ▼
    FastAPI Server (port 8080)
            │
            ▼
    SynthesisClient (synthesis.py)
      - wraps the embedding engine
      - keeps model in memory (~500 MB)
      - LRU cache for multi-vault
            │
            ▼
    Embedding Engine (src/temoa/engine/)
      - sentence-transformers embeddings
      - BM25 keyword index
      - NumPy vector store
            │
            ▼
    Obsidian Vault (.md files)
    + .temoa/ (embedding index, BM25 index)
```

**Key design**: the model stays loaded in a long-lived process, which keeps
search latency at ~400ms (vs ~2-3s if a subprocess reloaded it per query).
The engine was extracted from the standalone Synthesis project (2026-07) and
is a regular temoa package.

---

## Components

| File | Role |
|------|------|
| `server.py` | FastAPI app, HTTP endpoints, lifespan (model loading) |
| `cli.py` | Click CLI — 9 commands wrapping server and search logic |
| `pipeline.py` | Composable post-retrieval pipeline with `SearchContext` |
| `server_filters.py` | Filter functions: type, tag, property, path, file |
| `synthesis.py` | `SynthesisClient` — wrapper around the embedding engine |
| `engine/` | Embedding engine: pipeline, model registry, vault reader, chunking, store, temporal archaeology |
| `bm25_index.py` | BM25 keyword index for hybrid search |
| `reranker.py` | Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2) |
| `query_expansion.py` | TF-IDF query expansion for short queries |
| `time_scoring.py` | Exponential time-decay scoring with path traversal protection |
| `config.py` | Config loading, path expansion, validation |
| `client_cache.py` | LRU cache for `SynthesisClient` instances (multi-vault) |
| `rate_limiter.py` | Per-IP sliding-window rate limiting |
| `storage.py` | Storage directory derivation and vault validation |
| `exceptions.py` | Custom exception hierarchy (`TemoaError` base) |

---

## HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server status, vault connection check |
| `/config` | GET | Current configuration |
| `/vaults` | GET | List configured vaults with metadata |
| `/models` | GET | Available embedding models |
| `/stats` | GET | Index statistics (file count, embeddings) |
| `/reindex` | POST | Rebuild or incrementally update index |
| `/search` | GET | Main search endpoint |

### Search Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `q` | required | Search query |
| `vault` | config default | Vault to search |
| `limit` | 10 | Max results (1–100) |
| `min_score` | 0.3 | Minimum similarity threshold |
| `hybrid` | false | Enable BM25 + semantic (RRF fusion) |
| `rerank` | true | Cross-encoder re-ranking |
| `expand_query` | false | TF-IDF query expansion for short queries |
| `time_boost` | true | Exponential time-decay recency boost |
| `include_types` | — | JSON array of types to include |
| `exclude_types` | — | JSON array of types to exclude |
| `include_tags` | — | JSON array of tags to include |
| `exclude_tags` | — | JSON array of tags to exclude |
| `include_props` | — | JSON array of frontmatter properties to include |
| `exclude_props` | — | JSON array of frontmatter properties to exclude |
| `include_paths` | — | JSON array of path prefixes to include |
| `exclude_paths` | — | JSON array of path prefixes to exclude |
| `include_files` | — | JSON array of filenames to include |
| `exclude_files` | — | JSON array of filenames to exclude |
| `harness` | false | Return per-result component scores |
| `pipeline_debug` | false | Return per-stage timing and result counts |

---

## Search Pipeline

After retrieval, results flow through a sequence of conditional stages:

```
Retrieval (semantic, hybrid, or BM25-only)
    │
    ├─ ScoreFilterStage   — remove results below min_score (semantic mode only)
    ├─ StatusFilterStage  — remove results with status: inactive or hidden
    ├─ QueryFilterStage   — apply type/tag/property/path/file filters
    ├─ RerankStage        — cross-encoder reranking (if rerank=true)
    ├─ TimeBoostStage     — apply time-decay score boost (if time_boost=true)
    └─ LimitStage         — truncate to requested limit
```

Each stage has an `applies()` gate and can be skipped. Stages receive a mutable
`SearchContext` and modify it in place. With `pipeline_debug=true`, each stage
records its timing and result count.

### Score Envelope

Each result carries a `scores` dict alongside the legacy flat fields:

```json
{
  "scores": {
    "semantic": 0.85,
    "bm25": 0.42,
    "rrf": 0.63,
    "cross_encoder": 4.52,
    "time_boost": 1.15,
    "final": 0.91
  }
}
```

---

## Multi-Vault Support

Temoa supports multiple vaults via an LRU cache of `SynthesisClient` instances.

```
ClientCache (LRU, max 3 vaults)
  ├── vault: amoxtli  →  SynthesisClient (~500 MB, model + index in memory)
  ├── vault: work     →  SynthesisClient (~500 MB)
  └── (4th vault evicts LRU entry)
```

Each vault has an independent index stored in `vault/.temoa/model-name/`. The cache
makes repeated searches against the same vault fast (~400ms) while keeping total
memory bounded (~1.5 GB for 3 vaults).

**Vault switching**: ~400ms when cached, ~15–20s on first load (model initialization).

---

## Storage Layout

```
~/Obsidian/vault-name/
  └── .temoa/
      └── all-MiniLM-L6-v2/        ← one directory per model
          ├── embeddings.pkl        ← NumPy vector store + metadata
          ├── bm25_index.pkl        ← BM25 keyword index
          └── frontmatter_cache.pkl ← cached frontmatter for all files
```

Index files are binary and should be excluded from Obsidian Sync. The `.temoa/`
directory is created automatically on first `temoa index`.

---

## Configuration

Config is loaded from (in priority order):
1. `~/.config/temoa/config.json` (recommended)
2. `~/.temoa.json`
3. `./config.json` (development)

```json
{
  "vault_path": "~/Obsidian/amoxtli",
  "vaults": [
    {
      "name": "amoxtli",
      "path": "~/Obsidian/amoxtli",
      "is_default": true,
      "model": "all-MiniLM-L6-v2"
    }
  ],
  "default_model": "all-MiniLM-L6-v2",
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "client_cache_size": 3
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 30,
    "hybrid_enabled": true,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  },
  "rate_limits": {
    "search_per_hour": 1000,
    "reindex_per_hour": 5
  }
}
```

---

## Embedding Models

| Model | Dimensions | Speed | Notes |
|-------|-----------|-------|-------|
| `all-MiniLM-L6-v2` | 384 | Fast | Default |
| `all-MiniLM-L12-v2` | 384 | Medium | Better quality |
| `all-mpnet-base-v2` | 768 | Medium | Higher quality |
| `multi-qa-mpnet-base-cos-v1` | 768 | Medium | Q&A optimized |
| `paraphrase-albert-small-v2` | 768 | Medium | Paraphrase detection |

Model index stored separately per model name (`embeddings/model-name/`). Switching
models requires a full reindex.

---

## Adaptive Chunking

Files ≥ 4,000 characters are split into overlapping chunks at index time:

- **Chunk size**: 2,000 characters
- **Overlap**: 400 characters (prevents boundary misses)
- **Deduplication**: best-scoring chunk per file kept at search time

Without chunking, files > ~2,500 characters (512 tokens) are only partially indexed.
With chunking, a 9 MB file yields ~50 chunks, all fully searchable.

Index size grows ~3–4x with chunking enabled (acceptable — disk is cheap).

---

## Security

**Threat model**: single-user, Tailscale-isolated network. Focus is on preventing
accidental misuse, not sophisticated attackers.

- **CORS**: restrictive by default (localhost + Tailscale IP)
- **Rate limiting**: per-IP sliding window — 1,000 searches/hour, 5 reindexes/hour
- **Path traversal**: all file paths resolved and validated against vault root
- **Input validation**: FastAPI handles query parameter types and limits
- **No auth**: Tailscale provides network-level access control

---

## Error Handling

**Fail-open** (include result, continue): search filtering, optional metadata,
quality enhancements (query expansion, reranking, time boost)

**Fail-closed** (reject, prevent corruption): data modification, reindexing,
path traversal, model loading failure, config errors

Exception hierarchy in `exceptions.py`:
```
TemoaError
  ├── VaultReadError
  ├── SearchError
  ├── IndexError
  ├── ConfigError
  └── GleaningError  (legacy, retained for compat)
```

---

## Performance

| Operation | Time |
|-----------|------|
| Search (semantic) | ~400ms |
| Search (hybrid) | ~450ms |
| Search (+ reranking) | ~600ms |
| Short query with expansion + reranking | ~800–1000ms |
| Startup (model load, cached) | ~15–20s |
| Full index (3,059 files) | ~159s |
| Incremental reindex (no changes) | ~5s |
| Incremental reindex (5–10 new files) | ~6–8s |

Memory: ~600 MB single vault, ~1.5 GB for 3 cached vaults.

---

## Key Architectural Decisions

**DEC-009**: Direct imports over subprocess — keeps model in memory, 10× faster searches.

**DEC-013**: FastAPI lifespan for resource management — clean startup/shutdown.

**DEC-096**: v2.0 rebuild — strip to pure search API. Removed UI, gleanings, graph,
harness, inspector. Rationale: focus on the core value (search), extract gleaning
lifecycle to pixquitl, reduce maintenance surface.

---

**Related docs**:
- [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md) — detailed search algorithm reference
- [DEPLOYMENT.md](DEPLOYMENT.md) — launchd service setup, Tailscale configuration
- [TESTING.md](TESTING.md) — test baseline and organization
- [DECISIONS.md](DECISIONS.md) — full architectural decision record
