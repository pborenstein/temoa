# CHRONICLES.md - Project Lore & Design Discussions

> **Purpose**: This document captures key discussions, design decisions, and historical context for the Temoa project. Unlike IMPLEMENTATION.md (which tracks *what* to build) or CLAUDE.md (which explains *how* to build), Chronicles explains *why* we're building it this way.

**Created**: 2025-11-18
**Format**: Chronological entries with discussion summaries
**Audience**: Future developers, decision-makers, and your future self

---

## Chronicle Organization

The chronicles have been split into chapters for easier navigation:

### [Phase 0-1: Foundation](chronicles/phase-0-1-foundation.md)
**Entries 1-6** | Planning, Architecture, and MVP

- Entry 1: The Central Problem of AI
- Entry 2: Architectural Constraints & Deployment Model
- Entry 3: The Hardcoded Paths Saga
- Entry 4: Phase 0 Performance Investigation
- Entry 5: Is Synthesis Worth the Dependency?
- Entry 6: Phase 1 Complete - Production-Ready Server

### [Phase 2: Gleanings Integration](chronicles/phase-2-gleanings.md)
**Entries 7-9** | Making Gleanings Searchable

- Entry 7: Phase 2 Complete - Gleanings Integration
- Entry 8: CLI Implementation and Real-World Testing
- Entry 9: Gleanings Extraction Fixes

### [Phase 2.5: Deployment & Mobile Validation](chronicles/phase-2.5-deployment.md)
**Entries 10-12** | Real-World Usage and Gleaning Management

- Entry 10: Mid-Course Assessment - Pausing Before Phase 3
- Entry 11: Deployment Shakedown - Real-World Bugs Surface
- Entry 12: Gleanings Status Management - Active, Inactive, Hidden

---

## Quick Reference: Key Decisions

| Decision | Entry | Summary |
|----------|-------|---------|
| DEC-001: Project name (Temoa) | 6 | Named after Nahuatl "to seek" |
| DEC-009: Direct imports over subprocess | 4 | 10x faster searches |
| DEC-013: Modern FastAPI lifespan | 6 | Better resource management |
| DEC-014: Rename from Ixpantilia | 6 | Simpler, more memorable |
| DEC-015: Split implementation docs | 6 | Clearer phase tracking |
| DEC-016: Three-status model | 12 | active/inactive/hidden |
| DEC-017: Auto-restore inactive gleanings | 12 | Links that come back to life |

---

## Reading Guide

**If you're new to Temoa**, start with:
1. Entry 1 (The Central Problem) - understand the "why"
2. Entry 6 (Phase 1 Complete) - see what we built
3. Entry 10 (Mid-Course Assessment) - understand current status

**If you're debugging**, look for:
- Performance issues → Entry 4
- Architecture questions → Entry 2
- Path/config problems → Entry 3
- Gleanings bugs → Entries 9, 11

**If you're continuing development**, check:
- Latest entry in Phase 2.5 chapter
- IMPLEMENTATION.md for current phase status
- Open questions and decisions

---

**Created**: 2025-11-18
**Last Updated**: 2025-11-20
**Total Entries**: 12
