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

### Why Subprocess to Synthesis?
**Alternatives considered**:
1. Import Synthesis as Python module → tight coupling, harder to maintain
2. Keep Synthesis as service → more complex deployment
3. **Subprocess call** → clean separation, leverages existing CLI ✓

**Trade-offs**:
- Overhead: ~50-100ms subprocess startup
- Isolation: Synthesis changes don't break Temoa
- Simplicity: Well-defined interface via JSON

### File Size Considerations and Chunking

**Current Limitation** (as of Phase 3):
- Embedding models have **512 token limit** (~2,000-2,500 chars)
- sentence-transformers **silently truncates** text beyond this limit
- Only first ~2,500 characters of any file are searchable
- No warning or error when truncation occurs

**Impact by content type** (daily notes excluded by default):
| Content Type | Coverage | Status |
|--------------|----------|--------|
| **Gleanings** (type=gleaning) | 100% | ✅ Fully searchable (< 500 chars) |
| **Daily notes** (type=daily) | N/A | Not indexed (excluded via `exclude_types=daily`) |
| **Other types** (story, article, writering, reference) | Varies | ⚠️ Partially searchable (depends on file size) |
| **Books** (type=story, 100KB-9MB) | < 1% | ❌ Mostly unsearchable |

**Real example** (1002 vault with Project Gutenberg books):
```
File: 3254.md (9.1MB - John Galsworthy's complete works)
Model limit: 512 tokens (~2,500 chars)
Indexed: 0.027% of content
Lost: 99.973% of content
Result: Search for "Chapter 45" → ❌ NOT FOUND (past char 2,500)
```

**Chunking Status**:
- **DEC-085**: Adaptive chunking approved for Phase 4
- **Strategy**: Chunk files >4,000 chars into 2,000-char chunks with 400-char overlap
- **Why deferred**: Current vaults (amoxtli, rodeo) work acceptably for their primary use cases (gleanings + medium notes); book library support is additive

**Workaround**: For now, be aware that searches may miss content beyond the first ~2,500 characters in large files. Full chunking support coming in Phase 4.

**See**: docs/chronicles/production-hardening.md Entry 40 for full analysis and trade-offs

### Frontmatter-Aware Search Strategy

**Problem**: Tags and metadata need special handling - they're keywords, not concepts
**Solution**: Multi-layered approach combining semantic + keyword + metadata

**Experiments conducted** (see test-vault/):
1. **Phase 1: Semantic embedding** (prepend tags to content)
   - Result: Minimal improvement (<5%)
   - Why: Semantic embeddings dilute isolated keywords in long documents

2. **Phase 2: BM25 tag boosting** (include tags in BM25 index + score multiplier)
   - Result: 100% success in BM25-only mode, ~40% in hybrid
   - Why: Exact keyword matching works, but RRF fusion weakens it

3. **Final implementation**: Aggressive tag boosting in hybrid mode
   - BM25 indexes tags (repeated 2x for emphasis)
   - 5x score multiplier when query matches tags
   - Aggressive RRF boost (1.5-2.0x max_rrf) to overcome fusion penalty
   - Mark tag-boosted results to prevent downstream re-ranking from breaking them

**Key Insight**: Tags are categorical keywords, not concepts. Keyword search (BM25) handles them correctly, but they need aggressive boosting to survive hybrid fusion with semantic search.

**Description field handling**:
- Repeated 2x in BM25 index (similar weight to tags)
- Prepended to content for semantic embeddings
- Natural positional weight gives it influence without dilution

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

### Actual File Structure (Phase 3 Complete)

```python
src/temoa/
├── __init__.py
├── __main__.py          # CLI entry point
├── __version__.py       # Version string
├── server.py            # FastAPI app, main search pipeline
├── synthesis.py         # Synthesis client, hybrid search, RRF
├── bm25_index.py        # BM25 keyword search with tag boosting
├── reranker.py          # Cross-encoder re-ranking
├── query_expansion.py   # TF-IDF query expansion
├── time_scoring.py      # Time-aware exponential decay
├── config.py            # Configuration management
├── gleanings.py         # Gleaning extraction & parsing
├── normalizers.py       # URL normalization utilities
├── client_cache.py      # Multi-vault LRU caching
├── storage.py           # Index storage management
├── cli.py               # CLI commands (search, index, extract)
├── ui/
│   ├── search.html      # Main search interface
│   ├── manage.html      # Management UI
│   ├── manifest.json    # PWA manifest
│   └── assets/          # CSS, JS, images
└── scripts/
    ├── extract_gleanings.py   # Gleaning extraction
    └── maintain_gleanings.py  # Link checking, status updates

tests/
├── test_server.py       # API endpoint tests
├── test_synthesis.py    # Synthesis integration tests
├── test_gleanings.py    # Gleaning extraction tests
└── test_config.py       # Configuration tests

config.example.json      # Template configuration
pyproject.toml           # uv dependencies + dev tools
```

### Search Pipeline Pattern (Actual Implementation)

```python
# src/temoa/server.py - Multi-stage search pipeline
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models at startup, cleanup at shutdown"""
    # Startup: Initialize synthesis client with models
    synthesis = SynthesisClient(config)
    synthesis.initialize()  # Loads bi-encoder + cross-encoder + BM25
    app.state.synthesis = synthesis
    yield
    # Shutdown: cleanup
    synthesis.cleanup()

app = FastAPI(title="Temoa", version="0.6.0", lifespan=lifespan)

@app.get("/search")
async def search(
    request: Request,
    q: str,
    vault: str = None,
    limit: int = 10,
    min_score: float = 0.3,
    hybrid: bool = True,
    rerank: bool = True,
    expand_query: bool = True,
    time_boost: bool = True,
    include_types: str = None,
    exclude_types: str = "daily"
):
    """
    Multi-stage search pipeline:
    1. Query expansion (if query < 3 words and expand_query=true)
    2. Hybrid search (semantic + BM25 with RRF) or semantic-only
    3. Score threshold filtering
    4. Status filtering (remove inactive gleanings)
    5. Type filtering (include/exclude by frontmatter type)
    6. Time-aware boost (exponential decay)
    7. Cross-encoder re-ranking (if rerank=true)
    """

    # Get synthesis client (from cache or load)
    synthesis = get_client_for_vault(vault)

    # Stage 0: Query expansion
    expanded_query = q
    if expand_query and len(q.split()) < 3:
        expanded_query = query_expander.expand(q, synthesis)

    # Stage 1: Primary retrieval
    if hybrid:
        # Hybrid: Semantic + BM25 with RRF fusion and tag boosting
        results = synthesis.hybrid_search(
            expanded_query,
            limit=limit * 5,  # Fetch more for filtering
            tag_boost=5.0
        )
    else:
        # Semantic only
        results = synthesis.search(expanded_query, limit=limit * 5)

    # Stage 2-4: Filtering
    results = filter_by_score(results, min_score) if not hybrid else results
    results = filter_inactive_gleanings(results)
    results = filter_by_type(results, include_types, exclude_types)

    # Stage 5: Time-aware boost
    if time_boost:
        results = time_scorer.apply_boost(results)

    # Stage 6: Cross-encoder re-ranking
    if rerank and not any(r.get('tag_boosted') for r in results[:20]):
        # Skip reranking if top results are tag-boosted
        results = reranker.rerank(expanded_query, results[:100])

    return {
        "query": q,
        "expanded_query": expanded_query if expanded_query != q else None,
        "results": results[:limit],
        "filtered_count": {...}  # Stats about filtering
    }
```

### BM25 Tag Boosting Pattern

```python
# src/temoa/bm25_index.py - Tag-aware BM25 search
class BM25Index:
    def build(self, documents: List[Dict]):
        """Build BM25 index with frontmatter awareness"""
        corpus = []
        for doc in documents:
            title = doc.get('title', '')
            content = doc.get('content', '')
            description = doc.get('description', '')
            tags_raw = doc.get('tags', [])

            # Include tags in indexed text (repeated for emphasis)
            tags_text = ''
            if tags_raw and isinstance(tags_raw, list):
                tag_strings = [str(tag) for tag in tags_raw]
                tags_text = ' '.join(tag_strings * 2)  # Repeat 2x

            # Description gets similar weight (repeated 2x)
            description_text = (description + ' ' + description) if description else ''

            # Build indexed text: title + tags + description + content
            text = title + ' ' + tags_text + ' ' + description_text + ' ' + content
            corpus.append(self.tokenize(text))

        self.bm25 = BM25Okapi(corpus)

    def search(self, query: str, limit: int = 10, tag_boost: float = 5.0):
        """Search with tag-aware boosting"""
        scores = self.bm25.get_scores(self.tokenize(query))

        results = []
        for idx, base_score in enumerate(scores):
            doc = self.documents[idx]
            final_score = base_score
            tags_matched = []

            # Apply tag boost if query matches tags
            if tag_boost > 1.0:
                tags = doc.get('tags', [])
                tags_lower = [str(t).lower() for t in tags]
                query_tokens = self.tokenize(query.lower())

                for query_token in query_tokens:
                    for tag in tags_lower:
                        if query_token in tag or tag in query_token:
                            tags_matched.append(tag)
                            break

                if tags_matched:
                    final_score = base_score * tag_boost  # 5x boost!

            results.append({
                **doc,
                'bm25_score': final_score,
                'bm25_base_score': base_score,
                'tags_matched': tags_matched if tags_matched else None
            })

        return sorted(results, key=lambda x: x['bm25_score'], reverse=True)[:limit]
```

### Hybrid Search with Aggressive Tag Boosting

```python
# src/temoa/synthesis.py - RRF with tag boost preservation
def hybrid_search(self, query: str, limit: int = 10, tag_boost: float = 5.0):
    """Hybrid search with aggressive tag boosting to overcome RRF averaging"""

    # Fetch from both engines (3x desired results)
    semantic_results = self.search(query, limit=limit * 3)
    bm25_results = self.bm25_index.search(query, limit=limit * 3, tag_boost=tag_boost)

    # Merge with RRF (Reciprocal Rank Fusion)
    merged_results = self._merge_with_rrf(semantic_results, bm25_results)

    # CRITICAL: Aggressive boost for tag-matched results
    # RRF averages ranks and can bury perfect BM25 tag matches
    max_rrf = max((r.get('rrf_score', 0) for r in merged_results), default=0.1)

    for result in merged_results:
        tags_matched = result.get('tags_matched')
        bm25_score = result.get('bm25_score', 0)

        if tags_matched and bm25_score > 0:
            # AGGRESSIVE: Tag-matched results get 1.5x to 2.0x max_rrf
            max_bm25 = max((r.get('bm25_score', 0) for r in bm25_results), default=1.0)
            score_ratio = bm25_score / max_bm25
            boost_multiplier = 1.5 + (0.5 * score_ratio)  # 1.5x to 2.0x

            artificial_rrf = max_rrf * boost_multiplier
            result['rrf_score'] = artificial_rrf
            result['tag_boosted'] = True  # Mark to prevent downstream re-ranking

    # Re-sort by boosted RRF scores
    merged_results.sort(key=lambda x: x.get('rrf_score', 0), reverse=True)

    return merged_results[:limit]
```

### Configuration Format (Multi-Vault)

```json
{
  "vaults": [
    {
      "name": "amoxtli",
      "path": "~/Obsidian/amoxtli",
      "is_default": true
    },
    {
      "name": "work",
      "path": "~/Obsidian/work-vault",
      "is_default": false
    }
  ],
  "model": {
    "bi_encoder": "all-mpnet-base-v2",
    "cross_encoder": "cross-encoder/ms-marco-MiniLM-L-6-v2"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "hybrid_search_enabled": true,
    "rerank_enabled": true,
    "query_expansion_enabled": true,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  },
  "bm25": {
    "tag_boost": 5.0
  },
  "cache": {
    "max_vaults": 3
  }
}
```

**Configuration notes**:
- **Multi-vault**: Each vault gets independent index in `vault/.temoa/model-name/`
- **LRU cache**: Max 3 vaults in memory (~1.5GB RAM), fast switching
- **Index storage**: Always in `.temoa/` within vault (co-location)
- **All paths support `~` expansion**
- **Tag boost**: Default 5x multiplier for tag matches (configurable)
- See docs/ARCHITECTURE.md and docs/DECISIONS.md for rationale

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

## Key Architectural Insights for Future Development

### Understanding Frontmatter-Aware Search

The frontmatter-aware search implementation represents a critical architectural insight: **metadata requires multi-layered handling**.

**The Problem**: Tags like `[python, tool, obsidian]` are categorical keywords, not semantic concepts. They need different handling than body text.

**Failed Approach (Phase 1)**: Prepending tags to semantic embeddings
- Result: <5% improvement
- Why: Semantic models measure conceptual similarity, not keyword presence
- Isolated keywords get diluted in 1000+ character documents

**Successful Approach (Phase 2-3)**: Multi-layer strategy
1. **BM25 layer**: Index tags + description (repeated for emphasis)
2. **Tag boosting**: 5x score multiplier for exact tag matches
3. **RRF fusion**: Combine semantic (concepts) + BM25 (keywords)
4. **Aggressive boosting**: 1.5-2.0x max_rrf to overcome fusion averaging
5. **Tag-boosted marking**: Prevent downstream re-ranking from breaking tag matches

**Key Insight**: Don't fight the algorithms - use each for what it does well:
- Semantic search: Conceptual similarity, exploratory queries
- BM25: Exact keywords, proper nouns, categorical queries
- Hybrid: Best of both, with aggressive tuning to preserve tag signals

**Validation**: See test-vault/ for experimental results showing 100% tag match success in BM25-only mode, and how RRF fusion complicates this (requiring aggressive boosting).

### The Seven-Stage Pipeline Philosophy

Temoa's search pipeline is intentionally multi-stage, not monolithic:

```
Stage 0: Enhancement  (optional, <3 word queries)
Stage 1: Retrieval    (semantic + BM25, parallel)
Stage 2: Filtering    (score threshold, semantic only)
Stage 3: Status       (remove inactive gleanings)
Stage 4: Type         (frontmatter-based inclusion/exclusion)
Stage 5: Time Boost   (exponential decay, recency matters)
Stage 6: Re-ranking   (cross-encoder precision, expensive)
```

**Why not one model?**: Each stage solves a different problem:
- Retrieval: High recall (don't miss anything)
- Filtering: Noise reduction (remove unwanted)
- Boosting: Relevance tuning (recency, tags)
- Re-ranking: Precision (correct order)

**Toggleable**: Each stage can be enabled/disabled via query params, allowing A/B testing and user preference.

**Measured**: Each stage has measured impact (see docs/SEARCH-MECHANISMS.md for details).

### When to Add vs Extend

**Add a new stage** when:
- The feature is orthogonal to existing stages
- Users might want to disable it
- It has measurable impact you can validate
- Example: Time-aware scoring (separate concern from similarity)

**Extend existing stage** when:
- The feature enhances existing logic
- Disabling it would break the stage
- It's an implementation detail, not user-facing
- Example: Tag boosting within BM25 (not separate stage)

**Don't add** when:
- The feature is too coupled to be measured independently
- It optimizes an already-solved problem without measurable gain
- It adds latency without proportional quality improvement

This architecture enables **continuous improvement through experimentation** while maintaining **production stability** through toggleable features.

---

**Created**: 2025-11-18
**Last Major Update**: 2025-12-15 (frontmatter-aware search documentation)
**For**: Claude AI development sessions
**Owner**: pborenstein
**Project**: Temoa - Vault-First Research Workflow
