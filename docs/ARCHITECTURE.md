# ARCHITECTURE.md - Temoa System Architecture

> **Purpose**: This document explains the technical architecture of Temoa, how components interact, and how semantic search with embeddings works.

**Created**: 2025-11-22
**Last Updated**: 2026-01-26
**Status**: Phase 3.6 Complete (Experimentation Tools: Search Harness, Pipeline Viewer, Inspector, VaultGraph)

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [How Embeddings Work](#how-embeddings-work)
3. [Adaptive Chunking](#adaptive-chunking)
4. [Experimentation Tools](#experimentation-tools-phase-36)
5. [Multi-Vault Support](#multi-vault-support)
6. [Request Flow](#request-flow)
8. [Storage Architecture](#storage-architecture)
9. [Component Details](#component-details)
10. [Error Handling Philosophy](#error-handling-philosophy)
11. [Security Architecture](#security-architecture)
12. [Deployment Model](#deployment-model)
13. [Performance Characteristics](#performance-characteristics)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Mobile Device                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Web Browser (Safari, Chrome, etc.)               │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │         Temoa Web UI (search.html)                 │  │   │
│  │  │  - Search input                                    │  │   │
│  │  │  - Results display                                 │  │   │
│  │  │  - obsidian:// links                               │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ HTTP over Tailscale VPN          │
│                              │ (encrypted tunnel)               │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Local Machine (Desktop/Laptop)               │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Temoa FastAPI Server                         │  │
│  │                   (port 8080)                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Endpoints:                                         │  │  │
│  │  │  - GET  /search                                     │  │  │
│  │  │  - GET  /archaeology (temporal analysis)            │  │  │
│  │  │  - GET  /stats                                      │  │  │
│  │  │  - POST /reindex                                    │  │  │
│  │  │  - POST /extract (gleanings)                        │  │  │
│  │  │  - GET  /health                                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                          │                                │  │
│  │                          ▼                                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │       SynthesisClient (wrapper)                     │  │  │
│  │  │  - Direct Python imports (not subprocess)           │  │  │
│  │  │  - One-time model loading at startup                │  │  │
│  │  │  - Caches loaded model in memory                    │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Synthesis Engine                             │  │
│  │              (synthesis/)                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Core Components:                                   │  │  │
│  │  │  1. sentence-transformers (HuggingFace)             │  │  │
│  │  │  2. sklearn (cosine similarity)                     │  │  │
│  │  │  3. pickle (embedding storage)                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Obsidian Vault                               │  │
│  │          (~/Obsidian/vault-name/)                         │  │
│  │                                                           │  │
│  │  ├── Daily/                 (daily notes)                 │  │
│  │  ├── Journal/               (journal entries)             │  │
│  │  ├── L/                                                   │  │
│  │  │   └── Gleanings/         (extracted gleanings)         │  │
│  │  └── .temoa/                (Temoa data)                  │  │
│  │      ├── embeddings.pkl     (vector index)                │  │
│  │      ├── config.json        (local config)                │  │
│  │      └── extraction_state.json  (gleaning tracking)       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Principles:**

1. **Mobile-First**: The entire architecture optimizes for fast mobile access
2. **Local Processing**: All embeddings and search happen locally (no cloud APIs)
3. **Privacy**: No data leaves your network (Tailscale encrypts everything)
4. **Simplicity**: Direct imports, minimal layers, straightforward data flow

---

## How Embeddings Work

### What Are Embeddings?

**Embeddings** convert text into high-dimensional vectors (lists of numbers) that capture semantic meaning. Similar texts have similar vectors, enabling semantic search.

```
Traditional Keyword Search:
┌─────────────────────────────────────────────────────────────┐
│  Query: "machine learning"                                  │
│  Matches: Documents containing exact words "machine" AND    │
│           "learning"                                        │
│  Misses:  "neural networks", "deep learning", "AI models"   │
└─────────────────────────────────────────────────────────────┘

Semantic Search with Embeddings:
┌─────────────────────────────────────────────────────────────┐
│  Query: "machine learning"                                  │
│  Embedding: [0.42, -0.13, 0.87, ..., 0.21]  (384 numbers)   │
│  Finds:  "neural networks"    (similar vector)              │
│          "deep learning"      (similar vector)              │
│          "AI models"          (similar vector)              │
│          "supervised training" (similar vector)             │
└─────────────────────────────────────────────────────────────┘
```

### The Embedding Process

```
┌──────────────────────────────────────────────────────────────────┐
│                     INDEXING (One-time)                          │
└──────────────────────────────────────────────────────────────────┘

1. Read Vault Files
   ┌─────────────────────────────────────────────────────────┐
   │  File: "Daily/2025-11-22.md"                            │
   │  Content: "Today I learned about semantic search..."    │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
2. Load Transformer Model (sentence-transformers)
   ┌─────────────────────────────────────────────────────────┐
   │  Model: all-MiniLM-L6-v2 (or other)                     │
   │  Size: ~80MB                                            │
   │  Output: 384-dimensional vectors                        │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
3. Generate Embeddings
   ┌─────────────────────────────────────────────────────────┐
   │  Text → Tokenize → Neural Network → Vector              │
   │                                                         │
   │  "semantic search" → [0.42, -0.13, 0.87, ..., 0.21]     │
   │                       ↑                                 │
   │                  384 numbers                            │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
4. Store in Index
   ┌─────────────────────────────────────────────────────────┐
   │  File: .temoa/embeddings.pkl                            │
   │  Format: {                                              │
   │    "file_path": "Daily/2025-11-22.md",                  │
   │    "embedding": [0.42, -0.13, ..., 0.21],               │
   │    "metadata": {...}                                    │
   │  }                                                      │
   └─────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   SEARCHING (Per Query)                          │
└──────────────────────────────────────────────────────────────────┘

1. User Query
   ┌─────────────────────────────────────────────────────────┐
   │  Query: "obsidian plugins"                              │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
2. Generate Query Embedding (same model)
   ┌─────────────────────────────────────────────────────────┐
   │  "obsidian plugins" → [0.18, 0.56, -0.23, ..., 0.44]    │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
3. Compare with All Document Embeddings (cosine similarity)
   ┌─────────────────────────────────────────────────────────┐
   │  Query:    [0.18, 0.56, -0.23, ..., 0.44]               │
   │  Doc 1:    [0.21, 0.53, -0.19, ..., 0.47] → 0.92 ✓      │
   │  Doc 2:    [0.89, -0.12, 0.67, ..., 0.03] → 0.34        │
   │  Doc 3:    [0.15, 0.61, -0.28, ..., 0.51] → 0.95 ✓✓     │
   │            ↑                                            │
   │       Similarity scores (0-1)                           │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
4. Rank and Return Top Results
   ┌─────────────────────────────────────────────────────────┐
   │  Results:                                               │
   │  1. Doc 3: 0.95 similarity  "Plugin Development Guide"  │
   │  2. Doc 1: 0.92 similarity  "Using Dataview Plugin"     │
   │  3. ...                                                 │
   └─────────────────────────────────────────────────────────┘
```

### Cosine Similarity Explained

Cosine similarity measures the angle between two vectors. Closer angle = more similar meaning.

```
Vector Space (simplified to 2D):

        ▲
        │         ● Query: "obsidian"
        │       ╱
        │     ╱ 15° (high similarity = 0.97)
        │   ╱
        │ ● Doc1: "note-taking app"
        │
        │
        │
        │              ● Doc2: "cooking recipes"
        │                85° (low similarity = 0.09)
        │
        └────────────────────────────────────────────▶

Cosine Similarity Formula:
similarity = cos(θ) = (A · B) / (||A|| × ||B||)

Where:
- A, B are vectors (embeddings)
- · is dot product
- ||A|| is vector magnitude
- Result: 1.0 = identical, 0.0 = unrelated, -1.0 = opposite
```

### Why This Works

1. **Semantic Understanding**: The transformer model learned from billions of text examples
2. **Context Awareness**: "bank" (river) vs "bank" (finance) get different embeddings
3. **Language Agnostic**: Works across topics, writing styles, and domains
4. **No Training Needed**: Pre-trained models work out of the box

### Model Options in Temoa

| Model                        | Dimensions | Speed  | Quality | Use Case                     |
| ---------------------------- | ---------- | ------ | ------- | ---------------------------- |
| `all-MiniLM-L6-v2`           | 384        | Fast   | Good    | Default (fast mobile search) |
| `all-MiniLM-L12-v2`          | 384        | Medium | Better  | More nuanced search          |
| `all-mpnet-base-v2`          | 768        | Slower | Best    | Highest quality results      |
| `multi-qa-mpnet-base-cos-v1` | 768        | Slower | Best    | Optimized for Q&A            |

**Current Default**: `all-MiniLM-L6-v2` (good balance for mobile use)

### Token Limits

**Important**: All sentence-transformer models have maximum sequence lengths (typically 512 tokens ≈ 2,500 characters).

| Model | Max Tokens | Max Chars (approx) |
|-------|------------|--------------------|
| `all-mpnet-base-v2` | 512 | ~2,000-2,500 |
| `all-MiniLM-L6-v2` (default) | 512 | ~2,000-2,500 |
| `all-MiniLM-L12-v2` | 512 | ~2,000-2,500 |
| `paraphrase-albert-small-v2` | 100 | ~400 |

**Solution**: Temoa uses adaptive chunking for large files (see [Adaptive Chunking](#adaptive-chunking) section above), ensuring 100% content searchability regardless of file size.

---

## Adaptive Chunking

**Status**: IMPLEMENTED (Phase 3.5.2, December 2025)

Adaptive chunking solves the 512-token embedding limit by splitting large files into overlapping chunks, ensuring full content searchability.

**The Problem:**

All embedding models have token limits (typically 512 tokens ≈ 2,500 characters). Before chunking:
- Files >2,500 chars: Only first 2,500 chars searchable
- 9MB book: 0.027% coverage (99.973% missed)
- Matches after char 2,500: ❌ NOT FOUND

**The Solution:**

Files ≥ 4,000 characters are automatically split:
- **Chunk size**: 2,000 characters
- **Overlap**: 400 characters (prevents boundary misses)
- **Deduplication**: Best-scoring chunk per file (prevents duplicate results)
- **Sliding window**: Full content coverage

**Impact:**

```
Before Chunking:
  2,006 files → 2,006 searchable items (35% content coverage)

After Chunking:
  2,006 files → 8,755 searchable chunks (100% content coverage)

Search latency: No change (400ms - deduplication removes duplicates)
Index size: +3-4x (acceptable - disk space is cheap)
Indexing time: +2.5-3x (acceptable - indexing is infrequent)
```

**Configuration:**

```json
{
  "enable_chunking": true,
  "chunk_size": 2000,
  "chunk_overlap": 400,
  "chunk_threshold": 4000
}
```

CLI flag:
```bash
temoa index --enable-chunking
```

**See**: [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md#adaptive-chunking) for technical implementation details.

---

## Experimentation Tools (Phase 3.6)

**Status**: IMPLEMENTED (January 2026)

Temoa includes interactive tools for experimenting with search parameters, visualizing the search pipeline, and exploring document relationships. These tools are integrated into the main search interface.

### Search Harness (Client-Side Score Remixing)

The search harness enables real-time experimentation with search weights without server round-trips.

**Architecture Innovation**: Two-tier parameter model

```
┌─────────────────────────────────────────────────────────────┐
│ Server-Side Parameters (Require Re-fetch)                   │
│ - Hybrid weight (semantic vs BM25 balance)                  │
│ - Result limit (top-K selection)                            │
│ - Cross-encoder re-ranking (enable/disable)                 │
│ - Query expansion (enable/disable)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ Single API call
┌─────────────────────────────────────────────────────────────┐
│ Server Returns Raw Component Scores                         │
│ {                                                            │
│   "scores": {                                                │
│     "semantic": 0.85,        // Bi-encoder similarity        │
│     "bm25": 0.42,            // BM25 keyword score           │
│     "rrf": 0.63,             // Fused score                  │
│     "cross_encoder": 4.52,   // Re-ranking score             │
│     "time_boost": 1.15       // Temporal boost multiplier    │
│   }                                                          │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Client-Side Remix Parameters (Instant Re-sort)              │
│ - Mix balance (adjust semantic vs BM25 weight)              │
│ - Tag multiplier (boost tag-matched results)                │
│ - Time weight (emphasize recent documents)                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- **Instant feedback**: Adjust weights and see results re-sort in <50ms
- **Visual indicators**: Tag matches glow green, time-boosted dates glow purple
- **Parameter tracking**: Yellow border shows when server-side params changed

**API Integration**:
```
GET /search?q=query&harness=true
→ Returns result.scores object with all component scores
→ Returns harness.mix and harness.server metadata
→ Client remixes: final = (semantic × w_sem + bm25 × w_bm25) × tag_mult × time_mult
```

**Implementation**: `src/temoa/server.py` (harness parameter), `src/temoa/ui/search.html` (Explorer view)

### Pipeline Viewer (Stage-by-Stage Debugging)

Visualizes how results flow through the 8-stage search pipeline.

**Pipeline Stages Captured**:
```
Stage 0: Query Expansion (TF-IDF, optional)
   ↓ Timing: ~400ms (only for <3 word queries)

Stage 1: Initial Retrieval (bi-encoder semantic search)
   ↓ Timing: ~400ms
   ↓ Returns: Top 100 candidates (from 8,755 chunks)

Stage 1.5: Chunk Deduplication (if chunking enabled)
   ↓ Timing: <5ms
   ↓ Keep best chunk per file

Stage 2: Score Filtering (min_score threshold)
   ↓ Timing: <1ms

Stage 3: Status Filtering (exclude inactive gleanings)
   ↓ Timing: <1ms

Stage 4: Type Filtering (include/exclude by type)
   ↓ Timing: <1ms

Stage 5: Time-Aware Boost (exponential decay)
   ↓ Timing: <5ms
   ↓ Formula: boost = max_boost × (0.5 ** (days_old / half_life))

Stage 6: Cross-Encoder Re-Ranking (optional, default on)
   ↓ Timing: ~200ms
   ↓ Precision: +20-30% improvement

Stage 7: Top-K Selection (final results)
   ↓ Returns: User-specified limit (default 10)
```

**Captured Data Per Stage**:
- Result count (how many documents remain)
- Timing (milliseconds spent in stage)
- Top results with all scores (semantic, BM25, RRF, cross-encoder, time)
- Rank changes (which results moved up/down)
- Filtered items (what was removed and why)

**API Integration**:
```
GET /search?q=query&pipeline_debug=true
→ Returns pipeline object with stages array
→ Each stage: {name, timing_ms, result_count, top_results, removed_items}
→ Overhead: <50ms when enabled, 0ms when disabled
```

**Implementation**: `src/temoa/server.py` (pipeline_debug parameter), `src/temoa/ui/search.html` (collapsible stage view)

### Inspector (Document Exploration)

Detailed examination of individual search results with two layers of relatedness.

**Two Layers of Document Relatedness**:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Explicit Links (Wikilinks)                         │
│ - High signal: Human-curated relationships                  │
│ - Structural: How notes are connected                       │
│ - Uses vault wikilink graph (NetworkX + obsidiantools)      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Implicit Similarity (Embeddings)                   │
│ - Universal: Works on any text, no links required           │
│ - Semantic: Content-based relationships                     │
│ - Uses bi-encoder model (all-mpnet-base-v2)                 │
└─────────────────────────────────────────────────────────────┘
```

**Inspector Sections**:

1. **Score Breakdown**:
   - Visual bars for semantic, BM25, RRF, cross-encoder scores
   - Tag boost indicator (5x when active)
   - Time boost indicator (exponential decay formula)
   - Hover tooltips explaining each score type

2. **Similar by Topic** (Layer 2 - Semantic):
   - Top 6 semantically similar notes
   - Uses note title as search query
   - Pure semantic search (no BM25)
   - Amber chips distinguish from graph links

3. **Linked Notes** (Layer 1 - Structural):
   - Incoming links (notes linking TO this note)
   - Outgoing links (notes this note links TO)
   - 2-hop neighbors (excluding daily notes)
   - Blue chips for graph relationships
   - Click to open in Obsidian

4. **Metadata Display**:
   - Frontmatter fields (type, project, status, source, url)
   - Tags (all tags shown)
   - Dates (created, modified with relative time)
   - Full description text

**Implementation**: `src/temoa/ui/search.html` (Inspector pane in Explorer view)

### VaultGraph (Wikilink Analysis)

**Purpose**: Provides fast access to vault structure via wikilink relationships.

**Architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│ VaultGraph Class (src/temoa/vault_graph.py)                 │
│                                                              │
│ Dependencies:                                                │
│   - obsidiantools (v0.11.0): Vault parsing, wikilink extract│
│   - NetworkX: Graph algorithms, path finding                │
│                                                              │
│ Data Structure:                                              │
│   - Directed graph: A → B means "A links to B"              │
│   - Undirected graph: For neighborhood exploration          │
│   - Node: Note name (without .md extension)                 │
│   - Edge: Wikilink from one note to another                 │
└─────────────────────────────────────────────────────────────┘

Caching Strategy:
┌─────────────────────────────────────────────────────────────┐
│ First Load: ~90 seconds                                      │
│   - Parse all vault files for wikilinks                     │
│   - Build NetworkX graph                                    │
│   - Save to .temoa/vault_graph.pkl (~700KB)                 │
│                                                              │
│ Cached Load: ~0.1 seconds (900x faster)                     │
│   - Load pickled NetworkX graphs                            │
│   - Skip parsing, skip graph construction                   │
│                                                              │
│ Auto-Rebuild:                                                │
│   - Triggered on reindex (API: POST /reindex)               │
│   - Triggered on reindex (CLI: temoa index --vault X)       │
│   - Keeps graph in sync with vault changes                  │
└─────────────────────────────────────────────────────────────┘
```

**Key Methods**:
- `ensure_loaded()` - Lazy load with cache preference
- `get_neighbors(note, max_hops)` - Find connected notes within N hops
- `get_hub_notes()` - Find well-connected notes (high in/out degree)
- `get_path(source, target)` - Shortest path between two notes
- `rebuild_and_cache()` - Force rebuild from vault (during reindex)

**API Endpoints**:
```
GET /graph/neighbors?note=X&vault=Y
→ Returns incoming, outgoing, 2-hop neighbors

GET /graph/stats?vault=X
→ Returns node_count, edge_count, connected_components, isolated_notes

GET /similar?note=X&vault=Y&limit=6
→ Returns semantically similar notes (Layer 2)
```

**Storage**:
```
~/Obsidian/vault-name/
  └── .temoa/
      └── vault_graph.pkl     ← Cached NetworkX graphs (~700KB)
          └── {
              'graph': DirectedGraph,
              'undirected': UndirectedGraph,
              'cached_at': '2026-01-26T10:30:00',
              'node_count': 2006,
              'edge_count': 5423
          }
```

**Memory Usage**:
- Graph in memory: ~10-20MB (depending on vault size)
- Cache file on disk: ~700KB (2,000 notes, 5,000 links)
- Per-vault isolation: Each vault has independent cached graph

**Performance Characteristics**:
```
Operation                    Time       Notes
─────────────────────────────────────────────────────────────
Initial graph build          ~90s       One-time per vault
Cached graph load            ~0.1s      900x faster
get_neighbors()              <5ms       NetworkX BFS
get_hub_notes()              ~50ms      Iterate all nodes
get_path()                   <10ms      Shortest path (Dijkstra)
rebuild_and_cache()          ~90s       During reindex only
```

**Design Decisions**:

**DEC-092**: Use obsidiantools for vault graph analysis
- Mature library (v0.11.0), production-ready
- NetworkX integration (powerful graph algorithms)
- Handles Obsidian-specific wikilink syntax

**DEC-093**: Two layers of relatedness (explicit + implicit)
- Explicit links (wikilinks): High-signal, human-curated
- Implicit similarity (embeddings): Universal, works on any text
- Both layers complement each other

**DEC-094**: Lazy graph loading with persistent cache
- First load expensive (~90s), subsequent loads fast (~0.1s)
- Auto-rebuild on reindex keeps graph in sync
- Cache stored in `.temoa/` for vault co-location

### Integration with Main Interface

All experimentation tools are integrated into the unified search interface at `/search`:

**List View** (Simple):
- Standard search results
- Search history dropdown
- Quick access to results

**Explorer View** (Advanced):
- Three-pane layout: Controls | Results | Inspector
- Controls pane: Fetch (server params) + Live (remix params)
- Results pane: Click any result to inspect
- Inspector pane: Scores + Similar + Linked + Metadata

**View Toggle**:
- Button in header (List ⟷ Explorer)
- Keyboard shortcut: `t`
- State preserved across switches
- localStorage persistence

**Navigation**:
- All tools accessible from main search interface
- No context switching between separate pages
- Unified state management (query, results, params)

---

## Multi-Vault Support

**Added in Phase 3** (December 2025)

Temoa supports multiple vaults with independent indexes and LRU caching for efficient memory usage.

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Cache (LRU)                       │
│                                                             │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Vault: amoxtli │  │ Vault: 1002  │  │ Vault: test  │     │
│  ├────────────────┤  ├──────────────┤  ├──────────────┤     │
│  │ Bi-encoder     │  │ Bi-encoder   │  │ Bi-encoder   │     │
│  │ Cross-encoder. │  │ Cross-encoder│  │ Cross-encoder│     │
│  │ BM25 index     │  │ BM25 index   │  │ BM25 index   │     │
│  │ Embeddings     │  │ Embeddings   │  │ Embeddings   │     │
│  └────────────────┘  └──────────────┘  └──────────────┘     │
│       ~500MB           ~500MB           ~500MB              │
│                                                             │
│  Max 3 vaults cached (LRU eviction)                         │
│  Total memory: ~1.5GB                                       │
└─────────────────────────────────────────────────────────────┘
```

**Key Features:**

1. **Independent Indexes**: Each vault has its own `.temoa/model-name/` directory
2. **LRU Cache**: Max 3 vaults in memory (~1.5GB total)
3. **Fast Switching**: ~400ms when cached, ~15-20s on first load
4. **Per-Vault Configuration**: Model selection, chunking settings
5. **Vault Validation**: Prevents index corruption from wrong vault

**Storage Layout:**

```
~/Obsidian/amoxtli/
  └── .temoa/
      ├── all-mpnet-base-v2/      ← Model-specific indexes
      │   ├── embeddings.pkl
      │   ├── bm25_index.pkl
      │   └── frontmatter_cache.pkl
      └── config.json              ← Vault-local config

~/Obsidian/1002/
  └── .temoa/
      └── all-MiniLM-L6-v2/        ← Different model OK
          ├── embeddings.pkl
          └── ...
```

**Configuration:**

Global config (`~/.config/temoa/config.json`):
```json
{
  "vaults": {
    "amoxtli": {
      "path": "~/Obsidian/amoxtli",
      "model": "all-mpnet-base-v2"
    },
    "1002": {
      "path": "~/Obsidian/1002",
      "model": "all-MiniLM-L6-v2"
    }
  },
  "default_vault": "amoxtli"
}
```

**Usage:**

```bash
# CLI vault selection
temoa search "query" --vault amoxtli
temoa index --vault 1002

# API vault selection
GET /search?q=query&vault=amoxtli

# Web UI: Vault dropdown selector
```

**Performance:**

```
Cache Hit (vault already loaded):  ~400ms search
Cache Miss (load new vault):       ~15-20s + search
Cache Eviction (4th vault):        LRU removes oldest
```

---

## Request Flow

### Multi-Stage Search Pipeline (Phase 3)

Temoa uses a sophisticated multi-stage pipeline for high-precision search:

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Action (Mobile)                                         │
└─────────────────────────────────────────────────────────────────┘
    User types "AI" and presses Search
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. HTTP Request                                                 │
└─────────────────────────────────────────────────────────────────┘
    GET http://100.x.x.x:8080/search?q=AI&limit=10
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. FastAPI Endpoint (src/temoa/server.py)                       │
└─────────────────────────────────────────────────────────────────┘
    Multi-stage search pipeline:
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 0: Query Enhancement (optional)                     ║
    ╚═══════════════════════════════════════════════════════════╝
    Query: "AI" (<3 words, triggers expansion)
       ↓ QueryExpander (TF-IDF from top 5 initial results)
    Expanded: "AI machine learning neural networks"
    Time: ~400ms (only for short queries)
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 1: Initial Retrieval (bi-encoder)                   ║
    ╚═══════════════════════════════════════════════════════════╝
    Method: Semantic OR Hybrid (BM25 + semantic with RRF)
       ↓ Synthesis Engine (all-mpnet-base-v2)
       ↓ Searches chunked content (if chunking enabled)
    Returns: Top 100 candidates (from 8,755 chunks)
    Time: ~400ms
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 1.5: Chunk Deduplication (if chunking enabled)      ║
    ╚═══════════════════════════════════════════════════════════╝
    Keep only best-scoring chunk per file
    Prevents duplicate results from same document
    Time: <5ms
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 2: Filtering                                        ║
    ╚═══════════════════════════════════════════════════════════╝
    - Score threshold (min_score)
    - Status filter (exclude inactive gleanings)
    - Type filter (exclude/include by frontmatter type)
    Time: <1ms
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 3: Time-Aware Boost (optional)                      ║
    ╚═══════════════════════════════════════════════════════════╝
    Formula: boost = max_boost * (0.5 ** (days_old / half_life))
    Example: Today's doc → +20%, 90 days old → +10%, 1 year → +2%
    Time: <5ms
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 4: Cross-Encoder Re-Ranking (optional, default on)  ║
    ╚═══════════════════════════════════════════════════════════╝
    Model: ms-marco-MiniLM-L-6-v2 (cross-encoder)
       ↓ Precise pairwise scoring (query, doc)
    Re-ranks: Top 100 candidates
    Precision: +20-30% improvement
    Time: ~200ms
                              │
                              ▼
    ╔═══════════════════════════════════════════════════════════╗
    ║ STAGE 5: Top-K Selection                                  ║
    ╚═══════════════════════════════════════════════════════════╝
    Returns: Final 10 results (or user-specified limit)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Return Results                                               │
└─────────────────────────────────────────────────────────────────┘
    {
      "query": "AI",
      "expanded_query": "AI machine learning neural networks",
      "results": [
        {
          "title": "Neural Networks Overview",
          "similarity_score": 0.78,
          "cross_encoder_score": 4.52,
          "frontmatter": {"type": "gleaning"},
          "obsidian_uri": "obsidian://open?vault=..."
        },
        ...
      ]
    }
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Render in UI (search.html)                                   │
└─────────────────────────────────────────────────────────────────┘
    - Display expanded query (if applied)
    - Render collapsible results
    - Show cross-encoder scores (when re-ranking enabled)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. User Clicks Result                                           │
└─────────────────────────────────────────────────────────────────┘
    obsidian:// URI triggers Obsidian app to open the note

Total Time:
  - Semantic only: ~400ms
  - With re-ranking: ~600ms
  - Short query with expansion + re-ranking: ~800-1000ms
  (All well under <2s mobile target)
```

**Key Improvements Over Simple Search**:
- **Search parameters**: Configurable query parameters for tuning search behavior
- **Adaptive chunking**: 100% content searchability (vs 35% before)
- **Query expansion**: Handles short, ambiguous queries better
- **Cross-encoder re-ranking**: 20-30% precision improvement
- **Time-aware scoring**: Recent documents surface naturally
- **Type filtering**: Noise reduction (exclude daily notes by default)
- **Hybrid search**: Combines keyword (BM25) + semantic for best recall

See [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md) for detailed technical reference.

### Type Filtering Flow

**Added in Phase 2.5**: Results can be filtered by document type using frontmatter metadata.

```
┌────────────────────────────────────────────────────────────┐
│ Type Filtering (Applied After Search)                      │
└────────────────────────────────────────────────────────────┘

1. Search Returns Results (with cached frontmatter)
   ┌─────────────────────────────────────────────────────────┐
   │  [                                                      │
   │    {                                                    │
   │      "title": "Daily Note",                             │
   │      "frontmatter": {"type": "daily"},  ← Cached!       │
   │      "similarity_score": 0.85                           │
   │    },                                                   │
   │    {                                                    │
   │      "title": "Gleaning",                               │
   │      "frontmatter": {"type": "gleaning"},               │
   │      "similarity_score": 0.82                           │
   │    }                                                    │
   │  ]                                                      │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
2. Apply Type Filters (No File I/O!)
   ┌─────────────────────────────────────────────────────────┐
   │  exclude_types = ["daily"]  ← Default filter            │
   │                                                         │
   │  For each result:                                       │
   │    types = result.frontmatter.get("type")               │
   │    if types in exclude_types:                           │
   │      skip result  ← Filter out daily notes              │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
3. Filtered Results
   ┌─────────────────────────────────────────────────────────┐
   │  [                                                      │
   │    {                                                    │
   │      "title": "Gleaning",                               │
   │      "type": "gleaning",                                │
   │      "similarity_score": 0.82                           │
   │    }                                                    │
   │  ]                                                      │
   │  + filtered_count: {"by_type": 1, ...}                  │
   └─────────────────────────────────────────────────────────┘

Filter Performance: <1ms (uses cached frontmatter, no disk I/O)
```

**Supported Type Values:**
- `gleaning` - Extracted link/article from daily notes
- `writering` - Writing-related content
- `llmering` - LLM/AI-related content
- `article` - General articles
- `reference` - Reference material
- `note` - General notes
- `daily` - Daily notes (excluded by default)

**Filter Modes:**
```
Inclusive (--type gleaning,article):
  → Show ONLY results with these types

Exclusive (--exclude-type daily,note):
  → Hide results with these types

Default Behavior:
  exclude_types=["daily"]  ← Reduce noise from daily notes
```

### Performance Breakdown

```
Typical Search Request (400ms total):

┌────────────────────────────────────────────────────────┐
│ Component              Time      Percentage            │
├────────────────────────────────────────────────────────┤
│ HTTP Request (network) 20ms      5%   ▌                │
│ FastAPI Routing        10ms      3%   ▌                │
│ Query Embedding        80ms     20%   ████             │
│ Load Index             100ms    25%   █████            │
│ Similarity Calc        150ms    38%   ████████         │
│ Ranking & Format       30ms      8%   ██               │
│ HTTP Response          10ms      3%   ▌                │
└────────────────────────────────────────────────────────┘

Optimization Opportunities:
- Load Index: Could cache in RAM (future enhancement)
- Similarity Calc: Most time spent, but necessary
- Network: Tailscale VPN adds ~10-20ms overhead
```

### Startup Flow

```
┌─────────────────────────────────────────────────────────┐
│ Server Startup (one-time, ~15 seconds)                  │
└─────────────────────────────────────────────────────────┘

1. Load Configuration
   config.json → Config object (10ms)
                              │
                              ▼
2. Initialize Synthesis Client
   Import synthesis modules (500ms)
                              │
                              ▼
3. Load Transformer Model (THIS IS THE SLOW PART)
   ┌─────────────────────────────────────────────────────────┐
   │  sentence-transformers downloads/caches model           │
   │  - First run: Download ~80MB (one-time, 30-60s)         │
   │  - Subsequent: Load from cache (~2-3s)                  │
   │  - Initialize neural network (~10-12s)                  │
   └─────────────────────────────────────────────────────────┘
                              │
                              ▼
4. Model Ready in Memory
   All searches now use cached model (fast!)
                              │
                              ▼
5. Server Listening
   http://0.0.0.0:8080 ready to accept requests

This is why we use direct imports instead of subprocess:
- Subprocess: Load model EVERY search (2-3s each) ✗
- Direct import: Load model ONCE at startup (15s) ✓
- Searches after startup: 400ms ✓✓
```

---

## Storage Architecture

### File System Layout

```
~/Obsidian/vault-name/
│
├── Daily/                          # Daily notes (source of gleanings)
│   ├── 2025-11-20.md
│   ├── 2025-11-21.md
│   └── 2025-11-22.md
│       └── ## Gleanings          # Extracted from here
│           └── - [Title](URL) - Description
│
├── Journal/                        # Journal entries
│   └── 2025-11-22.md
│
├── L/                              # Library
│   └── Gleanings/                 # Extracted gleanings go here
│       ├── abc123def456.md        # MD5 hash of URL = filename
│       ├── 789ghi012jkl.md
│       └── ...
│           └── Each file contains:
│               - Frontmatter (title, url, date, tags, status)
│               - Description
│               - Auto-fetched metadata (if available)
│
└── .temoa/                         # Temoa data directory
    ├── embeddings.pkl             # Vector index (binary)
    │   └── {
    │       "file_path": str,
    │       "embedding": [float × 384],
    │       "metadata": {...}
    │   }
    │
    ├── config.json                # Vault-local config (optional)
    ├── extraction_state.json      # Gleaning extraction tracking
    │   └── {
    │       "processed_files": [
    │         {"path": "Daily/2025-11-22.md", "timestamp": ...}
    │       ],
    │       "last_run": "2025-11-22T10:30:00"
    │   }
    │
    └── gleaning_status.json       # Gleaning status tracking
        └── {
            "abc123def456": {
              "status": "inactive",
              "reason": "Dead link (404)",
              "updated": "2025-11-22T14:30:00"
            }
        }
```

### Gleaning File Format

```markdown
---
title: "Dataview Plugin Documentation"
url: "https://blacksmithgu.github.io/obsidian-dataview/"
date: "2025-11-22"
timestamp: "14:30"
tags:
  - obsidian
  - plugins
  - dataview
type: gleaning                         # NEW: Type for filtering
status: active
migrated_from: null
---

A comprehensive guide to using the Dataview plugin for querying your Obsidian vault like a database.

<!-- Auto-fetched metadata (if available) -->
- Fetched: 2025-11-22T14:31:00
- Status Code: 200
- Content Type: text/html
```

**Type Field Format** (added Phase 2.5):
```yaml
# Single type
type: gleaning

# Multiple types (OR matching)
type:
  - writering
  - article

# Alternative inline format
type: [writering, article]
```

### Configuration Files

```
Global Config (~/.config/temoa/config.json):
┌────────────────────────────────────────────────────────┐
│ {                                                      │
│   "vault_path": "~/Obsidian/vault-name",               │
│   "synthesis_path": "old-ideas/synthesis",             │
│   "storage_dir": null,     // Use .temoa/ in vault     │
│   "default_model": "all-MiniLM-L6-v2",                 │
│   "server": {                                          │
│     "host": "0.0.0.0",                                 │
│     "port": 8080                                       │
│   },                                                   │
│   "search": {                                          │
│     "default_limit": 10,                               │
│     "max_limit": 100,                                  │
│     "timeout": 10                                      │
│   }                                                    │
│ }                                                      │
└────────────────────────────────────────────────────────┘

Vault-Local Config (vault/.temoa/config.json):
┌─────────────────────────────────────────────────────────┐
│ {                                                       │
│   "storage_dir": "~/custom-index-location",  // Override│
│   "excluded_paths": ["Private/", "Archive/"],           │
│   "custom_patterns": ["Notes/**/*.md"]                  │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

### Index File Structure

```
.temoa/embeddings.pkl (pickle format):
┌───────────────────────────────────────────────────────────┐
│ {                                                         │
│   "embeddings": [                                         │
│     {                                                     │
│       "file_path": "L/Gleanings/abc123.md",               │
│       "embedding": [0.42, -0.13, ..., 0.21], // 384 floats│
│       "metadata": {                                       │
│         "title": "Plugin Guide",                          │
│         "tags": ["obsidian", "plugins"],                  │
│         "modified": "2025-11-22T10:00:00"                 │
│       }                                                   │
│     },                                                    │
│     { ... },  // 2000+ more entries                       │
│   ],                                                      │
│   "model_name": "all-MiniLM-L6-v2",                       │
│   "indexed_at": "2025-11-22T09:00:00",                    │
│   "total_files": 2281                                     │
│ }                                                         │
└───────────────────────────────────────────────────────────┘

File Size Estimates:
- 1000 files: ~5 MB
- 2000 files: ~10 MB
- 5000 files: ~25 MB

(384 floats × 4 bytes + metadata overhead)
```

---

## Component Details

### 1. FastAPI Server (`src/temoa/server.py`)

**Purpose**: HTTP API layer, handles requests, coordinates components

```
Key Responsibilities:
┌─────────────────────────────────────────────────────────┐
│ 1. HTTP endpoint routing                                │
│ 2. Request validation (query params, limits)            │
│ 3. SynthesisClient lifecycle management                 │
│ 4. Response formatting (JSON, obsidian:// URIs)         │
│ 5. Error handling and logging                           │
│ 6. CORS headers (for browser access)                    │
└─────────────────────────────────────────────────────────┘

API Endpoints (grouped by function):

Core Search & Discovery:
┌────────────────────┬──────────────────────────────────────┐
│ GET  /search       │ Semantic/hybrid search               │
│ GET  /archaeology  │ Temporal analysis of topics          │
└────────────────────┴──────────────────────────────────────┘

Vault Management:
┌────────────────────┬──────────────────────────────────────┐
│ GET  /vaults       │ List configured vaults               │
│ GET  /stats        │ Basic vault statistics               │
│ GET  /stats/advanced│ Extended vault statistics           │
│ GET  /config       │ Vault configuration (chunking, model)│
│ GET  /models       │ List available embedding models      │
│ POST /reindex      │ Rebuild embedding index              │
└────────────────────┴──────────────────────────────────────┘

Gleaning Management:
┌─────────────────────────────────┬───────────────────────┐
│ POST /extract                   │ Extract from daily    │
│ GET  /gleanings                 │ List with filters     │
│ GET  /gleanings/{id}            │ Get single gleaning   │
│ POST /gleanings/{id}/status     │ Update status         │
│ GET  /gleaning/stats            │ Counts by status      │
└─────────────────────────────────┴───────────────────────┘

Graph Exploration (Phase 3.6):
┌─────────────────────────────────┬───────────────────────┐
│ GET  /graph/neighbors           │ Wikilink connections  │
│ GET  /graph/stats               │ Graph statistics      │
│ GET  /similar                   │ Semantic neighbors    │
└─────────────────────────────────┴───────────────────────┘

UI & PWA:
┌────────────────────┬──────────────────────────────────────┐
│ GET  /             │ Main search UI (search.html)         │
│ GET  /manage       │ Management UI (reindex, extract)     │
│ GET  /manifest.json│ PWA manifest                         │
│ GET  /health       │ Server health check                  │
└────────────────────┴──────────────────────────────────────┘

Documentation:
┌────────────────────┬──────────────────────────────────────┐
│ GET  /docs         │ Interactive API reference (Swagger)  │
└────────────────────┴──────────────────────────────────────┘

For complete API documentation with request/response schemas,
parameters, and interactive testing, visit: http://SERVER:8080/docs

Search Query Parameters:
┌────────────────────┬─────────────────────────────────────┐
│ q                  │ Search query (required)             │
│ limit              │ Max results (default: 10)           │
│ min_score          │ Min similarity (default: 0.3)       │
│ hybrid             │ Use BM25+semantic (default: false)  │
│ include_types      │ Include only these types (optional) │
│ exclude_types      │ Exclude these types (default: daily)│
└────────────────────┴─────────────────────────────────────┘
```

### 2. SynthesisClient (`src/temoa/synthesis.py`)

**Purpose**: Wrapper around Synthesis engine, manages embeddings

```
Key Responsibilities:
┌─────────────────────────────────────────────────────────┐
│ 1. Direct imports of Synthesis modules                  │
│ 2. Model loading and caching                            │
│ 3. Search method delegation                             │
│ 4. Index management (build, update)                     │
│ 5. Obsidian URI generation                              │
│ 6. Result formatting                                    │
└─────────────────────────────────────────────────────────┘

Key Methods:
┌────────────────────────────────────────────────────────┐
│ search(query, limit) → List[SearchResult]              │
│ archaeology(topic, limit) → List[TemporalResult]       │
│ reindex(force=False) → IndexStats                      │
│ get_stats() → VaultStats                               │
│ health_check() → HealthStatus                          │
└────────────────────────────────────────────────────────┘
```

### 3. Synthesis Engine (`old-ideas/synthesis/`)

**Purpose**: Core semantic search engine (external dependency)

```
Key Components:
┌─────────────────────────────────────────────────────────┐
│ main.py              CLI entry point                    │
│ searcher.py          Search logic, similarity calc      │
│ indexer.py           Embedding generation, storage      │
│ models.py            Model management                   │
│ vault_parser.py      Markdown/frontmatter parsing       │
└─────────────────────────────────────────────────────────┘

External Libraries:
┌─────────────────────────────────────────────────────────┐
│ sentence-transformers  Pre-trained embedding models     │
│ sklearn                Cosine similarity                │
│ numpy                  Vector operations                │
│ pickle                 Embedding serialization          │
└─────────────────────────────────────────────────────────┘

Note: Synthesis is a separate project, Temoa wraps it.
We do NOT modify Synthesis code, only import and call it.
```

### 4. Configuration System (`src/temoa/config.py`)

**Purpose**: Centralized configuration management

```
Configuration Hierarchy:
┌─────────────────────────────────────────────────────────┐
│ 1. Defaults (hardcoded)                                 │
│    ↓ (override)                                         │
│ 2. Global config (~/.config/temoa/config.json)          │
│    ↓ (override)                                         │
│ 3. Environment variables (TEMOA_*)                      │
│                                                         │
│ Result: Merged configuration object                     │
└─────────────────────────────────────────────────────────┘

Key Features:
- Path expansion (~/, $HOME)
- Validation (required fields, types)
- Sensible defaults
- Override mechanism
```

### 5. Web UI (`src/temoa/ui/search.html`)

**Purpose**: Mobile-first search interface

```
Technologies:
┌─────────────────────────────────────────────────────────┐
│ - Vanilla HTML/CSS/JavaScript (no frameworks)           │
│ - Responsive design (mobile-first)                      │
│ - Fetch API for HTTP requests                           │
│ - CSS Grid for layout                                   │
└─────────────────────────────────────────────────────────┘

Features:
┌─────────────────────────────────────────────────────────┐
│ - Real-time search (debounced input)                    │
│ - Result cards with similarity scores                   │
│ - obsidian:// URI links                                 │
│ - Loading states and error handling                     │
│ - Dark mode support (system preference)                 │
└─────────────────────────────────────────────────────────┘
```

### 6. Gleaning Extraction (`scripts/extract_gleanings.py`)

**Purpose**: Extract and manage gleanings from daily notes

```
Extraction Process:
┌─────────────────────────────────────────────────────────┐
│ 1. Scan daily note patterns (Daily/**/*.md)             │
│ 2. Find ## Gleanings sections                           │
│ 3. Parse gleaning formats:                              │
│    - Markdown links: - [Title](URL) - Description       │
│    - Naked URLs: - https://... (fetch title from web)   │
│    - Multi-line descriptions (> quoted lines)           │
│ 4. Generate MD5 hash from URL (deduplication)           │
│ 5. Create gleaning file in L/Gleanings/                 │
│ 6. Track state to avoid re-processing                   │
└─────────────────────────────────────────────────────────┘

Status Management:
┌─────────────────────────────────────────────────────────┐
│ active    Normal gleaning, included in search           │
│ inactive  Dead link, excluded from search, auto-restore │
│ hidden    Manually hidden, never auto-restored          │
└─────────────────────────────────────────────────────────┘
```

---

## Error Handling Philosophy

### Fail-Open vs Fail-Closed

Temoa uses different error handling strategies depending on the operation's criticality and impact on user experience.

**Fail-Open** (include on error, continue gracefully):
- **Search result filtering** - Better to show too much than miss relevant results
  - If frontmatter can't be parsed → include the file in results
  - If status can't be determined → treat as "active"
  - Example: `filter_by_type()` catches file read errors and includes files
- **Optional metadata** - Missing data doesn't prevent core functionality
  - Missing description → use empty string
  - Missing tags → use empty list
  - Missing dates → omit from display
- **Search enhancements** - Quality features shouldn't break basic search
  - Query expansion fails → continue with original query
  - Re-ranking fails → use original ordering
  - Time scoring fails → no temporal boost
- **Snippet extraction** - Better to show basic info than fail completely
  - Can't extract context → show title only
  - Encoding errors → show file path

**Fail-Closed** (reject on error, prevent corruption):
- **Authentication/authorization** - Deny access on error (future feature)
- **Data modification** - Reject rather than corrupt
  - Gleaning extraction fails → report error, don't create invalid file
  - Reindex with errors → abort and preserve old index
- **Security validation** - Path traversal → reject immediately
  - File path outside vault → skip file, log warning
  - Malicious relative paths → validate and reject
- **Critical operations** - System integrity over availability
  - Server initialization fails → don't start server
  - Model loading fails → don't accept requests
  - Config errors → don't start with defaults

### Exception Types

Temoa uses specific exception types (defined in `src/temoa/exceptions.py`) instead of bare `except Exception`:

```python
class TemoaError(Exception):
    """Base exception for all Temoa errors"""

class VaultReadError(TemoaError):
    """Error reading vault files"""

class SearchError(TemoaError):
    """Error during search operation"""

class IndexError(TemoaError):
    """Error during indexing"""

class ConfigError(TemoaError):
    """Configuration error"""

class GleaningError(TemoaError):
    """Error during gleaning operations"""
```

**Guidelines**:

1. **Catch specific exceptions first**:
   ```python
   try:
       content = file.read()
   except (FileNotFoundError, OSError, UnicodeDecodeError) as e:
       logger.debug(f"Expected error: {e}")
       # Handle gracefully
   except Exception as e:
       logger.error(f"Unexpected error: {e}", exc_info=True)
       # Re-raise or handle conservatively
   ```

2. **Never catch system exceptions**:
   - `KeyboardInterrupt` - User wants to stop the process
   - `SystemExit` - Process is exiting
   - `MemoryError` - System is out of memory

3. **Log appropriately**:
   - `logger.debug()` - Expected errors in fail-open scenarios
   - `logger.warning()` - Recoverable errors that shouldn't happen
   - `logger.error()` - Unexpected errors, use `exc_info=True` for traceback

4. **HTTP endpoints**: FastAPI handles most errors
   - Catch all exceptions in endpoints and return HTTP 500
   - FastAPI handles `KeyboardInterrupt` at application level
   - Always log unexpected errors with full traceback

### Exception Handling Patterns

**Pattern 1: Fail-Open for Optional Features**
```python
try:
    metadata, _ = parse_file(file_path)
    types = parse_type_field(metadata or {})
except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError) as e:
    # Expected failures - fail-open
    logger.debug(f"Error reading frontmatter: {e}")
    types = []
except Exception as e:
    # Unexpected error - log but still fail-open
    logger.warning(f"Unexpected error: {e}")
    types = []
```

**Pattern 2: Fail-Closed for Critical Operations**
```python
try:
    self.pipeline = EmbeddingPipeline(vault_root, model_name)
except (ImportError, RuntimeError, IOError, OSError) as e:
    # Expected failures - re-raise
    raise SynthesisError(f"Failed to initialize: {e}")
except Exception as e:
    # Unexpected error - log and re-raise
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise SynthesisError(f"Failed to initialize: {e}")
```

**Pattern 3: HTTP Endpoint Error Handling**
```python
@app.get("/search")
async def search_endpoint():
    try:
        # ... search logic ...
        return results
    except SynthesisError as e:
        # Expected search failure
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Security Architecture

### Overview

Temoa's security model is designed for single-user, trusted network deployment (Tailscale). The focus is on preventing accidental misuse and DoS attacks rather than sophisticated attackers.

**Threat Model**:
- **In Scope**: Accidental misuse, resource exhaustion, path traversal
- **Out of Scope**: Authentication (trusted network), encryption (Tailscale), multi-tenancy

### CORS Protection

**Default Behavior** (Phase 4):
- Restrictive by default: `localhost` and `127.0.0.1` only
- Automatically includes Tailscale IP if `TAILSCALE_IP` env var set
- Logs warning if wildcard (`*`) is configured

**Configuration Priority**:
1. `TEMOA_CORS_ORIGINS` environment variable (comma-separated)
2. `server.cors_origins` in config.json
3. Safe defaults (localhost + 127.0.0.1 + Tailscale IP)

**Implementation**: `src/temoa/server.py` lines 347-382

```python
# Example configuration
{
  "server": {
    "cors_origins": [
      "http://localhost:8080",
      "http://127.0.0.1:8080",
      "http://100.x.x.x:8080"  # Tailscale IP
    ]
  }
}
```

**Security Impact**:
- Prevents cross-site request forgery (CSRF)
- Blocks unauthorized web applications from accessing API
- Allows legitimate access from Tailscale network

### Rate Limiting

**Purpose**: DoS protection for expensive operations

**Protected Endpoints** (Phase 4):
- `/search`: 1,000 requests/hour (generous for interactive use)
- `/archaeology`: 20 requests/hour (expensive temporal analysis)
- `/reindex`: 5 requests/hour (very expensive, should be rare)
- `/extract`: 10 requests/hour (expensive gleaning extraction)

**Implementation**:
- `src/temoa/rate_limiter.py` - Sliding window algorithm
- In-memory storage (resets on server restart)
- Per-IP tracking

**Configuration**:
```json
{
  "rate_limits": {
    "search_per_hour": 1000,
    "archaeology_per_hour": 20,
    "reindex_per_hour": 5,
    "extract_per_hour": 10
  }
}
```

**Behavior**:
- Returns HTTP 429 (Too Many Requests) when limit exceeded
- Clear error message: "Too many X requests. Maximum Y per hour. Try again later."
- Limits reset after window expires (sliding, not fixed intervals)

**Security Impact**:
- Prevents accidental resource exhaustion (e.g., runaway script)
- Protects against basic DoS attacks
- Does not prevent legitimate heavy use (limits are generous)

### Path Traversal Protection

**Purpose**: Prevent access to files outside vault

**Implementation** (`src/temoa/time_scoring.py` lines 71-80):
```python
# Validate all file paths
file_path_resolved = file_path.resolve()
vault_path_resolved = vault_path.resolve()

if not str(file_path_resolved).startswith(str(vault_path_resolved)):
    logger.warning(f"Path traversal attempt: {result['relative_path']}")
    continue  # Skip this result
```

**Protection**:
- Resolves paths to absolute form (handles symlinks, `.`, `..`)
- Validates resolved path is within vault
- Logs warning for detected attempts
- Silently skips malicious results (fail-open for search, fail-closed for access)

**Test Coverage**: `tests/test_edge_cases.py::TestPathTraversalAttempts`

**Security Impact**:
- Prevents reading files outside vault (e.g., `/etc/passwd`)
- Protects against `../` traversal attacks
- Safe even with malicious vault content (gleanings from untrusted sources)

### Input Validation

**Query Parameters**:
- Length limits enforced by FastAPI (max query string length)
- Special characters handled by URL encoding
- No SQL injection risk (no database)
- No XSS risk (API only, no HTML rendering)

**File Paths**:
- All paths validated against vault root (see Path Traversal Protection)
- Relative paths resolved before use
- Symlinks followed and validated

**Frontmatter**:
- YAML parsing errors handled gracefully (fail-open)
- Invalid values ignored, not processed
- No code execution risk (YAML safe_load)

### Network Security

**Deployment Model**:
- Runs on `0.0.0.0:8080` (listens all interfaces)
- Access controlled by Tailscale network (WireGuard encryption)
- No authentication within Tailscale network (trusted)
- No HTTPS (encrypted by Tailscale tunnel)

**Why This Works**:
- Tailscale creates a private network (only user's devices)
- WireGuard provides strong encryption
- No exposure to public internet
- Single-user assumption (no multi-tenancy)

**Future Considerations** (if needed):
- API keys for authentication
- HTTPS if exposing beyond Tailscale
- User management for multi-user scenarios

### Data Privacy

**No External Services**:
- All embeddings computed locally (sentence-transformers)
- No API calls for search or indexing
- Vault data never leaves local machine/network

**Future LLM Integration** (Phase 4):
- Will use local Apantli proxy
- User controls which LLM provider (if any)
- Vault context sent to LLM only when explicitly used

### Security Checklist

For production deployment:

- [x] CORS origins configured (not wildcard)
- [x] Rate limits appropriate for use case
- [x] Path traversal protection enabled (automatic)
- [x] Tailscale network configured and tested
- [x] Server not exposed to public internet
- [ ] Regular updates of dependencies (`uv sync`)
- [ ] Monitor logs for suspicious activity (optional)
- [ ] Backup vault regularly (separate from security)

### Security vs. Usability Trade-offs

**Decisions Made**:

1. **No Authentication**: Tailscale provides network-level auth, adding another layer adds friction without meaningful security benefit for single-user
2. **Generous Rate Limits**: Prevents accidents, not sophisticated attacks (Tailscale network is trusted)
3. **Fail-Open Search**: Better to show too much than miss results (UX over paranoia)
4. **In-Memory Rate Limiting**: Simple, sufficient for trusted network, resets are acceptable

**Appropriate For**:
- Personal knowledge management
- Trusted Tailscale network
- Single-user scenarios
- Local/private data

**NOT Appropriate For**:
- Public internet exposure
- Multi-tenant SaaS
- Untrusted networks
- Sensitive/classified data requiring strict access control

---

## Deployment Model

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Tailscale VPN Network                      │
│                   (encrypted WireGuard tunnel)                  │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │ Mobile Device    │              │ Desktop Machine  │         │
│  │ (iOS/Android)    │              │ (Server)         │         │
│  │                  │              │                  │         │
│  │ Tailscale IP:    │◄────────────►│ Tailscale IP:    │         │
│  │ 100.x.x.y        │   Encrypted  │ 100.x.x.x        │         │
│  │                  │   Tunnel     │                  │         │
│  │ Browser:         │              │ Temoa Server:    │         │
│  │ http://100.x.x.x │              │ 0.0.0.0:8080     │         │
│  │      :8080       │              │                  │         │
│  └──────────────────┘              └──────────────────┘         │
│                                                                 │
│  Both devices on same "tailnet" (virtual LAN)                   │
│  No port forwarding, no public IP, no HTTPS needed              │
└─────────────────────────────────────────────────────────────────┘

Security:
- Tailscale encrypts all traffic (WireGuard protocol)
- Only devices on your tailnet can access server
- No authentication needed (trust network)
- No HTTPS needed (encrypted by Tailscale)
```

### Server Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                         Server Startup                          │
└─────────────────────────────────────────────────────────────────┘

Option 1: Manual (development)
┌────────────────────────────────────────────────────────┐
│ $ cd ~/projects/temoa                                  │
│ $ uv run temoa server                                  │
│ > Server starting on http://0.0.0.0:8080               │
│ > Loading model... (15s)                               │
│ > Model loaded: all-MiniLM-L6-v2                       │
│ > Server ready                                         │
└────────────────────────────────────────────────────────┘

Option 2: Background (long-running)
┌────────────────────────────────────────────────────────┐
│ $ nohup uv run temoa server > temoa.log 2>&1 &         │
│ > [1] 12345                                            │
│ $ tail -f temoa.log                                    │
└────────────────────────────────────────────────────────┘

Option 3: Systemd (production)
┌────────────────────────────────────────────────────────┐
│ $ sudo systemctl start temoa                           │
│ $ sudo systemctl enable temoa  # Start on boot         │
│ $ journalctl -u temoa -f       # View logs             │
└────────────────────────────────────────────────────────┘
```

### Automation

```
Daily Workflow:
┌─────────────────────────────────────────────────────────────────┐
│ 1. Extract gleanings from new daily notes                       │
│    (cron job: daily at 11 PM)                                   │
│                                                                 │
│ 2. Reindex vault (pick up new gleanings)                        │
│    (automatic after extraction)                                 │
│                                                                 │
│ 3. Maintenance (check dead links, update statuses)              │
│    (manual or weekly cron)                                      │
└─────────────────────────────────────────────────────────────────┘

Cron Setup:
┌────────────────────────────────────────────────────────┐
│ # Extract gleanings daily at 11 PM                     │
│ 0 23 * * * cd ~/projects/temoa && \                    │
│   uv run temoa extract --auto-reindex                  │
│                                                        │
│ # Maintenance weekly on Sundays at 2 AM                │
│ 0 2 * * 0 cd ~/projects/temoa && \                     │
│   uv run temoa gleaning maintain                       │
└────────────────────────────────────────────────────────┘
```

---

## Key Architectural Decisions

### DEC-009: Direct Imports Over Subprocess

**Problem**: Subprocess calls to Synthesis were slow (2-3s per search)
**Solution**: Import Synthesis code directly, load model once at startup
**Impact**: 10x faster searches (400ms vs 2-3s)

**Before (Subprocess)**:
```python
# Each search:
result = subprocess.run(["uv", "run", "main.py", "search", query])
# → Model loads EVERY time (2-3s)
```

**After (Direct Import)**:
```python
# Startup (once):
from synthesis import Searcher
searcher = Searcher(model="all-MiniLM-L6-v2")  # 15s one-time

# Each search:
results = searcher.search(query)  # 400ms ✓
```

### DEC-013: Modern FastAPI Lifespan

**Problem**: Model needed to load at startup, unload at shutdown
**Solution**: Use FastAPI lifespan context manager
**Impact**: Clean resource management, proper shutdown

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model
    synthesis = SynthesisClient(config)
    await synthesis.initialize()
    yield {"synthesis": synthesis}
    # Shutdown: cleanup
    await synthesis.cleanup()
```

### Storage in Vault (.temoa/)

**Why**: Co-location with data, simple deployment
**Trade-offs**:
- ✓ Automatic sync with vault location
- ✓ No separate configuration needed
- ✗ Index files can get large (exclude from sync)
- ✗ Mixed concerns (user data + system data)

**Future**: Allow configurable storage location if needed

### DEC-092: Use obsidiantools for Vault Graph Analysis

**Problem**: Need to explore note relationships beyond semantic similarity
**Solution**: Use obsidiantools library with NetworkX for wikilink graph analysis
**Impact**: Production-ready graph features with powerful algorithms

**Why obsidiantools**:
- Mature library (v0.11.0), actively maintained
- NetworkX integration (BFS, shortest path, hub detection)
- Handles Obsidian-specific wikilink syntax
- Proven in production by other tools

### DEC-093: Two Layers of Document Relatedness

**Insight**: Temoa was treating notes as isolated islands, ignoring explicit human-curated relationships

**Solution**: Support both layers of relatedness:
1. **Explicit links (wikilinks)** - High signal, structural, human-curated
2. **Implicit similarity (embeddings)** - Universal, semantic, works on any text

**Impact**: Richer exploration beyond pure semantic search

**Complementary, not competing**:
- Wikilinks show intentional connections
- Embeddings find unexpected similarities
- Together: structural + semantic understanding

### DEC-094: Client-Side Score Remixing

**Problem**: Experimenting with search weights requires server round-trips (slow feedback loop)
**Solution**: Two-tier parameter model - server returns raw scores, client remixes instantly
**Impact**: <50ms feedback for weight adjustments vs ~400ms API calls

**Architecture**:
```
Server-side (require re-fetch): hybrid_weight, limit, rerank, expand
Client-side (instant remix):    mix_balance, tag_mult, time_weight
```

**Why this works**:
- Component scores (semantic, BM25, time) are independent
- Final score is linear combination: easily recalculated
- Browser can re-sort results without server
- Enables rapid parameter experimentation

### DEC-095: Lazy Graph Loading with Persistent Cache

**Problem**: Building wikilink graph takes ~90 seconds (too slow for every search)
**Solution**: Cache NetworkX graphs to `.temoa/vault_graph.pkl`, lazy load on demand
**Impact**: 900x faster load (0.1s vs 90s)

**Cache Strategy**:
- First load: Build + cache (~90s)
- Subsequent: Load from cache (~0.1s)
- Auto-rebuild: On reindex only (keeps graph in sync)
- Per-vault: Independent cached graphs

**Trade-offs**:
- ✓ Fast access to graph features
- ✓ No startup penalty
- ✗ Graph stale until next reindex (acceptable - vault changes infrequent)

---

## Performance Characteristics

### Scalability

```
Files Indexed vs. Search Time:
┌────────────────────────────────────────────────────────┐
│ 100 files    →  380ms search                           │
│ 500 files    →  390ms search                           │
│ 1000 files   →  400ms search                           │
│ 2000 files   →  410ms search   ← Current production    │
│ 5000 files   →  450ms search   (estimated)             │
│ 10000 files  →  550ms search   (estimated)             │
└────────────────────────────────────────────────────────┘

Why it scales well:
- Cosine similarity is O(n) with number of documents
- NumPy vector operations are highly optimized (C)
- Most time in embedding query, not comparing
```

### Memory Usage

```
Component Memory:
┌────────────────────────────────────────────────────────┐
│ Transformer Model:     ~500 MB  (loaded at startup)    │
│ Embedding Index:       ~10 MB   (2000 files × 384d)    │
│ FastAPI Runtime:       ~50 MB                          │
│ Python Interpreter:    ~30 MB                          │
│ ─────────────────────────────────────────────────────  │
│ Total:                 ~600 MB  (constant)             │
└────────────────────────────────────────────────────────┘

Scales linearly with vault size:
- 5000 files: ~650 MB
- 10000 files: ~700 MB
```

### Disk Usage

```
Per-file Storage:
┌────────────────────────────────────────────────────────┐
│ Embedding:    384 floats × 4 bytes = 1.5 KB            │
│ Metadata:     ~500 bytes                               │
│ Total:        ~2 KB per file                           │
└────────────────────────────────────────────────────────┘

Vault Sizes:
┌────────────────────────────────────────────────────────┐
│ 1000 files:    ~2 MB index                             │
│ 2000 files:    ~4 MB index                             │
│ 5000 files:    ~10 MB index                            │
│ 10000 files:   ~20 MB index                            │
└────────────────────────────────────────────────────────┘
```

### Performance Optimizations (Phase 2)

**Production Hardening Phase 2** implemented significant latency improvements:

**Total Improvement**: 700-1300ms latency reduction per search

#### File I/O Elimination (500-1000ms savings)

**Problem**: `filter_inactive_gleanings()` opened and read every result file to check status

**Before**:
```python
for result in results:
    with open(result["file_path"], "r") as f:  # 50 file reads!
        content = f.read()
    status = parse_frontmatter_status(content)
```

**After**:
```python
for result in results:
    status = result.get("frontmatter", {}).get("status", "active")
```

**Impact**:
- 50 results = 50 file reads eliminated
- ~500-1000ms on HDD, ~50-100ms on SSD
- Frontmatter already cached from indexing

#### Tag Matching Optimization (200-300ms savings)

**Problem**: Quadratic O(N²) tag matching loop

**Before**:
```python
for query_token in query_tokens:  # O(N)
    for tag in tags_lower:         # O(M)
        if query_token in tag or tag in query_token:
            tags_matched.append(tag)
# Total: O(N × M) for every document
```

**After**:
```python
# Exact match first (O(N) with set intersection)
query_set = set(query_tokens)
tag_set = set(tags_lower)
exact_matches = list(query_set & tag_set)

# Substring match only if needed (rare)
if not exact_matches:
    for query_token in query_tokens:
        for tag in tags_lower:
            if query_token in tag:
                exact_matches.append(tag)
                break
```

**Impact**:
- 10,000 docs × 10 tags × 5 query tokens: 500k → 150k operations
- ~200-300ms saved on large vaults
- Maintains backward compatibility

#### Memory Leak Fix

**Problem**: Large embedding arrays not explicitly released in hybrid search

**Fix**:
```python
try:
    embeddings_array, metadata_list, _ = self.pipeline.store.load_embeddings()
    # ... use embeddings ...
finally:
    if 'embeddings_array' in locals():
        del embeddings_array
    if 'metadata_list' in locals():
        del metadata_list
    import gc
    gc.collect()
```

**Impact**:
- Faster memory reclamation in long-running server
- Reduced peak memory usage
- More stable performance over time

#### Test Coverage

All optimizations validated with **171/171 tests passing** (zero regressions)

---

## Future Architecture Considerations

### Caching Layer (Phase 3)

If search performance degrades:

```
┌─────────────────────────────────────────────────────────┐
│ Query Cache (LRU):                                      │
│   "obsidian" → [cached results]                         │
│   TTL: 1 hour                                           │
│   Max size: 100 queries                                 │
└─────────────────────────────────────────────────────────┘

Benefits:
- Repeated queries instant (<10ms)
- Reduces CPU/battery on mobile
- Popular topics cached

Costs:
- Stale results after vault updates
- Memory overhead (~5-10 MB)
- Cache invalidation complexity
```

### PWA Support

**Status**: IMPLEMENTED (Phase 3.5 QoL)

Progressive Web App features for mobile:

```
┌─────────────────────────────────────────────────────────┐
│ manifest.json:                                          │
│   [DONE] Install to home screen                         │
│   [DONE] App icons and branding                         │
│   [DONE] Standalone display mode                        │
│                                                         │
│ Service Worker: (future)                                │
│   [FUTURE] Cache UI assets                              │
│   [FUTURE] Background sync                              │
│   [FUTURE] Offline fallback                             │
└─────────────────────────────────────────────────────────┘
```

Current implementation allows installing Temoa as a standalone app on iOS/Android with app-like experience. Full offline support planned for future enhancement.

### LLM Integration (Phase 4)

Vault-first chat with context:

```
┌─────────────────────────────────────────────────────────┐
│ User: "How do I use Dataview?"                          │
│   ↓                                                     │
│ 1. Search vault: "dataview usage"                       │
│ 2. Retrieve top 5 results                               │
│ 3. Format as XML context                                │
│ 4. Send to LLM with prompt                              │
│ 5. LLM responds using vault knowledge                   │
│ 6. Citations back to vault files                        │
└─────────────────────────────────────────────────────────┘

Integration with Apantli (LLM proxy)
```

---

## Troubleshooting Architecture

### Common Issues

**Search Returns No Results:**
```
Check:
1. Is index built? (temoa stats → embeddings count)
2. Is vault path correct? (temoa config)
3. Are files actually indexed? (check .temoa/embeddings.pkl)
4. Try broader query ("obsidian" vs "obsidian dataview plugin")
```

**Search is Slow (>2s):**
```
Check:
1. Model loaded? (should happen at startup once)
2. Index file large? (>50 MB might need optimization)
3. Network latency? (Tailscale usually adds <20ms)
4. Server resources? (top/htop for CPU/memory)
```

**Model Won't Load:**
```
Check:
1. Disk space? (model cache needs ~500 MB)
2. Network access? (first download needs internet)
3. Python version? (needs 3.11+)
4. Dependencies installed? (uv sync)
```

---

## Summary

Temoa's architecture is designed for:

1. **Speed**: Direct imports, model caching, <500ms searches
2. **Simplicity**: Minimal layers, straightforward data flow
3. **Privacy**: All local processing, no cloud dependencies
4. **Mobile-First**: Optimized for phone access over VPN
5. **Reliability**: Well-tested, production-ready components

The key insight: **Treat Synthesis as a library, not a service.** This single decision (DEC-009) made everything fast enough for mobile use, enabling the core behavioral hypothesis to be tested.

---

**Created**: 2025-11-22
**For**: Developers, contributors, and future architectural decisions
**Related Docs**:
- [CLAUDE.md](../CLAUDE.md) - Development guide
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Project plan
- [CHRONICLES.md](CHRONICLES.md) - Design discussions
