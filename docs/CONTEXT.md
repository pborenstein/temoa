---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-27
last_commit: d696882
branch: main
---

# Current Context

## Current Focus

Removed search profiles feature entirely (DEC-095). Profiles were an unused abstraction layer; all search parameters continue to work as direct query params.

## Active Tasks

- [x] Remove search profiles (search_profiles.py, tests, server, CLI, UI, docs)
- [ ] Fix the 42 files with unparseable YAML frontmatter in vault (user task)

## Blockers

None.

## Context

- **Search profiles removed**: Deleted search_profiles.py, test_search_profiles.py, /profiles endpoint, --profile CLI flag, profile dropdown in UI. All search params (hybrid, rerank, expand_query, time_boost, type filters) still work directly.
- **Tests: 167 passing** (was 171; difference is the 4 deleted profile test functions). 37 known failures unchanged.
- **Graph build async**: `/reindex` returns immediately; graph rebuilds in daemon thread (~90s)
- **Experimentation Phase Active**: Search Harness, Inspector, Pipeline Viewer all functional

## Next Session

Continue experimentation with Search Harness tools, or move to Phase 4 (Vault-First LLM). User may want to investigate/fix the 42 files with bad YAML frontmatter.
