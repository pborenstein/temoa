---
phase: "Experimentation"
phase_name: "Stale Index Cleanup + UX Polish"
updated: 2026-02-08
last_commit: 413db30
branch: main
---

# Current Context

## Current Focus

Completed UX polish: viewport scrolling keeps selected item visible during slider reordering, selection highlighting fixed, all stale index and UI improvements done.

## Active Tasks

- [x] Detect and skip missing files during search (graceful handling)
- [x] Auto-clean stale index entries on reindex
- [x] Fix Time Boost display to show effective boost (time_boost × time_weight)
- [x] Fix search history auto-run behavior (now fills input for editing)
- [x] Keep selected item in viewport during reordering (scroll to keep visible)

## Blockers

None

## Context

- **Stale Index Cleanup**: VaultReader now checks file existence before reading, EmbeddingPipeline.clean_stale_entries() runs on every reindex
- **Time Boost Display**: Inspector shows effective boost = time_boost × time_weight (e.g., 0.09 × 2.0 = 18%)
- **Search History UX**: Clicking history item fills input and focuses it for editing, no auto-run
- **Viewport Scrolling**: Selected item stays visible during reordering - instant scroll before FLIP animation, top-of-card priority
- **Selection Highlighting**: Fixed data-path selector so clicked items highlight immediately

## Next Session

All polish tasks complete! Ready for next experimentation phase feature or user feedback.
