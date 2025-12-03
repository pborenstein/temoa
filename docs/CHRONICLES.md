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

### [Phase 3: Enhanced Features](chronicles/phase-3-enhanced-features.md) ✅ COMPLETE
**Entries 20-31** | Technical Debt, Search Quality, and UX Polish

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

---

## Quick Reference: Key Decisions

| Decision | Entry | Summary |
|----------|-------|---------|
| DEC-001: Project name (Temoa) | 6 | Named after Nahuatl "to seek" |
| DEC-009: Direct imports over subprocess | 4 | 10x faster searches |
| DEC-013: Modern FastAPI lifespan | 6 | Better resource management |
| DEC-014: Rename from Ixpantilia | 6 | Simpler, more memorable |
| DEC-015: Split implementation docs | 6 | Clearer phase tracking |
| DEC-016: Three-status model | 13 | active/inactive/hidden |
| DEC-017: Auto-restore inactive gleanings | 13 | Links that come back to life |
| DEC-021: Postel's Law for Gleanings | 10 | Be liberal in input, conservative in output |
| DEC-022: Title fetching for naked URLs | 10 | Fetch web titles for completeness |
| DEC-023: Case-sensitive pattern matching | 10 | Only search Daily/Journal (capital-case) |
| DEC-024: Themes by Period feature | 14 | Document for future, focus on present |
| DEC-025: Default exclude daily type | 15 | Reduce noise in search results |
| DEC-026: Hybrid search for daily notes | 15 | Daily notes work better with BM25+semantic |
| DEC-027: Compact collapsible results | 17 | Default collapsed, expand on demand |
| DEC-028: Centralized state management | 17 | Versioned localStorage, race condition prevention |
| DEC-029: Safe DOM manipulation | 17 | Replace innerHTML with createElement (XSS protection) |
| DEC-030: Barber pole progress indicator | 18 | Classic macOS-style indeterminate progress |
| DEC-031: Confirmation dialog for reindex | 18 | Prevent accidental expensive operations |
| DEC-032: Checkboxes below button | 18 | Action first, options second (natural hierarchy) |
| DEC-033: Modification time for change detection | 19 | Fast, already tracked (vs content hash) |
| DEC-034: Rebuild BM25 fully (not incremental) | 19 | BM25 fast (<5s), merging adds complexity |
| DEC-035: DELETE→UPDATE→APPEND merge order | 19 | Immutable order to avoid index corruption |
| DEC-036: Multi-vault storage strategy | 20 | Auto-derive as vault/.temoa/ (co-location) |
| DEC-037: Validation before operations | 20 | Fail early with clear error, require --force |
| DEC-038: Auto-migration of old indexes | 20 | Seamless upgrade, no user action required |
| DEC-042: Search is primary, vault is infrequent | 22 | Move vault selector to bottom (search is primary) |
| DEC-043: Common settings above the fold | 22 | Move hybrid checkbox outside Options (frequent use) |
| DEC-044: Inline search button for mobile | 22 | Button inside search box (visible with keyboard up) |
| DEC-045: Actions first on management page | 22 | Reorder sections (actions > stats) |
| DEC-046: Replace gear icon with text | 22 | "Manage" text aligned right (clearer navigation) |
| DEC-047: Lifespan over module-level init | 23 | Use FastAPI lifespan for initialization (testability, best practice) |
| DEC-048: Keep Synthesis sys.path usage | 23 | Isolate to helper method (bundled dependency, simpler than importlib) |
| DEC-049: App state pattern for dependencies | 23 | Store in app.state, extract in endpoints (simpler than Depends()) |
| DEC-050: Scripts as package | 23 | Move to src/temoa/scripts/ (proper structure, no sys.path hacks) |
| DEC-051: Modification time for incremental extraction | 24 | Use st_mtime for change detection (fast, already tracked) |
| DEC-052: Incremental by default for auto-reindex | 24 | Auto-reindex uses force=False (30x speedup) |
| DEC-053: Use uvicorn.config.LOGGING_CONFIG for timestamps | 25 | Modify uvicorn's config, don't replace it (proven pattern from apantli) |
| DEC-054: Enable re-ranking by default | 26 | Re-ranking on by default (significant quality gain for 200ms cost) |
| DEC-055: Re-rank top 100 candidates | 26 | Balance between recall and speed (100 pairs @ 2ms = 200ms) |
| DEC-056: Use ms-marco-MiniLM-L-6-v2 model | 26 | Fast (~2ms/pair), accurate (MS MARCO trained), proven in production |
| DEC-057: TF-IDF over LLM-based expansion | 27 | Fast (~50ms), no external APIs, deterministic, proven technique |
| DEC-058: Expand only short queries (<3 words) | 27 | Short queries benefit most, saves latency, simple rule |
| DEC-059: Show expanded query to user | 27 | Transparency builds trust, educational, allows refinement |
| DEC-060: Exponential decay (not linear) | 27 | Natural, intuitive half-life parameter, smooth gradient |
| DEC-061: Default half-life of 90 days | 27 | Matches common vault patterns, configurable per-user |
| DEC-062: Apply boost before re-ranking | 27 | Combines recency with relevance, clean separation |
| DEC-063: Comprehensive search documentation | 28 | Document all mechanisms, rationale, and performance (SEARCH-MECHANISMS.md) |
| DEC-064: Archive completed implementation plans | 28 | Clean docs/ after phase completion, preserve in archive/ |
| DEC-065: Navigation README for docs/ | 28 | Index all documentation (docs/README.md for discovery) |
| DEC-066: Cache-first for UI, network-first for API | 29 | Service worker uses different strategies per resource type |
| DEC-067: rsvg-convert over ImageMagick | 29 | Proper Unicode emoji rendering in PNG icons |
| DEC-068: Standalone display mode for PWA | 29 | Launches without browser chrome (native app feel) |
| DEC-069: Version 0.4.0 → 0.5.0 | 29 | Minor bump for PWA (significant new capability) |
| DEC-070: Checkbox organization by frequency | 30 | Hybrid at top, quality toggles in Options (2x2 grid) |
| DEC-071: Search history max 10 items | 31 | Balance utility and UI clutter (browser pattern) |
| DEC-072: Show history only when input empty | 31 | Don't interfere with typing/autocomplete |
| DEC-073: GitHub-style `/` shortcut | 31 | Familiar pattern, selects text for replacement |
| DEC-074: Query persists after search | 31 | User feedback - query disappearing was annoying |

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
**Last Updated**: 2025-12-03
**Total Entries**: 31
