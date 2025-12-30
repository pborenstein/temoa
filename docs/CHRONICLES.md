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
**Entries 7-10** | Making Gleanings Searchable

- Entry 7: Phase 2 Complete - Gleanings Integration
- Entry 8: CLI Implementation and Real-World Testing
- Entry 9: Gleanings Extraction Fixes
- Entry 10: Extraction Shakedown - Format Flexibility & Filesystem Edge Cases

### [Phase 2.5: Deployment & Mobile Validation](chronicles/phase-2.5-deployment.md)
**Entries 11-19** | Real-World Usage and Gleaning Management

- Entry 11: Mid-Course Assessment - Pausing Before Phase 3
- Entry 12: Deployment Shakedown - Real-World Bugs Surface
- Entry 13: Gleanings Status Management - Active, Inactive, Hidden
- Entry 14: Architecture Documentation - Explaining the Machine
- Entry 15: Type Filtering - From Noise to Signal
- Entry 16: UI Refinement - Polish Through Real Usage
- Entry 17: Compact Collapsible UI - Mobile Testing Drives Major Refactor
- Entry 18: Management Page - Centralizing Vault Operations
- Entry 19: Incremental Reindexing - 30x Speedup for Daily Use

### [Phase 3: Implementation](chronicles/phase-3-implementation.md) ✅ COMPLETE
**Entries 20-32** | Technical Debt, Search Quality, and UX Polish

- Entry 20: Multi-Vault Support - Preventing Data Loss
- Entry 21: Multi-Vault Webapp UI
- Entry 22: UI Cleanup - Mobile-First Space Optimization
- Entry 23: Technical Debt Refactoring - Clean Foundation
- Entry 24: Incremental Extraction Bugs - The Devil in the Details
- Entry 25: Logging Enhancement - Adding Timestamps
- Entry 26: Cross-Encoder Re-Ranking - Two-Stage Retrieval
- Entry 27: Query Expansion and Time-Aware Scoring - Search Quality Stack Complete
- Entry 28: Documentation and Organization - SEARCH-MECHANISMS.md
- Entry 29: PWA Support - One-Tap Access to Vault Search
- Entry 30: Mobile UI Refinement - Checkbox Reorganization
- Entry 31: Search History and Keyboard Shortcuts - Phase 3 Complete
- Entry 32: Documentation Style Conformance

### [Production Hardening](chronicles/production-hardening.md) 🔵 ONGOING
**Entries 33-44** | Real-World Usage Fixes

- Entry 33: Production Hardening - Query Expansion Default Change
- Entry 34: State Management Refactoring - Eliminating "Hodge Podge"
- Entry 35: Unicode Surrogate Sanitization
- Entry 36: launchd Service Management - Following the Apantli Pattern
- Entry 37: Gleaning Normalization - GitHub URL Cleanup
- Entry 38: Frontmatter-Aware Search - Tag Boosting and Description Integration
- Entry 39: Vault Format Agnostic - Plain Text File Support
- Entry 40: Token Limits and Chunking Requirement Discovery
- Entry 41: Documentation Cleanup and Critical Bug Fixes
- Entry 42: Documentation Strategy and CLAUDE.md Thinning
- Entry 43: launchd Service Configuration Updates
- Entry 44: GitHub Gleaning Enrichment System

---

## Architectural Decisions

**All architectural decisions have been moved to [DECISIONS.md](DECISIONS.md)**

That document contains:
- Complete decision registry (DEC-001 through DEC-085)
- Decision governance process for LLMs and contributors
- Historical notes about numbering gaps
- Deprecated/superseded decisions

**Quick access to key decisions**:
- [DEC-009: Direct imports over subprocess](DECISIONS.md#decision-registry) - 10x faster searches
- [DEC-027: Compact collapsible results](DECISIONS.md#decision-registry) - Mobile-first UX
- [DEC-036: Multi-vault storage strategy](DECISIONS.md#decision-registry) - vault/.temoa/ co-location
- [DEC-054: Enable re-ranking by default](DECISIONS.md#decision-registry) - Search quality improvement

See [DECISIONS.md](DECISIONS.md) for the complete list with governance process.

---

## Reading Guide

**If you're new to Temoa**, start with:
1. Entry 1 (The Central Problem) - understand the "why"
2. Entry 6 (Phase 1 Complete) - see what we built
3. Entry 11 (Mid-Course Assessment) - understand current status

**If you're debugging**, look for:
- Performance issues → Entry 4
- Architecture questions → Entry 2
- Path/config problems → Entry 3
- Gleanings bugs → Entries 9, 10, 12

**If you're continuing development**, check:
- Latest entry in Phase 2.5 chapter
- IMPLEMENTATION.md for current phase status
- Open questions and decisions

---

**Created**: 2025-11-18
**Last Updated**: 2025-12-29
**Total Entries**: 44
**Decisions**: See [DECISIONS.md](DECISIONS.md) for complete decision registry (DEC-001 through DEC-091)
