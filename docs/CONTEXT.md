---
phase: "Experimentation"
phase_name: "Gleanings Rethink"
updated: 2026-02-06
last_commit: 003bf9b
branch: filters-and-combs
---

# Current Context

## Current Focus

Filtering work surfaced fundamental issues with gleanings system. Pivoting to fix gleanings first before continuing with query/result filtering architecture.

## Active Tasks

- [x] Document gleaning problems (GitHub template, two-phase filtering insight)
- [ ] Fix GitHub gleaning extraction (better descriptions without requiring manual input)
- [ ] Update gleaning template/format
- [ ] Test gleaning improvements on existing gleanings
- [ ] Return to filtering: implement Query filters (pre-fetch) vs Result filters (post-fetch)

## Blockers

None.

## Context

- **Key insight**: Two-phase filtering needed - Query filters (pre-fetch/server) vs Result filters (post-fetch/client)
- **Gleaning problem**: GitHub repos missing "why I saved this" context, template is redundant
- **No manual descriptions**: User doesn't add context when saving gleanings, can't require it
- **Terminology decided**: "Query filters" and "Result filters" (not "search" vs "display")
- **Staying on branch**: Gleanings and filtering are intertwined, keeping together makes sense
- **Chronicle entry 67**: Documented problems in gleanings-rethink-2026-02.md

## Next Session

Start fixing gleaning extraction - focus on GitHub repos first. Need to extract better descriptions automatically without requiring manual input.
