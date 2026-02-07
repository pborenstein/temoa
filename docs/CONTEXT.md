---
phase: "Experimentation"
phase_name: "Two-Phase Filtering"
updated: 2026-02-07
last_commit: 82a4e84
branch: filters-and-combs
---

# Current Context

## Current Focus

Query Filter implemented with generic property filtering. Performance issue: inclusive filters search entire vault first (slow). Need architectural fix or usage guidance.

## Active Tasks

- [x] Query Filter (server-side) - generic property/tag/path/file filtering
- [x] Query Filter UI section with clear button
- [x] Generic filter functions (not just type/status)
- [x] Cancel button for slow searches
- [ ] Performance optimization for inclusive filters (architectural)

## Blockers

Architectural limitation: can't filter BEFORE semantic search. Inclusive filters (`[type:daily]`) search entire vault then filter (30+ seconds). Exclude filters (`-[type:gleaning]`) are fast.

## Context

- **Query Filter (✓ Implemented)**: Server-side filtering using Obsidian syntax
  - Properties: `[type:gleaning]`, `[title:foo]`, `[any:value]`
  - Tags: `tag:python`, Paths: `path:Gleanings`, Files: `file:README`
  - Sends JSON arrays to `/search`: `include_props`, `exclude_props`, etc.
  - Cancel button for slow searches (AbortController)
- **Performance Issue**: Inclusive filters slow (search all → filter). Exclude filters fast (search limited → filter)
- **Workaround**: Use exclude filters (`-[type:daily]`) instead of include (`[type:gleaning]`)
- **Long-term fix**: Pass filters to Synthesis BEFORE semantic search (requires Synthesis changes)

## Next Session

Consider: (1) Add pre-filtering to Synthesis, (2) Document performance trade-offs, (3) Add UI warnings for slow filter patterns, or (4) Accept current behavior with guidance.
