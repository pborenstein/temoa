# CLAUDE.md - Development Guide for Temoa

> **Purpose**: Context and guidance for Claude AI across development sessions.

**Last Updated**: 2026-07-04
**Project Status**: Search Quality Experimentation — Pure Search Engine
**Current Version**: 2.0.0
**Current Branch**: `main`

---

## Project Overview

**Temoa** is a local semantic search server for Obsidian vaults. FastAPI server → embedding engine (`temoa.engine`) → multi-stage search pipeline (semantic + BM25 + frontmatter) → results.

**Problem Solved**: Saved links and notes accumulate but never resurface. Temoa makes your vault the first place to check before external search.

**Vault**: `~/Obsidian/amoxtli`

---

## Key Principles

1. **uv shop** — always use `uv`. Never pip, poetry, or other tools.
2. **No hardcoded paths** — use `pathlib`, `~` expansion, relative paths. Never `/Users/`, `/home/`.
3. **Mobile-first** — if it doesn't work on phone, it doesn't work. Target < 2s response time.
4. **Privacy & local** — no external APIs for search/embeddings. Everything runs locally.
5. **Avoid over-engineering** — no JS frameworks, no complex state, no premature abstraction.
6. **Plan like waterfall, implement in agile** — detailed upfront planning, iterative small commits.

---

## Architectural Constraints

- **Vault format agnostic**: optimized for Obsidian markdown/frontmatter, must also work with plain text files
- **Index location**: stored in `.temoa/` within vault (configurable); should NOT sync via Obsidian Sync
- **Network**: Tailscale VPN, single-user, no auth/HTTPS needed
- **Configuration over convention**: all paths/locations in `config.json`

---

## Project Structure

```
temoa/
├── CLAUDE.md             # This file
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md   # System architecture & data flow
│   ├── SEARCH-MECHANISMS.md  # Search algorithms & ranking
│   ├── IMPLEMENTATION.md # Progress tracking (source of truth for phase status)
│   ├── chronicles/       # Design discussions & decision log (v2 era; v1 in archive/chronicles-v1/)
│   ├── DECISIONS.md      # Architectural decision records
│   ├── TESTING.md        # Test baseline, known failures
│   └── DEPLOYMENT.md     # Launchd service setup
├── src/temoa/            # Temoa source code
│   ├── server.py         # FastAPI app, endpoints, lifespan
│   ├── cli.py            # Click CLI — 9 commands
│   ├── pipeline.py       # Composable post-retrieval pipeline
│   ├── server_filters.py # Filter functions (type, tag, property, path, file)
│   ├── synthesis.py      # SynthesisClient wrapper, hybrid search
│   ├── engine/           # Embedding engine (pipeline, models, store, chunking, archaeology)
│   ├── bm25_index.py     # BM25 keyword index
│   ├── reranker.py       # Cross-encoder re-ranking
│   ├── query_expansion.py # TF-IDF query expansion
│   ├── time_scoring.py   # Time-aware scoring
│   ├── search_log.py     # SQLite search query log
│   ├── config.py         # Configuration management
│   ├── client_cache.py   # Multi-vault LRU cache
│   ├── rate_limiter.py   # Per-IP sliding-window rate limiter
│   └── storage.py        # Storage directory derivation, vault validation
├── tests/                # Test suite
├── launchd/              # macOS service management
├── config.json           # Local config (not committed)
├── config.example.json   # Config template
└── pyproject.toml        # uv dependencies
```

---

## Critical Context: Embedding Engine

**Location**: `src/temoa/engine/` — extracted from the standalone Synthesis project (2026-07), now a regular temoa package
**Role**: Sentence-transformer embeddings, model registry, vault reader, chunking, temporal archaeology. `SynthesisClient` (synthesis.py) wraps it and keeps the model in memory.

**Models available** (configured per vault):
- `all-MiniLM-L6-v2` (384d, fast) — default
- `all-mpnet-base-v2` (768d, better quality)
- `all-MiniLM-L12-v2` (384d, better quality)

---

## Current State

**v2.0.0 — pure search engine.** UI, gleanings, and graph removed. Gleaning lifecycle lives in pixquitl (`~/projects/nahuatl-PROJECTS/pixquitl`).

See `docs/IMPLEMENTATION.md` and `docs/CONTEXT.md` for current status.

### Test Baseline

Run `uv run pytest`. Current: 156 passed, 0 failed, 0 skipped.

---

## Quick Reference Commands

```bash
# Dev server (auto-reload)
./dev.sh

# Run server
uv run temoa server

# Tests
uv run pytest

# Search
uv run temoa search "query" --vault amoxtli --limit 10 --hybrid

# Reindex (incremental)
uv run temoa reindex --vault amoxtli

# Full index rebuild
uv run temoa index --vault amoxtli --force

# Temporal analysis
uv run temoa archaeology "topic" --vault amoxtli

# Index stats
uv run temoa stats --vault amoxtli

# Config / vault list
uv run temoa config
uv run temoa vaults

# launchd service
cd launchd && ./install.sh
launchctl list | grep temoa
```

---

## Documentation Index

| Doc | Purpose |
|-----|---------|
| `docs/IMPLEMENTATION.md` | Phase progress, active tasks, what to work on next |
| `docs/ARCHITECTURE.md` | System architecture, data flow, security, performance |
| `docs/SEARCH-MECHANISMS.md` | All search algorithms, ranking, tag boosting, chunking |
| `docs/TESTING.md` | Test baseline, known failures, debugging |
| `docs/chronicles/` | Design discussions & decision history (v2 era; v1 in `docs/archive/chronicles-v1/`) |
| `docs/DECISIONS.md` | Architectural decision records |
| `docs/DEPLOYMENT.md` | Launchd service setup |
| `docs/RESEARCH-NOTES.md` | External research, tool comparisons, actionable ideas |

---

**Owner**: pborenstein | **Created**: 2025-11-18 | **Last Updated**: 2026-07-04
