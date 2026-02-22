---
phase: "Experimentation"
phase_name: "Performance Fix: Eliminate Double Vault Scan"
updated: 2026-02-21
last_commit: c35f847
branch: main
---

# Current Context

## Current Focus

Fixed double vault scan during incremental extract+reindex. `_find_changed_files` now returns its vault content so the incremental reindex path can reuse it instead of calling `read_vault()` again.

## Active Tasks

- [x] Fix double vault scan during incremental reindex

## Blockers

None

## Context

- **Double scan root cause**: `_find_changed_files()` called `read_vault()` to build changeset; incremental reindex path then called `read_vault()` again to rebuild BM25
- **Fix**: `_find_changed_files` now includes `"vault_content"` key in return dict; incremental path assigns `vault_content = changes["vault_content"]`
- **BM25 note**: reused vault_content is non-chunked (same as before — `_find_changed_files` never passed chunking args); behavior unchanged
- **Tests**: unit tests can't exercise this path (requires real vault/index); validated by code inspection

## Next Session

Ready for next feature or user-reported issue. Consider testing the fix against the real vault with an incremental extract+reindex to confirm only one "Reading vault files" progress bar appears.
