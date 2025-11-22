# ARCHITECTURE.md - Temoa System Architecture

> **Purpose**: This document explains the technical architecture of Temoa, how components interact, and how semantic search with embeddings works.

**Created**: 2025-11-22
**Last Updated**: 2025-11-22
**Status**: Phase 2.5 (Mobile Validation)

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [How Embeddings Work](#how-embeddings-work)
3. [Request Flow](#request-flow)
4. [Storage Architecture](#storage-architecture)
5. [Component Details](#component-details)
6. [Deployment Model](#deployment-model)

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
│  │  │  - One-time model loading at startup               │  │  │
│  │  │  - Caches loaded model in memory                   │  │  │
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
│  │  ├── Daily/                 (daily notes)                │  │
│  │  ├── Journal/               (journal entries)            │  │
│  │  ├── L/                                                  │  │
│  │  │   └── Gleanings/         (extracted gleanings)       │  │
│  │  └── .temoa/                (Temoa data)                 │  │
│  │      ├── embeddings.pkl     (vector index)               │  │
│  │      ├── config.json        (local config)               │  │
│  │      └── extraction_state.json  (gleaning tracking)      │  │
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
│  Misses:  "neural networks", "deep learning", "AI models"  │
└─────────────────────────────────────────────────────────────┘

Semantic Search with Embeddings:
┌─────────────────────────────────────────────────────────────┐
│  Query: "machine learning"                                  │
│  Embedding: [0.42, -0.13, 0.87, ..., 0.21]  (384 numbers)  │
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
   │            ↑                                             │
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

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | Default (fast mobile search) |
| `all-MiniLM-L12-v2` | 384 | Medium | Better | More nuanced search |
| `all-mpnet-base-v2` | 768 | Slower | Best | Highest quality results |
| `multi-qa-mpnet-base-cos-v1` | 768 | Slower | Best | Optimized for Q&A |

**Current Default**: `all-MiniLM-L6-v2` (good balance for mobile use)

---

## Request Flow

### Search Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Action (Mobile)                                         │
└─────────────────────────────────────────────────────────────────┘
    User types "obsidian plugins" and presses Search
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. HTTP Request                                                 │
└─────────────────────────────────────────────────────────────────┘
    GET http://100.x.x.x:8080/search?q=obsidian+plugins&limit=10
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. FastAPI Endpoint (src/temoa/server.py)                       │
└─────────────────────────────────────────────────────────────────┘
    @app.get("/search")
    async def search_vault(q: str, limit: int = 10):
        results = synthesis.search(q, limit)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. SynthesisClient Wrapper (src/temoa/synthesis.py)             │
└─────────────────────────────────────────────────────────────────┘
    def search(self, query: str, limit: int):
        # Direct function call (model already loaded)
        embeddings = self.searcher.search(query, limit)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Synthesis Engine (old-ideas/synthesis/)                      │
└─────────────────────────────────────────────────────────────────┘
    - Generate query embedding (50-100ms)
    - Load stored embeddings from .temoa/embeddings.pkl (100-150ms)
    - Calculate cosine similarities (100-150ms)
    - Rank results (10-20ms)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Return Results                                               │
└─────────────────────────────────────────────────────────────────┘
    [
      {
        "path": "L/Gleanings/abc123.md",
        "title": "Dataview Plugin Guide",
        "similarity_score": 0.95,
        "obsidian_uri": "obsidian://open?vault=..."
      },
      ...
    ]
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Render in UI (search.html)                                   │
└─────────────────────────────────────────────────────────────────┘
    JavaScript updates results div with clickable links
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. User Clicks Result                                           │
└─────────────────────────────────────────────────────────────────┘
    obsidian:// URI triggers Obsidian app to open the note

Total Time: ~400ms (meets <2s target)
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
┌─────────────────────────────────────────────────────────────────┐
│ Server Startup (one-time, ~15 seconds)                          │
└─────────────────────────────────────────────────────────────────┘

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
   │  sentence-transformers downloads/caches model            │
   │  - First run: Download ~80MB (one-time, 30-60s)          │
   │  - Subsequent: Load from cache (~2-3s)                   │
   │  - Initialize neural network (~10-12s)                   │
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
status: active
migrated_from: null
---

A comprehensive guide to using the Dataview plugin for querying your Obsidian vault like a database.

<!-- Auto-fetched metadata (if available) -->
- Fetched: 2025-11-22T14:31:00
- Status Code: 200
- Content Type: text/html
```

### Configuration Files

```
Global Config (~/.config/temoa/config.json):
┌─────────────────────────────────────────────────────────┐
│ {                                                       │
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
│     "max_limit": 50,                                   │
│     "timeout": 10                                      │
│   }                                                    │
│ }                                                      │
└─────────────────────────────────────────────────────────┘

Vault-Local Config (vault/.temoa/config.json):
┌─────────────────────────────────────────────────────────┐
│ {                                                       │
│   "storage_dir": "~/custom-index-location",  // Override│
│   "excluded_paths": ["Private/", "Archive/"],          │
│   "custom_patterns": ["Notes/**/*.md"]                 │
│ }                                                      │
└─────────────────────────────────────────────────────────┘
```

### Index File Structure

```
.temoa/embeddings.pkl (pickle format):
┌─────────────────────────────────────────────────────────┐
│ {                                                       │
│   "embeddings": [                                       │
│     {                                                   │
│       "file_path": "L/Gleanings/abc123.md",            │
│       "embedding": [0.42, -0.13, ..., 0.21],  // 384 floats│
│       "metadata": {                                    │
│         "title": "Plugin Guide",                       │
│         "tags": ["obsidian", "plugins"],               │
│         "modified": "2025-11-22T10:00:00"              │
│       }                                                │
│     },                                                 │
│     { ... },  // 2000+ more entries                    │
│   ],                                                   │
│   "model_name": "all-MiniLM-L6-v2",                    │
│   "indexed_at": "2025-11-22T09:00:00",                 │
│   "total_files": 2281                                  │
│ }                                                      │
└─────────────────────────────────────────────────────────┘

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

Endpoints:
┌────────────────────┬─────────────────────────────────────┐
│ GET  /search       │ Semantic search                     │
│ GET  /archaeology  │ Temporal analysis of topics         │
│ GET  /stats        │ Vault statistics                    │
│ POST /reindex      │ Rebuild embedding index             │
│ POST /extract      │ Extract gleanings from daily notes  │
│ GET  /health       │ Server health check                 │
│ GET  /             │ Serve web UI (search.html)          │
│ GET  /docs         │ OpenAPI documentation               │
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
│ search(query, limit) → List[SearchResult]             │
│ archaeology(topic, limit) → List[TemporalResult]       │
│ reindex(force=False) → IndexStats                      │
│ get_stats() → VaultStats                              │
│ health_check() → HealthStatus                         │
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
│ $ sudo systemctl enable temoa  # Start on boot        │
│ $ journalctl -u temoa -f       # View logs            │
└────────────────────────────────────────────────────────┘

Option 4: Docker (containerized)
┌────────────────────────────────────────────────────────┐
│ $ docker-compose up -d                                 │
│ $ docker logs -f temoa                                 │
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

### PWA Support (Phase 3)

Progressive Web App for mobile:

```
┌─────────────────────────────────────────────────────────┐
│ manifest.json:                                          │
│   - Install to home screen                              │
│   - Offline fallback                                    │
│   - App-like experience                                 │
│                                                         │
│ Service Worker:                                         │
│   - Cache UI assets                                     │
│   - Background sync                                     │
└─────────────────────────────────────────────────────────┘
```

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
