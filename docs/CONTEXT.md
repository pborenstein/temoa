---
phase: "Search Quality Experimentation"
phase_name: "Pure Search Engine"
updated: 2026-07-04
last_commit: d9ed540
branch: main
---

# Current Context

## Current Focus

Repo cleanup complete: v1-era docs archived, tracking reframed around the pure
search engine. Next up: use the search log to pick and measure one search
quality improvement.

## Active Tasks

- [x] Archive v1 chronicles to `docs/archive/chronicles-v1/`; chronicles/ now holds only the v2 era
- [x] Rewrite IMPLEMENTATION.md: v1 phase ladder condensed to a history table
- [x] Remove dead code: `src/temoa/ui/` (unused since v2 rebuild), unused `GleaningError`
- [x] Wrapup: Entry 102, DEC-103
- [ ] Build up search log data, then pick one improvement to measure

## Blockers

None

## Context

- 155 tests passing
- `search_log.db` in `.temoa/`; CLI logs vault as full path, server logs vault name (minor inconsistency)
- Cross-encoder scores are unbounded signed logits: positive = answers query, negative = doesn't; only meaningful relative to each other within one query
- Observed: hybrid hurts conceptual queries (BM25 floods with keyword matches the reranker scores poorly)
- qmd pipeline improvements in docs/archive/ (position-aware blending, heading-aware chunking, zeitgeist chunking)

## Next Session

Run real searches, build up log data, then pick one improvement to measure:
position-aware reranker blending (fix hybrid burying good semantic results) or
zeitgeist snapshot chunking.
