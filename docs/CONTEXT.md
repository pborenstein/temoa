---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-27
last_commit: c74152a
branch: main
---

# Current Context

## Current Focus

Version housekeeping: unified version number across pyproject.toml, __version__.py, and docs to 0.7.0.

## Active Tasks

- [x] Bump pyproject.toml from 0.6.0 to 0.7.0
- [x] Update __version__.py fallback from 0.4.0-dev to 0.7.0
- [ ] Fix the 42 files with unparseable YAML frontmatter in vault (user task)

## Blockers

None.

## Context

- **Version unified to 0.7.0**: pyproject.toml is the single source of truth; __version__.py reads it via importlib.metadata at runtime
- **Graph build async**: `/reindex` returns immediately; graph rebuilds in daemon thread (~90s)
- **42 bad frontmatter files**: Listed by name in WARNING log; user can fix the YAML
- **Experimentation Phase Active**: Search Harness, Inspector, Pipeline Viewer all functional

## Next Session

Continue experimentation with Search Harness tools, or move to Phase 4 (Vault-First LLM). User may want to investigate/fix the 42 files with bad YAML frontmatter.
