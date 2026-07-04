---
phase: "Search Quality Experimentation"
phase_name: "Pure Search Engine"
updated: 2026-07-04
last_commit: 6cb546a
branch: main
---

# Current Context

## Current Focus

Repo cleanup complete: v1 docs archived, synthesis engine folded into
`src/temoa/engine/`, all docs congruent. Ready to cut v2.1.0 and get back to
search quality work.

## Active Tasks

- [x] Archive v1 chronicles; reframe IMPLEMENTATION.md (Entry 102, DEC-103)
- [x] Extract synthesis → `src/temoa/engine/`; delete vendored dir (Entry 103, DEC-104)
- [x] Fix `temoa archaeology` (broken CLI schema + top_k arg)
- [x] Docs congruence pass (TESTING.md, config examples, README)
- [ ] Release v2.1.0 (releaserator)
- [ ] Restart launchd service to pick up new code
- [ ] Build up search log data, then pick one improvement to measure

## Blockers

None

## Context

- 156 tests passing; `synthesis_path` in config.json is now ignored (legacy)
- launchd service still running pre-extraction code until restarted
- Cross-encoder scores are unbounded signed logits; only comparable within one query
- Observed: hybrid hurts conceptual queries (BM25 floods with keyword matches)
- qmd pipeline improvement plans in docs/archive/ (position-aware blending, etc.)

## Next Session

Run real searches, build up log data, then pick one improvement to measure:
position-aware reranker blending or zeitgeist snapshot chunking.
