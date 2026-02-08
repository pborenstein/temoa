---
phase: "Experimentation"
phase_name: "Stale Index Cleanup + UX Polish"
updated: 2026-02-08
last_commit: 613b6b4
branch: main
---

# Current Context

## Current Focus

Fixed stale index entries (auto-cleanup on reindex) and UX improvements: search history now fills input without auto-running, Time Boost display shows effective boost with time_weight multiplier.

## Active Tasks

- [x] Detect and skip missing files during search (graceful handling)
- [x] Auto-clean stale index entries on reindex
- [x] Fix Time Boost display to show effective boost (time_boost × time_weight)
- [x] Fix search history auto-run behavior (now fills input for editing)
- [ ] Keep selected item in viewport during reordering (scroll to keep visible)

## Blockers

None

## Context

- **Stale Index Cleanup**: VaultReader now checks file existence before reading, EmbeddingPipeline.clean_stale_entries() runs on every reindex
- **Time Boost Display**: Inspector shows effective boost = time_boost × time_weight (e.g., 0.09 × 2.0 = 18%)
- **Search History UX**: Clicking history item fills input and focuses it for editing, no auto-run
- **Next Feature**: Viewport auto-scroll to keep selected item visible during FLIP reordering animations

## Next Session

Implement viewport scrolling to keep selected item visible during slider-driven reordering. When user adjusts sliders with Inspector open, smoothly scroll results container so selected item stays in view through FLIP animation. See search.html lines 3184-3254 (remixAndRender function) and lines 3905+ (renderInspector).
