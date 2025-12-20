# CLAUDE.md - Development Guide for Temoa

> **Purpose**: This document provides context and guidance for Claude AI when working on the Temoa project across multiple sessions.

**Last Updated**: 2025-12-15
**Project Status**: Phase 3 Complete ✅
**Current Version**: 0.6.0
**Current Branch**: `main`

---

## Project Overview

**Temoa** is a local semantic search server for Obsidian vaults, enabling vault-first research workflows. It uses the **Synthesis** semantic search engine with advanced multi-stage pipeline including frontmatter-aware search.

**Problem Solved**: Saved links and notes accumulate but never resurface when needed during research. Temoa makes your vault the first place to check before external search.

**Core Architecture**: FastAPI server → Direct Synthesis imports → Multi-stage search pipeline (semantic + BM25 + frontmatter) → Results

**Current Features** (Phase 3 Complete):
- **Frontmatter-aware search**: Tag boosting (5x multiplier) + description field indexing
- **Hybrid search**: BM25 + semantic with RRF fusion and aggressive tag boosting
- **Search quality pipeline**: Query expansion, cross-encoder re-ranking, time-aware scoring
- **Multi-vault support**: LRU cache (max 3 vaults), independent indexes
- **PWA support**: Installable on mobile devices
- **Incremental reindexing**: 30x faster (5s vs 159s)
- **Type filtering**: Exclude/include by frontmatter type field
- **Gleaning management**: Status tracking, URL normalization, auto-restore
- **Search history and keyboard shortcuts**: UI optimizations for mobile

---

## Key Project Principles

### 1. We Are a uv Shop
- **Always use uv** for Python dependency management
- Never suggest pip, poetry, or other tools
- Commands: `uv sync`, `uv run`, `uv add <package>`

### 2. Plan Like Waterfall, Implement in Agile
- Detailed upfront planning in documentation
- Iterative implementation with small PRs
- Each phase builds on validated previous work

### 3. Mobile-First Design
- If it doesn't work well on mobile, it doesn't work
- Target: < 2 second response time from phone
- Simple, clean UI optimized for small screens

### 4. Privacy & Local Processing
- No external APIs for search/embeddings (Synthesis is local)
- LLM calls only in Phase 4 (and user-controlled)
- Tailscale network for secure access

### 5. Avoid Over-Engineering
- Keep solutions simple and focused
- No categories, no complex state management
- Simple individual files, semantic search finds connections

### 6. No Hardcoded Paths
- **Always use relative paths** in configs and scripts
- **Never** hardcode `/Users/`, `/home/`, `/System/`, or any absolute paths
- Use `pathlib` methods like `.relative_to()`, not string manipulation
- Use `~` expansion or `$SCRIPT_DIR` patterns for portability
- **Why**: Development happens across Mac, VM, and future contributor environments

---

## Architectural Constraints

These constraints shape how Temoa is built. See [docs/CHRONICLES.md](docs/CHRONICLES.md) Entry 2 for detailed discussion.

### 1. Vault Format Agnostic
- **Optimized for**: Obsidian vault (markdown, frontmatter, wikilinks)
- **Must work with**: Plain text files in directories
- **Test**: Point at folder of .txt files → search should still work
- **Why**: Future-proof, tool-independent, Synthesis already supports this

### 2. Vector Database Storage
- **Phase 1 decision**: Store in `.temoa/` within vault
- **Must be configurable**: Allow index outside vault if needed
- **Options**: Inside vault, outside vault, user-specified path
- **Why**: Co-location is simple, but we might need flexibility later

### 3. Obsidian Sync Awareness
- **Context**: Vault syncs via Obsidian Sync (to mobile)
- **Index should NOT sync**: Too large, not useful on mobile (yet)
- **Implementation**: Document how to exclude `.temoa/` from sync
- **Flexibility**: Keep option open for mobile-side search in future

### 4. Network Model (Tailscale)
- **Deployment**: Local machine (desktop/laptop), not public internet
- **Access**: Tailscale VPN creates "fake local network"
- **Security**: Trust Tailscale network, no auth/HTTPS in Phase 1
- **Why**: Single-user, encrypted by Tailscale, avoid premature complexity

### 5. Configuration Over Convention
- **Principle**: "Don't paint ourselves into a corner"
- **Implementation**: All paths/locations in `config.json`
- **Flexibility**: Easy to change decisions as we learn
- **Example**: Index location, Synthesis path, model selection

---

## Project Structure

```
temoa/
├── README.md              # Project overview (user-facing)
├── CLAUDE.md             # This file (development guide)
├── docs/                 # Comprehensive documentation
│   ├── ARCHITECTURE.md   # System architecture & embeddings explained
│   ├── SEARCH-MECHANISMS.md  # All search algorithms & ranking methods
│   ├── IMPLEMENTATION.md # Detailed waterfall plan & progress
│   ├── CHRONICLES.md     # Design discussions & decision log
│   ├── DECISIONS.md      # Architectural decision records
│   ├── GLEANINGS.md      # Gleaning extraction & management
│   └── DEPLOYMENT.md     # Launchd service setup
├── synthesis/           # Bundled search engine (read-only)
├── src/temoa/           # Temoa source code
│   ├── server.py         # FastAPI app, endpoints, main pipeline
│   ├── synthesis.py      # Synthesis client wrapper, hybrid search
│   ├── bm25_index.py     # BM25 keyword search with tag boosting
│   ├── reranker.py       # Cross-encoder re-ranking
│   ├── query_expansion.py # TF-IDF query expansion
│   ├── time_scoring.py   # Time-aware scoring
│   ├── config.py         # Configuration management
│   ├── gleanings.py      # Gleaning extraction logic
│   ├── normalizers.py    # URL normalization
│   ├── client_cache.py   # Multi-vault LRU cache
│   ├── ui/               # Web interface
│   │   ├── search.html   # Main search UI
│   │   └── manifest.json # PWA manifest
│   └── scripts/          # CLI tools
│       ├── extract_gleanings.py   # Gleaning extraction
│       └── maintain_gleanings.py  # Link checking & maintenance
├── tests/               # Test suite
├── test-vault/          # Test data & experimental results
│   ├── BM25_TAG_BOOSTING_RESULTS.md  # Tag boosting experiments
│   └── FRONTMATTER_EXPERIMENT_RESULTS.md  # Frontmatter weighting tests
├── launchd/             # macOS service management
├── config.example.json  # Configuration template
└── pyproject.toml       # uv dependencies (includes nahuatl-frontmatter)
```

---

## Critical Context

### The Synthesis Project

**Location**: `synthesis/` (bundled with Temoa)
**Actual Location**: `.tools/synthesis/` in main Obsidian vault

**Status**: Production-ready, do NOT modify
**Purpose**: Local semantic search engine with embeddings

**Key Capabilities**:
```bash
# Semantic search with JSON output
uv run main.py search "query" --json

# Temporal analysis (interest archaeology)
uv run main.py archaeology "topic" --json

# Vault statistics
uv run main.py stats

# Model information
uv run main.py models
```

**Models Available**:
- `all-MiniLM-L6-v2` (384d, fast) - default
- `all-mpnet-base-v2` (768d, better quality)
- `all-MiniLM-L12-v2` (384d, better quality)
- `paraphrase-albert-small-v2` (768d)
- `multi-qa-mpnet-base-cos-v1` (768d, Q&A optimized)

**Current Coverage**: 1,899 vault files

**Temoa's Role**: Import Synthesis modules directly, call functions via Python API, serve via HTTP

---

## Development Phases

### Phase 0: Discovery & Validation ✅
**Goal**: Answer open questions before implementation

**Tasks**:
1. Test Synthesis performance (cold start, warm, response times)
2. Check if daily notes are indexed (where gleanings currently live)
3. Prototype subprocess call to Synthesis (measure overhead)
4. Design mobile UX (mockup, test obsidian:// URIs)
5. Extract 10-20 sample gleanings (validate end-to-end flow)

**Success Criteria**: Clear answers to architecture questions, performance validated

### Phase 1: Minimal Viable Search ✅
**Goal**: Basic semantic search working from mobile

**Deliverables**:
- FastAPI server with `/search` endpoint
- Simple HTML/JS web UI
- Deployed on local network via Tailscale
- Sub-2-second response times validated

**Success Criteria**: Can search vault from phone, results open in Obsidian

### Phase 2: Gleanings Integration
**Goal**: Gleanings surfaced via semantic search

**Deliverables**:
- Extraction script (`glean.py`) for daily notes
- Migration script for 505 historical gleanings
- Synthesis re-indexing workflow
- Automated extraction (cron or manual trigger)

**Success Criteria**: All gleanings searchable, new ones captured regularly

### Phase 3: Enhanced Features ✅
**Goal**: Improve search quality and UX based on real usage

**Completed**:
- Multi-vault support (webapp + CLI with LRU cache)
- Search quality pipeline:
  - Cross-encoder re-ranking (20-30% precision improvement)
  - Query expansion (TF-IDF for short queries)
  - Time-aware scoring (90-day half-life boost)
  - Hybrid search (BM25 + semantic with RRF)
- PWA support (installable on mobile)
- Search history (last 10 searches)
- Keyboard shortcuts (`/`, `Esc`, `t`)
- UI optimization (inline search button, compact header)
- Incremental reindexing (30x speedup)
- Type filtering and gleaning management

**Success Criteria**: Phase 3 complete, ready for Phase 4 or production hardening

### Phase 4: Vault-First LLM (Future)
**Goal**: LLMs check vault before internet

**Deliverables**:
- `/chat` endpoint with vault context
- Integration with Apantli LLM proxy
- XML context format (adopted from Copilot)
- Citation system for vault sources

**Success Criteria**: Vault-first becomes default research mode

---

## Technical Decisions

### Why FastAPI?
- Modern async Python framework
- Auto-generated OpenAPI docs
- Easy testing with pytest
- Good for calling subprocesses asynchronously
- Familiar to most Python developers

### File Size Limitations

**Current Limitation**: Embedding models have 512 token limit (~2,500 chars). Files larger than this are silently truncated - only the first ~2,500 characters are searchable.

**Chunking Support**: Approved in DEC-085, implementation tracked in [#43](https://github.com/pborenstein/temoa/issues/43)

**See**: docs/chronicles/entry-40-chunking.md for full analysis and trade-offs

### Frontmatter-Aware Search

Tags are keywords, not concepts. Temoa uses multi-layer approach:
- BM25 for exact keyword matching (tags indexed with 2x repetition)
- 5x score boost when query matches tags
- Aggressive RRF fusion tuning (1.5-2.0x) to preserve tag signals in hybrid search
- Description field: repeated 2x in BM25, prepended to content for semantic embeddings

**See**: docs/SEARCH-MECHANISMS.md and test-vault/BM25_TAG_BOOSTING_RESULTS.md for experimental validation

---

## Implementation Patterns

### Core Architecture

**Search Pipeline**: Multi-stage approach (expansion → retrieval → filtering → boost → re-rank)
- Implementation: src/temoa/server.py (search endpoint)
- 7-stage pipeline: query expansion, hybrid retrieval, score filtering, status filtering, type filtering, time boost, cross-encoder re-ranking
- All stages toggleable via query parameters
- Details: docs/SEARCH-MECHANISMS.md

**Hybrid Search**: Semantic + BM25 with RRF fusion
- Implementation: src/temoa/synthesis.py (hybrid_search method)
- Combines semantic similarity with keyword matching
- RRF (Reciprocal Rank Fusion) merges results
- Tag boosting: 5x multiplier + aggressive RRF boost (1.5-2.0x)
- Details: docs/SEARCH-MECHANISMS.md

**BM25 Tag Boosting**: Exact keyword matching for frontmatter
- Implementation: src/temoa/bm25_index.py
- Tags and descriptions repeated 2x in corpus for emphasis
- 5x score multiplier when query matches tags
- Validation: test-vault/BM25_TAG_BOOSTING_RESULTS.md

**Multi-Vault Support**: LRU cache with independent indexes
- Implementation: src/temoa/client_cache.py
- Max 3 vaults in memory (~1.5GB total)
- Per-vault indexes stored in `.temoa/model-name/`
- Fast switching: ~400ms when cached
- Details: docs/ARCHITECTURE.md

**Cross-Encoder Re-ranking**: Precision improvement for top results
- Implementation: src/temoa/reranker.py
- Model: cross-encoder/ms-marco-MiniLM-L-6-v2
- 20-30% precision improvement
- Only applied to non-tag-boosted results

### Configuration

**Multi-vault config**: See config.example.json for template
- Vault definitions with paths and defaults
- Model selection (bi-encoder, cross-encoder)
- Search parameters (limits, thresholds, boosting)
- Server settings (host, port)
- Implementation: src/temoa/config.py

### Testing

**Test structure**: See tests/ directory
- API endpoint tests: tests/test_server.py
- Search integration: tests/test_synthesis.py
- Gleaning extraction: tests/test_gleanings.py
- Run with: `uv run pytest`

### Key Implementation Principles

1. **Direct imports over subprocess**: Synthesis imported as Python module (10x faster)
2. **Lifespan pattern**: Models loaded once at startup, not per-request
3. **LRU caching**: Multi-vault support with memory-efficient cache eviction
4. **Incremental indexing**: 30x speedup by detecting unchanged files
5. **Tag-boosted marking**: Preserve tag matches through re-ranking pipeline

## Current State Summary (Phase 3 Complete)

### Completed Features

**Frontmatter-Aware Search** (NEW):
- ✅ **Tag boosting**: 5x BM25 score multiplier when query matches tags
- ✅ **Aggressive RRF boost**: 1.5-2.0x max_rrf to overcome fusion averaging
- ✅ **Tag indexing**: Tags repeated 2x in BM25 corpus for emphasis
- ✅ **Description indexing**: Repeated 2x in BM25, prepended to semantic embeddings
- ✅ **Tag-boosted marking**: Prevents downstream re-ranking from breaking tag matches
- ✅ **Experimental validation**: See test-vault/ for Phase 1 & 2 results

**Search Quality Pipeline**:
- ✅ **7-stage pipeline**: Expansion → retrieval → filtering → time-boost → re-ranking
- ✅ **Cross-encoder re-ranking**: ms-marco-MiniLM-L-6-v2 (20-30% precision improvement)
- ✅ **Query expansion**: TF-IDF pseudo-relevance feedback (<3 word queries)
- ✅ **Time-aware scoring**: Exponential decay (90-day half-life, 20% max boost)
- ✅ **Hybrid search**: BM25 + semantic with RRF fusion (default mode)
- ✅ **Type filtering**: Include/exclude by frontmatter type field
- ✅ **Status filtering**: Exclude inactive/hidden gleanings
- ✅ **Score threshold**: Min similarity filtering (semantic mode)

**Multi-Vault Support**:
- ✅ **LRU cache**: Max 3 vaults in memory (~1.5GB RAM total)
- ✅ **Independent indexes**: Each vault has `.temoa/model-name/` directory
- ✅ **Fast switching**: ~400ms when cached, ~15-20s on first load
- ✅ **Vault selector**: Dropdown in web UI
- ✅ **CLI support**: `--vault` flag for all commands
- ✅ **Validation**: Prevents index corruption from wrong vault
- ✅ **Per-vault configuration**: Filter preferences persist per vault

**UX/UI Optimizations**:
- ✅ **PWA support**: Installable on mobile (manifest.json, service worker ready)
- ✅ **Search history**: Last 10 searches with click-to-rerun (localStorage)
- ✅ **Keyboard shortcuts**: `/` focus, `Esc` clear, `t` toggle expanded
- ✅ **Collapsible results**: Default collapsed with expandable metadata
- ✅ **Inline search button**: Visible when keyboard shown on mobile
- ✅ **Management page**: Reindex, extract, gleaning maintenance
- ✅ **Dark mode**: System preference detection
- ✅ **Responsive design**: Mobile-first, tested on iOS/Android

**Performance Optimizations**:
- ✅ **Incremental reindexing**: 30x speedup (5s vs 159s for unchanged vault)
- ✅ **Direct imports**: 10x faster than subprocess (~400ms vs 2-3s)
- ✅ **FastAPI lifespan**: Models loaded once at startup, not per request
- ✅ **Parallel fetch**: Semantic + BM25 run concurrently when possible
- ✅ **Cached frontmatter**: Type/status filtering uses cached metadata (no disk I/O)

**Gleaning Management**:
- ✅ **Extraction from daily notes**: Multiple format support (markdown links, naked URLs)
- ✅ **URL normalization**: Strips tracking params, normalizes domains
- ✅ **Status tracking**: active/inactive/hidden with auto-restore
- ✅ **Link checking**: Maintenance tool detects dead links (404)
- ✅ **Description management**: Extract and update gleaning descriptions
- ✅ **Duplicate detection**: MD5 hash of URL prevents duplicates
- ✅ **Multi-line support**: Quoted descriptions, inline descriptions

### Performance Characteristics

**Search latency** (3,000 file vault):
- Semantic only: ~400ms
- Hybrid (BM25 + semantic): ~450ms
- With cross-encoder re-ranking: ~600ms
- Short query (expansion + re-ranking): ~800-1000ms
- **All well under <2s mobile target ✓**

**Memory usage**:
- Bi-encoder model (all-mpnet-base-v2): ~900MB
- Cross-encoder model (ms-marco-MiniLM): ~90MB
- BM25 index (3,000 docs): ~5MB
- Embeddings (3,000 docs, 768d): ~18MB
- **Single vault total**: ~800MB
- **Multi-vault (3 cached)**: ~1.5GB

**Reindexing** (3,059 file vault):
- Full reindex: ~159s (build all embeddings)
- Incremental (no changes): ~5s (30x faster)
- Incremental (5 new files): ~6-8s
- Incremental (50 changed files): ~15-20s

**Disk usage**:
- Embeddings (768d): ~6KB per document
- BM25 index: ~1.5KB per document
- **3,000 doc vault**: ~25MB total index size

### Next Steps

**Option A: Phase 4 - Vault-First LLM**
- `/chat` endpoint with vault context
- Integration with Apantli LLM proxy
- Citation system for vault sources

**Option B: Production Hardening**
- Error handling and edge cases
- Performance monitoring/metrics
- Backup/recovery procedures
- More comprehensive testing
- User documentation

---

## Git Workflow

### Branch Naming
All Claude development branches follow pattern: `claude/semantic-search-server-<session-id>`

### Commit Messages
- Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`
- Be descriptive about what changed and why
- Example: `feat: add /search endpoint with Synthesis integration`

### Push Requirements
- Always use: `git push -u origin <branch-name>`
- Branch must start with `claude/` and end with session ID
- Retry up to 4 times with exponential backoff on network errors

---

## Success Metrics Reminder

### Quantitative
- Response time: < 2s from mobile
- Relevance: Top 3 useful in 80%+ queries
- Coverage: All 505+ gleanings searchable
- Usage: 5+ searches per day

### Qualitative
- Vault-first habit formed (check before googling)
- Finding forgotten gleanings regularly
- Lower friction than Obsidian native search

---

## What Not to Do

### ❌ Don't Over-Engineer
- No complex categorization systems
- No state management for gleanings
- No web frameworks beyond FastAPI
- No client-side JS frameworks (React, Vue, etc.)

### ❌ Don't Modify Synthesis Core
- Synthesis is bundled read-only dependency
- We import and extend it (SynthesisClient wrapper), not modify it
- BM25, reranking, query expansion are Temoa features (not Synthesis)
- If you need to change search behavior, do it in Temoa layers

### ❌ Don't Ignore Mobile
- Every feature must work well on phone
- Test on actual mobile devices
- Keep UI simple and fast

### ❌ Don't Skip Discovery
- Phase 0 must answer all open questions
- Measure performance before optimizing
- Validate assumptions with user (pborenstein)

---

## Quick Reference Commands

### Development
```bash
# Install dependencies (includes nahuatl-frontmatter from ../nahuatl-frontmatter)
uv sync

# Run server in development mode (auto-reload, verbose logging)
./dev.sh

# Run server directly
uv run temoa server

# Run tests
uv run pytest

# Type check
uv run mypy src/
```

### CLI Commands
```bash
# Search
uv run temoa search "query" --vault amoxtli --limit 10 --hybrid

# Index vault (incremental by default)
uv run temoa index --vault amoxtli

# Force full reindex
uv run temoa index --vault amoxtli --force

# Extract gleanings from daily notes
uv run temoa extract --vault amoxtli

# Maintain gleanings (check links, update statuses)
uv run temoa gleaning maintain --vault amoxtli

# Check configuration
uv run temoa config

# List vaults
uv run temoa vaults
```

### Deployment (macOS launchd)
```bash
# Install launchd service
cd launchd && ./install.sh

# View logs
./view-logs.sh

# Uninstall service
./uninstall.sh

# Check service status
launchctl list | grep temoa
```

### Git Operations
```bash
# Create feature branch
git checkout -b claude/feature-name-<session-id>

# Commit changes (use conventional commits)
git add .
git commit -m "feat: add tag boosting to BM25 search"

# Push to remote
git push -u origin claude/feature-name-<session-id>
```

---

## Resources

### Documentation (Read These First!)
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture, embeddings explained, request flow
- **[docs/SEARCH-MECHANISMS.md](docs/SEARCH-MECHANISMS.md)** - All search algorithms, ranking, quality enhancements
- **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)** - Detailed waterfall plan & progress tracking
- **[docs/CHRONICLES.md](docs/CHRONICLES.md)** - Design discussions & decision log
- **[docs/DECISIONS.md](docs/DECISIONS.md)** - Architectural decision records (ADRs)
- [docs/GLEANINGS.md](docs/GLEANINGS.md) - Gleaning extraction & management guide
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Launchd service setup (macOS)
- [docs/DOCUMENTATION-GUIDE.md](docs/DOCUMENTATION-GUIDE.md) - How to maintain docs

### Test Results & Experiments
- [test-vault/BM25_TAG_BOOSTING_RESULTS.md](test-vault/BM25_TAG_BOOSTING_RESULTS.md) - Phase 2 tag boosting experiments
- [test-vault/FRONTMATTER_EXPERIMENT_RESULTS.md](test-vault/FRONTMATTER_EXPERIMENT_RESULTS.md) - Phase 1 semantic weighting tests

### External Links
- [uv documentation](https://github.com/astral-sh/uv) - Python package manager
- [FastAPI documentation](https://fastapi.tiangolo.com/) - Web framework
- [sentence-transformers](https://www.sbert.net/) - Semantic search models
- [rank-bm25](https://github.com/dorianbrown/rank_bm25) - BM25 implementation
- [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI) - Deep linking

---

## Session Checklist

When starting a new development session:

1. ✅ Read this CLAUDE.md file
2. ✅ Check current phase in docs/IMPLEMENTATION.md
3. ✅ Review recent design discussions in docs/CHRONICLES.md
4. ✅ Review open questions relevant to current phase
5. ✅ Check git status and ensure on correct branch
5. ✅ Run any existing tests to establish baseline
6. ✅ Communicate plan to user before major changes
7. ✅ Use TodoWrite to track work during session
8. ✅ Commit frequently with clear messages
9. ✅ Update documentation as architecture evolves

---

**Created**: 2025-11-18
**Last Major Update**: 2025-12-19 (thinned CLAUDE.md, removed duplicate content)
**For**: Claude AI development sessions
**Owner**: pborenstein
**Project**: Temoa - Vault-First Research Workflow
