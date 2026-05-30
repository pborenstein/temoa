# CODEX SPEAKS: Fresh-Eyes Review of Temoa

## Executive Read
Temoa feels like three things at once:
1. A real, useful product (search server + UI + CLI).
2. An active experimentation lab (harness, pipeline debug, chronicles).
3. A knowledge artifact (extensive historical docs and design logs).

That is a strength, but right now the boundaries between those modes are blurry. The core architecture is solid, yet reliability and maintainability are being taxed by drift between implementation, tests, and documentation.

## What Looks Strong
- The project has unusually good technical memory in `docs/chronicles/` and architecture docs.
- The search pipeline is thoughtfully layered (query expansion, retrieval, filters, rerank, time boost, introspection).
- Multi-vault/client-cache architecture is practical and clearly intentional.
- You have strong product instincts: practical CLI, web UI, and mobile-first workflows are all present.

## Priority Findings

### P0: `/search` can return HTTP 500 due to non-JSON-safe floats
- Evidence: server tests fail with `ValueError: Out of range float values are not JSON compliant` at `src/temoa/server.py:1798` (`JSONResponse(content=data)`).
- Impact: user-facing query failures; search endpoint reliability risk.
- Observation: Unicode is sanitized (`sanitize_unicode`), but non-finite floats (`NaN`, `inf`) are not normalized before JSON serialization.

### P0: Storage safety validation is misaligned with current storage layout
- In `src/temoa/storage.py:69`, `validate_storage_safe()` reads `storage_dir / "index.json"`.
- In `src/temoa/storage.py:168`, metadata is read from model-specific `storage_dir / model / "index.json"`.
- Result: safety checks can silently miss existing model-scoped indices, which is exactly what `tests/test_storage.py` failures show.
- Impact: false sense of safety around index overwrite/mismatch protection.

### P1: Server path ignores vault-specific model selection
- `src/temoa/server.py:313` creates clients with `model=config.default_model` in `get_client_for_vault()`.
- CLI search explicitly resolves vault-specific model (`src/temoa/cli.py:181-216`).
- Impact: behavior divergence between API/server and CLI for the same vault config; hard-to-explain search quality/index mismatch.

### P1: Test suite currently does not represent runnable reality
- `tests/test_gleanings.py:16-17` imports `extract_gleanings` from `scripts/`, but code now lives under `src/temoa/scripts/`.
- `tests/test_synthesis.py:11` hard-requires local `config.json` that is not present in repo.
- `tests/test_config.py` attempts home-directory writes (`~/test-vault`) and fails in restricted environments.
- Net result from run: collection/runtime errors and multiple failures not tied to one subsystem.

### P2: Environment/setup drift is visible in tooling
- `.venv/bin/pytest` has a stale interpreter path (`/Users/philip/projects/temoa/...`) after repo relocation.
- This is a small but telling sign that reproducibility has drifted from current workspace assumptions.

### P2: Framework deprecation warnings are already live
- `src/temoa/server.py:2495` and `src/temoa/server.py:2540` still use `regex=` in FastAPI `Query`, now deprecated in favor of `pattern=`.
- Not urgent, but a straightforward maintenance cleanup before future framework upgrades.

## Strategic Observation
You have enough capability to be both a stable personal tool and an active research playground, but not under one undifferentiated execution path.

The current pain is not “bad architecture”; it is **mode mixing**:
- Production behavior and experimental behavior share too much runtime/test surface.
- Documentation is rich but no longer tightly coupled to what is executable now.

## Suggested Direction (High-Level)
1. Split runtime modes explicitly: `stable` vs `experimental` switches (or profiles) for server features and tests.
2. Rebuild a hermetic test baseline: one command, one fixture config, no home-path assumptions.
3. Make storage/model semantics uniform across CLI + API + validation utilities.
4. Add a final JSON-safety normalization pass for floats before responses.

## Verification Notes
Commands executed during review included repository scan and targeted test runs via `.venv/bin/python -m pytest`.

Observed test status from sampled run:
- `12 failed, 26 passed, 6 skipped, 6 errors` (plus deprecation warnings)
- Additional collection failure in `tests/test_gleanings.py` when running full suite.
