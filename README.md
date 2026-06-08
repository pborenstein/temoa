# Temoa

> [Temoa](https://nahuatl.wired-humanities.org/content/temoa) (Nahuatl): To search for, to seek

Local semantic search server for Obsidian vaults. Search by meaning over HTTP — accessible from mobile via Tailscale.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

## What it does

Temoa indexes your vault with sentence-transformer embeddings and serves a search API. You query it over HTTP; it returns ranked results with Obsidian URIs.

| Feature | Description |
|:--------|:------------|
| Semantic search | Find notes by meaning, not exact keywords |
| Hybrid search | Combine BM25 keyword search with semantic embeddings (RRF fusion) |
| Cross-encoder re-ranking | Two-stage retrieval for 20–30% better precision |
| Query expansion | Automatically expand short queries using TF-IDF |
| Time-aware scoring | Boost recent documents with configurable decay |
| Type/tag/property filtering | Filter results by frontmatter fields |
| Adaptive chunking | Full searchability for large files (>4,000 chars) |
| Multi-vault support | Independent indexes per vault, LRU-cached in memory |

## Installation

```bash
git clone https://github.com/pborenstein/temoa
cd temoa
uv sync
```

## Configuration

Create `~/.config/temoa/config.json`:

```json
{
  "vaults": [
    {
      "name": "myvault",
      "path": "~/Obsidian/myvault",
      "is_default": true,
      "model": "all-MiniLM-L6-v2"
    }
  ],
  "default_vault": "myvault",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  }
}
```

Config is searched in order: `~/.config/temoa/config.json`, `~/.temoa.json`, `./config.json`.

## Quick Start

```bash
# Build embedding index (first time)
temoa index

# Start server
temoa server

# Search from CLI
temoa search "semantic search"

# Or via HTTP
curl "http://localhost:8080/search?q=semantic+search"

# Access from mobile (via Tailscale)
# http://<tailscale-ip>:8080/search?q=...
```

First startup downloads the model (~80 MB, one-time). Subsequent starts take ~15s.

## CLI Commands

```bash
temoa server              # Start HTTP server
temoa search "query"      # Search from terminal
temoa index               # Build index from scratch (first time / forced rebuild)
temoa reindex             # Incremental update (new and modified files only)
temoa stats               # Vault statistics
temoa config              # Show current configuration
temoa vaults              # List configured vaults and their models
temoa archaeology "topic" # Show when you were interested in a topic over time
```

### Index vs Reindex

| Command | Files processed | Time | Use case |
|:--------|:----------------|:-----|:---------|
| `temoa index` | All files | ~2–3 min | First time, forced rebuild |
| `temoa reindex` | New and modified only | ~5s | Daily use |

## HTTP API

### `GET /search`

```bash
curl "http://localhost:8080/search?q=query&limit=10&hybrid=true"
```

| Parameter | Default | Description |
|:----------|:--------|:------------|
| `q` | required | Search query |
| `vault` | config | Vault name |
| `limit` | 10 | Max results (1–100) |
| `min_score` | 0.3 | Minimum similarity (0–1) |
| `hybrid` | false | BM25 + semantic search |
| `rerank` | true | Cross-encoder re-ranking |
| `expand_query` | false | TF-IDF expansion for short queries |
| `time_boost` | true | Recency boost |
| `include_types` | — | JSON array of types to include |
| `exclude_types` | — | JSON array of types to exclude |
| `include_tags` | — | JSON array of tags |
| `exclude_tags` | — | JSON array of tags to exclude |
| `include_paths` | — | Path prefixes to include |
| `exclude_paths` | — | Path prefixes to exclude |

**Response:**
```json
{
  "query": "semantic search",
  "results": [
    {
      "title": "Semantic Search Tools",
      "relative_path": "L/Gleanings/abc123.md",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://open?vault=myvault&file=...",
      "description": "Overview of semantic search implementations",
      "tags": ["search", "ai"],
      "frontmatter": {"type": "gleaning"},
      "scores": {
        "semantic": 0.847,
        "bm25": 0.42,
        "rrf": 0.63,
        "cross_encoder": 4.52,
        "final": 0.91
      }
    }
  ],
  "total": 15,
  "model": "all-MiniLM-L6-v2",
  "vault": "myvault"
}
```

### Other Endpoints

| Endpoint | Method | Description |
|:---------|:-------|:------------|
| `/health` | GET | Server status |
| `/config` | GET | Current configuration |
| `/vaults` | GET | Configured vaults |
| `/models` | GET | Available embedding models |
| `/stats` | GET | Index statistics |
| `/reindex` | POST | Rebuild or update index (`?force=false`) |
| `/archaeology` | GET | Temporal interest analysis (`?q=topic`) |

## Available Models

| Model | Dimensions | Speed | Notes |
|:------|:-----------|:------|:------|
| `all-MiniLM-L6-v2` | 384 | Fast | Default |
| `all-MiniLM-L12-v2` | 384 | Medium | Better quality |
| `all-mpnet-base-v2` | 768 | Medium | Higher quality |
| `multi-qa-mpnet-base-cos-v1` | 768 | Medium | Q&A optimized |

## Mobile Access via Tailscale

1. Install Tailscale on server and phone
2. Start server: `temoa server`
3. Get server IP: `tailscale ip -4`
4. Search from phone: `http://<tailscale-ip>:8080/search?q=...`

Tailscale encrypts all traffic — no HTTPS or port forwarding needed.

## Deployment (macOS launchd)

```bash
cd launchd
./install.sh
launchctl list | grep temoa
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full setup guide.

## Search Pipeline

1. **Query expansion** (optional) — expand short queries (<3 words) with TF-IDF
2. **Retrieval** — semantic (bi-encoder) or hybrid (semantic + BM25 with RRF)
3. **Score filter** — remove results below `min_score`
4. **Status filter** — remove `status: inactive/hidden` results
5. **Query filter** — apply type/tag/property/path/file filters
6. **Re-ranking** (optional) — cross-encoder precision boost (~200ms, +20–30%)
7. **Time boost** (optional) — exponential decay recency boost
8. **Top-K** — return final `limit` results

## Performance

| Operation | Time |
|:----------|:-----|
| Search (semantic) | ~400ms |
| Search (hybrid) | ~450ms |
| Search (+ reranking) | ~600ms |
| Startup (model cached) | ~15–20s |
| Full reindex (3,059 files) | ~159s |
| Incremental reindex (no changes) | ~5s |

Memory: ~600 MB single vault, ~1.5 GB for 3 cached vaults.

## Architecture

```
CLI / HTTP client
    │
FastAPI Server (server.py)
    │
SynthesisClient (synthesis.py) — model in memory
    │
Synthesis Engine (synthesis/) — sentence-transformers + NumPy
    │
Obsidian Vault + .temoa/ index
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Philosophy

> You don't have an organization problem. You have a surfacing problem.

- Search by meaning — embeddings find connections keywords miss
- Mobile-first — your vault in your pocket
- Local processing — no cloud, no external APIs, full privacy
- Vault-first habit — check your notes before searching the internet

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture
- [docs/SEARCH-MECHANISMS.md](docs/SEARCH-MECHANISMS.md) — search algorithms
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — launchd service, Tailscale
- [docs/TESTING.md](docs/TESTING.md) — test baseline
- [CLAUDE.md](CLAUDE.md) — development guide

---

**Version**: 2.0.0 | **Created**: 2025-11-17 | **Last Updated**: 2026-06-07
