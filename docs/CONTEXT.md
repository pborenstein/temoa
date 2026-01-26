---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-25
last_commit: 50267fc
branch: knobs-and-dials
---

# Current Context

## Current Focus

Score explainers and UX improvements complete. Added comprehensive tooltips, help panel, and fixed view switching bugs.

## Active Tasks

- [x] Add tooltips to all scores (Semantic, BM25, RRF, Cross-Enc, Final)
- [x] Add help panel with comprehensive scoring documentation
- [x] Improve control tooltips (Fetch/Live sliders)
- [x] Fix view switching to preserve results across List ⟷ Explorer
- [x] Move search history from sidebar to header (shared across views)
- [x] Fix tooltip clipping issues (dynamic positioning)
- [x] Fix tag multiplier minimum to 1.0 (no "death penalty" mode)

## Blockers

None.

## Context

- **Score Explainers**: All scores have detailed tooltips explaining scale, meaning, and impact
  - Semantic (0-1), BM25 (0-30+), RRF (0-0.05), Cross-Enc (-12 to +12), Final (dynamic)
  - Tooltips use smart positioning to avoid clipping outside panes
- **Help Panel**: "?" button in Inspector shows comprehensive guide (scoring, controls, pipeline)
- **View Switching**: Results now persist when toggling List ⟷ Explorer (re-renders for new view)
- **Search History**: Moved to header as horizontal chips, visible in both views
- **Tag Multiplier**: Range 1.0-10.0 (1.0=neutral, 5.0=default, 10.0=max boost)
- **Files**: `src/temoa/ui/search.html` (2,750+ lines with new features)

## Next Session

Consider committing changes. Test tooltip positioning on different screen sizes. Explore Phase 2 features (profile save/load, export).
