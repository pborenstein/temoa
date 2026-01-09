# IMPLEMENTATION.md - Temoa Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document tracks progress across all implementation phases. Original planning documents archived in `docs/archive/original-planning/`. Detailed implementation notes in `docs/chronicles/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 3.5 (Profiles & Chunking) ✅ COMPLETE → Ready for Next Phase
**Last Updated**: 2026-01-04
**Current Version**: 0.7.0
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

- Validated performance: 400ms search time, scales to 2,289 files
- Identified architecture: FastAPI server with direct Synthesis imports (not subprocess)
- Mobile use case validated (< 1s response time)

See: chronicles/phase-0-1-foundation.md (Entry 4)

---

## Phase 1: Minimal Viable Search ✅

**Status**: COMPLETE (2025-11-18)

- FastAPI server with direct Synthesis imports (10x faster than subprocess)
- Mobile web UI with obsidian:// links
- 400ms search latency (5x better than 2s target)
- 24 passing tests, 1,180 lines production code

See: chronicles/phase-0-1-foundation.md (Entry 6)

---

## Phase 2: Gleanings Integration ✅

**Status**: COMPLETE (2025-11-19)

- Extraction system for daily notes (MD5-based IDs, incremental mode)
- Migrated 505 historical gleanings
- API endpoint for reindexing
- Production validation: 1,368 gleanings from 742 daily notes

See: chronicles/phase-2-gleanings.md (Entries 7, 9)

---

## CLI Implementation ✅

**Status**: COMPLETE (2025-11-19)

- Click-based CLI with 9 subcommands (config, index, search, stats, etc.)
- Validated on production vault (2,281 files indexed in ~17s)
- Color-coded output, comprehensive help text

See: chronicles/phase-2-gleanings.md (Entry 8)

---

## Phase 2.5: Mobile Validation + UI Optimization ✅

**Status**: COMPLETE (2025-11-24)

- Deployed via Tailscale, behavioral hypothesis validated
- Gleaning status management (active/inactive/hidden with auto-restore)
- Type filtering and UI refinement (compact collapsible results)
- Management page with progress indicators
- Incremental reindexing (30x speedup: 5s vs 159s)

See: chronicles/phase-2.5-deployment.md (Entries 11-19)

---

## Phase 3: Enhanced Features ✅

**Status**: COMPLETE (2025-12-01)

**Part 0: Multi-Vault Support** - LRU cache (max 3 vaults), independent indexes, webapp selector

**Part 1: Technical Debt** - FastAPI lifespan pattern, removed sys.path hacks, app state pattern

**Part 2: Search Quality** - Cross-encoder re-ranking (20-30% precision gain), TF-IDF query expansion, time-aware scoring

**Part 3: UI/UX** - PWA support (installable), search history, keyboard shortcuts, mobile-first optimization

See: chronicles/phase-3-implementation.md (Entries 20-32)

---
## Production Hardening 🔵

**Status**: IN PROGRESS (2025-12-06 onwards)

**Part 1: Infrastructure & Critical Fixes** - ✅ COMPLETE
- Vault format agnostic support (plain text files)
- Critical bug fixes (pipeline order, path traversal, query expansion)
- Unicode sanitization

**Part 2: Deployment** - ✅ COMPLETE
- macOS launchd service management (auto-start, auto-restart, port 8080)

**Part 3: Search Quality** - ✅ COMPLETE
- Frontmatter-aware search (BM25 tag boosting with 5x multiplier, 100% success for tag queries)
- Description field integration

**Part 4: Gleaning Enhancement** - ✅ COMPLETE
- URL normalization system (GitHub cleanup, emoji removal)
- GitHub API enrichment (7 metadata fields, 259 repos enriched)

**Part 5: Code Quality & Refinement** - ✅ COMPLETE (2026-01-09)
- [x] Comprehensive code review (2026-01-05) - 20 issues identified
- [x] Production hardening roadmap created (6 phases, 25-30 hours estimated)
- [x] Phase 0: Testing Infrastructure (223 tests, 171 passing baseline, TESTING.md)
- [x] Phase 1: Low-Risk Simplifications (config docs, frontmatter helper, history limits)
- [x] Phase 2: Performance Optimizations (700-1300ms latency reduction)
- [x] Phase 3: Error Handling (specific exception types, fail-open/closed philosophy)
- [x] Phase 4: Security Hardening (CORS restrictive defaults, rate limiting, path validation)
- [x] Phase 5: Architecture Improvements (SKIPPED - optional, working well as-is)
- [x] Phase 6: Documentation & Polish (TESTING.md, ARCHITECTURE.md, CLAUDE.md, IMPLEMENTATION.md updated)

See: chronicles/production-hardening.md (Entries 33-46), docs/PRODUCTION-HARDENING-ROADMAP.md, docs/TESTING.md

---

## Phase 3.5: Specialized Search Modes 🔵

**Status**: IN PROGRESS
**Branch**: `phase-3.5-search-modes`
**Version**: 0.7.0 (in development)
**Duration**: 10-14 days (estimated)

**Goal**: Enable optimized search experiences for different content types through user-selectable profiles, adaptive chunking, and metadata-aware ranking.

**See**: [docs/phases/phase-3.5-specialized-search.md](phases/phase-3.5-specialized-search.md) for complete plan

### Sub-phases Overview

- [x] 3.5.1: Core Profile System (3-4 days) ✅ **COMPLETE**
- [x] 3.5.2: Adaptive Chunking (4-5 days) ✅ **COMPLETE**
- [ ] 3.5.3: Metadata Boosting (2 days)
- [ ] 3.5.4: Profile Recommendation (1-2 days)
- [ ] 3.5.5: UI Updates (2 days)
- [ ] 3.5.6: Documentation & Testing (1-2 days)

### Phase 3.5.1: Core Profile System ✅ COMPLETE

**Completed**: 2025-12-30
**Branch**: `phase-3.5-search-modes`
**Commit**: `e68f724`

**Deliverables**:
- ✅ `src/temoa/search_profiles.py` - SearchProfile dataclass + 5 built-in profiles
- ✅ Server: `/search?profile=<name>` parameter, `/profiles` API endpoint
- ✅ CLI: `--profile` flag for search, `temoa profiles` command
- ✅ Configuration: Custom profile loading from config
- ✅ Tests: 10 unit tests (all passing)

**Built-in Profiles**:
1. **repos** - GitHub repos/tech (70% BM25, metadata boosting)
2. **recent** - Recent work (7-day half-life, 90-day cutoff)
3. **deep** - Long-form content (80% semantic, chunking support)
4. **keywords** - Exact matching (80% BM25, fast)
5. **default** - Balanced (current behavior)

**Files Created**:
- `src/temoa/search_profiles.py` (224 lines)
- `tests/test_search_profiles.py` (10 tests)
- `docs/phases/phase-3.5-specialized-search.md` (complete plan)

**Files Modified**:
- `src/temoa/server.py` - Profile parameter integration
- `src/temoa/cli.py` - Profile flag and profiles command

### Phase 3.5.2: Adaptive Chunking ✅ COMPLETE

**Completed**: 2025-12-30
**Branch**: `phase-3.5-search-modes`
**Commits**: `37ce8f9`, `ebbc70b`, `c1da088`, `3c3da84`, `8c1dc1c`

**Deliverables**:
- ✅ `synthesis/src/embeddings/chunking.py` - Core chunking logic (207 lines)
- ✅ Updated `synthesis/src/embeddings/vault_reader.py` - Chunk support
- ✅ Updated `synthesis/src/embeddings/pipeline.py` - Chunking parameters
- ✅ Updated `src/temoa/synthesis.py` - Deduplication + chunk metadata
- ✅ CLI: `--enable-chunking`, `--model` flags for index/reindex
- ✅ Server: `/reindex` chunking query parameters
- ✅ Tests: 19 unit tests for chunking (all passing)

**Chunking Parameters**:
- `chunk_size`: 2000 chars (well within 512 token limit)
- `chunk_overlap`: 400 chars (preserves context at boundaries)
- `chunk_threshold`: 4000 chars (minimum size before chunking)

**Key Features**:
- Sliding window chunking with overlap
- Smart final chunk merging (avoids tiny trailing chunks)
- Per-vault model selection via config or `--model` flag
- Chunk deduplication (keeps best-scoring chunk per file)
- Progress messages during model loading delays

**Files Created**:
- `synthesis/src/embeddings/chunking.py` (207 lines)
- `tests/test_chunking.py` (19 tests)

**Files Modified**:
- `synthesis/src/embeddings/vault_reader.py` - read_file_chunked(), chunk metadata
- `synthesis/src/embeddings/pipeline.py` - chunking parameters
- `src/temoa/synthesis.py` - deduplicate_chunks(), search integration
- `src/temoa/server.py` - /reindex chunking params
- `src/temoa/cli.py` - --enable-chunking, --model flags, vault-specific model selection
- `.gitignore` - Fixed to allow tests/ directory

**Impact**:
- Files >4000 chars now fully searchable (previously truncated at ~2500 chars)
- Example: 9MB book → 4.4x content items (2006 files → 8755 searchable chunks)
- Backward compatible (chunking disabled by default)

---

### Next Session Start Here

**Current Branch**: `main`
**Current Focus**: Phase 3.5 (Profiles & Chunking) complete - Ready for next phase or refinements

**Recent Work**:

*2026-01-04*: Documentation cleanup
- ✅ Updated ARCHITECTURE.md for Phase 3.5 (profiles, chunking, multi-vault, 22 API endpoints)
- ✅ Updated DEPLOYMENT.md for Phase 3.5 (config format, chunking clarification)
- ✅ Archived QoL materials to docs/archive/QoL-improvements/
- ✅ Updated docs navigation (README.md, archive README)
- ✅ Removed DOCUMENTATION-GUIDE.md (session workflows now in plinth plugin)
- Commits: 7f498aa, 9975e0b, 61c2dfb

*2026-01-02*:
- ✅ Completed all QoL improvements (Phases 1-5)
- ✅ Mobile testing validated (iOS/Android working well)
- ✅ Squash merged qol-detour → phase-3.5-search-modes
- ✅ Branch cleanup (qol-detour deleted)
- ✅ Web UI now at feature parity with CLI

**QoL Improvements**: ✅ COMPLETE (3-4 days)
1. ✅ **Phase 1**: Search result redesign (content-first layout, dates visible) - COMPLETE
2. ✅ **Phase 2**: Profile integration (dropdown in web UI) - COMPLETE
3. ✅ **Phase 3**: Management enhancements (gleaning management, model selection, advanced stats) - COMPLETE
4. ✅ **Phase 4-5**: Integration & testing (mobile-first) - COMPLETE
5. Squash merged to phase-3.5-search-modes (commit 12d2e64)

**Next**: Resume Phase 3.5.3 - Metadata Boosting (with web UI from day 1)

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

**Last Updated**: 2026-01-01
**Current Phase**: 3.5 (Specialized Search Modes)
**Next**: See CONTEXT.md for current session state
