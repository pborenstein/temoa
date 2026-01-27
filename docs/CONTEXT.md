---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-26
last_commit: e1a8a67
branch: knobs-and-dials
---

# Current Context

## Current Focus

Inspector UX improvements: graph caching for fast loading, search history dropdown, section ordering.

## Active Tasks

- [x] Fix graph chips to open in Obsidian
- [x] Add "Similar by Topic" section to Inspector
- [x] Implement graph caching (90s → 0.1s load time)
- [x] Replace search history pills with dropdown
- [x] Swap order: Similar by Topic before Linked Notes
- [ ] Test end-to-end: full Inspector functionality

## Blockers

None.

## Context

- **Graph caching**: VaultGraph now persists to `.temoa/vault_graph.pkl`
  - First load: ~90s (builds from obsidiantools)
  - Cached load: ~0.1s
  - Rebuilds automatically on `temoa index` / `temoa reindex` / `/reindex`
- **Search history**: Now a dropdown under search input instead of pills
  - Arrow keys to navigate, Enter to select, X to delete individual items
  - Shows on focus when input is empty
- **Inspector order**: Similar by Topic (semantic) now appears before Linked Notes (graph)

## Next Session

Test the full Inspector with both sections. Commit the current changes.
