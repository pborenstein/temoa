---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-05-30
last_commit: 1ef34ca
branch: claude/docs-codebase-review-5YeTG
---

# Current Context

## Current Focus

Temoa has been rebuilt as a pure search engine. Gleaning extraction, graph,
and UI are gone. The server is a clean JSON API; the CLI has 8 commands.

## Active Tasks

- [x] Strip gleanings/graph/UI from server.py (2671 → 430 lines)
- [x] Create composable pipeline abstraction (pipeline.py + server_filters.py)
- [x] Wire server.search() through default_pipeline()
- [x] Delete gleanings.py, normalizers.py, github_client.py, vault_graph.py, scripts/
- [x] Strip CLI to 8 commands; search uses default_pipeline()
- [x] Clean up CLI help text and command descriptions
- [ ] Merge branch to main / open PR

## Blockers

None

## Context

- Branch `claude/docs-codebase-review-5YeTG` has 6 commits ahead of main
- Server is pure JSON API — no UI served, no gleaning routes, no graph routes
- Pipeline abstraction: SearchContext → Stage protocol → Pipeline runner → default_pipeline()
- Score envelope: set_score/score_view alongside legacy flat fields (strangler-safe)
- CLI commands: server, search, archaeology, stats, index, reindex, config, vaults
- 147 tests passing (was 216; 69 gleaning/normalizer tests removed with the code)

## Next Session

Decide whether to merge the branch, then start new work: config-driven pipeline
profiles (`search.profiles` in config.json, `profile` query param) or baseline
search performance documentation.
