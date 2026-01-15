---
phase: "Experimentation"
phase_name: "Knobs & Dials - Search Tuning"
updated: 2026-01-14
last_commit: 2182b5a
last_entry: 46
branch: main
---

# Current Context

## Current Focus

**NEW PHASE**: Experimentation with search parameters. The production hardening is complete - now we experiment with different combinations of knobs and dials to optimize search quality for real-world usage patterns.

## Active Tasks

- [ ] Define experimentation framework (what to measure, how to compare)
- [ ] Identify key tunable parameters (weights, thresholds, boosts)
- [ ] Create reproducible test queries with expected results
- [ ] Document baseline performance before tuning

## Blockers

None

## Context

- **Production hardening complete**: Phases 0-4 + 6 done, system is stable
- **Phase 4 (LLM)**: Moved to backburner (`docs/archive/backburner/phase-4-llm.md`)
- **Edge case test failures**: 37 known failures, not blocking - can revisit later
- **Current knobs available**:
  - Hybrid weight (BM25 vs semantic ratio)
  - Tag boost multiplier (currently 5x)
  - RRF fusion parameters
  - Time decay half-life (currently 90 days)
  - Cross-encoder re-ranking toggle
  - Query expansion threshold
  - Search profiles (repos, recent, deep, keywords, default)

## Next Session

User has notes to develop for experimentation direction. Review notes and plan approach.
