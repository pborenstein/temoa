---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-06-08
last_commit: d2dbaba
branch: main
---

# Current Context

## Current Focus

Search query logging infrastructure. Every search (HTTP + CLI) now persists to `.temoa/search_log.db` so we can measure whether algorithm changes actually help.

## Active Tasks

- [x] SQLite search log (SearchLog class, aiosqlite)
- [x] Server wires log in lifespan, logs after each search
- [x] CLI search command logs (including vault path, mode, results)
- [x] `temoa log` command — recent searches + --stats
- [x] Pipeline stage timing always captured (not just pipeline_debug)
- [x] Test suite uses tmp_path for log (not live vault)

## Blockers

None

## Context

- 155 tests passing (196 in CLAUDE.md was stale — update it)
- search_log.db stored in `.temoa/` alongside vector index
- CLI logs vault as full path (not name) — minor inconsistency with server
- `temoa log` displays local time; DB stores UTC
- qmd pipeline improvements in docs/archive/ (position-aware blending, heading-aware chunking, zeitgeist chunking)

## Next Session

Now that logging is in place, good next steps: run some real searches and look at the log, then tackle a search quality improvement (zeitgeist chunking, position-aware blending, or multi-model experiment) and use the log to compare.
