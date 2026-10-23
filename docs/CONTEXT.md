---
phase: "Search Quality Experimentation"
phase_name: "Pure Search Engine"
updated: 2026-10-22
last_commit: 5c0c9fb
branch: main
---

# Current Context

## Current Focus

Search quality needs an outcome signal, not just a query log
(`docs/SEARCH-QUALITY-PLAN.md`). Phase 0 harvester is done; its candidates
need review before they count as judgments.

## Active Tasks

- [x] Write search-quality plan (SEARCH-QUALITY-PLAN.md)
- [x] Stop Claude Code transcripts expiring (`cleanupPeriodDays: 36500`, user settings)
- [x] Phase 0: transcript harvester → `~/Obsidian/amoxtli/.temoa/candidates.jsonl`
- [ ] Review candidates (`scripts/show_candidates.py`); decide judgment storage
- [ ] Phase 1: `caller`/`session` columns, print log id with CLI results
- [ ] Phase 2: `judgments` table + `temoa judge`; one step added to temoa-search skill
- [ ] Phase 3: `temoa eval` (recall@10, MRR, flood rate by mode)

## Blockers

None

## Context

- Harvest: 17 real searches in 8 transcripts (earlier "24 in 10" counted quoted
  mentions). Candidates: used 6, missed 23, unopened 147, context 16, grep_only 149
- Known misses confirmed: Josiah (relevant hits at ranks 7-8, 9 grep finds) and
  1095 tax form (answers in 4 daily notes, top 3 unrelated)
- Agents often pipe `temoa search` through grep/python; 5 rows are `parse: loose`.
  Phase 1's printed log id + `--json` would make this exact
- How-to for both scripts: `scripts/README.md`
- CLI does not call the server; each `temoa search` loads models in-process

## Next Session

Philip reviews candidates. Then start Phase 1: `caller`/`session` columns in
`search_log.py` with a migration, and print the log row id in CLI output.
