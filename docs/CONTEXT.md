---
phase: "Search Quality Experimentation"
phase_name: "Pure Search Engine"
updated: 2026-07-06
last_commit: 21d1ccb
branch: main
---

# Current Context

## Current Focus

v2.1.0 released and launchd service restarted on new code. Clarified CLI/server
architecture. Ready for search quality work: build log data, measure one improvement.

## Active Tasks

- [x] Release v2.1.0 (tag exists, HEAD is the version bump)
- [x] Restart launchd service (PID confirmed started after v2.1.0 commit)
- [ ] Build up search log data, then pick one improvement to measure

## Blockers

None

## Context

- CLI does NOT call the server: each `temoa search` builds its own SynthesisClient
  in-process and pays full model load; server keeps models warm via client_cache
- CLI and server share only disk state: config.json + `.temoa/` index
- Multi-vault registry in config.json is v1 web-app legacy; possible simplifications:
  thin HTTP-client CLI mode, or drop multi-vault (discussed, no decision)
- Cross-encoder scores are unbounded signed logits; only comparable within one query
- Observed: hybrid hurts conceptual queries (BM25 floods with keyword matches)

## Next Session

Run real searches, build up log data, then pick one improvement to measure:
position-aware reranker blending or zeitgeist snapshot chunking.
