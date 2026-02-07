---
phase: "Experimentation"
phase_name: "Two-Phase Filtering"
updated: 2026-02-07
last_commit: 6ed7394
branch: filters-and-combs
---

# Current Context

## Current Focus

Results Filter complete! Need to implement Query Filter (server-side type/status filtering).

## Active Tasks

- [x] Results Filter (client-side) - tag, path, file filtering on cached results
- [x] Obsidian syntax parser (lexer + AST evaluation)
- [x] Reset/clear controls
- [ ] Query Filter (server-side) - type, status filtering at fetch time
- [ ] Separate Query Filter UI section above Results Filter
- [ ] Query Filter clear button

## Blockers

None.

## Context

- **Results Filter (✓ Complete)**: Client-side filtering of cached results using Obsidian syntax
  - Filters: `tag:python`, `path:Gleanings`, `file:README`
  - Instant feedback (no server round-trip)
  - Clear button (✕) and included in Reset Mix
- **Query Filter (⚠ TODO)**: Server-side filtering at fetch time
  - Filters: `type:gleaning`, `status:active`, `[property:value]` syntax
  - Sends `include_types`/`exclude_types` params to `/search` endpoint
  - More efficient (don't fetch what you don't need)
  - Needs separate UI section with own clear button

## Next Session

Implement Query Filter section: extract type/status from AST, send as query params, add UI section above Results Filter.
