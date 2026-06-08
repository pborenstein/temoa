---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-06-07
last_commit: 96b9938
branch: main
---

# Current Context

## Current Focus

Temoa is a clean pure search API. Launchd service and cahuitl cron updated.
System is fully operational in its rebuilt form.

## Active Tasks

- [x] Strip gleanings/graph/UI from server.py (2671 → 430 lines)
- [x] Create composable pipeline abstraction (pipeline.py + server_filters.py)
- [x] Strip CLI to 8 commands; search uses default_pipeline()
- [x] Clean up CLI help text
- [x] Restore type filtering (--type / --exclude-type, filter_by_type in pipeline)
- [x] Extract gleaning code to pixquitl repo
- [x] Merge branch to main (48c90ec)
- [x] Restart launchd service (new server live)
- [x] Update cahuitl cron to use `pixquitl extract` instead of `temoa extract`

## Blockers

None

## Context

- `--type` / `--exclude-type` use `normalize_type()` from `nahuatl_frontmatter`
- tlatecpana `temoa-search` skill uses CLI directly — no skill changes needed
- pixquitl extracted at `~/projects/nahuatl-PROJECTS/pixquitl` (gleaning lifecycle)
- 196 tests passing

## Next Session

No queued tasks. Identify what to work on next.
