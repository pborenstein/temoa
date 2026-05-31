---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-05-30
last_commit: 48c90ec
branch: main
---

# Current Context

## Current Focus

Temoa is a clean pure search API. Type filtering restored after discovering
tlatecpana skills depend on `--type gleaning` / `--exclude-type daily`.

## Active Tasks

- [x] Strip gleanings/graph/UI from server.py (2671 → 430 lines)
- [x] Create composable pipeline abstraction (pipeline.py + server_filters.py)
- [x] Strip CLI to 8 commands; search uses default_pipeline()
- [x] Clean up CLI help text
- [x] Restore type filtering (--type / --exclude-type, filter_by_type in pipeline)
- [x] Extract gleaning code to pixquitl repo
- [x] Merge branch to main (48c90ec)

## Blockers

None

## Context

- Branch has 8 commits ahead of main; all work on `claude/docs-codebase-review-5YeTG`
- `--type` / `--exclude-type` use `normalize_type()` from `nahuatl_frontmatter`
- tlatecpana `temoa-search` skill uses CLI directly — no skill changes needed
- pixquitl extracted at `~/projects/nahuatl-PROJECTS/pixquitl` (gleaning lifecycle)
- 147 tests passing

## Next Session

Restart launchd service to pick up the new server, then update cahuitl
cron to use `pixquitl extract` instead of `temoa extract`.
