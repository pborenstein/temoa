# IMPLEMENTATION.md - Temoa Development Plan

> This document is the durable milestone record for temoa as a **pure search
> engine** (v2.0+). For current session state and day-to-day active tasks,
> [CONTEXT.md](CONTEXT.md) is the live source — it is updated every session and
> may be ahead of this file.
>
> The v1 era (UI-centric search tool with gleaning extraction, web UI, and
> graph features) is history: see [History: v1 Era](#history-v1-era-2025-11--2026-05)
> below and `docs/archive/chronicles-v1/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Search Quality Experimentation 🔵 ACTIVE
**Last Updated**: 2026-07-06
**Current Version**: 2.0.0
**Current Branch**: `main`

---

## Core Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, embeddings explanation, data flow |
| [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md) | Search algorithms, ranking, score interpretation |
| [chronicles/](chronicles/) | Design discussions and decision history (v2 era) |
| [RESEARCH-NOTES.md](RESEARCH-NOTES.md) | External research, tool comparisons, actionable ideas |
| [CLAUDE.md](../CLAUDE.md) | Development guide for AI sessions |
| This file | Implementation progress tracking |

---

## History: v1 Era (2025-11 – 2026-05)

Temoa started as a UI-centric search tool with a mobile web UI, gleaning
extraction from daily notes, and vault graph features. Phases 0–3.5 plus
production hardening built and polished that tool. In 2026-05 it was rebuilt
as a pure search engine (server.py 2671 → 430 lines): the web UI, graph code,
and gleaning lifecycle were removed. Gleanings now live in
[pixquitl](../../pixquitl).

Condensed milestones (details in `docs/archive/chronicles-v1/`):

| Milestone | Completed | Highlights |
|-----------|-----------|------------|
| Phase 0–1: Foundation | 2025-11-18 | FastAPI + direct Synthesis imports, 400ms search |
| Phase 2: Gleanings + CLI | 2025-11-19 | Extraction system, Click CLI |
| Phase 2.5: Mobile + UI | 2025-11-24 | Tailscale deploy, incremental reindex (30x) |
| Phase 3: Enhanced Features | 2025-12-01 | Multi-vault, cross-encoder reranking, query expansion, time scoring, PWA |
| Production Hardening | 2025-12 – 2026-03 | Security, launchd service, BM25 tag boosting, test hygiene (0 failures), GitHub enrichment |
| Phase 3.5: Adaptive Chunking | 2025-12-30 | Sliding-window chunking, per-vault models |
| Search Harness UI | 2026-01 – 2026-02 | Score mixer, pipeline viewer, query filters (removed in v2) |
| **v2.0 Rebuild: Pure Search Engine** | 2026-05-30 | UI/gleanings/graph removed, composable pipeline, 8-command CLI |

---

## Current Era: Search Quality Experimentation 🔵

**Status**: ACTIVE (since v2.0 rebuild, 2026-05-30)
**Goal**: Use real search-log data to measure and improve search quality

### Done

- [x] v2.0 rebuild: composable pipeline (`pipeline.py`), `server_filters.py`, stripped CLI
- [x] Restore type filtering (`--type`/`--exclude-type`, `include_types`/`exclude_types`) — Entry 97
- [x] Versioned releases v1.1.0 / v2.0.0 — Entry 98
- [x] Documentation overhaul for v2.0.0 — Entry 99
- [x] Zeitgeist integration design notes ([ZEITGEIST-INTEGRATION.md](ZEITGEIST-INTEGRATION.md)) — Entry 100
- [x] Search query logging: SQLite `search_log.db`, `temoa log` / `--detail` / `--stats` — Entry 101
- [x] SEARCH-MECHANISMS.md: cross-encoder score explanation + log reading guide
- [x] Repo cleanup: v1 chronicles archived, tracking reframed — Entry 102, DEC-103
- [x] Synthesis extraction: engine folded into `src/temoa/engine/`, vendored dir deleted — Entry 103, DEC-104
- [x] Fix `temoa archaeology` (nonexistent `top_k` arg, wrong response schema in CLI display)
- [x] Release v2.1.0; launchd service restarted on new code

### Open

- [ ] Build up search log data from real usage; review with `temoa log --stats`
- [ ] Known-miss list: queries where temoa returned nothing but the answer was in the vault — collect as regression set
- [ ] Score baseline: calibrate what a "good" cross-encoder score looks like with known-good queries
- [ ] Position-aware reranker blending — fix hybrid burying good semantic results (BM25 floods conceptual queries; plan in `docs/archive/qmd-pipeline-improvements.md`)
- [ ] Zeitgeist snapshot chunking (see ZEITGEIST-INTEGRATION.md)
- [ ] Config-driven pipeline profiles (`search.profiles` in config.json, `profile` query param)
- [ ] Fix vault logging inconsistency: CLI logs full path, server logs vault name
- [ ] Evaluate v1 config legacy: multi-vault registry, CLI duplicating engine in-process
      vs. thin HTTP client to warm server (discussed 2026-07-06, no decision)

### Tunable Parameters

| Parameter | Location | Current Value | Range |
|-----------|----------|---------------|-------|
| Hybrid weight | `synthesis.py` | 0.5 | 0.0-1.0 (0=BM25, 1=semantic) |
| Tag boost multiplier | `bm25_index.py` | 5x | 1x-10x |
| RRF k parameter | `synthesis.py` | 60 | 1-100 |
| Time decay half-life | `time_scoring.py` | 90 days | 7-365 days |
| Query expansion threshold | `query_expansion.py` | <3 words | 1-5 words |
| Cross-encoder re-rank | `server.py` | enabled | on/off |
| Score threshold | `server.py` | 0.3 | 0.1-0.8 |
| Top-k retrieval | `server.py` | 50 | 10-200 |

### Methodology

1. **Baseline**: Record current performance on standard queries
2. **Isolate**: Change one parameter at a time
3. **Measure**: Compare relevance (top-3 hit rate) and latency
4. **Document**: Record what works and why

---

## Phase 4: Vault-First LLM ⚪

**Status**: Backburner
**Goal**: LLMs check vault before internet

See [archive/backburner/phase-4-llm.md](archive/backburner/phase-4-llm.md) for full plan.

---

**Last Updated**: 2026-07-06
**Current Phase**: Search Quality Experimentation
**Next**: See [CONTEXT.md](CONTEXT.md) for current session state and active tasks (live source of truth)
