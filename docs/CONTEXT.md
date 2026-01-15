---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-15
last_commit: e73b2c6
branch: knobs-and-dials
---

# Current Context

## Current Focus

Building a "Search Harness" - interactive score mixer to experiment with search parameter weights and see how they affect result ordering in real-time.

## Active Tasks

- [x] Fix cross_encoder_score display bug
- [x] Fix pipeline diagram in SEARCH-MECHANISMS.md
- [x] Add `?harness=true` API parameter for structured score output
- [x] Build harness.html page with client-side re-mixing
- [ ] Add `temoa harness` CLI command
- [ ] Profile saving (localStorage for UI, config.json for CLI)

## Blockers

None

## Context

- **Plan**: `docs/plans/search-harness-plan.md` - full implementation plan
- **Phase 2 complete**: `/harness` page with client-side remix, tooltips, semantic/BM25 balance slider
- **Tests**: 13/13 passing (includes `test_harness_page`)
- **UI features**: Info tooltips on all params, compact 2:1:1 layout (slider:tags:time)
- **Slider**: Single semantic/BM25 balance slider replaces two separate inputs

## Next Session

Phase 3: Add `temoa harness` CLI command. See Phase 3 in `docs/plans/search-harness-plan.md`.
