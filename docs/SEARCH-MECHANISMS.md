# Search Mechanisms in Temoa

> **Purpose**: Technical documentation of all search algorithms, ranking methods, and quality enhancements in Temoa.

**Last Updated**: 2025-12-03
**Status**: Phase 3 Complete
**Version**: 0.6.0

---

## Overview

Temoa uses a multi-stage search pipeline. This document explains each mechanism, why it was chosen, and how they work together.

The search pipeline consists of:

1. **Core Search Methods** - Primary retrieval mechanisms (semantic, BM25, hybrid)
2. **Query Enhancement** - Pre-processing to improve query quality (expansion)
3. **Result Filtering** - Post-processing to remove unwanted results (status, type, score)
4. **Ranking Enhancement** - Re-ranking and boosting for better precision (time-aware, cross-encoder)
5. **Multi-Vault Support** - Search across multiple vaults with independent indexes

---

## Table of Contents

- [Core Search Methods](#core-search-methods)
  - [Semantic Search (Bi-Encoder)](#1-semantic-search-bi-encoder)
  - [Keyword Search (BM25)](#2-keyword-search-bm25)
  - [Hybrid Search (RRF)](#3-hybrid-search-rrf)
- [Query Enhancement](#query-enhancement)
  - [Query Expansion](#query-expansion)
- [Result Filtering](#result-filtering)
  - [Score Threshold Filtering](#1-score-threshold-filtering)
  - [Status Filtering (Inactive Gleanings)](#2-status-filtering-inactive-gleanings)
  - [Type-Based Filtering](#3-type-based-filtering)
- [Ranking Enhancement](#ranking-enhancement)
  - [Time-Aware Scoring](#1-time-aware-scoring)
  - [Cross-Encoder Re-Ranking](#2-cross-encoder-re-ranking)
- [Multi-Vault Support](#multi-vault-support)
- [Complete Pipeline Flow](#complete-pipeline-flow)
- [Performance Characteristics](#performance-characteristics)

---

## Core Search Methods

### 1. Semantic Search (Bi-Encoder)

**File**: `src/temoa/synthesis.py::SynthesisClient.search()`

**What it does**: Finds documents that are semantically similar to the query, even if they don't share exact keywords.

**How it works**:
1. Query and documents are encoded separately into dense vector embeddings (384 or 768 dimensions)
2. Uses sentence-transformers models (e.g., `all-MiniLM-L6-v2`, `all-mpnet-base-v2`)
3. Similarity computed via cosine distance between query and document embeddings
4. Model loaded once at startup, kept in memory for fast searches (~400ms)

**Why we chose it**:
- **Conceptual matching**: Finds "AI ethics research" when you search for "responsible machine learning"
- **Fast**: Pre-computed embeddings mean search is just vector comparison
- **Good recall**: Casts a wide net to find potentially relevant documents
- **Battle-tested**: Sentence-transformers is the industry standard for semantic search

**Strengths**:
- Understands synonyms, paraphrasing, and related concepts
- Works well for exploratory searches ("what did I write about X?")
- Excellent recall - rarely misses relevant documents

**Weaknesses**:
- **Weak precision**: Ranking order often suboptimal (relevant doc might be #7 instead of #1)
- **Misses exact mentions**: "Obsidian Sync" might rank lower than a document about Obsidian that mentions many plugins
- **Context dilution**: Important mentions buried in long documents get diluted in document-level embedding

**Performance**: ~400ms per search (model in memory)

**Example**:
```python
# Query: "machine learning ethics"
# Returns documents about:
# - AI safety
# - Responsible AI development
# - Algorithmic bias
# Even if they never use exact phrase "machine learning ethics"
```

---

### 2. Keyword Search (BM25)

**File**: `src/temoa/bm25_index.py::BM25Index.search()`

**What it does**: Finds documents containing exact or near-exact keyword matches, ranked by statistical relevance.

**How it works**:
1. Documents tokenized into words (lowercase, whitespace split)
2. BM25 (Best Match 25) algorithm scores each document based on:
   - **Term frequency**: How often query terms appear in document
   - **Inverse document frequency**: Rarity of terms (rare terms = higher score)
   - **Document length normalization**: Prevents long documents from dominating
3. Uses `rank_bm25` library (implementation of Okapi BM25)

**Why we chose it**:
- **Exact mention detection**: Finds things semantic search misses
- **Standard algorithm**: BM25 is used by Elasticsearch and Lucene
- **Fast**: Index fits in memory, search takes milliseconds
- **Lightweight**: ~5MB index for 3,000 documents

**Strengths**:
- Finds exact mentions that semantic search might miss
- Good for proper nouns ("Obsidian Sync", "Joan Doe")
- Works well for acronyms and technical terms
- Statistically sound ranking (TF-IDF family)

**Weaknesses**:
- No concept understanding (won't find "AI" when you search "artificial intelligence")
- Sensitive to exact wording
- Doesn't understand synonyms or paraphrasing

**Performance**: <50ms per search

**When used**:
- In hybrid mode (`hybrid=true` parameter)
- Via dedicated endpoint `/search?hybrid=true` (default in UI)

**Example**:
```python
# Query: "Obsidian Sync"
# BM25 will rank highest:
# 1. Document with multiple mentions of "Obsidian Sync"
# 2. Document mentioning "Sync" in Obsidian context
# Even if semantic similarity is lower
```

---

### 3. Hybrid Search (RRF)

**File**: `src/temoa/synthesis.py::SynthesisClient.hybrid_search()`

**What it does**: Combines semantic and keyword search results using Reciprocal Rank Fusion (RRF).

**How it works**:
1. Runs both semantic and BM25 search in parallel (fetch 3x desired results from each)
2. Merges results using RRF algorithm:
   ```
   RRF_score(doc) = sum(1 / (60 + rank_in_list)) for each list
   ```
3. **Special boosting**: High BM25 matches without semantic match get boosted to prevent RRF from penalizing them too much
4. Results include `similarity_score`, `bm25_score`, and `rrf_score` fields

**Why we chose it**:
- **Combines strengths**: Semantic recall + keyword precision
- **Simple algorithm**: RRF is used by many search engines
- **Complementary**: Semantic finds conceptual matches, BM25 catches exact mentions

**How RRF works in detail**:
- Documents appearing in both lists get highest scores (strong signal!)
- Documents in one list still appear (but ranked lower)
- Rank position matters more than absolute scores
- K=60 is standard constant (well-tested in research)

**Special Handling for BM25-only results**:
```python
# Problem: RRF heavily penalizes docs in only one list
# Solution: Boost high BM25 scores that missed semantic search
# Effect: "Obsidian Sync" exact mention won't be buried
```

**Performance**: ~450ms (semantic 400ms + BM25 50ms, parallel when possible)

**Configuration**:
- Enabled via `?hybrid=true` parameter (default in UI)
- Can be set as default in config: `"hybrid_search_enabled": true`

**Example**:
```python
# Query: "Obsidian Sync setup"
#
# Semantic finds:
# - "Setting up Obsidian Sync" (high similarity)
# - "Obsidian plugins overview" (mentions sync)
#
# BM25 finds:
# - "Obsidian Sync setup guide" (exact match)
# - "Sync troubleshooting" (keyword match)
#
# RRF merges:
# → "Obsidian Sync setup guide" ranks #1 (in both lists!)
# → "Setting up Obsidian Sync" ranks #2 (semantic + partial BM25)
```

---

## Query Enhancement

### Query Expansion

**File**: `src/temoa/query_expansion.py::QueryExpander.expand()`

**What it does**: Automatically expands short, ambiguous queries by adding relevant terms extracted from initial search results.

**How it works** (Pseudo-Relevance Feedback):
1. **Detection**: Triggers only for queries < 3 words (e.g., "AI", "obsidian sync")
2. **Initial search**: Runs search with original query, fetches top 5 results
3. **Term extraction**: Uses TF-IDF to find important terms in those 5 results
   - TF-IDF identifies terms that are:
     - Frequent in these results (TF = Term Frequency)
     - Rare in general corpus (IDF = Inverse Document Frequency)
4. **Expansion**: Appends top 3 terms to original query
5. **Re-search**: Runs new search with expanded query

**Why we chose it**:
- **No LLM needed**: TF-IDF is fast, deterministic, and doesn't require API calls
- **User's intent**: Initial results reflect what the user might be looking for
- **Standard technique**: Pseudo-relevance feedback is used in information retrieval
- **Minimal latency**: Only ~50ms for TF-IDF computation

**Strengths**:
- Disambiguates short queries automatically
- Uses actual vault content (not external knowledge)
- Transparent - expanded query shown to user

**Weaknesses**:
- Assumes top-5 initial results are relevant (garbage in, garbage out)
- Adds latency for short queries (~400ms extra search)
- Can go off-track if initial results are poor

**Performance**:
- Initial search: ~400ms
- TF-IDF extraction: ~50ms
- Re-search: ~400ms
- **Total**: ~850ms (only for queries < 3 words)

**Configuration**:
- Enabled by default (`?expand_query=true`)
- Can be disabled via `?expand_query=false`

**Example**:
```python
# Original query: "AI"
#
# Initial results contain:
# - "Machine learning ethics and safety"
# - "Neural network architectures"
# - "AI tools for writing"
#
# TF-IDF extracts: "machine learning", "ethics", "neural"
#
# Expanded query: "AI machine learning ethics neural"
#
# → Better results: More specific to ML/ethics context
```

**When to disable**:
- Query is already specific (>= 3 words)
- User wants exact match for short term
- Latency is critical

---

## Result Filtering

After retrieving results, several filters refine the list before presenting to user.

### 1. Score Threshold Filtering

**File**: `src/temoa/server.py::search()` (lines 608-611)

**What it does**: Removes results below minimum similarity score (semantic mode only).

**How it works**:
- Default threshold: `min_score=0.3` (configurable via `?min_score=` parameter)
- Only applies in **semantic-only mode** (not hybrid)
- Hybrid mode skips this (RRF score is different scale)

**Why we chose it**:
- **Quality control**: Prevents very weak matches from appearing
- **User control**: Let users tighten or loosen quality bar

**Configuration**: `?min_score=0.3` (default), range: 0.0-1.0

---

### 2. Status Filtering (Inactive Gleanings)

**File**: `src/temoa/server.py::filter_inactive_gleanings()`

**What it does**: Removes gleanings marked as `inactive` or `hidden` from search results.

**How it works**:
1. Reads frontmatter from each result
2. Checks `status:` field
3. Filters out:
   - `status: inactive` - Dead links, auto-detected by maintenance tool
   - `status: hidden` - Manually hidden by user
4. Keeps:
   - `status: active` - Normal gleanings
   - No status field - Regular vault documents

**Why we chose it**:
- **Gleaning lifecycle**: Dead links shouldn't pollute search results
- **User control**: Hide duplicates or unwanted gleanings
- **Auto-restore**: Inactive links automatically restored if they come back online

**Performance**: Fast (reads cached frontmatter from results, no file I/O)

---

### 3. Type-Based Filtering

**File**: `src/temoa/server.py::filter_by_type()`

**What it does**: Filters results by document `type` field in frontmatter.

**How it works**:
1. Reads `type:` field from frontmatter (cached in results)
2. Supports:
   - Single type: `type: gleaning`
   - Multiple types (YAML array): `type: [writering, article]`
3. Two modes:
   - **Inclusive** (`?include_types=gleaning,article`): Keep ONLY these types
   - **Exclusive** (`?exclude_types=daily`): Remove these types
4. Default: `exclude_types=daily` (hides daily notes)

**Why we chose it**:
- **Noise reduction**: Daily notes often clutter results
- **Focus search**: "Show only gleanings" or "hide reference docs"
- **Flexible**: Both whitelist and blacklist modes

**Performance**: <1ms (uses cached frontmatter)

**Configuration**:
- `?include_types=gleaning,article` - Whitelist
- `?exclude_types=daily,note` - Blacklist (default: `daily`)

**Example**:
```python
# Query: "obsidian plugins"
# Without filtering: 50 results (20 daily notes, 15 gleanings, 15 articles)
# With exclude_types=daily: 30 results (15 gleanings, 15 articles)
# With include_types=gleaning: 15 results (only gleanings)
```

---

## Ranking Enhancement

After filtering, these mechanisms improve ranking precision.

### 1. Time-Aware Scoring

**File**: `src/temoa/time_scoring.py::TimeAwareScorer.apply_boost()`

**What it does**: Boosts recent documents using exponential time-decay formula.

**How it works**:
1. Gets file modification time for each result
2. Calculates age in days
3. Applies exponential decay boost:
   ```python
   boost_factor = max_boost * (0.5 ** (days_old / half_life_days))
   boosted_score = similarity_score * (1 + boost_factor)
   ```
4. Default parameters:
   - `max_boost = 0.2` (20% boost for today's docs)
   - `half_life_days = 90` (boost decays by 50% every 3 months)

**Why we chose it**:
- **Recency matters**: Recent notes often more relevant to current interests
- **Gentle boost**: Doesn't completely override similarity scores
- **Configurable**: Users can adjust decay rate and max boost
- **Near-zero cost**: <5ms overhead

**Decay curve**:
- Today: +20% boost
- 90 days ago: +10% boost (half-life)
- 180 days ago: +5% boost
- 1 year ago: +2% boost
- Old docs still appear, just ranked slightly lower

**Performance**: <5ms (file mtime lookup is fast)

**Configuration** (in `config.json`):
```json
{
  "search": {
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  }
}
```

**Example**:
```python
# Query: "best AI tools"
#
# Before time boost:
# 1. "AI Tools Review 2021" (sim: 0.85, 3 years old)
# 2. "My AI Toolkit 2024" (sim: 0.83, recent)
#
# After time boost:
# 1. "My AI Toolkit 2024" (boosted: 0.83 * 1.20 = 0.996)
# 2. "AI Tools Review 2021" (boosted: 0.85 * 1.02 = 0.867)
```

---

### 2. Cross-Encoder Re-Ranking

**File**: `src/temoa/reranker.py::CrossEncoderReranker.rerank()`

**What it does**: Re-ranks top candidates using a more accurate but slower cross-encoder model.

**How it works** (Two-Stage Retrieval):

**Stage 1 - Fast Retrieval (Bi-Encoder)**:
- Semantic search retrieves top 100 candidates (~400ms)
- Good recall, weak precision

**Stage 2 - Precise Re-Ranking (Cross-Encoder)**:
- Process each (query, document) pair together
- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~90MB)
- Trained on millions of query-document pairs
- Learns relevance patterns bi-encoders can't capture
- Re-rank top 100, return top 10 (~200ms)

**Bi-Encoder vs Cross-Encoder**:

```
Bi-Encoder (current semantic search):
  Query → Embedding: [0.2, 0.8, -0.1, ...]
  Doc → Embedding:   [0.3, 0.7,  0.0, ...]
  Score = cosine_similarity(query_emb, doc_emb)

  ✓ Fast: Pre-computed embeddings
  ✗ Weak: No interaction between query and document

Cross-Encoder (re-ranking):
  Input: "[CLS] query text [SEP] document text [SEP]"
  → Transformer processes together
  → Output: Relevance score

  ✓ Accurate: Learns query-document interactions
  ✗ Slow: Must process each pair separately
```

**Why we chose it**:
- **Measured improvement**: 20-30% improvement in Precision@5
- **Standard approach**: Used by Elasticsearch, Weaviate, Pinecone
- **Acceptable latency**: ~200ms for 100 pairs is fast enough for mobile
- **Two-stage retrieval**: Bi-encoder recall + cross-encoder precision

**Performance**:
- Model loading: ~1s (one-time at startup)
- Re-ranking: ~2ms per pair, ~200ms for 100 pairs
- Total search time: ~600ms (400ms bi-encoder + 200ms cross-encoder)

**Quality Improvement** (measured):
```
Query: "obsidian"

WITHOUT re-ranking (bi-encoder only):
1. Obsidian Garden Gallery        (sim: 0.672)
2. 12 Best Alternatives            (sim: 0.643)
3. Claude AI for Obsidian          (sim: 0.632)

WITH re-ranking (cross-encoder):
1. mfarragher/obsidiantools        (cross: 4.673, sim: 0.575) ← Better!
2. Obsidian-Templates              (cross: 4.186, sim: 0.579)
3. 12 Best Alternatives            (cross: 3.157, sim: 0.643)
```

Notice: Cross-encoder correctly ranks "obsidiantools" #1 despite lower bi-encoder similarity, because it's more specifically about Obsidian itself.

**Configuration**:
- Enabled by default (`?rerank=true`)
- Disable with `?rerank=false` for faster searches
- Re-ranks top 100 candidates (configurable in code)

**When to disable**:
- Speed is critical (saves ~200ms)
- Very large result sets (re-ranking 1000+ items)
- Debugging (to isolate bi-encoder performance)

---

## Multi-Vault Support

**File**: `src/temoa/client_cache.py`, `src/temoa/config.py`

**What it does**: Search across multiple Obsidian vaults with independent indexes and fast vault switching.

**How it works**:
1. Each vault has independent index stored in `vault/.temoa/model-name/`
2. LRU cache keeps up to 3 vaults in memory (~1.5GB RAM total)
3. Vault switching is fast when cached (~400ms), slower on first load (~15-20s for model loading)
4. Web UI provides vault selector dropdown
5. CLI supports `--vault` flag for all commands

**Architecture**:
```python
# Config format
{
  "vaults": [
    {"name": "main", "path": "~/Obsidian/main-vault", "is_default": true},
    {"name": "work", "path": "~/Obsidian/work-vault", "is_default": false}
  ]
}

# LRU cache (max 3 vaults)
client_cache = {
  "main": SynthesisClient(...),    # Most recently used
  "work": SynthesisClient(...),    # Second most recent
  "archive": SynthesisClient(...)  # Least recent (evicted next)
}
```

**Why we chose it**:
- **Independent indexes**: Each vault has its own embeddings, no cross-contamination
- **LRU caching**: Fast switching between frequently-used vaults
- **Memory-bounded**: Limits to 3 vaults to prevent memory bloat
- **Co-location**: Index stored in vault (`.temoa/`) for simplicity

**Performance**:
- Cached vault switch: ~400ms (already in memory)
- Uncached vault switch: ~15-20s (load models + index)
- Memory per vault: ~500-800MB (model + embeddings + BM25 index)

**Configuration**:
```
# Search specific vault via API
GET /search?q=obsidian&vault=work

# Search specific vault via CLI
temoa search "obsidian" --vault work

# Index specific vault
temoa index --vault work
```

**Validation**:
- Each vault index includes metadata (vault path, model)
- Server validates vault path matches before operations
- Prevents accidental index corruption from wrong vault
- `--force` flag allows override with warning

---

## Complete Pipeline Flow

Here's how all mechanisms work together in the `/search` endpoint:

```
User Query: "AI" (short query)
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 0: Query Expansion (if query < 3 words)       │
│ - Fetch top 5 results with original query           │
│ - Extract key terms via TF-IDF                      │
│ - Append expansion terms                            │
│ - Result: "AI machine learning neural networks"     │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 1: Primary Retrieval                          │
│ - IF hybrid=true:                                   │
│   • Semantic search (top 150)                       │
│   • BM25 search (top 150)                           │
│   • Merge with RRF                                  │
│ - ELSE:                                             │
│   • Semantic search only (top 100)                  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: Score Filtering (semantic mode only)       │
│ - Remove results with similarity < min_score (0.3)  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Status Filtering                           │
│ - Remove inactive/hidden gleanings                  │
│ - Check frontmatter status field                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 4: Type Filtering                             │
│ - Apply include_types (whitelist)                   │
│ - Apply exclude_types (blacklist, default: daily)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 5: Time-Aware Boost (if enabled)              │
│ - Get file modification times                       │
│ - Apply exponential decay boost                     │
│ - Re-sort by boosted scores                         │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 6: Cross-Encoder Re-Ranking (if enabled)      │
│ - Take top 100 candidates                           │
│ - Score each (query, doc) pair with cross-encoder   │
│ - Re-sort by cross-encoder scores                   │
│ - Return top N results                              │
└─────────────────────────────────────────────────────┘
    ↓
Final Results (sorted by relevance)
```

**Default Configuration** (all features enabled):
```
?hybrid=true          → Hybrid search (BM25 + semantic)
?expand_query=true    → Query expansion for short queries
?rerank=true          → Cross-encoder re-ranking
?time_boost=true      → Time-aware scoring
?exclude_types=daily  → Hide daily notes
?min_score=0.3        → Minimum similarity threshold
```

---

## Performance Characteristics

### Latency Breakdown

**Fast Path** (long query, semantic-only, no re-ranking):
```
Semantic search:      ~400ms
Score filtering:        <1ms
Status filtering:       <1ms
Type filtering:         <1ms
─────────────────────────────
Total:                ~400ms
```

**Typical Path** (all features enabled):
```
Semantic search:      ~400ms
BM25 search:           ~50ms (parallel with semantic)
RRF merge:             ~10ms
Score filtering:        <1ms
Status filtering:       <1ms
Type filtering:         <1ms
Time-aware boost:       ~5ms
Cross-encoder:        ~200ms
─────────────────────────────
Total:                ~600ms
```

**Slow Path** (short query with expansion, all features):
```
Initial search:       ~400ms (for expansion)
TF-IDF extraction:     ~50ms
Expanded search:      ~400ms
BM25 search:           ~50ms (parallel)
RRF merge:             ~10ms
Filtering:              ~5ms
Time-aware boost:       ~5ms
Cross-encoder:        ~200ms
─────────────────────────────
Total:                ~900ms
```

**Mobile Target**: < 2 seconds (all scenarios well under target ✓)

### Memory Usage

- **Bi-encoder model**: ~400MB (all-MiniLM-L6-v2) or ~900MB (all-mpnet-base-v2)
- **Cross-encoder model**: ~90MB (ms-marco-MiniLM-L-6-v2)
- **BM25 index**: ~5MB per 3,000 documents
- **Embeddings**: ~2MB per 1,000 documents (384d) or ~5MB (768d)

**Total** (3,000 doc vault, MiniLM): ~500MB

### Scaling Characteristics

| Vault Size | Indexing Time | Search Time | Memory |
|------------|---------------|-------------|--------|
| 1,000 docs | ~50s          | ~400ms      | ~200MB |
| 3,000 docs | ~160s         | ~400ms      | ~500MB |
| 10,000 docs| ~8-10 min     | ~400ms      | ~1.5GB |

**Key insight**: Search time is **constant** regardless of vault size (vector similarity is O(n) but with fast BLAS operations).

---

## Decision Rationale Summary

| Mechanism | Why Chosen | Alternative Considered |
|-----------|------------|------------------------|
| **Semantic (Bi-Encoder)** | Fast, good recall, understands concepts | OpenAI embeddings (requires API, cost) |
| **BM25** | Catches exact mentions | TF-IDF (BM25 is strictly better) |
| **Hybrid (RRF)** | Simple, effective | Learned fusion (too complex) |
| **Query Expansion** | No LLM needed, uses vault content | LLM reformulation (Phase 4) |
| **Cross-Encoder** | 20-30% quality boost, acceptable latency | More candidates (diminishing returns) |
| **Time Boost** | Near-zero cost, gentle improvement | Manual date filters (less automatic) |

---

## Configuration Reference

### Search Endpoint Parameters

```
GET /search?
  q=<query>                    # Required: Search query
  &vault=<name>                # Optional: Vault to search (default: config vault)
  &limit=<int>                 # Optional: Max results (default: 10, max: 100)
  &min_score=<float>           # Optional: Min similarity (0.0-1.0, default: 0.3)
  &hybrid=<bool>               # Optional: Use hybrid search (default: true)
  &rerank=<bool>               # Optional: Use re-ranking (default: true)
  &expand_query=<bool>         # Optional: Expand short queries (default: true)
  &time_boost=<bool>           # Optional: Boost recent docs (default: true)
  &include_types=<csv>         # Optional: Whitelist types (e.g., "gleaning,article")
  &exclude_types=<csv>         # Optional: Blacklist types (default: "daily")
```

### Config File Options

```json
{
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 10,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  },
  "hybrid_search_enabled": true
}
```

---

## Future Enhancements

**Not Yet Implemented** (see Phase 4):

- **LLM-based query reformulation**: Better query understanding
- **Result clustering**: Group similar results together
- **Multi-field boosting**: Weight title matches higher than body matches
- **Learning to rank**: Machine learning model trained on user clicks

**Explicitly Skipped**:

- Elasticsearch/Solr integration (too heavy for local use)
- Graph-based retrieval (vault not connected enough)
- Neural search with ONNX (sentence-transformers works)

---

## Related Documentation

- [PHASE-3-PART-2-SEARCH-QUALITY.md](PHASE-3-PART-2-SEARCH-QUALITY.md) - Implementation plan for search enhancements
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and embeddings explanation
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Progress tracking across all phases
- [CHRONICLES.md](CHRONICLES.md) - Design discussions and decision history

---

**Created**: 2025-12-01
**Author**: Claude (with pborenstein)
**Purpose**: Technical reference for understanding Temoa's search mechanisms
