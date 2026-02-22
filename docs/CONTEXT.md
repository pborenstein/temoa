---
phase: "Experimentation"
phase_name: "Test Hygiene"
updated: 2026-02-21
last_commit: b090774
branch: main
---

# Current Context

## Current Focus

Test Hygiene phase: cleaned 33 failing tests to 0 failures. Fixed 2 real bugs in normalizers. Discussion started about the 15 skipped tests -- next session should resolve them.

## Active Tasks

- [x] Fix all 33 failing tests (done: 196 passed, 0 failed, 15 skipped)
- [x] Fix 2 real bugs in `normalizers.py` (case-insensitive domain, double-slash paths)
- [ ] Resolve skipped tests (see Next Session)

## Blockers

None

## Context

- **New baseline**: 196 passed, 0 failed, 15 skipped
- **Skipped test analysis (15 tests)**:
  - `test_multi_vault_integration.py` (5 skipped): 2 are **duplicates** of passing `test_storage.py` tests (vault mismatch, force override). 3 are CLI integration tests needing a model loaded.
  - `test_synthesis.py` (8 skipped): 7 skip because no `config.json`; 1 skips for "path validation happens during import". These test `SynthesisClient` init/search/stats against a real vault.
  - `test_edge_cases.py` (2 skipped): Disk full scenarios -- legitimate infrastructure skips.
- **Key insight from discussion**: "Requires full Synthesis integration" is misleading -- Synthesis IS fully integrated. The real issue is these tests need a model loaded and a vault to point at. That's a test fixture problem, not an architecture problem.

## Next Session

Resolve the 15 skipped tests. The user's position: a test that never runs is not a test. Options per group:

1. **Multi-vault duplicates (2 tests)**: Delete -- already covered by `test_storage.py`
2. **Multi-vault CLI tests (3 tests)**: Either make them run with a temp vault + small model, or delete if the underlying logic is already tested
3. **Synthesis integration (8 tests)**: Either make them run (temp vault, bundled model) or delete -- the server tests already exercise search via HTTP
4. **Disk full (2 tests)**: Probably delete -- can't meaningfully test without OS-level mocking
