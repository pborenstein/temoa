---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-21
last_commit: 2508210
branch: knobs-and-dials
---

# Current Context

## Current Focus

Built pipeline step viewer (`/pipeline`) to visualize search results at each stage of the 8-stage pipeline.

## Active Tasks

- [x] Backend: Add `pipeline_debug=true` parameter and state capture
- [x] Frontend: Create pipeline.html with stage visualization
- [x] Integration: Add nav links between Search/Harness/Pipeline
- [x] Documentation: Update SEARCH-MECHANISMS.md and chronicles
- [ ] Testing: User feedback on pipeline viewer usefulness

## Blockers

None

## Context

- **Pipeline viewer** at `/pipeline` shows results flow through 7 stages (0, 1, 3-7)
- **State capture**: Minimal overhead (<50ms), includes timing, rank changes, filtered items
- **Three tools**: Search (main UI) ↔ Harness (score mixer) ↔ Pipeline (stage viewer)
- **Entry 53**: Added to `docs/chronicles/experimentation-harness.md`
- **Stage 2 combined**: Chunk deduplication happens inside `hybrid_search()`, so Stage 1 shows "Primary Retrieval & Chunk Deduplication"

## Next Session

Continue experimentation phase or move to production deployment. Pipeline viewer provides all necessary debugging tools for tuning search quality.
