# CLAUDE.md - Development Guide for Temoa

> **Purpose**: This document provides context and guidance for Claude AI when working on the Temoa project across multiple sessions.

**Last Updated**: 2025-12-03
**Project Status**: Phase 3 Complete ✅
**Current Version**: 0.6.0
**Current Branch**: `main`

---

## Project Overview

**Temoa** is a local semantic search server for Obsidian vaults, enabling vault-first research workflows. It wraps the **Synthesis** semantic search engine with an HTTP API and mobile-friendly interface.

**Problem Solved**: Saved links and notes accumulate but never resurface when needed during research. Temoa makes your vault the first place to check before external search.

**Core Architecture**: FastAPI server → Direct Synthesis imports → Multi-stage search pipeline → Results

**Current Features** (Phase 3 Complete):
- Multi-vault support with LRU caching
- Search quality pipeline (query expansion, cross-encoder re-ranking, time-aware scoring)
- PWA support (installable on mobile)
- Incremental reindexing (30x faster)
- Type filtering and gleaning management
- Search history and keyboard shortcuts

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
├── docs/                 # Planning documents
│   ├── IMPLEMENTATION.md # Detailed waterfall plan
│   ├── CHRONICLES.md     # Design discussions & decision log
│   ├── IXPANTILIA.md    # Original 847-line plan
│   └── copilot-learnings.md  # Obsidian Copilot analysis
├── synthesis/           # Production search engine (DO NOT MODIFY)
├── src/                 # Temoa source code
├── scripts/             # Extraction and maintenance scripts
├── tests/               # Test suite
├── config.example.json  # Configuration template
└── pyproject.toml       # uv dependencies
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

### Why Subprocess to Synthesis?
**Alternatives considered**:
1. Import Synthesis as Python module → tight coupling, harder to maintain
2. Keep Synthesis as service → more complex deployment
3. **Subprocess call** → clean separation, leverages existing CLI ✓

**Trade-offs**:
- Overhead: ~50-100ms subprocess startup
- Isolation: Synthesis changes don't break Temoa
- Simplicity: Well-defined interface via JSON

### Why Not Chunking?
**Obsidian Copilot uses 6000-char chunks**, but Temoa doesn't need this because:
- Gleanings are small (< 500 chars typically)
- Already atomic units (one link per note)
- Synthesis handles short documents well
- Reduces implementation complexity

**Re-evaluate if**: Gleanings grow to include long summaries/notes

### Why No Caching Initially?
- Synthesis may already be fast (measure first!)
- Server has more RAM than mobile (less constrained)
- Avoid cache invalidation complexity
- Easier to debug without caching layer

**Add caching if**: Search takes > 500ms consistently, same queries repeat often

### Where Should Temoa Live?
**Options**:
1. Integrate into Apantli (LLM proxy) → single service, mixed concerns
2. Separate service → clean separation, can be called by Apantli
3. Inside vault like Synthesis → co-located with data

**Recommendation**: Start separate, integrate with Apantli in Phase 4 if needed

---

## Implementation Guidelines

### File Structure for Implementation

```python
# Planned structure (to be created)

src/
├── __init__.py
├── server.py           # FastAPI app, endpoints
├── synthesis.py        # Synthesis subprocess wrapper
├── config.py           # Configuration management
└── ui/
    └── search.html     # Mobile web UI

tests/
├── test_server.py      # API endpoint tests
├── test_synthesis.py   # Synthesis integration tests
└── test_ui.py          # UI rendering tests

config.example.json     # Template configuration
pyproject.toml          # uv dependencies
```

### Server Implementation Pattern

```python
# src/server.py (skeleton)
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import subprocess
import json
from pathlib import Path

app = FastAPI(title="Temoa", version="0.1.0")

SYNTHESIS_PATH = Path("~/.obsidian/vaults/main/.tools/synthesis").expanduser()

@app.get("/search")
async def search_vault(q: str, limit: int = 10, model: str = None):
    """Semantic search via Synthesis"""

    # Build command
    cmd = ["uv", "run", "main.py", "search", q, "--json"]
    if model:
        cmd.extend(["--model", model])

    # Run Synthesis (subprocess)
    result = subprocess.run(
        cmd,
        cwd=SYNTHESIS_PATH,
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        return {"error": "Search failed", "stderr": result.stderr}

    # Parse JSON output
    data = json.loads(result.stdout)

    return {
        "query": q,
        "results": data["results"][:limit],
        "total": len(data["results"]),
        "model": model or "default"
    }

@app.get("/")
async def index():
    """Serve search UI"""
    return HTMLResponse(SEARCH_UI_HTML)
```

### Configuration Format

```json
{
  "vault_path": "~/Obsidian/amoxtli",
  "synthesis_path": "~/.obsidian/vaults/main/.tools/synthesis",
  "index_path": null,
  "default_model": "all-MiniLM-L6-v2",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 50
  }
}
```

**Configuration notes**:
- `index_path`: If `null`, defaults to `.temoa/` inside vault. Can override to store index elsewhere.
- All paths support `~` expansion
- See docs/CHRONICLES.md Entry 2 for architectural rationale

### Testing Approach

```python
# tests/test_server.py
import pytest
from fastapi.testclient import TestClient
from src.server import app

client = TestClient(app)

def test_search_endpoint():
    response = client.get("/search?q=semantic+search")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "query" in data

def test_search_with_limit():
    response = client.get("/search?q=AI&limit=5")
    data = response.json()
    assert len(data["results"]) <= 5
```

### UI Implementation (Simple HTML)

```html
<!-- src/ui/search.html -->
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Temoa - Vault Search</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      max-width: 800px;
      margin: 0 auto;
      padding: 20px;
      background: #fafafa;
    }
    input {
      width: 100%;
      padding: 12px;
      font-size: 16px;
      border: 2px solid #ddd;
      border-radius: 8px;
    }
    button {
      width: 100%;
      padding: 12px;
      margin-top: 10px;
      font-size: 16px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 8px;
    }
    .result {
      background: white;
      border: 1px solid #ddd;
      padding: 15px;
      margin: 10px 0;
      border-radius: 8px;
    }
    .score {
      color: #666;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <h1>🔍 Temoa</h1>
  <input id="query" type="text" placeholder="Search your vault..." autofocus />
  <button onclick="search()">Search</button>
  <div id="results"></div>

  <script>
    async function search() {
      const q = document.getElementById('query').value;
      if (!q) return;

      const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();

      const html = data.results.map(r => `
        <div class="result">
          <h3><a href="${r.obsidian_uri}">${r.title}</a></h3>
          <div class="score">Similarity: ${r.similarity_score.toFixed(3)}</div>
          <div style="color: #888; font-size: 0.9em">${r.relative_path}</div>
        </div>
      `).join('');

      document.getElementById('results').innerHTML = html || '<p>No results found</p>';
    }

    document.getElementById('query').addEventListener('keypress', e => {
      if (e.key === 'Enter') search();
    });
  </script>
</body>
</html>
```

---

## Common Patterns from Copilot Analysis

### XML Context Format for LLMs (Phase 4)

```python
def format_for_llm(results):
    """Format search results for LLM context (Copilot pattern)"""
    docs = []
    for r in results:
        doc = f"""<retrieved_document>
<title>{r['title']}</title>
<path>{r['relative_path']}</path>
<similarity>{r['similarity_score']:.3f}</similarity>
<content>
{r.get('content', '')}
</content>
</retrieved_document>"""
        docs.append(doc)

    return "\n\n".join(docs)
```

### Grep-First Recall (If Needed for Performance)

```python
import subprocess
from pathlib import Path

def grep_filter(query: str, vault_path: Path) -> list[Path]:
    """Fast grep to filter candidate files before Synthesis (Copilot pattern)"""
    keywords = query.lower().split()
    grep_pattern = "|".join(keywords)

    result = subprocess.run(
        ["grep", "-ril", "-E", grep_pattern, str(vault_path)],
        capture_output=True,
        text=True
    )

    paths = [Path(p) for p in result.stdout.strip().split("\n") if p]
    return paths[:200]  # Limit like Copilot
```

---

## Current State Summary (Phase 3 Complete)

### Completed Features

**Search Quality**:
- ✅ Multi-stage pipeline (expansion → retrieval → filtering → time-boost → re-ranking)
- ✅ Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2)
- ✅ Query expansion (TF-IDF, <3 words)
- ✅ Time-aware scoring (exponential decay, 90-day half-life)
- ✅ Hybrid search (BM25 + semantic with RRF fusion)
- ✅ Type filtering (exclude/include by document type)

**Multi-Vault**:
- ✅ LRU cache (max 3 vaults, ~1.5GB RAM)
- ✅ Independent indexes per vault (vault/.temoa/)
- ✅ Vault selector in web UI
- ✅ `--vault` CLI flag for all commands
- ✅ Validation to prevent data loss

**UX/UI**:
- ✅ PWA support (installable on mobile)
- ✅ Search history (last 10 searches, localStorage)
- ✅ Keyboard shortcuts (`/` focus, `Esc` clear, `t` toggle expanded)
- ✅ Compact collapsible results (default collapsed)
- ✅ Inline search button (visible with keyboard up)
- ✅ Management page (reindex, extract controls)

**Performance**:
- ✅ Incremental reindexing (30x speedup: 5s vs 159s)
- ✅ Direct imports (not subprocess, 10x faster)
- ✅ Search: ~400-1000ms depending on options
- ✅ FastAPI lifespan pattern (proper initialization)

**Gleanings**:
- ✅ Extraction from daily notes (multiple formats)
- ✅ Status management (active/inactive/hidden)
- ✅ Auto-restore for dead links that come back
- ✅ Maintenance tools (link checking, descriptions)

### Performance Characteristics

**Search latency** (3,000 file vault):
- Semantic: ~400ms
- Hybrid: ~450ms
- With re-ranking: ~600ms
- Short query with expansion + re-ranking: ~800-1000ms

**Memory**:
- Single vault: ~800 MB (bi-encoder + cross-encoder)
- Multi-vault (3 cached): ~1.5 GB

**Reindexing** (3,059 file vault):
- Full: ~159s
- Incremental (no changes): ~5s (30x faster)
- Incremental (5 new files): ~6-8s

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

### ❌ Don't Modify Synthesis
- It's production-ready and working
- Treat as external dependency
- Interface via subprocess + JSON only

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
# Install dependencies
uv sync

# Run server (when implemented)
uv run src/server.py

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Type check
uv run mypy src/
```

### Test Synthesis Directly
```bash
cd synthesis/
uv run main.py search "semantic search" --json
uv run main.py archaeology "AI" --json
uv run main.py stats
uv run main.py models
```

### Git Operations
```bash
# Create feature branch
git checkout -b claude/semantic-search-server-<session-id>

# Commit changes
git add .
git commit -m "feat: add search endpoint"

# Push to remote
git push -u origin claude/semantic-search-server-<session-id>
```

---

## Resources

### Documentation
- [docs/IXPANTILIA.md](docs/IXPANTILIA.md) - Original plan (847 lines)
- [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) - Detailed waterfall plan
- [docs/CHRONICLES.md](docs/CHRONICLES.md) - Design discussions & decision log
- [docs/copilot-learnings.md](docs/copilot-learnings.md) - Obsidian Copilot analysis (1119 lines)
- [synthesis/CLAUDE.md](synthesis/CLAUDE.md) - Synthesis project guide

### External Links
- [uv documentation](https://github.com/astral-sh/uv)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [sentence-transformers](https://www.sbert.net/)
- [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)

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
**For**: Claude AI development sessions
**Owner**: pborenstein
**Project**: Temoa - Vault-First Research Workflow
