# CLAUDE.md - Development Guide for Temoa

> **Purpose**: Context and guidance for Claude AI across development sessions.

**Last Updated**: 2026-06-07
**Project Status**: Experimentation Phase Active — Pure Search Engine
**Current Version**: 2.0.0
**Current Branch**: `main`

---

## Project Overview

**Temoa** is a local semantic search server for Obsidian vaults. FastAPI server → direct Synthesis imports → multi-stage search pipeline (semantic + BM25 + frontmatter) → results.

**Problem Solved**: Saved links and notes accumulate but never resurface. Temoa makes your vault the first place to check before external search.

**Vault**: `~/Obsidian/amoxtli`

---

## Key Principles

1. **uv shop** — always use `uv`. Never pip, poetry, or other tools.
2. **No hardcoded paths** — use `pathlib`, `~` expansion, relative paths. Never `/Users/`, `/home/`.
3. **Mobile-first** — if it doesn't work on phone, it doesn't work. Target < 2s response time.
4. **Privacy & local** — no external APIs for search/embeddings. Synthesis is local.
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
│   ├── chronicles/       # Design discussions & decision log (by phase)
│   ├── DECISIONS.md      # Architectural decision records
│   ├── TESTING.md        # Test baseline, known failures
│   └── DEPLOYMENT.md     # Launchd service setup
├── synthesis/            # Core search engine (bundled)
├── src/temoa/            # Temoa source code
│   ├── server.py         # FastAPI app, endpoints, lifespan
│   ├── cli.py            # Click CLI — 8 commands
│   ├── pipeline.py       # Composable post-retrieval pipeline
│   ├── server_filters.py # Filter functions (type, tag, property, path, file)
│   ├── synthesis.py      # SynthesisClient wrapper, hybrid search
│   ├── bm25_index.py     # BM25 keyword index
│   ├── reranker.py       # Cross-encoder re-ranking
│   ├── query_expansion.py # TF-IDF query expansion
│   ├── time_scoring.py   # Time-aware scoring
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

## Critical Context: Synthesis

**Location**: `synthesis/` (bundled) — modifiable; it's Temoa's own code, not a vendor dependency
**Role**: Local semantic search engine; Temoa imports it directly as a Python module (10x faster than subprocess)

**Models available** (configured per vault):
- `all-MiniLM-L6-v2` (384d, fast) — default
- `all-mpnet-base-v2` (768d, better quality)
- `all-MiniLM-L12-v2` (384d, better quality)

---

## Current State

**v2.0.0 — pure search engine.** UI, gleanings, and graph removed. Gleaning lifecycle lives in pixquitl (`~/projects/nahuatl-PROJECTS/pixquitl`).

See `docs/IMPLEMENTATION.md` and `docs/CONTEXT.md` for current status.

### Test Baseline

Run `uv run pytest`. Current: 196 passed, 0 failed, 0 skipped.

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
| `docs/chronicles/` | Design discussions & decision history (organized by phase) |
| `docs/DECISIONS.md` | Architectural decision records |
| `docs/DEPLOYMENT.md` | Launchd service setup |
| `docs/RESEARCH-NOTES.md` | External research, tool comparisons, actionable ideas |

---

**Owner**: pborenstein | **Created**: 2025-11-18 | **Last Updated**: 2026-06-07
