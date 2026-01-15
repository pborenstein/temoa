---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-15
last_commit: 9e6d219
last_entry: 50
branch: knobs-and-dials
---

# Current Context

## Current Focus

Building a "Search Harness" - interactive score mixer to experiment with search parameter weights and see how they affect result ordering in real-time.

## Active Tasks

- [x] Fix cross_encoder_score display bug (search.html:2407 looks for wrong field)
- [x] Fix pipeline diagram in SEARCH-MECHANISMS.md (shows 7 stages, should be 8)
- [x] Add `?harness=true` API parameter for structured score output
- [ ] Build Web UI harness panel with client-side re-mixing
- [ ] Add `temoa harness` CLI command
- [ ] Profile saving (localStorage for UI, config.json for CLI)

## Blockers

None

## Context

- **Plan**: `docs/plans/search-harness-plan.md` - full implementation plan
- **API done**: `?harness=true` returns `result.scores` object + `harness.mix`/`harness.server` metadata
- **Pipeline fixed**: Now shows 8 stages with chunk deduplication (Stage 2) and correct order
- **Tests added**: `test_search_harness_parameter` and `test_search_without_harness` (12/12 pass)
- **No sliders**: Use number inputs for weight adjustments

## Next Session

Build the Web UI harness panel with client-side re-mixing. See Phase 2 in `docs/plans/search-harness-plan.md`.
