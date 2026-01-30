---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-29
last_commit: e8b3349
branch: main
---

# Current Context

## Current Focus

Testing plinth's token-efficient documentation system with opencode. Created NO-CLAUDE-SKILLS.md guide for using plinth without Claude Code skills.

## Active Tasks

- [x] Remove search profiles (search_profiles.py, tests, server, CLI, UI, docs)
- [x] Create NO-CLAUDE-SKILLS.md guide for opencode compatibility
- [ ] Fix the 42 files with unparseable YAML frontmatter in vault (user task)

## Blockers

None.

## Context

- **Search profiles removed**: Deleted search_profiles.py, test_search_profiles.py, /profiles endpoint, --profile CLI flag, profile dropdown in UI. All search params (hybrid, rerank, expand_query, time_boost, type filters) still work directly.
- **Tests: 167 passing** (was 171; difference is the 4 deleted profile test functions). 37 known failures unchanged.
- **Graph build async**: `/reindex` returns immediately; graph rebuilds in daemon thread (~90s)
- **Experimentation Phase Active**: Search Harness, Inspector, Pipeline Viewer all functional

## Next Session

Test NO-CLAUDE-SKILLS.md with other projects, or continue Temoa experimentation. User may want to fix YAML frontmatter issues or explore Phase 4 (Vault-First LLM).
