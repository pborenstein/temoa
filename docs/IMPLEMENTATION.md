# IMPLEMENTATION.md - Temoa Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document tracks progress across all implementation phases. Original planning documents archived in `docs/archive/original-planning/`. Detailed implementation notes in `docs/chronicles/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 3 ✅ COMPLETE → Production Hardening 🔵 ONGOING
**Last Updated**: 2025-12-19
**Current Version**: 0.6.0
**Current Branch**: `main`
**Estimated Timeline**: 4-6 weeks for Phases 0-2, ongoing for Phases 3-4

---

## Core Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, embeddings explanation, data flow |
| [CHRONICLES.md](CHRONICLES.md) | Design discussions and decision history |
| [CLAUDE.md](../CLAUDE.md) | Development guide for AI sessions |
| This file | Implementation progress tracking |

---

## Phase Overview

| Phase | Status | Duration | Dependencies |
|-------|--------|----------|--------------|
| Phase 0: Discovery & Validation | ✅ **COMPLETE** | 1 day | None |
| Phase 1: Minimal Viable Search | ✅ **COMPLETE** | 1 day | Phase 0 ✅ |
| Phase 2: Gleanings Integration | ✅ **COMPLETE** | 1 day | Phase 1 ✅ |
| Phase 2.5: Mobile Validation + UI | ✅ **COMPLETE** | 1 week | Phase 2 ✅ |
| Phase 3: Enhanced Features | ✅ **COMPLETE** | 2 weeks | Phase 2.5 ✅ |
| [Phase 4: Vault-First LLM](archive/original-planning/phase-4-llm.md) | ⚪ Future | 7-10 days | Phase 3 ✅ |

---

## Phase 0: Discovery & Validation ✅

**Status**: COMPLETE (2025-11-18)
**Goal**: Answer all open questions and validate architectural assumptions

### Key Findings

- ✅ Bottleneck identified: Model loading (2.8s per invocation)
- ✅ Actual search is fast: ~400ms once model loaded
- ✅ Scales well: 2,289 files = same speed as 13 files
- ✅ Daily notes ARE indexed (gleanings searchable)
- ✅ Solution validated: HTTP server wrapper with direct imports

### Key Decisions

1. **Architecture**: FastAPI server importing Synthesis code directly (not subprocess)
2. **Expected performance**: ~400-500ms per search (meets < 1s target)
3. **No caching needed initially**: Search is fast enough without it
4. **Mobile use case validated**: 400ms excellent for habit formation

### Original Plan

See [archive/original-planning/phase-0-discovery.md](archive/original-planning/phase-0-discovery.md) (historical)

**Detailed findings**: See `docs/phase0-results.md` and `docs/CHRONICLES.md` Entry 4

---

## Phase 1: Minimal Viable Search ✅

**Status**: COMPLETE (2025-11-18) + Management Page (2025-11-24)
**Goal**: Build FastAPI server that wraps Synthesis with direct imports for fast search
**Duration**: 1 day (faster than estimated!)

### Architecture (based on Phase 0 findings)

- FastAPI server imports Synthesis code directly (NOT subprocess)
- Model loaded ONCE at startup (~10-15s)
- Each search: direct function call (~400ms)
- Simple HTML UI for mobile testing
- Target: < 500ms response time

### Tasks Completed

- [x] 1.1: Project Setup
- [x] 1.2: Configuration Management
- [x] 1.3: Synthesis Direct Import Wrapper
- [x] 1.4: FastAPI Server
- [x] 1.5: Mobile Web UI
- [x] 1.6: Basic Testing
- [x] 1.7: Documentation

### Deliverables

- [x] Working FastAPI server (`src/temoa/server.py` - 309 lines)
- [x] Configuration system (`src/temoa/config.py` - 141 lines)
- [x] Synthesis wrapper (`src/temoa/synthesis.py` - 296 lines)
- [x] Mobile web UI (`src/temoa/ui/search.html` - 411 lines)
- [x] Basic test suite (`tests/` - 24 passing, 1 skipped)
- [x] Project documentation (README, API docs)
- [x] `pyproject.toml` with dependencies

### Success Criteria

- [x] Server runs and is accessible from mobile
- [x] Search works end-to-end (query → Synthesis → results)
- [x] Results open in Obsidian mobile app
- [x] Response time < 2 seconds from mobile (actually ~400ms!)
- [x] Basic tests pass (24 passed, 1 skipped)
- [x] Code is clean and documented

### Key Achievements

**Performance** (exceeds all targets):
- Search response time: ~400ms (target: < 2s) ✅ 5x better
- Model loading: Once at startup (~15s one-time) ✅
- Scales to 2,289 files without degradation ✅

**Implementation** (1,180 lines of production code):
- 5 core modules (config, server, synthesis, __main__, ui)
- 24 passing tests with comprehensive coverage
- OpenAPI documentation at `/docs`
- Mobile-first UI with vanilla HTML/JS

**Key Decisions**:
- DEC-009: Direct imports (not subprocess) → 10x faster searches
- DEC-013: Modern FastAPI lifespan pattern
- DEC-014: Project renamed from Ixpantilia to Temoa
- DEC-015: Split implementation plan into phase files

See [docs/CHRONICLES.md Entry 6](CHRONICLES.md#entry-6-phase-1-complete---from-zero-to-production-ready-server-2025-11-18) for detailed retrospective.

### Original Plan

See [archive/original-planning/phase-1-mvp.md](archive/original-planning/phase-1-mvp.md) (historical)

---

## Phase 2: Gleanings Integration ✅

**Status**: COMPLETE (2025-11-19)
**Goal**: Make gleanings searchable via semantic search
**Duration**: 1 day (faster than estimated!)

### Tasks Completed

- [x] 2.1: Gleanings Extraction Script
- [x] 2.2: Historical Gleanings Migration
- [x] 2.3: Synthesis Re-indexing
- [x] 2.4: Automated Extraction

### Deliverables

- [x] `scripts/extract_gleanings.py` - Production gleaning extraction
- [x] `scripts/migrate_old_gleanings.py` - Historical migration
- [x] `scripts/extract_and_reindex.sh` - Combined workflow
- [x] Automation setup (cron/systemd configurations)
- [x] Documentation in `docs/GLEANINGS.md`
- [x] `/reindex` API endpoint in server

### Success Criteria

- [x] All 505+ gleanings extracted and migrated (516 total)
- [x] Extraction scripts working with incremental mode
- [x] Re-indexing integrated via API endpoint
- [x] Automation configured (cron and systemd options)
- [x] Complete documentation written

### Key Achievements

**Extraction System** (Task 2.1):
- Parses daily notes with `## Gleanings` sections
- Extracts format: `- [Title](URL) - Description`
- Creates individual markdown files in `L/Gleanings/`
- MD5-based gleaning IDs for deduplication
- State tracking in `.temoa/extraction_state.json`
- Incremental mode (process only new files)
- Tested: 6 gleanings extracted from test-vault

**Historical Migration** (Task 2.2):
- Migrated 505 gleanings from old-gleanings JSON
- Preserved all metadata (category, tags, timestamp)
- Marked with `migrated_from: old-gleanings`
- Tested: All 505 gleanings successfully migrated

**Re-indexing Support** (Task 2.3):
- Added `SynthesisClient.reindex()` method
- Added `POST /reindex` endpoint to FastAPI server
- Triggers Synthesis vault re-indexing
- Returns status with file count

**Automation** (Task 2.4):
- Combined extraction + reindex workflow script
- Cron job example (daily at 11 PM)
- Systemd service and timer units
- Logging and dry-run support

**Documentation**:
- Complete workflow guide in `docs/GLEANINGS.md`
- Format specification
- Extraction and migration instructions
- Automation setup (cron and systemd)
- Troubleshooting and best practices

### Testing Results

- ✅ Extracted 6 gleanings from daily notes
- ✅ Migrated 505 historical gleanings
- ✅ Total: 516 gleanings in test-vault
- ✅ Incremental extraction (no duplicates)
- ✅ State tracking verified

**Key Decisions**:
- Gleanings stored as individual markdown files (not in daily notes)
- MD5-based IDs from URLs for deduplication
- State file tracks processed files for incremental extraction
- Combined workflow script for ease of automation

See [docs/CHRONICLES.md Entry 7](#) for detailed retrospective.

### Production Validation (2025-11-19)

**First real extraction from production vault** (742 daily notes):

```
Total gleanings found: 1,368
New gleanings created: 661
Duplicates skipped: 707
Files processed: 742
```

**Bugs discovered and fixed**:
- CLI argument mismatch (positional vs named args)
- Extraction pattern didn't match production format (`- [Title](URL)  [HH:MM]` + description on next line)
- `--full` flag didn't clear state (still skipped "duplicates")
- Tags display error (integers mixed with strings)
- Reindex didn't discover new files without `--force` flag
- Search results lacked context (no snippets)

**All issues resolved**. Gleanings now fully functional and searchable.

See [docs/CHRONICLES.md Entry 9](#) for detailed bug analysis and fixes.

### Original Plan

See [archive/original-planning/phase-2-gleanings.md](archive/original-planning/phase-2-gleanings.md) (historical)

---

## CLI Implementation ✅

**Status**: COMPLETE (2025-11-19)
**Goal**: Easy command-line access for daily use
**Duration**: 1 day

### What Was Built

**Click-based CLI** (similar to obsidian-tag-tools pattern):

```bash
temoa config              # Show current configuration
temoa index               # Build embedding index from scratch
temoa reindex             # Incremental updates (daily use)
temoa search "query"      # Quick searches from terminal
temoa archaeology "topic" # Temporal analysis
temoa stats               # Vault statistics
temoa extract             # Extract gleanings from daily notes
temoa migrate             # Migrate old gleanings
temoa server              # Start FastAPI server
```

**Installation**: `uv tool install --editable .`

### Deliverables

- [x] `src/temoa/cli.py` (463 lines) - Complete CLI with all subcommands
- [x] `[project.scripts]` entry point in pyproject.toml
- [x] `[tool.uv] package=true` for uv tool install support
- [x] All commands support `--help` and `--json` flags
- [x] Proper error handling and user-friendly output
- [x] Color-coded output for better readability

### Success Criteria

- [x] Can run `temoa` command from any directory
- [x] All operations work (config, index, search, stats, server)
- [x] Installation via `uv tool install --editable .`
- [x] Help text is clear and actionable
- [x] Performance validated on production vault (2,281 files)

### Bugs Fixed

**Stats Display Issue**:
- **Problem**: `temoa stats` showed "Embeddings: 0" even though search worked perfectly
- **Root cause**: CLI looked for `total_embeddings` key, but Synthesis returns `num_embeddings`
- **Fix**: Updated key name + improved model name extraction from nested dict
- **Discovery**: Created `debug_stats.py` script to inspect actual JSON structure (script removed 2025-11-23, issue resolved)

### Real-World Validation

**Production test** (user's actual vault):
- ✅ Index: 2,281 files processed in ~17 seconds
- ✅ Search: `temoa search "obsidian"` returned accurate results
- ✅ Stats: Displays correctly (2,281 embeddings, 2,006 tags, 31 directories)
- ✅ Performance: ~400ms search time (meets <2s target)

### Key Decisions

- **DEC-019**: Use Click framework for familiar UX pattern
- **DEC-020**: Split `index` vs `reindex` for clear intent

See [docs/CHRONICLES.md Entry 8](CHRONICLES.md#entry-8-cli-implementation-and-first-real-world-testing-2025-11-19) for detailed retrospective.

---

## Phase 2.5: Mobile Validation + UI Optimization ✅

**Status**: COMPLETE (2025-11-24)
**Goal**: Validate core behavioral hypothesis and optimize UI for mobile use
**Duration**: 1 week (2025-11-19 → 2025-11-24)

### Why This Phase Existed

Testing the behavioral hypothesis: *"If I can search my vault from my phone in <2 seconds, I'll check it before Googling."*

Phase 2.5 grew organically from mobile validation into extensive UI polish and feature development:
- Deployment and real-world testing
- Gleaning status management (active/inactive/hidden)
- Type filtering system
- UI refinement based on actual mobile usage
- Incremental reindexing (30x speedup)

### Major Achievements

**Deployment & Real-World Testing** (Entries 11-12):
- Server deployed via Tailscale, accessible from mobile
- First production bugs discovered and fixed
- Behavioral hypothesis validated: vault-first search habit formed

**Gleaning Status Management** (Entry 13):
- Three-status model: active/inactive/hidden
- Auto-restoration for inactive links that come back
- Frontmatter + JSON status tracking

**Type Filtering** (Entry 15):
- Document type detection (daily/note/gleaning)
- exclude_types parameter (default: exclude daily notes)
- Hybrid search recommendation for daily notes

**UI Refinement** (Entries 16-17):
- Mobile testing drives compact collapsible UI
- Centralized state management (versioned localStorage)
- Safe DOM manipulation (XSS protection)
- Default collapsed results to save mobile space

**Management Page** (Entry 18):
- Centralized vault operations (reindex, extract)
- Barber pole progress indicator
- Confirmation dialogs for expensive operations

**Incremental Reindexing** (Entry 19):
- 30x speedup: 5s vs 159s (modification time-based change detection)
- DELETE→UPDATE→APPEND merge order to avoid corruption
- BM25 rebuilt fully, embeddings merged incrementally

### Detailed Implementation

See [chronicles/phase-2.5-deployment.md](chronicles/phase-2.5-deployment.md) for detailed session notes (Entries 11-19).

**Key Decisions**:
- DEC-016: Three-status model (active/inactive/hidden)
- DEC-017: Auto-restore inactive gleanings
- DEC-025: Default exclude daily type
- DEC-026: Hybrid search for daily notes
- DEC-027: Compact collapsible results
- DEC-033: Modification time for change detection

---
## Temoa Usage (Week of YYYY-MM-DD)

### Day 1 (YYYY-MM-DD)
- Searches performed: X
- Found what I needed: Y/N
- Opened in Obsidian: Y/N
- Response time feel: Fast/OK/Slow
- Friction points:
  - [List anything that prevented usage or was annoying]
- Feature wishes:
  - [List features you wished existed during usage]

### Day 2 (YYYY-MM-DD)
...
```

### What to Do After 1-2 Weeks

**Review your usage log:**
1. Count total searches
2. Identify pattern: Did usage increase or decrease?
3. List friction points that occurred multiple times
4. Note which features you actually wished for

**Decide Phase 3 scope:**

**If hypothesis validated** (you used it, habit formed):
- ✅ Proceed to Phase 3
- Focus on features that reduce friction you experienced
- Example: If searches often found nothing → improve search quality
- Example: If opening results was annoying → improve UI
- Example: If wanted to see temporal patterns → build archaeology UI

**If hypothesis failed** (didn't use it, no habit):
- ❌ Don't build Phase 3 features yet
- Investigate root cause:
  - Too slow? → Optimize, add caching
  - Not useful? → Improve search algorithm
  - Forgot it existed? → Add home screen PWA
  - Results not relevant? → Better embeddings, different model
- **Fix the blocker**, then retry Phase 2.5

**If partially worked** (used sometimes, inconsistent):
- 🤔 Identify barriers to consistent usage
- Example: Only used at desk → need PWA for easier mobile access
- Example: Only used for specific topics → need better archaeology
- **Build what removes the barrier**, not what sounds cool

### Key Insight

**From CHRONICLES Entry 1:**
> This is not a technology problem. It's a **retrieval behavior problem**.

Phase 2.5 answers the critical question: **Does making vault search fast and accessible actually change behavior?**

If yes → Build features to make it indispensable (Phase 3)
If no → Fix root cause, then retest
If partially → Remove specific barriers, then retest

---

## Phase 3: Enhanced Features ✅

**Status**: COMPLETE (2025-12-01)
**Goal**: Fix technical debt and improve search quality based on real usage
**Duration**: 2 weeks

### What Was Built

Phase 3 delivered comprehensive improvements across five major areas:

**Part 0: Multi-Vault Support** (Entry 20-21):
- LRU client cache (max 3 vaults, ~1.5GB RAM)
- Independent indexes per vault (vault/.temoa/)
- Validation to prevent data loss
- Webapp vault selector UI with state persistence

**Part 1: Technical Debt** (Entry 23):
- FastAPI lifespan pattern (proper initialization)
- Removed sys.path hacks, moved scripts to package
- App state pattern for dependencies
- Incremental extraction fix (mtime-based tracking)
- Auto-reindex speedup (30x: force=False)

**Part 2: Search Quality** (Entry 26-27):
- Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2, 20-30% precision improvement)
- Query expansion (TF-IDF for short queries, <3 words)
- Time-aware scoring (exponential decay, 90-day half-life)
- All enabled by default, ~600-1000ms total latency

**Part 3a: UI/UX Polish** (Entry 22, 30):
- Mobile-first space optimization
- Vault selector at bottom (search is primary)
- Hybrid checkbox above the fold
- Inline search button (visible with keyboard up)
- Checkbox organization by frequency (2x2 grid)

**Part 3b: PWA Support** (Entry 29):
- Installable on mobile (one-tap access)
- Service worker with cache-first strategy
- Standalone display mode (no browser chrome)
- rsvg-convert for proper emoji rendering in icons

**Part 3c: Search History & Keyboard Shortcuts** (Entry 31):
- Last 10 searches in dropdown
- `/` to focus, `Esc` to clear, `t` to toggle expanded
- Query persists after search (user feedback)

### Performance Characteristics

**Search latency** (3,000 file vault):
- Semantic: ~400ms
- Hybrid: ~450ms
- With re-ranking: ~600ms
- Short query + expansion + re-ranking: ~800-1000ms

**Memory**: Single vault ~800MB, multi-vault (3 cached) ~1.5GB

**Reindexing**: Full ~159s, incremental (no changes) ~5s

### Detailed Implementation

See [chronicles/phase-3-implementation.md](chronicles/phase-3-implementation.md) for detailed session notes (Entries 20-32).

**Key Decisions**:
- DEC-036: Multi-vault storage strategy (vault/.temoa/)
- DEC-047: Lifespan over module-level init
- DEC-054: Enable re-ranking by default
- DEC-057: TF-IDF over LLM-based expansion
- DEC-060: Exponential decay (not linear)
- DEC-066: Cache-first for UI, network-first for API
- DEC-071: Search history max 10 items

---
## Production Hardening (Post-Phase 3) 🔵

**Status**: ONGOING
**Branch**: `pseudo-vaults` (was `main`)
**Version**: 0.6.0

### Completed Work

#### Vault Format Agnostic Support (2025-12-17)

**Goal**: Support plain text files without frontmatter, validate architectural constraint

**Changes Made**:
- Updated `synthesis/src/embeddings/vault_reader.py` to include `**/*.txt` pattern
- Added nahuatl-frontmatter as synthesis dependency
- Implemented YAML frontmatter sanitization in nahuatl-frontmatter:
  - Auto-quote colon-containing values
  - File descriptor-level stderr suppression for PyYAML C library
  - Parse errors changed to DEBUG level
- Updated Python requirement to >=3.10

**Testing**: 2 pseudo-vaults with 1002 files each
- `markdown-files/`: .md with frontmatter ✅
- `text-files/`: .txt without frontmatter ✅
- Both index cleanly with 0 error messages

**Impact**: Validates "Vault Format Agnostic" architectural constraint - temoa now works with any text file collection regardless of format or frontmatter validity.

**Commits**:
- nahuatl-frontmatter `0e2ca01` - YAML sanitization and error suppression
- nahuatl-frontmatter `90a60c3` - Remove __pycache__ from git
- temoa `38dd49b` - Vault format agnostic support

#### Documentation Cleanup and Critical Bug Fixes (2025-12-19)

**Goal**: Clean up completed planning documents and address 3 critical bugs from code review

**Critical Bugs Fixed** (commit 26e20c6):
1. **Pipeline order bug**: Time boost now runs AFTER cross-encoder re-ranking (was before, which mutated scores incorrectly)
2. **Path traversal vulnerability**: Added path validation in time_scoring.py to prevent directory traversal attacks
3. **Query expansion error handling**: Added try/except, logging for empty results, graceful fallback to original query

**Documentation Updates**:
- Archived `GLEANING-NORMALIZATION-PLAN.md` (implementation complete 2025-12-14)
- Archived `SEARCH-QUALITY-REVIEW.md` (critical fixes complete)
- Updated `SEARCH-MECHANISMS.md` with frontmatter-aware search section and query expansion default change

**Testing**: All fixes verified with integration tests

**Commits**:
- `26e20c6` - "fix: address critical bugs from search quality review"
- `5f1d86e` - "docs: mark critical bugs as fixed in search quality review"
- `ea28473` - "docs: archive search quality review after completing critical fixes"
- `6cbb224` - "docs: archive completed gleaning normalization plan"
- `fcaaa97` - "docs: update SEARCH-MECHANISMS.md with frontmatter-aware search and query expansion changes"

**Files Modified**:
- Code: `src/temoa/server.py`, `src/temoa/time_scoring.py`
- Docs: `SEARCH-MECHANISMS.md`, 2 files archived

#### Query Expansion Default Change (2025-12-06)

**Issue Identified**: Real-world usage showed query expansion (enabled by default) was unhelpful for person names. Short queries (<3 words) are often names, not topics that benefit from TF-IDF expansion.

**Changes Made**:
- Changed `expand_query` default from `True` to `False` in:
  - CLI (`--expand/--no-expand` flag)
  - Server API (`/search` endpoint)
  - Web UI (expansion checkbox)
- Updated API documentation in README.md
- Added TODO in `src/temoa/query_expansion.py` for future smart suggestions
- Added Phase 4+ task "Smart Query Suggestions" to Phase 4 plan

**Rationale**:
- Person names ("Philip Borenstein") are common short queries → expansion adds noise
- Hybrid search works better for exact name matching (BM25 component)
- Keep expansion as opt-in feature for topical queries

**Future Enhancement**: Smart query-aware suggestions (see Phase 4.3 below)

**Commits**:
- 79aa611 - "fix: disable query expansion by default based on production usage"
- b97310c - "fix: remove checked attribute from expand-query checkbox (actual fix)"

**Note**: Two-part fix was needed. Part 1 changed defaults in code, but checkbox still appeared checked due to HTML `checked` attribute (not persisted in localStorage).

#### Unicode Surrogate Sanitization (2025-12-08)

**Issue Identified**: Production search queries hitting malformed Unicode in vault content caused `UnicodeEncodeError: surrogates not allowed` when serializing JSON responses.

**Error Example**:
```
UnicodeEncodeError: 'utf-8' codec can't encode characters in position 24583-24584: surrogates not allowed
```

**Root Cause**: Some vault files contain invalid Unicode surrogate pairs that can't be encoded to UTF-8 for JSON responses.

**Solution Implemented**:
- Added `sanitize_unicode()` helper function that recursively walks response data
- Replaces invalid surrogates with Unicode replacement character (�)
- Applied to all endpoints returning vault content:
  - `/search` endpoint
  - `/archaeology` endpoint
  - `/stats` endpoint

**Files Modified**:
- `src/temoa/server.py` - Added sanitization function and applied to 3 endpoints

**Impact**: Graceful handling of malformed Unicode in vault content, prevents 500 errors during search.

**Commit**: 03d3468 - "fix: sanitize Unicode surrogates in JSON responses"

#### launchd Service Management (2025-12-13)

**Goal**: Add production-ready macOS service management following the apantli pattern

**Implementation**:
- Created `launchd/` directory with service management files:
  - `temoa.plist.template` - Service configuration (port 4001, auto-start, auto-restart)
  - `install.sh` - Automated installation script
  - `README.md` - Comprehensive documentation
- Created helper scripts in project root (matching apantli pattern):
  - `dev.sh` - Development mode (stops service, runs with --reload using uv)
  - `view-logs.sh` - Log viewer utility
- Updated `docs/DEPLOYMENT.md` with macOS deployment section

**Key Features**:
- Auto-start on login (RunAtLoad: true)
- Auto-restart on crash (KeepAlive: true)
- Port 4001 (pairs with apantli on 4000)
- Accessible on LAN/Tailscale (host: 0.0.0.0)
- Centralized logging (`~/Library/Logs/temoa.log`)
- Service naming: `dev.{username}.temoa`

**Files Created**:
- `launchd/temoa.plist.template`
- `launchd/install.sh`
- `launchd/README.md`
- `dev.sh` (root)
- `view-logs.sh` (root)

**Installation**: `./launchd/install.sh`

**Pattern Matching**: Closely follows apantli's proven launchd service pattern for consistency across related projects.

**Commits**:
- 1e663a7 - "feat: add launchd service management for macOS"
- 9e9bfe6 - "fix: add port conflict handling to dev.sh"
- 379ae34 - "fix: move dev.sh and view-logs.sh to root, match apantli pattern"

**Note**: Initial implementation had scripts in `launchd/` subdirectory and complex port checking logic. Fixed to match apantli's simpler pattern with scripts in project root and using uv for command execution.

#### Gleaning Normalization (2025-12-14)

**Goal**: Clean up GitHub gleaning titles and descriptions, remove emojis, create extensible normalizer system

**Problem**: GitHub gleanings had verbose titles like `"user/repo: Description"` and redundant descriptions with emojis.

**Implementation**:
- Created URL normalizer system with registry pattern (`src/temoa/normalizers.py`)
- `GitHubNormalizer` - Extracts clean `user/repo` titles, removes redundant suffixes, strips emojis
- `DefaultNormalizer` - Pass-through for non-GitHub URLs (backward compatible)
- Integrated with extraction script (new gleanings auto-normalized)
- Created backfill script for existing gleanings (`scripts/normalize_existing_gleanings.py`)
- Comprehensive unit tests (21 tests, all passing)

**Results**:
- 214 GitHub gleanings normalized out of 852 total
- Titles: `"user/repo: Description"` → `"user/repo"`
- Descriptions: Cleaned of redundant repo names, "Contribute to..." suffixes, and emojis
- Non-GitHub URLs unchanged (backward compatible)

**Files Created**:
- `src/temoa/normalizers.py` (174 lines) - Normalizer system
- `tests/test_normalizers.py` (181 lines) - Comprehensive tests
- `scripts/normalize_existing_gleanings.py` (134 lines) - Backfill script
- `docs/GLEANING-NORMALIZATION-PLAN.md` (568 lines) - Implementation plan

**Files Modified**:
- `src/temoa/scripts/extract_gleanings.py` - Integrated normalizer
- `docs/GLEANINGS.md` - Documented normalization behavior

**Extensibility**: Easy to add normalizers for YouTube, Reddit, etc. in future.

**Commits**:
- a8a152a - "feat: add URL normalization system for gleanings"

#### GitHub Gleaning Enrichment (2025-12-29)

**Goal**: Transform GitHub gleanings from basic HTML scraping to rich, API-powered entries with comprehensive repository metadata

**Problem**: GitHub gleanings lacked useful context - just scraped HTML titles and minimal descriptions. No visibility into repo language, popularity, topics, or archived status.

**Implementation**:
- Created `GitHubClient` class - API wrapper with rate limiting, error handling, README parsing
- Extended `maintain_gleanings.py` with `enrich_github_gleaning()` method
- Updated `GitHubNormalizer` to preserve `"user/repo: Description"` format (instead of stripping it)
- Added CLI flags: `--enrich-github` and `--github-token`
- Detects already-enriched gleanings (skips if `github_stars` field exists)

**Metadata Enriched** (7 fields):
- `title`: `"user/repo: Official description"` format
- `description`: Official repository description
- `github_language`: Primary programming language
- `github_stars`: Star count (integer)
- `github_topics`: Repository topics (YAML list)
- `github_archived`: Archived status (boolean)
- `github_last_push`: Last push date (ISO 8601)
- `github_readme_excerpt`: First paragraph from README (max 500 chars)

**Testing**:
- Tested on 3 sample gleanings (dry-run + real)
- All metadata fields populated correctly
- Topics formatted as JSON array (YAML compatible)
- Already-enriched detection working (skips re-enrichment)
- Rate limiting verified (2.5s between requests)

**Files Created**:
- `src/temoa/github_client.py` (350 lines) - GitHub API client

**Files Modified**:
- `src/temoa/scripts/maintain_gleanings.py` (+150 lines) - Added enrichment method and CLI flags
- `src/temoa/normalizers.py` (20 lines modified) - Preserve `"user/repo: Description"` format

**Usage**:
```bash
export GITHUB_TOKEN="ghp_..."
uv run python src/temoa/scripts/maintain_gleanings.py \
  --vault-path ~/Obsidian/amoxtli \
  --enrich-github \
  --no-check-links \
  --no-add-descriptions
```

**Status**: ✅ Complete - Implementation, backfill, and documentation finished

**Backfill Results** (2025-12-30):
- Total gleanings: 902
- GitHub enriched: 259 repositories
- Already enriched: 0 (first run)
- Errors: 18 (gist URLs not supported)
- Skipped (hidden): 34
- Duration: ~13 minutes
- Documentation updated: GLEANINGS.md

---

#### Frontmatter-Aware Search (2025-12-14)

**Goal**: Leverage curated frontmatter metadata (tags, description) to improve search relevance

**Problem**: Tags and descriptions are user-curated metadata but weren't influencing search results. Documents with perfect tag matches were often buried in results.

**Investigation**: Two-phase approach
- Phase 1: Semantic embedding concatenation → <5% improvement (ineffective)
- Phase 2: BM25 tag boosting → 100% success for tag queries

**Implementation**:

**BM25 Tag Boosting** (`src/temoa/bm25_index.py`):
- Include tags in indexed text (repeated 2x for term frequency)
- Apply 5x score multiplier when query tokens match document tags
- Track matched tags in search results

**Hybrid Search RRF Boost** (`src/temoa/synthesis.py`):
- Aggressive boost (1.5-2.0x max_rrf) for tag-matched results
- Fixes issue where RRF averaging buried exact tag matches
- Mark tag-boosted results to prevent downstream re-scoring

**Critical Bugs Fixed**:
- Time-aware scoring now detects hybrid mode and boosts `rrf_score` instead of `similarity_score`
- Cross-encoder reranking skipped when tag boosts present (exact matches don't need re-evaluation)
- Type filtering now infers `type: none` for files without `type:` field, `type: gleaning` for `gleaning_id`

**Description Field Integration**:
- Added to BM25 index (repeated 2x, similar weight to tags)
- Prepended to semantic embeddings for positional weight
- Ready to leverage when descriptions are present in frontmatter

**Results**:
- Tag queries have 100% success rate for documents with matching tags
- "zettelkasten books" → Book tagged [zettelkasten, book] ranks #1 (was buried before)
- No performance degradation (~400-1000ms search times maintained)

**Files Modified**:
- `src/temoa/bm25_index.py` - Tag and description in index, tag boosting
- `src/temoa/synthesis.py` - Aggressive RRF boost for tag matches
- `src/temoa/time_scoring.py` - Hybrid mode detection, RRF score boosting
- `src/temoa/cli.py` - Skip reranking when tag boosts present
- `src/temoa/server.py` - Type inference system
- `synthesis/src/embeddings/vault_reader.py` - Description prepending

**Test Data Created**:
- `test-vault/test_queries.json` - 8 validation queries
- `test-vault/run_baseline.sh`, `run_hybrid_test.sh` - Test scripts
- `test-vault/BM25_TAG_BOOSTING_RESULTS.md` - Phase 2 results
- `test-vault/FRONTMATTER_EXPERIMENT_RESULTS.md` - Phase 1 baseline

**Commits**:
- d39462f - "Add tag-aware search boosting for hybrid search"
- f0a88ee - "Include description field in search indexing"

**PR**: #40

### Next Production Hardening Items

Based on continued real-world usage, consider:
- [x] Error handling edge cases (Unicode surrogates fixed)
- [x] macOS deployment automation (launchd service management)
- [x] Vault format agnostic support (plain text files)
- [x] YAML frontmatter error suppression
- [ ] Performance monitoring/metrics
- [ ] Additional UX improvements from user feedback
- [ ] Mobile validation of PWA installation
- [ ] More comprehensive testing

### Next Session Start Here

**Current Branch**: `main`
**Current Focus**: Production hardening complete - ready for Phase 4 or additional polish

**Recent Work** (2025-12-19):
- Fixed 3 critical bugs from SEARCH-QUALITY-REVIEW.md (pipeline order, path traversal, error handling)
- Cleaned up documentation (archived completed plans)
- Updated SEARCH-MECHANISMS.md with frontmatter-aware search documentation
- Thinned CLAUDE.md from 1,138 → 623 lines (45% reduction, removed duplicates)
- Created GitHub issue #43 for chunking implementation (DEC-085)
- Established pattern: Deferred work → GitHub issues

**To Continue**:
1. Consider beginning Phase 4 (Vault-First LLM) if core features are stable
   - Chunking support tracked in #43 (deferred until Phase 4)
2. Additional UX improvements from user feedback
3. Mobile validation of PWA installation
4. Performance monitoring/metrics implementation

---

## Phase 4: Vault-First LLM ⚪

**Status**: Future
**Goal**: LLMs check vault before internet
**Duration**: 7-10 days

### Tasks Overview

- [ ] 4.1: Chat Endpoint with Context
- [ ] 4.2: Citation System
- [ ] 4.3: Smart Query Suggestions (Phase 4+)

### Deliverables

- [ ] `/chat` endpoint
- [ ] Apantli integration
- [ ] Citation system
- [ ] Vault-first chat UI
- [ ] Smart query-aware search mode suggestions

### Success Criteria

- [ ] Vault-first becomes default research mode
- [ ] LLM responses build on existing knowledge
- [ ] Citations work reliably

### Future Enhancement: Smart Query Suggestions

**Context**: Real-world usage (Phase 3 production hardening) revealed that query expansion is often unhelpful for person names. Short queries < 3 words are frequently names, not topics needing expansion.

**Examples**:
- `"Philip Borenstein"` → Query expansion OFF, Hybrid search ON (BM25 helps with exact name matching)
- `"AI"` → Query expansion ON (becomes "AI machine learning neural networks")
- `"React hooks"` → Semantic search (concept-based understanding)

**Proposed Feature** (Phase 4+):
- Analyze query content before search
- Suggest optimal search modes based on query patterns
- Detection heuristics:
  - **Person name**: Capitalized words, 2-3 tokens, not in technical vocabulary
  - **Technical term**: Known framework/library names, acronyms
  - **Topic**: General vocabulary, benefit from expansion
- UI: Show suggestion chips (e.g., "This looks like a name. Try hybrid search?")
- Smart defaults: Auto-apply suggested modes with user override

**Implementation Notes**:
- Use NLP patterns or simple heuristics (capitalization, length, vocabulary lists)
- Store user preferences (learn from overrides)
- Keep it lightweight (<50ms analysis time)

### Detailed Plan

See [phases/phase-4-llm.md](phases/phase-4-llm.md)

---

## Dependencies & Prerequisites

### System Requirements

- Python 3.11+
- uv package manager
- Synthesis installed and working
- Obsidian vault accessible
- Tailscale network (for mobile access)

### External Dependencies

- **Synthesis**: Must be installed and operational
- **Obsidian Mobile**: For testing obsidian:// URIs
- **Apantli** (Phase 4): LLM proxy for vault-first chat

---

## Testing Strategy

### Unit Tests
- Configuration loading
- Synthesis wrapper methods
- API endpoint logic

### Integration Tests
- Synthesis subprocess calls
- End-to-end search flow
- Mobile UI functionality

### Performance Tests
- Search response times
- Concurrent request handling
- Mobile network conditions

### Manual Tests
- Mobile browser compatibility
- obsidian:// URI behavior
- PWA installation

---

## Deployment Strategy

### Development
```bash
uv run python -m temoa
```

### Production (Systemd)
```ini
[Unit]
Description=Temoa Semantic Search Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/temoa
ExecStart=/path/to/temoa/.venv/bin/uvicorn temoa.server:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Synthesis performance inadequate | High | Phase 0 validates performance first ✅ |
| obsidian:// URIs don't work on mobile | High | Phase 0 tests on actual devices |
| Subprocess overhead too high | Medium | ✅ Resolved: Using direct imports instead |
| Gleanings extraction breaks on edge cases | Medium | Extensive testing with real data |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Phase 0 reveals architectural issues | High | ✅ Complete - no blockers found |
| Synthesis changes break integration | Medium | Version pin Synthesis, test regularly |
| Mobile testing requires physical devices | Low | Use Tailscale for remote testing |

---

## Success Metrics

### Phase 1 Metrics
- Search response time < 2s from mobile
- Can perform 10 consecutive searches without errors
- obsidian:// links work 100% of time

### Phase 2 Metrics
- All 505+ gleanings searchable
- Gleaning extraction runs daily without failures
- Search finds relevant gleanings in top 5 results

### Phase 3 Metrics
- Daily usage > 5 searches
- Archaeology used > 1x per week
- PWA installed and used regularly

### Phase 4 Metrics
- Vault-first chat used > 3x per week
- LLM responses cite vault sources > 50% of time
- User reports building on existing knowledge

---

## Timeline

```
Week 1: Phase 0 (Discovery) ✅
  Days 1-2: Performance testing, prototyping, architecture decisions

Week 2-3: Phase 1 (MVP) 🔵
  Days 3-5: Project setup, configuration, Synthesis wrapper
  Days 6-7: FastAPI server, basic UI
  Days 8-9: Testing, documentation, mobile validation

Week 4: Phase 2 (Gleanings)
  Days 10-11: Extraction scripts, migration
  Days 12-13: Automation, testing, refinement

Week 5-6: Phase 3 (Enhanced Features)
  Days 14-16: Archaeology endpoint, enhanced UI
  Days 17-19: PWA support, performance optimization
  Day 20: Testing, polish

Week 7+: Phase 4 (Vault-First LLM)
  Future development based on Phase 1-3 learnings
```

---

**Plan Created**: 2025-11-18
**Plan Status**: Phase 0 Complete ✅ | Phase 1 Ready
**Next Review**: After Phase 1 completion
