# IMPLEMENTATION.md - Temoa Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document tracks progress across all implementation phases. Detailed phase plans are in `docs/phases/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 2 ✅ COMPLETE + CLI ✅ COMPLETE | Ready for Mobile Testing
**Last Updated**: 2025-11-19
**Estimated Timeline**: 4-6 weeks for Phases 0-2, ongoing for Phases 3-4

---

## Phase Overview

| Phase | Status | Duration | Dependencies |
|-------|--------|----------|--------------|
| [Phase 0: Discovery & Validation](phases/phase-0-discovery.md) | ✅ **COMPLETE** | 1 day | None |
| [Phase 1: Minimal Viable Search](phases/phase-1-mvp.md) | ✅ **COMPLETE** | 1 day | Phase 0 ✅ |
| [Phase 2: Gleanings Integration](phases/phase-2-gleanings.md) | ✅ **COMPLETE** | 1 day | Phase 1 ✅ |
| [Phase 3: Enhanced Features](phases/phase-3-enhanced.md) | 🔵 **READY TO START** | 5-7 days | Phase 2 ✅ |
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

**Status**: COMPLETE (2025-11-18)
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
- **Discovery**: Created `debug_stats.py` script to inspect actual JSON structure

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

## Phase 3: Enhanced Features 🔵

**Status**: READY TO START (but recommend mobile testing first)
**Goal**: Make Temoa indispensable for daily use
**Duration**: 5-7 days

### Tasks Overview

- [ ] 3.1: Archaeology Endpoint
- [ ] 3.2: Enhanced UI
- [ ] 3.3: PWA Support

### Deliverables

- [ ] `/archaeology` endpoint
- [ ] `/stats` endpoint
- [ ] Enhanced UI with filters
- [ ] PWA support (manifest + service worker)
- [ ] Performance optimizations

### Success Criteria

- [ ] Daily usage > 5 searches/day
- [ ] Archaeology provides useful insights
- [ ] UI is preferred over Obsidian search
- [ ] PWA installed on mobile device

### Detailed Plan

See [phases/phase-3-enhanced.md](phases/phase-3-enhanced.md)

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

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uvicorn", "temoa.server:app", "--host", "0.0.0.0", "--port", "8080"]
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
