---
phase: "Experimentation"
phase_name: "CODEX-SPEAKS Bug Fixes"
updated: 2026-02-21
last_commit: a545bfb
branch: main
---

# Current Context

## Current Focus

Addressed four categories of bugs from CODEX-SPEAKS code review: P0 data-safety issues (float sanitization, vault validation path), P1 issues (server ignoring vault model config, test import hacks), and P2 deprecation warnings.

## Active Tasks

- [x] Fix 1 (P0): `sanitize_unicode()` now handles NaN/inf floats → `None`
- [x] Fix 2 (P0): `validate_storage_safe()` uses model-scoped path; `get_vault_metadata()` returns `None` when `vault_path` absent
- [x] Fix 3 (P1): Server `get_client_for_vault()` respects vault-specific model config
- [x] Fix 4a (P1): `test_gleanings.py` uses proper package import (removed `sys.path` hack)
- [x] Fix 4b (P1): `test_synthesis.py` skips gracefully when `config.json` absent
- [x] Fix 4c (P1): `test_config.py` tilde test uses `tmp_path` (no `~/` side effects)
- [x] Fix 5 (P2): Replaced deprecated `regex=` with `pattern=` in two `Query()` calls

## Blockers

None

## Context

- **P0 data safety**: Float NaN/inf from cross-encoder/BM25 now sanitized before JSON; vault mismatch check now looks at correct `storage_dir/model/index.json` path
- **Vault model**: CLI already respected vault-specific model; server was silently ignoring it — now consistent
- **Test isolation**: `test_synthesis.py` was crashing at collection time without `config.json`; now skips cleanly
- **Pre-existing failures unchanged**: `test_config_missing_file_raises_error`, `test_edge_cases`, `test_normalizers` — all pre-existing, not caused by these fixes

## Next Session

Ready for next feature or issue. Consider running tests against real vault to confirm storage validation works correctly with model-scoped paths.
