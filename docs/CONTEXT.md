---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-04-18
last_commit: 6bc239a
branch: main
---

# Current Context

## Current Focus

Implemented `--log-format` flag for `temoa extract` and `temoa reindex` to produce single-line markdown log entries for cron jobs.

## Active Tasks

- [x] 181 remaining empty gleaning descriptions — done via Obsidian vault skill
- [x] `--log-format` flag for extract and reindex commands
- [ ] Update crontab to use `--log-format` (user to do manually)
- [ ] Document baseline search performance (latency, relevance)
- [ ] Define test query suite with expected results
- [ ] Phase 1: implement qmd pipeline improvements (see `docs/plans/qmd-pipeline-improvements.md`)
- [ ] Phase 2: dashboard zeitgeist surface (see `docs/plans/dashboard-zeitgeist-surface.md`)

## Blockers

None

## Context

- `--log-format` output: `## YYYY-MM-DD HH:MM | command | stats | mode` — appended to `~/Obsidian/amoxtli/log/temoa-log.md`
- Graph rebuild skipped when no files changed (saves ~80s); rebuilds when files change (~90s, expected for 7897 nodes)
- `show_progress` threaded through synthesis.py → vault_reader.py; tqdm suppressed via `disable=not show_progress`
- **Synthesis is modifiable** — DEC-012 "do NOT modify" was Phase 1-2 only; CLAUDE.md corrected
- Miyo is Copilot Plus's bundled sidecar (port 8742); Temoa could speak the Miyo API dialect if needed

## Next Session

Start Phase 1 pipeline work: read `synthesis/` chunking internals, implement position-aware score blending in `reranker.py` (self-contained, testable first), then tackle heading-aware chunking.
