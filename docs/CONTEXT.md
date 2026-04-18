---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-04-18
last_commit: de5b5a1
branch: main
---

# Current Context

## Current Focus

Cron-friendly log format complete. Graph rebuild decoupled from reindex via new `temoa build-graph` command.

## Active Tasks

- [x] 181 remaining empty gleaning descriptions — done via Obsidian vault skill
- [x] `--log-format` flag for extract and reindex commands
- [x] `temoa build-graph` command (separate ~80s graph rebuild, supports `--log-format`)
- [ ] Add `build-graph` to crontab (user to do manually, suggested: `0 8,20 * * *`)
- [ ] Document baseline search performance (latency, relevance)
- [ ] Define test query suite with expected results
- [ ] Phase 1: implement qmd pipeline improvements (see `docs/plans/qmd-pipeline-improvements.md`)
- [ ] Phase 2: dashboard zeitgeist surface (see `docs/plans/dashboard-zeitgeist-surface.md`)

## Blockers

None

## Context

- `--log-format` output: `## YYYY-MM-DD HH:MM | command | stats | extra` — appended to `~/Obsidian/amoxtli/log/temoa-log.md`
- `reindex --log-format` never rebuilds the graph; graph is only for similar-notes UI, not search
- `build-graph` runs obsidiantools (~78s for 7897 nodes); deletions alone don't trigger graph rebuild
- `show_progress` threaded through synthesis.py → vault_reader.py; tqdm suppressed via `disable=not show_progress`
- **Synthesis is modifiable** — DEC-012 "do NOT modify" was Phase 1-2 only; CLAUDE.md corrected

## Next Session

Start Phase 1 pipeline work: read `synthesis/` chunking internals, implement position-aware score blending in `reranker.py` (self-contained, testable first), then tackle heading-aware chunking.
