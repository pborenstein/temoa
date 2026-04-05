---
phase: "Experimentation"
phase_name: "Knobs & Dials"
updated: 2026-04-04
last_commit: 157cffe
branch: main
---

# Current Context

## Current Focus

Research session: reviewed Karpathy's LLM Wiki pattern and tobi/qmd. Wrote `docs/RESEARCH-NOTES.md` with findings, comparisons, and actionable ideas for Temoa.

## Active Tasks

- [ ] 181 remaining empty gleaning descriptions — accept or manual (or LLM-generate)
- [ ] Document baseline search performance (latency, relevance)
- [ ] Define test query suite with expected results

## Blockers

None

## Context

- `docs/RESEARCH-NOTES.md` is new — captures external research with provenance
- qmd (tobi/qmd) does same hybrid search pipeline as Temoa in TypeScript; 17k stars
- Karpathy's LLM Wiki pattern frames the vault as a persistent compounding wiki — Temoa is its search layer
- Key idea from qmd: position-aware score blending (varies RRF/reranker ratio by rank position)
- Gleaning descriptions = wiki page quality; 181 empty = 181 degraded search results

## Next Session

Start Experimentation phase: either (1) fill gleaning descriptions via LLM generation, or (2) run baseline search benchmarks and test position-aware score blending from the harness.
