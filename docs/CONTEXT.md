---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-06-07
last_commit: 8516252
branch: main
---

# Current Context

## Current Focus

Documentation overhaul complete. All docs now reflect v2.0.0 (pure search engine).

## Active Tasks

- [x] Tag v1.1.0 and v2.0.0, push GitHub releases
- [x] Full docs overhaul — ARCHITECTURE, README, IMPLEMENTATION, DECISIONS, DEPLOYMENT, CLAUDE.md, SEARCH-MECHANISMS
- [x] Delete 8 stale docs, archive MULTI-MODEL-PLAN and qmd pipeline improvements

## Blockers

None

## Context

- v1.1.0 = last version with UI/gleanings/graph (40e5bb6), available on GitHub
- v2.0.0 = pure search engine, all docs now accurate to this state
- pixquitl handles gleaning extraction
- qmd pipeline improvements preserved in docs/archive/ (position-aware blending, heading-aware chunking, zeitgeist chunking)
- 196 tests passing

## Next Session

Good candidates: qmd pipeline improvements (reranker.py blending, heading-aware chunking) or multi-model experimentation.
