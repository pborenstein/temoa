---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-27
last_commit: 58351b5
branch: main
---

# Current Context

## Current Focus

Vault graph build improvements: suppressed obsidiantools stdout spam, added file-level error reporting, moved graph rebuild to background thread during reindex.

## Active Tasks

- [x] Suppress ugly frontmatter parse errors from obsidiantools during graph build
- [x] Log filenames of files with bad YAML frontmatter (not just count)
- [x] Move graph rebuild to background thread in `/reindex` endpoint
- [ ] Fix the 42 files with unparseable YAML frontmatter in vault (user task)

## Blockers

None.

## Context

- **Graph build now async**: `/reindex` returns immediately; graph rebuilds in daemon thread (~90s)
- **CLI graph build still sync**: Intentional -- CLI users expect blocking completion
- **obsidiantools stdout capture**: `redirect_stdout` captures `print()` spam, extracts filenames via regex
- **42 bad frontmatter files**: Now listed by name in WARNING log; user can fix the YAML
- **Version**: 0.7.0, Experimentation Phase Active

## Next Session

Continue experimentation with Search Harness tools, or move to Phase 4 (Vault-First LLM). User may want to investigate/fix the 42 files with bad YAML frontmatter.
