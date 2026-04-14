---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-04-13
last_commit: 9dae4cb
branch: main
---

# Current Context

## Current Focus

Planning session: investigated Miyo/Obsidian Copilot, scoped two improvement tracks, corrected false Synthesis constraint.

## Active Tasks

- [ ] 181 remaining empty gleaning descriptions — accept or manual (or LLM-generate)
- [ ] Document baseline search performance (latency, relevance)
- [ ] Define test query suite with expected results
- [ ] Phase 1: implement qmd pipeline improvements (see `docs/plans/qmd-pipeline-improvements.md`)
- [ ] Phase 2: dashboard zeitgeist surface (see `docs/plans/dashboard-zeitgeist-surface.md`)

## Blockers

None

## Context

- **Synthesis is modifiable** — DEC-012 "do NOT modify" was Phase 1-2 only; CLAUDE.md corrected
- Two new plans written: pipeline improvements (position-aware blending, smart chunking, zeitgeist chunking) and dashboard surface (snapshot previews, cluster pill links)
- Claude Code Remote Control (`claude remote-control` + tmux) is the path to iOS vault access — user is on Pro/Max, CC v2.1.105
- Miyo is Copilot Plus's bundled sidecar (port 8742); Temoa could speak the Miyo API dialect as a compatibility shim if needed
- Zeitgeist snapshots are high-density signal — Connections/Clusters sections should be chunked separately from the Inventory list noise

## Next Session

Start Phase 1 pipeline work: read `synthesis/` chunking internals, implement position-aware score blending in `reranker.py` (self-contained, testable first), then tackle heading-aware chunking.
