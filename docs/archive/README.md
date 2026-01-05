# Documentation Archive

This directory contains historical documentation that has been completed, superseded, or consolidated.

## Directory Structure

### `phase-2.5-completed/`
Documentation from Phase 2.5 implementation (2025-11-20 to 2025-11-24):

- **COMPACT-VIEW-PLAN.md** - Implementation plan for collapsible results UI (completed)
- **MANAGEMENT-PAGE-PLAN.md** - Implementation plan for management page (completed)
- **GLEANING-STATUS.md** - Feature documentation for active/inactive/hidden status (implemented, now part of ARCHITECTURE.md)
- **SEARCH-QUALITY.md** - Min-score filtering implementation (completed, part of system)
- **MIDCOURSE-2025-11-19.md** - Mid-course assessment after Phase 2, decision to add Phase 2.5

### `reviews/`
Comprehensive reviews conducted at end of Phase 2.5 (2025-11-23):

- **ARCHITECTURAL-REVIEW.md** - System architecture assessment, technical debt identification
- **SEARCH-ARCHITECTURE-REVIEW.md** - Search quality analysis, improvement recommendations
- **UI-REVIEW.md** - Web UI assessment, enhancement opportunities

**Note**: These three reviews were consolidated into `PHASE-3-READY.md` (parent directory).

### `QoL-improvements/`
Quality of Life improvements implementation (2025-12-30 to 2026-01-02):

- **PLAN.md** - Five-phase QoL improvement plan (completed, squash merged to phase-3.5-search-modes)
- **before-*.png** - Screenshots of UI before improvements (3 images)

**Implemented features**:
- Content-first search results layout
- Profile selector dropdown in UI
- Enhanced management page (gleaning stats, advanced stats, model selector)
- Mobile-optimized UX (collapsible results, keyboard shortcuts)
- PWA manifest for installable web app

**Status**: All phases complete, merged to main branch

### `original-planning/`
Initial project planning documents:

- **PROJECT-PROPOSAL.md** - Original project vision and architecture (formerly TEMOA.md)
  - Created 2025-11-17
  - Historical value: Shows initial thinking, open questions, and approach
  - Superseded by: IMPLEMENTATION.md and ARCHITECTURE.md

## Active Documentation

Current, living documentation is in the parent `docs/` directory:

- **ARCHITECTURE.md** - System architecture (kept up to date)
- **CHRONICLES.md** - Decision history and design discussions
- **IMPLEMENTATION.md** - Phase tracking and progress
- **PHASE-3-READY.md** - Next phase consolidated plan
- **DEPLOYMENT.md** - Operations guide
- **GLEANINGS.md** - User guide for gleanings feature

## When to Archive Documents

Archive documents when:
1. **Implementation complete** - Plan documents for finished features
2. **Superseded** - Information moved to living docs (ARCHITECTURE.md, etc.)
3. **Consolidated** - Multiple reviews combined into single actionable plan
4. **Historical checkpoint** - Mid-course assessments, decision points

Keep active when:
- Document is regularly updated (ARCHITECTURE.md, CHRONICLES.md, IMPLEMENTATION.md)
- Content is current reference material (DEPLOYMENT.md, GLEANINGS.md)
- Plan is for upcoming work (PHASE-3-READY.md)

---

**Archive Created**: 2025-11-24
**Last Updated**: 2026-01-04
