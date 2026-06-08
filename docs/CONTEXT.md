---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-06-08
last_commit: c0f123c
branch: main
---

# Current Context

## Current Focus

Search log infrastructure complete. Using it to observe real search behavior and understand score signals before tackling algorithm improvements.

## Active Tasks

- [x] SQLite search log (SearchLog, aiosqlite, server + CLI)
- [x] `temoa log` / `temoa log --detail` / `temoa log --stats`
- [x] SEARCH-MECHANISMS.md: cross-encoder score explanation + log reading guide

## Blockers

None

## Context

- 155 tests passing (CLAUDE.md says 196 — stale, update it)
- `search_log.db` in `.temoa/`; CLI logs vault as full path, server logs vault name (minor inconsistency)
- Cross-encoder scores are unbounded signed logits: positive = answers query, negative = doesn't; only meaningful relative to each other within one query
- Observed: hybrid hurts conceptual queries (BM25 floods with keyword matches the reranker scores poorly)
- qmd pipeline improvements in docs/archive/ (position-aware blending, heading-aware chunking, zeitgeist chunking)

## Next Session

Run real searches, build up log data, then pick one improvement to measure: position-aware reranker blending (fix hybrid burying good semantic results) or zeitgeist snapshot chunking.
