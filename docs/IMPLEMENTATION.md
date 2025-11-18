# IMPLEMENTATION.md - Temoa Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document tracks progress across all implementation phases. Detailed phase plans are in `docs/phases/`.

**Project**: Temoa - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 0 ✅ COMPLETE | Phase 1 READY TO START
**Last Updated**: 2025-11-18
**Estimated Timeline**: 4-6 weeks for Phases 0-2, ongoing for Phases 3-4

---

## Phase Overview

| Phase | Status | Duration | Dependencies |
|-------|--------|----------|--------------|
| [Phase 0: Discovery & Validation](phases/phase-0-discovery.md) | ✅ **COMPLETE** | 1 day | None |
| [Phase 1: Minimal Viable Search](phases/phase-1-mvp.md) | 🔵 **READY TO START** | 2-3 days | Phase 0 ✅ |
| [Phase 2: Gleanings Integration](phases/phase-2-gleanings.md) | ⚪ Not Started | 3-4 days | Phase 1 |
| [Phase 3: Enhanced Features](phases/phase-3-enhanced.md) | ⚪ Not Started | 5-7 days | Phase 2 |
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

## Phase 1: Minimal Viable Search 🔵

**Status**: READY TO START
**Goal**: Build FastAPI server that wraps Synthesis with direct imports for fast search
**Duration**: 2-3 days

### Architecture (based on Phase 0 findings)

- FastAPI server imports Synthesis code directly (NOT subprocess)
- Model loaded ONCE at startup (~10-15s)
- Each search: direct function call (~400ms)
- Simple HTML UI for mobile testing
- Target: < 500ms response time

### Tasks Overview

- [ ] 1.1: Project Setup
- [ ] 1.2: Configuration Management
- [ ] 1.3: Synthesis Direct Import Wrapper
- [ ] 1.4: FastAPI Server
- [ ] 1.5: Mobile Web UI
- [ ] 1.6: Basic Testing
- [ ] 1.7: Documentation

### Deliverables

- [ ] Working FastAPI server (`src/temoa/server.py`)
- [ ] Configuration system (`src/temoa/config.py`)
- [ ] Synthesis wrapper (`src/temoa/synthesis.py`)
- [ ] Mobile web UI (`src/temoa/ui/search.html`)
- [ ] Basic test suite (`tests/`)
- [ ] Project documentation (README, API docs)
- [ ] `pyproject.toml` with dependencies

### Success Criteria

- [ ] Server runs and is accessible from mobile
- [ ] Search works end-to-end (query → Synthesis → results)
- [ ] Results open in Obsidian mobile app
- [ ] Response time < 2 seconds from mobile
- [ ] Basic tests pass
- [ ] Code is clean and documented

### Detailed Plan

See [phases/phase-1-mvp.md](phases/phase-1-mvp.md)

---

## Phase 2: Gleanings Integration ⚪

**Status**: Not Started
**Goal**: Make gleanings searchable via semantic search
**Duration**: 3-4 days

### Tasks Overview

- [ ] 2.1: Gleanings Extraction Script
- [ ] 2.2: Historical Gleanings Migration
- [ ] 2.3: Synthesis Re-indexing
- [ ] 2.4: Automated Extraction

### Deliverables

- [ ] `scripts/extract_gleanings.py` - Gleaning extraction
- [ ] `scripts/migrate_old_gleanings.py` - Historical migration
- [ ] `L/Gleanings/` - All gleanings as individual notes
- [ ] Automation setup (cron/systemd)
- [ ] Documentation in `docs/GLEANINGS.md`

### Success Criteria

- [ ] All 505+ gleanings are searchable
- [ ] New gleanings extracted regularly
- [ ] Search finds gleanings with good relevance
- [ ] Extraction is automated

### Detailed Plan

See [phases/phase-2-gleanings.md](phases/phase-2-gleanings.md)

---

## Phase 3: Enhanced Features ⚪

**Status**: Not Started
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
