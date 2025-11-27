# IMPLEMENTATION.md - Temoa Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document tracks progress across all implementation phases. Detailed phase plans are in `docs/phases/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 2 ✅ COMPLETE + CLI ✅ COMPLETE | Phase 2.5 ✅ COMPLETE | Phase 3 Part 0 ✅ COMPLETE | Multi-Vault Webapp 🔵 IN PROGRESS (Backend Complete)
**Last Updated**: 2025-11-26
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
| [Phase 0: Discovery & Validation](phases/phase-0-discovery.md) | ✅ **COMPLETE** | 1 day | None |
| [Phase 1: Minimal Viable Search](phases/phase-1-mvp.md) | ✅ **COMPLETE** | 1 day | Phase 0 ✅ |
| [Phase 2: Gleanings Integration](phases/phase-2-gleanings.md) | ✅ **COMPLETE** | 1 day | Phase 1 ✅ |
| **Phase 2.5: Mobile Validation + UI** | ✅ **COMPLETE** | 1 week | Phase 2 ✅ |
| [Phase 3: Enhanced Features](PHASE-3-READY.md) | 🔵 **READY** | 2 weeks | Phase 2.5 ✅ |
| [Phase 4: Vault-First LLM](phases/phase-4-llm.md) | ⚪ Future | 7-10 days | Phase 3, Apantli |

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

### Detailed Plan

See [phases/phase-0-discovery.md](phases/phase-0-discovery.md)

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

### Detailed Plan

See [phases/phase-1-mvp.md](phases/phase-1-mvp.md)

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

### Detailed Plan

See [phases/phase-2-gleanings.md](phases/phase-2-gleanings.md)

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

### Why This Phase Exists

**From CHRONICLES.md Entry 10:**
> **Technology works. Behavioral hypothesis untested.**

All engineering is complete. But we haven't validated the core hypothesis:

> **"If I can search my vault from my phone in <2 seconds, I'll check it before Googling. Over time, this habit makes past research compound."**

This is a **behavioral hypothesis**, not a technical one. It requires:
- Real mobile device (not VM testing)
- Real vault with your gleanings
- Real daily usage over time
- Real measurement of behavior change

**Risk of skipping this phase**: Build Phase 3 features (archaeology UI, PWA, filters) that don't address actual friction points or aren't used.

### Tasks Overview

**Deployment & Setup:**
- [ ] 2.5.1: Deploy server to always-on machine (desktop/laptop)
- [ ] 2.5.2: Configure Tailscale for mobile access
- [ ] 2.5.3: Test from actual mobile device (iOS/Android)

**Usage Tracking (Manual):**
- [ ] 2.5.4: Use daily for 1-2 weeks
- [ ] 2.5.5: Track search count, response times, habit formation
- [ ] 2.5.6: Document friction points and missing features

**Validation:**
- [ ] 2.5.7: Measure behavioral change (vault-first vs. Google-first)
- [ ] 2.5.8: Decide Phase 3 scope based on real usage data

### Deliverables

**Quick Start Guides:**
- [x] `docs/DEPLOYMENT.md` - Step-by-step server deployment
- [x] `scripts/test_api.sh` - API smoke test harness
- [x] `docs/MIDCOURSE-2025-11-19.md` - Assessment and rationale

**Usage Documentation:**
- [ ] Daily usage log (in personal vault, not committed)
- [ ] Friction points document (what prevented usage)
- [ ] Feature requests based on real needs

### Gleaning Status Management (2025-11-20)

**Status**: COMPLETE - Three-status model with auto-restoration

Implemented comprehensive status management for gleanings after real-world usage revealed need:

**Three Status Types:**
1. **active**: Normal gleanings, included in search
2. **inactive**: Dead links, excluded from search, auto-restores if link comes back
3. **hidden**: Manually hidden, never checked by maintenance tool

**Features:**
- Status persists in `.temoa/gleaning_status.json` and gleaning frontmatter
- Reason field tracks why status changed
- Maintenance tool checks links and marks dead ones inactive
- Auto-restoration when inactive links become alive again
- Progress tracking with ETA for long maintenance runs
- Backfill logic for existing inactive gleanings

**Commits:**
- 8de00f5: Initial status management (active/inactive)
- 3858429: Frontmatter format changes
- fbe9701: Fix /gleanings endpoint
- e60cde5: Add description field and maintenance tool
- c6e8db3: Add progress tracking
- b3694aa: Backfill reasons for inactive gleanings
- 5af166c: Add reason field to frontmatter
- 95099c6: Add 'hidden' status and auto-restore

**Commands:**
```bash
# Mark gleaning status
temoa gleaning mark <id> --status inactive --reason "dead link"
temoa gleaning mark <id> --status hidden --reason "duplicate"

# List by status
temoa gleaning list --status inactive
temoa gleaning list --status hidden

# Run maintenance (check links, add descriptions)
temoa gleaning maintain
```

See [chronicles/phase-2.5-deployment.md Entry 12](CHRONICLES.md) for detailed design rationale.

### Deployment Shakedown (2025-11-20)

**Status**: COMPLETE - Deployment testing revealed and fixed critical bugs

During initial deployment testing, discovered and fixed 4 critical bugs:

**Bug 1: Storage Path Mismatch** (files_indexed: 0)
- **Problem**: Health endpoint showed `files_indexed: 0` despite 2942 files indexed
- **Cause**: Server looked in `synthesis/embeddings/` instead of `vault/.temoa/`
- **Fix**: Pass `storage_dir=config.storage_dir` to SynthesisClient (commit: 7dfbe1c)
- **Impact**: Health checks now correctly report indexed file count

**Bug 2: Circular Config Dependency**
- **Problem**: Config search included `.temoa/config.json` (relative to cwd), but config contains vault_path
- **Cause**: Can't find config without knowing vault location; can't know vault without reading config
- **Fix**: Removed vault-local search, config is now global-only (commit: 35947f1)
- **Impact**: Can run temoa commands from any directory

**Bug 3: Gleaning Titles as MD5 Hashes**
- **Problem**: Search results showed "e1471cc011dc" instead of actual titles
- **Cause**: Gleanings missing `title:` in frontmatter, Synthesis fell back to filename
- **Fix**: Updated extraction scripts to add `title:` field, created repair script (commit: a1daadd)
- **Impact**: Better search UX - can identify gleanings by title

**Bug 4: YAML Parsing Errors**
- **Problem**: `mapping values are not allowed here` for titles with colons
- **Cause**: Unquoted title values like "obsidian-sanctum: A theme" broke YAML parsing
- **Fix**: Quote title values with `json.dumps()` to handle special characters (commit: aeb0edf)
- **Impact**: All gleaning titles parse correctly, no YAML errors

**Enhancement: /extract API Endpoint**
- **Added**: `POST /extract` endpoint for gleaning extraction via API (commit: c13e431)
- **Features**:
  - `incremental=true` (default): Only process new files
  - `auto_reindex=true` (default): Auto-reindex after extraction
- **Impact**: Can trigger extraction from web UI or automation without CLI

**Commits in this session:**
- 7dfbe1c: fix: pass storage_dir to SynthesisClient
- 35947f1: fix: remove vault-local config search
- a1daadd: fix: add title field to gleaning frontmatter
- aeb0edf: fix: quote title values for YAML safety
- c13e431: feat: add /extract endpoint

**Updated Deliverables:**
- [x] Fixed storage path configuration
- [x] Simplified config search (global-only)
- [x] Gleaning titles display properly
- [x] `/extract` API endpoint added
- [x] `scripts/add_titles_to_gleanings.py` - Repair tool for existing gleanings (completed migration, script removed 2025-11-23)

### Extraction Shakedown (2025-11-21)

**Status**: COMPLETE - Real-world extraction revealed format gaps and filesystem edge cases

During production extraction from 742 daily notes, discovered and fixed 5 critical issues:

**Issue 1: Case-Insensitive Filesystem Duplicates**
- **Problem**: On macOS APFS, both `Daily/**/*.md` and `daily/**/*.md` patterns matched same files
- **Evidence**: Output showed "Processing: daily/2025/.../file.md" then "Processing: Daily/2025/.../file.md"
- **Impact**: Confusing output, potential duplicate processing
- **Fix**: Added `seen_paths` set with `Path.resolve()` deduplication (commit: c356fdb)
- **Result**: Each file processed exactly once, clean output

**Issue 2: Missing 'hidden' Status in CLI**
- **Problem**: System supported three statuses (active/inactive/hidden), CLI only exposed active/inactive
- **Impact**: Users couldn't mark gleanings as permanently hidden
- **Fix**: Added 'hidden' to CLI choices and help text (commit: c356fdb)
- **Result**: All three statuses now accessible via `temoa gleaning mark`

**Issue 3: Multiple Gleaning Formats Not Supported**
- **Problem**: Only markdown links `- [Title](URL)` were extracted
- **Evidence**: User had 766 gleanings, only 689 extracted (77 missing = 10% loss)
- **Impact**: Naked URLs, multi-line descriptions completely ignored
- **Fix**: Implemented comprehensive pattern matching (commit: 6db212d):
  - Markdown links with timestamps: `- [Title](URL)  [HH:MM]`
  - Naked URLs with bullet: `- https://...` (fetches title from web)
  - Naked URLs bare: `https://...` (no bullet, fetches title)
  - Multi-line descriptions: ALL consecutive `>` lines captured
  - Timestamps: `[HH:MM]` extracted and preserved in date field
- **Result**: Now captures 766/766 gleanings (100% coverage)
- **Performance**: Title fetching adds ~1.5s per naked URL

**Issue 4: Dry Run Fetching Titles Wastefully**
- **Problem**: `--dry-run` made HTTP requests to fetch titles, then discarded them
- **Impact**: Wasted time and bandwidth during preview
- **Fix**: Skip title fetching during dry run, use placeholders (commit: ead20e3)
- **Result**: Instant dry run preview

**Issue 5: Lowercase Patterns Causing Confusion**
- **Problem**: Patterns `["Daily/**/*.md", "daily/**/*.md"]` worked on Linux but confused users on macOS
- **Evidence**: User said "daily is BAD BAD BAD" when seeing `daily/` in output
- **Impact**: Even though deduplication worked, output was confusing
- **Fix**: Removed lowercase patterns entirely (commit: ef105f4)
- **Result**: Clean output showing only actual directory names

**Enhancement: Diagnostic Tool**
- **Added**: `scripts/analyze_gleaning_formats.py` - Pre-extraction analysis tool
- **Features**:
  - Scans vault for all gleaning formats
  - Shows examples of each format found
  - Reports coverage statistics
  - Estimates extraction time for naked URLs
- **Impact**: Users can preview what will be extracted before running full extraction

**Commits in this session:**
- c356fdb: fix: resolve case-insensitive filesystem duplicate extraction bug
- c356fdb: feat: add 'hidden' status support to CLI
- 6db212d: feat: support multiple gleaning formats and naked URLs
- aa903e5: docs: update GLEANINGS.md with multiple format support
- 493143c: fix: update diagnostic script to reflect current format support
- ead20e3: fix: skip title fetching during dry run
- ef105f4: fix: remove lowercase daily/journal patterns (user preference)

**Test Coverage Added:**
- [x] Case-insensitive filesystem deduplication test
- [x] Extract gleanings without duplicate processing test
- [x] All 19 gleaning tests passing

**Updated Deliverables:**
- [x] Multiple format support (5 different formats)
- [x] Title fetching from web for naked URLs
- [x] Multi-line description extraction
- [x] Timestamp preservation
- [x] Case-insensitive filesystem handling
- [x] Diagnostic analysis tool
- [x] Updated documentation (GLEANINGS.md)

**Production Results:**
```
Total gleanings found: 766
New gleanings created: 739
Duplicates skipped: 27
Files processed: 374
Coverage: 100% (was 90% before fixes)
```

### UI Refinement (2025-11-23)

**Status**: COMPLETE - Web interface polished based on real usage feedback

During production usage of the web UI, identified and implemented several UX improvements to enhance readability and reduce screen clutter (especially on mobile).

**Improvements Made:**

1. **Score Badge Repositioned:**
   - Moved similarity score from left to right side of result header
   - Title now primary identifier (leftmost), score is metadata (rightmost)
   - Creates clean visual hierarchy: content → relevance

2. **Project-To Badge Repositioned:**
   - Moved project-to badge next to score on right side
   - Groups related metadata together (both about document status/relevance)
   - Second line reserved for document attributes (type, tags)

3. **Validation Error Handling:**
   - Enhanced error display to parse FastAPI validation error structure
   - Shows specific field-level errors with helpful messages
   - Example: "Validation error: String should have at least 1 character (query → q)"
   - Helps users understand and fix validation issues

4. **Compact and Collapsible Stats Panel:**
   - Default collapsed state shows summary: "📊 Stats (2,942 files, 10 results)"
   - Saves 7 lines of vertical space on mobile
   - Expands on click to show full details
   - State persisted in localStorage (remembers preference)

5. **Final Layout:**
   ```
   Title of document              project-to: phase3 [0.654]
   type: gleaning
   ```
   - Primary info (title) left-aligned
   - Metadata (project-to, score) right-aligned
   - Attributes (type, tags) on second line
   - Clean, scannable hierarchy

**Visual Design Principles:**
- Information hierarchy: Title → Metadata → Attributes → Context
- Space optimization: Collapsible sections, compact summaries
- Error communication: Specific, helpful, actionable messages
- Mobile-first: Minimize scrolling, maximize content visibility

**Commits:**
- abb74e5: feat: move score badge to rightmost position in result header
- d02ee39: feat: move project-to badge next to score in result header
- 1a18714: fix: handle validation errors properly in UI
- 36d895e: feat: compact and collapsible stats panel
- 94cb4f4: feat: reposition type badge next to score badge in result header

**Impact:**
- Cleaner, more scannable search results
- Less scrolling required on mobile (stats collapsed by default)
- Better error feedback when validation fails
- Professional, polished interface ready for mobile validation

### Type Filtering Implementation (2025-11-23)

**Status**: COMPLETE - Comprehensive type-based filtering with cached frontmatter optimization

Implemented full type-based filtering system for search results after user identified need to filter daily notes and other document types.

**Core Features:**

1. **Frontmatter Type Field Support:**
   - Single string: `type: gleaning`
   - YAML array: `type: [writering, article]`
   - Block format: `type:\n  - writering\n  - article`
   - Added `parse_type_field()` function in `gleanings.py`

2. **Dual Filtering Modes:**
   - Inclusive filtering: `--type gleaning,article` (show only these types)
   - Exclusive filtering: `--exclude-type daily,note` (hide these types)
   - Default behavior: `exclude_types=["daily"]` to reduce noise
   - OR-logic matching for arrays

3. **CLI Integration:**
   - Added `--type/-t` and `--exclude-type/-x` flags to search command
   - Logging configuration to suppress noisy synthesis module logs
   - Filter statistics display in results

4. **Web UI Controls:**
   - Multi-select dropdowns for include/exclude type selection
   - Type badge display in search results
   - Updated stats panel to show filtered counts
   - CSS styling for type controls

5. **API Endpoint Updates:**
   - `/search` endpoint now accepts `include_types` and `exclude_types` parameters
   - Updated response includes `filtered_count` statistics
   - Filter chain: score → status → type → daily notes → limit

**Issues Discovered and Fixed:**

**Issue 1: Missing Frontmatter Dependency**
- **Problem**: `No module named 'frontmatter'` error on first search attempt
- **Cause**: `python-frontmatter` not in dependencies
- **Fix**: Added `python-frontmatter>=1.0.0` to pyproject.toml (commit: 13bef34)
- **Impact**: Type filtering now works correctly

**Issue 2: Excessive Logging Spam**
- **Problem**: Hundreds of VaultReader initialization logs on every search
- **Cause**: Initial `filter_by_type()` implementation read files for every result, triggering synthesis module logs
- **Fix 1**: Added logging configuration to CLI to suppress INFO logs (commit: 3cb340a)
- **Fix 2**: Better fix - optimized to use cached frontmatter instead (commit: 68ac23a)
- **Impact**: Clean output, no file I/O during filtering

**Issue 3: Performance Degradation from File I/O**
- **Problem**: Type filtering was reading files for every search result
- **Evidence**: User noted "but this didn't happen before?" - new performance issue
- **Cause**: `filter_by_type()` called `VaultReader.read_file()` for each result
- **Fix**: Refactored to use cached frontmatter from Synthesis results (commit: 68ac23a)
- **Result**: Zero file I/O during filtering, <1ms overhead

**Optimization Details:**

Before optimization:
```python
# Read file for every result - SLOW
with open(result_path) as f:
    post = frontmatter.load(f)
    types = parse_type_field(post.metadata)
```

After optimization:
```python
# Use cached frontmatter from Synthesis - FAST
frontmatter_data = result.get("frontmatter")
if frontmatter_data is not None:
    types = parse_type_field(frontmatter_data)  # No file I/O!
```

**Migration Support:**
- Created `scripts/add_type_to_daily_notes.py` migration script (completed migration, script removed 2025-11-23)
- Adds `type: daily` to all files in Daily/ directory
- Includes `--dry-run` mode for safe testing
- Provides detailed summary of changes

**Supported Document Types:**
- `gleaning` - Extracted links/articles from daily notes
- `writering` - Writing-related content
- `llmering` - LLM/AI-related content
- `article` - General articles
- `reference` - Reference material
- `note` - General notes
- `daily` - Daily notes (excluded by default)

**Commits in this session:**
- 2c1cfe6: feat: implement type-based filtering for search results
- 13bef34: fix: add missing python-frontmatter dependency
- 3cb340a: fix: reduce noisy logging output in CLI
- 68ac23a: perf: use cached frontmatter for type filtering

**Updated Deliverables:**
- [x] `parse_type_field()` function in `src/temoa/gleanings.py`
- [x] `filter_by_type()` function in `src/temoa/server.py`
- [x] CLI flags: `--type` and `--exclude-type` in `src/temoa/cli.py`
- [x] Web UI type controls in `src/temoa/ui/search.html`
- [x] Migration script: `scripts/add_type_to_daily_notes.py` (completed migration, script removed 2025-11-23)
- [x] Updated API endpoint documentation
- [x] Performance optimization using cached frontmatter

**Architecture Decision:**
- Cache frontmatter during index/reindex operations (Synthesis does this automatically)
- Use cached metadata for filtering (no file I/O required)
- Default excludes daily type to reduce noise from daily notes
- Both path-based and type-based filtering work together (AND logic)

### Compact Collapsible UI (2025-11-24)

**Status**: COMPLETE - Major UI overhaul based on mobile testing feedback

During mobile validation, discovered UI issues that needed addressing for practical daily use.

**Problem Identified**:
- Options sections took up too much vertical space
- With keyboard up on mobile, Search button not visible
- Results took up too much space in default view
- Need to scan many results quickly (mobile scrolling)

**Solution: Compact Collapsible Results**

**Features Implemented:**

1. **Collapsible Result Cards**:
   - Default: Single line (title + badges)
   - Click to expand: Full details (path, description, tags)
   - Multiple results can be expanded simultaneously
   - Arrow indicators (▶ collapsed, rotated when expanded)
   - State persists in localStorage (per-device)

2. **Result Controls**:
   - "Collapse All" button
   - "Expand All" button
   - Keyboard shortcuts: `c` = collapse all, `e` = expand all

3. **Consolidated Options**:
   - All controls in single "Options" collapsible section
   - Was: Two sections (basic controls + advanced options)
   - Now: One section (collapsed by default)
   - Tighter spacing: 10px padding (vs 12-16px), 8px input padding (vs 10px)
   - Shorter labels: "Min Score" (vs "Min Similarity Score"), "Limit" (vs "Result Limit (max 100)")
   - Smaller selects: size="3" (vs size="4")

4. **Responsive Result Layout**:
   - Collapsed: Title and badges stacked vertically (better for narrow screens)
   - Expanded: Title left, badges right (better use of horizontal space)
   - Compact padding: 12px when collapsed, 20px when expanded

**Technical Implementation:**

1. **State Management Foundation**:
   - Centralized state object replacing scattered state (closures, DOM)
   - Versioned localStorage (`temoa_v1_ui_state`)
   - Race condition prevention (request ID tracking)
   - Backward compatibility (migrates old `advancedExpanded` → `optionsExpanded`)

2. **Safe DOM Manipulation**:
   - Replaced all `innerHTML` with `createElement` APIs
   - XSS protection via automatic escaping (`textContent`)
   - Component factory functions:
     - `createResultCard(result, expanded)`
     - `createResultHeader(result)` - Title + badges
     - `createResultDetails(result)` - Path, description, tags
     - `createBadge(type, content, href)` - Reusable badge
     - `createTag(tag)` - Tag component
     - `createErrorCard()` - Fallback on errors
   - Event delegation (single click handler for all cards)

3. **Error Boundaries**:
   - `safeRender(renderFn, fallback)` wrapper
   - Graceful fallback on render failures
   - Prevents UI crashes

4. **Performance**:
   - Event delegation (1 handler vs N handlers)
   - Conditional DOM rendering (details only added when expanded)
   - No performance regression (<1ms state management overhead)

**Commits:**
- 161b79b: feat: compact collapsible results + mobile optimization

**Files Changed:**
- `src/temoa/ui/search.html` (~400 lines added/modified)
- `pyproject.toml` (version 0.1.3 → 0.2.0)
- `docs/COMPACT-VIEW-PLAN.md` (implementation plan)

**Impact:**
- Search button visible with keyboard up on mobile
- Can quickly scan many results (collapsed view)
- Expand only what's interesting
- Cleaner, more professional interface
- Zero external dependencies maintained
- XSS vulnerabilities eliminated

### Management Page (2025-11-24)

**Status**: COMPLETE - Administrative interface for vault operations

Added comprehensive management interface at `/manage` for vault maintenance and monitoring.

**Features Implemented:**

1. **System Health Monitoring**:
   - Real-time health status display
   - Model information (name, embeddings count)
   - Files indexed count
   - Status indicators (🟢 healthy, 🔴 unhealthy)

2. **Vault Statistics**:
   - Total embeddings count
   - Tag count with breakdown
   - Directory count
   - Fetched from `/stats` endpoint
   - Updated after reindex operations

3. **Reindex Vault Control**:
   - Button to trigger full vault reindex
   - Confirmation dialog (prevents accidental clicks)
   - Barber pole progress indicator (classic macOS style)
   - Status messages during and after reindex
   - Automatic stats refresh on completion

4. **Extract Gleanings Control**:
   - Button to trigger gleaning extraction
   - Configurable options (checkboxes):
     - Incremental mode (default: on) - only new files
     - Auto-reindex (default: on) - reindex after extraction
   - Status messages with extraction statistics
   - Results display (total found, created, duplicates skipped)

5. **Navigation**:
   - Gear icon (⚙︎) in search page header links to management
   - "Back to Search" link in management page
   - Consistent styling across pages

**Technical Implementation:**

1. **UI Components**:
   - Dark theme matching search page
   - Mobile-responsive layout
   - Safe DOM manipulation (createElement)
   - Barber pole CSS animation for progress
   - Indeterminate progress bar (no percentage)

2. **API Integration**:
   - `/health` endpoint for status monitoring
   - `/stats` endpoint for vault statistics
   - `/reindex` endpoint (POST) for reindexing
   - `/extract` endpoint (POST) for gleaning extraction

3. **Progress Feedback**:
   - "Working..." message with barber pole
   - Operation-specific success messages
   - Error handling with user-friendly messages
   - Stats auto-refresh after operations

**Bug Fixes:**

**Issue 1: Stats Display Bug**
- **Problem**: `total_tags` and `directories` showed as undefined
- **Cause**: Response structure nested under `stats` key
- **Fix**: Access `data.stats.total_tags` instead of `data.total_tags`
- **Impact**: Stats now display correctly in management page

**Issue 2: Checkbox Layout**
- **Problem**: Checkboxes appeared above Extract button (confusing)
- **Cause**: DOM insertion order in initial implementation
- **Fix**: Repositioned checkboxes below button using insertBefore
- **Impact**: Clearer visual hierarchy (action → options)

**Commits:**
- bef5807: feat: add management page with reindex and extraction controls

**Files Added:**
- `src/temoa/ui/manage.html` (547 lines) - Management interface
- `docs/MANAGEMENT-PAGE-PLAN.md` (302 lines) - Implementation plan

**Files Modified:**
- `src/temoa/server.py` - Add `/manage` route
- `src/temoa/ui/search.html` - Add navigation to management page

**Impact:**
- Easy access to vault maintenance operations
- No need for CLI access during mobile usage
- Visual feedback for long-running operations
- Centralized administration interface
- Consistent UX with search page

### Incremental Reindexing (2025-11-25)

**Status**: COMPLETE - True incremental reindexing implemented with 30x speedup

During Phase 2.5 usage, identified that both `temoa index` and `temoa reindex` performed full rebuilds (~159 seconds), making daily reindexing tedious. Implemented true incremental reindexing.

**Core Implementation:**

1. **File Tracking in Index** (`synthesis/src/embeddings/store.py`)
   - Added `file_tracking` dictionary to `index.json`
   - Tracks modification time, content length, and index position for each file
   - Automatically rebuilt on every save (positions always correct)

2. **Change Detection** (`src/temoa/synthesis.py::_find_changed_files()`)
   - Compares current vault state with file_tracking from last index
   - Detects new files (not in tracking)
   - Detects modified files (different modification timestamp)
   - Detects deleted files (in tracking but not in vault)
   - Returns `None` if no previous index (triggers full rebuild fallback)

3. **Embedding Merge** (`src/temoa/synthesis.py::_merge_embeddings()`)
   - **CRITICAL ORDER**: DELETE (reverse) → UPDATE → APPEND
   - Heavily documented with DANGER ZONES warnings
   - Rebuilds position maps after deletions to avoid index corruption
   - Handles edge cases (no embeddings, only deletions, etc.)

4. **Updated CLI Commands**
   - `temoa index` - Full rebuild (force=True, all files)
   - `temoa reindex` - Incremental update (force=False, only changed files)
   - No flags except `--vault` (clean, simple)

5. **Management UI Enhancement**
   - Added "Full rebuild" checkbox for reindex operation
   - Default: unchecked (incremental mode)
   - Checkbox controls force parameter

**Performance Results** (3,059 file vault, `all-mpnet-base-v2`):

| Operation | Time | Files Processed | Speedup |
|-----------|------|-----------------|---------|
| Full index (`temoa index`) | 159s | 3,059 files | Baseline |
| Incremental (no changes) | 4.8s | 0 files | **30x faster** |
| Incremental (5 new files) | 6-8s | 5 files | **25x faster** |

**Testing:**
- ✅ No changes scenario: 4.76 seconds
- ✅ 5 new files after extraction: ~6-8 seconds
- ✅ Change detection working correctly
- ✅ No data corruption (verified with search after reindex)

**Documentation:**
- Updated README.md with performance comparison table
- Updated DEPLOYMENT.md with incremental reindexing guidance
- Added comprehensive DANGER ZONES documentation in plan

**Commits:**
- 3776158: Added file_tracking to storage
- 605ae69: Implemented incremental reindexing core logic
- 4b21318: Updated CLI to use incremental by default
- da6d422: Added status document
- 0af1ee7: Documentation and UI controls

**Known Issue Identified:**

**Multi-Vault Support Problem**: When using `--vault` flag to index a different vault, the storage_dir still comes from config (pointing to the config's vault), not the command-line vault. This means:
- ❌ Index for different vault overwrites config vault's index
- ❌ Confusion about which index belongs to which vault

**Solution Required**: Derive storage_dir from the vault being indexed, not from config. See Phase 3 for fix.

### Success Criteria

**Deployment Working:**
- [x] Server accessible from mobile via Tailscale
- [x] `http://<tailscale-ip>:8080/health` returns "healthy"
- [x] `/search` endpoint returns results
- [x] obsidian:// URIs open Obsidian mobile app

**Performance Validated:**
- [x] Search responds in <2s from phone (in real network conditions)
- [x] Model loads successfully at startup (~13-15s)
- [x] 766+ gleanings searchable
- [x] UI usable on mobile screen size
- [x] Compact UI solves "can't see Search button with keyboard up" problem

**UI Improvements:**
- [x] Collapsible results (default: single line)
- [x] Click to expand individual results
- [x] Collapse All / Expand All controls
- [x] Keyboard shortcuts (c, e)
- [x] Consolidated Options section
- [x] State persistence (per-device)
- [x] Safe DOM manipulation (XSS protection)
- [x] Error boundaries (graceful failures)

**Behavioral Hypothesis:**
- [x] Mobile testing validated UI usability
- [ ] Long-term usage tracking (ongoing)
- [ ] Vault-first habit formation (ongoing observation)

### Failure Indicators (What to watch for)

**Don't use it**:
- Hypothesis failed, pivot needed
- Ask: Why didn't I use it? Too slow? Not useful? Forgot it existed?

**Too slow**:
- Searches take >3s from mobile
- Need caching or optimization
- Or: Network issue, not code issue

**obsidian:// URIs broken**:
- Links don't open Obsidian app
- Need fallback or different approach
- Test on both iOS and Android

**UI too clunky**:
- Hard to use on mobile screen
- Need UX redesign, not more features
- Keep it simple

**Results not relevant**:
- Search doesn't find what you need
- Improve search quality (better embeddings? different model?)
- Or: Need better gleanings extraction

### Quick Deployment Checklist

**Server Setup (5 minutes):**
```bash
# On always-on machine (desktop/laptop)
cd ~/projects/temoa
uv sync

# Create config pointing to your vault
cat > config.json << 'EOF'
{
  "vault_path": "~/Obsidian/your-vault",
  "synthesis_path": "synthesis",
  "index_path": null,
  "default_model": "all-MiniLM-L6-v2",
  "server": {"host": "0.0.0.0", "port": 8080},
  "search": {"default_limit": 10, "max_limit": 100, "timeout": 10}
}
EOF

# Build index (first time only, ~15-20 seconds)
uv run temoa index

# Start server
uv run temoa server
# Or: nohup uv run temoa server > temoa.log 2>&1 &
```

**Tailscale Setup (2 minutes):**
```bash
# On server machine
tailscale ip -4  # Note this IP (e.g., 100.x.x.x)

# On mobile device
# Install Tailscale app
# Connect to same tailnet
# Bookmark: http://100.x.x.x:8080
```

**Quick Test:**
```bash
# From mobile browser
http://100.x.x.x:8080/health
# Should see: {"status": "healthy", "model": "all-MiniLM-L6-v2", ...}

# Try search
http://100.x.x.x:8080/search?q=obsidian&limit=5
# Click a result, should open Obsidian app
```

### Usage Tracking Template

**Daily Note Entry:**
```markdown
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

## Phase 3: Enhanced Features 🔵

**Status**: READY - Phase 2.5 validation complete, behavioral hypothesis confirmed
**Goal**: Fix technical debt and improve search quality based on real usage
**Duration**: 2 weeks (consolidated from comprehensive reviews)
**Plan**: See [PHASE-3-READY.md](PHASE-3-READY.md) for consolidated implementation plan

### Part 0: Multi-Vault Support (CRITICAL FIX) ✅

**Status**: COMPLETE (2025-11-26)

- [x] Fix `--vault` flag to derive storage_dir from vault path, not config
- [x] Ensure each vault has its own independent index
- [x] Add validation to prevent vault mismatch before operations
- [x] Add --force flag for override with warning
- [x] Add vault metadata to index.json for validation
- [x] Auto-migrate old indexes without metadata
- [x] Comprehensive unit tests (13 tests, all passing)

**Deliverables**:
- `src/temoa/storage.py` (195 lines) - Vault-aware storage utilities
- Updated all CLI commands (index, reindex, search, archaeology, stats)
- Unit tests in `tests/test_storage.py`
- Integration test structure in `tests/test_multi_vault_integration.py`
- Documentation in `docs/chronicles/phase-3-enhanced-features.md` Entry 20

**Key Features**:
- Config vault: Uses config's storage_dir (honors user config)
- Other vaults: Auto-derives as `vault/.temoa/` (independent indexes)
- Validation: Fails with clear error before data loss
- Force: `--force` flag allows override
- Backward compatible: Existing indexes auto-migrate

See: `docs/chronicles/phase-3-enhanced-features.md` Entry 20 for detailed implementation notes.

### Multi-Vault Webapp Support 🔵

**Status**: IN PROGRESS (2025-11-26) - Backend Complete, UI Pending
**Branch**: `claude/multi-vault-webapp-support`
**Goal**: Extend multi-vault support to webapp with vault selector UI

**Phase 1 (Backend)** - ✅ COMPLETE:
- [x] Extend config.py with vault management methods (get_all_vaults, get_default_vault, find_vault)
- [x] Create client_cache.py with LRU cache (max 3 vaults, ~1.5GB RAM)
- [x] Replace global synthesis client with client cache
- [x] Add get_client_for_vault() helper function
- [x] Add /vaults endpoint to list configured vaults
- [x] Update /search endpoint to accept vault parameter
- [x] Update /archaeology endpoint to accept vault parameter
- [x] Update /stats endpoint to accept vault parameter
- [x] Update /reindex endpoint to accept vault parameter (with cache invalidation)
- [x] Update /extract endpoint to accept vault parameter (with cache invalidation)

**Phase 2 (UI)** - ⏳ PENDING:
- [ ] Add vault selector component to search.html
- [ ] Add vault selector component to manage.html
- [ ] Implement JavaScript vault state management
- [ ] Update API calls to include vault parameter
- [ ] Test multi-vault UI functionality

**Phase 3 (Testing & Docs)** - ⏳ PENDING:
- [ ] Write unit tests for client cache
- [ ] Integration testing with multiple vaults
- [ ] Update documentation and migration guide

**Commits (3)**:
- `6b297bb`: Config + Client Cache
- `39cdd0a`: Search endpoint + /vaults API
- `9bfb2a0`: All remaining endpoints

**Key Features**:
- LRU cache for fast vault switching (~400ms when cached)
- All endpoints accept optional `?vault=...` parameter
- Cache invalidation after reindex/extract
- Backward compatible (defaults to config vault)
- Pre-warms default vault at startup

**Next Session**: Continue with UI implementation (Phase 2)
- Vault selector dropdowns (HTML/CSS)
- JavaScript state management (URL > localStorage > default)
- Wire up API calls

**Estimated Remaining**: ~2-3 hours (UI) + 1-2 hours (testing/docs)

### Part 1: Technical Debt (Foundation)

- [ ] Fix module-level initialization
- [ ] Remove sys.path manipulation
- [ ] Introduce service layer

### Part 2: Search Quality (High Value)

- [ ] Cross-encoder re-ranking (Priority 1)
- [ ] Query expansion for short queries
- [ ] Time-aware scoring

### Part 3: UI/UX Polish

- [ ] PWA support (home screen install)
- [ ] Keyboard shortcuts (/, Esc)
- [ ] Search history

### Success Criteria

- [ ] Technical debt eliminated (no module-level init, no sys.path hacks)
- [ ] Search quality improved 20-30% (cross-encoder)
- [ ] PWA installable on mobile
- [ ] All tests passing, no performance regression

### Detailed Plan

**Primary**: [PHASE-3-READY.md](PHASE-3-READY.md) - Consolidated from 3 comprehensive reviews
**Reference**: [phases/phase-3-enhanced.md](phases/phase-3-enhanced.md) - Original outline

---

## Phase 4: Vault-First LLM ⚪

**Status**: Future
**Goal**: LLMs check vault before internet
**Duration**: 7-10 days

### Tasks Overview

- [ ] 4.1: Chat Endpoint with Context
- [ ] 4.2: Citation System

### Deliverables

- [ ] `/chat` endpoint
- [ ] Apantli integration
- [ ] Citation system
- [ ] Vault-first chat UI

### Success Criteria

- [ ] Vault-first becomes default research mode
- [ ] LLM responses build on existing knowledge
- [ ] Citations work reliably

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
