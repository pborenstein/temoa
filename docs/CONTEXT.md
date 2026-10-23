---
phase: "Search Quality Experimentation"
phase_name: "Pure Search Engine"
updated: 2026-10-22
last_commit: bbfa860
branch: main
---

# Current Context

## Current Focus

Search quality needs an outcome signal, not just a query log. Plan written in
`docs/SEARCH-QUALITY-PLAN.md`: capture what agents use and what grep finds that
Temoa missed, turn that into a judged test set, then measure one change.

## Active Tasks

- [x] Write search-quality plan (SEARCH-QUALITY-PLAN.md)
- [x] Stop Claude Code transcripts expiring (`cleanupPeriodDays: 36500`, user settings)
- [ ] Phase 0: read-only transcript harvester → candidate judgments JSONL
- [ ] Phase 1: `caller`/`session` columns, print log id with CLI results
- [ ] Phase 2: `judgments` table + `temoa judge`; one step added to temoa-search skill
- [ ] Phase 3: `temoa eval` (recall@10, MRR, flood rate by mode)

## Blockers

None

## Context

- search_log.db: 452 searches 2026-06-08 to 2026-10-23 (357 hybrid, 94 semantic), no outcomes
- Transcripts on disk go back to 2026-09-22; 10 contain `temoa search`, 24 searches,
  18 followed by grep/find within three tool calls (crude; not all are misses)
- Worked miss (2026-10-22, Josiah query, hybrid): top 3 were BM25 floods, the 2 relevant
  hits were semantic-only at ranks 7-8, 4 relevant notes not returned (found by grep)
- LLM agents are the only users; Philip doesn't use the web UI. CLAUDE.md's
  "mobile-first" principle predates this and is stale
- CLI does not call the server; each `temoa search` loads models in-process

## Next Session

Write the Phase 0 harvester: walk `~/.claude/projects/*/*.jsonl`, pair each
`temoa search` with the reads and greps that follow it, write candidate judgments
for Philip to review.
