---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-15
last_commit: 8a7e717
branch: knobs-and-dials
---

# Current Context

## Current Focus

Refining harness UI - improving clarity of Fetch vs Live parameters and visual feedback for score components.

## Active Tasks

- [x] Fix cross_encoder_score display bug
- [x] Fix pipeline diagram in SEARCH-MECHANISMS.md
- [x] Add `?harness=true` API parameter for structured score output
- [x] Build harness.html page with client-side re-mixing
- [x] Harness UI refinements (this session)
- [ ] Add `temoa harness` CLI command
- [ ] Profile saving (localStorage for UI, config.json for CLI)

## Blockers

None

## Context

- **Plan**: `docs/plans/search-harness-plan.md` - full implementation plan
- **Fetch/Live split**: Fetch (server retrieval) now comes before Live (client remix) in UI
- **Both sliders**: Fetch balance and Live balance now both use slider UI (0-100 scale)
- **Visual feedback**: Time-boosted dates glow purple, matched tags glow green
- **Tags=0**: Disables tag boosting (treats as 1x multiplier, not 0x)
- **Slider persistence**: Fixed bug where Live slider reset after search

## Next Session

Phase 3: Add `temoa harness` CLI command. See Phase 3 in `docs/plans/search-harness-plan.md`.
