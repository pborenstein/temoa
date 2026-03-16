---
phase: "Experimentation"
phase_name: "Gleanings Cleanup"
updated: 2026-03-16
last_commit: 56c93b7
branch: main
---

# Current Context

## Current Focus

GitHub title fix is deployed and verified — re-extraction ran, 0 files left with bare `github.com` titles. CLAUDE.md slimmed from 719 to 155 lines.

## Active Tasks

- [x] Fix `extract_gleanings.py`: GitHub URLs use API, not HTML scrape
- [x] Run full re-extraction on `~/Obsidian/amoxtli` with fixed extractor
- [x] Verify GitHub gleanings have correct `user/repo: description` titles
- [ ] Handle remaining domain-fallback titles (YouTube x19, paywalled — likely manual)
- [ ] Address gleanings with empty descriptions

## Blockers

None

## Context

- Full re-extraction complete; no bare `github.com` titles remain
- GitHub titles now formatted as `"user/repo: repo description"` from API
- YouTube/WaPo/WSJ/NYer domain-fallbacks are expected — those sites block scrapers
- CLAUDE.md trimmed to ~155 lines (was 719); history lives in IMPLEMENTATION.md + chronicles
- Test baseline: 196 passed, 0 failed, 0 skipped

## Next Session

Decide what to do about YouTube x19 and other paywalled domain-fallback titles. Then move to the Experimentation phase: document baseline search performance and start parameter tuning.
