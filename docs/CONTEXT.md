---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-14
last_commit: 60d6dc3
last_entry: 46
branch: knobs-and-dials
---

# Current Context

## Current Focus

Building a "Search Harness" - interactive score mixer to experiment with search parameter weights and see how they affect result ordering in real-time.

## Active Tasks

- [ ] Fix cross_encoder_score display bug (search.html:2407 looks for wrong field)
- [ ] Fix pipeline diagram in SEARCH-MECHANISMS.md (shows 7 stages, should be 8)
- [ ] Add `?harness=true` API parameter for structured score output
- [ ] Build Web UI harness panel with client-side re-mixing
- [ ] Add `temoa harness` CLI command
- [ ] Profile saving (localStorage for UI, config.json for CLI)

## Blockers

None

## Context

- **Plan created**: `docs/plans/search-harness-plan.md` - full implementation plan
- **Key insight**: Two-tier params - client-mixable (instant) vs server-side (re-fetch)
- **All raw scores preserved**: semantic, bm25, rrf, cross_encoder, time_boost survive pipeline
- **Profile saving**: localStorage for Web UI (simple), config.json for CLI
- **No sliders**: Use number inputs for weight adjustments

## Next Session

Implement the harness starting with bug fixes, then API changes. See `docs/plans/search-harness-plan.md`.
