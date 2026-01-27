---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-26
last_commit: 1f29eed
branch: knobs-and-dials
---

# Current Context

## Current Focus

Implementing Option C from Entry 59 - adding "Similar by Topic" section to Inspector that shows semantic neighbors alongside graph neighbors.

## Active Tasks

- [x] Fix graph chips to open in Obsidian (was searching for note name)
- [x] Write Entry 59: Graph-Enhanced Discovery planning doc
- [x] Add "Similar by Topic" section to Inspector pane
- [x] Create fetchSemanticNeighbors() function
- [x] Create createSimilarChip() helper (orange/amber color scheme)
- [ ] Test end-to-end: graph links + semantic neighbors

## Blockers

None.

## Context

- **Graph chips fixed**: Now open notes in Obsidian instead of searching
- **Entry 59 written**: Planning doc with 5 options for using graph data
- **Option C implemented**: "Similar by Topic" section added to Inspector
  - Uses note title as semantic search query
  - Pure semantic search (hybrid_weight=1.0)
  - Filters out current note, shows top 6 neighbors
  - Orange/amber chips to distinguish from graph links (blue/green)
  - Chips open in Obsidian on click

## Color Scheme

| Chip Type | Background | Text Color |
|-----------|------------|------------|
| Incoming (← links here) | rgba(100, 150, 200, 0.2) | #8ab4d8 (blue) |
| Outgoing (→ links to) | rgba(150, 200, 100, 0.2) | #a8d080 (green) |
| 2-hop neighbors | rgba(150, 150, 150, 0.15) | #999 (gray) |
| Similar by Topic | rgba(200, 150, 100, 0.2) | #d8a87c (amber) |

## Next Session

Test the full Inspector with both graph and semantic neighbors. Consider:
1. Graph loading performance (90s first request)
2. Whether semantic neighbors add useful signal vs noise
3. Overlap between graph and semantic neighbors (interesting data point)
