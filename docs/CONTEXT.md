---
phase: "Production Hardening"
phase_name: "Part 8: Bug Fixes"
updated: 2026-03-16
last_commit: c36a042
branch: main
---

# Current Context

## Current Focus

Fixed two bugs this session: (1) manage page showing "not indexed / Last Indexed: Never" after reindex, (2) gleaning files with emoji in titles containing invalid surrogate pair YAML escapes.

## Active Tasks

- [x] Fix "not indexed" after reindex: call `validate_storage_safe()` post-reindex to re-inject `vault_path`
- [x] Fix surrogate pair YAML escapes in gleaning files (21 files repaired, `ensure_ascii=False` in extractor)
- [x] Restore emptied gleaning file `0caac197ccc7.md` from extraction state
- [x] Fix broken venv (directory renamed, shebang stale — recreated via `uv sync`)
- [ ] 181 remaining empty descriptions — floor without LLM, accept or manual

## Blockers

None

## Context

- `validate_storage_safe()` in `storage.py` handles missing `vault_path` via migration path — called after both reindex and auto-reindex in extract endpoint
- Surrogate pairs (`\uD83E\uDDC0`) in YAML frontmatter are rejected by obsidiantools/pyyaml; fix is `json.dumps(..., ensure_ascii=False)`
- `0caac197ccc7.md` was 0 bytes — restored from `extraction_state.json`
- Test baseline: 196 passed, 0 failed, 0 skipped

## Next Session

Move to Experimentation phase: document baseline search performance and start parameter tuning with the Search Harness.
