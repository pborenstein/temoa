# Search Mechanisms in Temoa

> **Purpose**: Technical documentation of all search algorithms, ranking methods, and quality enhancements in Temoa.

**Last Updated**: 2025-12-31
**Status**: Phase 3.5 In Progress (Adaptive Chunking & Search Profiles)
**Version**: 0.7.0

---

## Overview

Temoa uses a multi-stage search pipeline. This document explains each mechanism, why it was chosen, and how they work together.

The search pipeline consists of:

1. **Core Search Methods** - Primary retrieval mechanisms (semantic, BM25, hybrid)
2. **Query Enhancement** - Pre-processing to improve query quality (expansion)
3. **Result Filtering** - Post-processing to remove unwanted results (status, type, score)
4. **Ranking Enhancement** - Re-ranking and boosting for better precision (time-aware, cross-encoder)
5. **Adaptive Chunking** - Large document splitting for full content coverage (Phase 3.5.2)
6. **Search Profiles** - Optimized search modes for different content types (Phase 3.5.1)
7. **Multi-Vault Support** - Search across multiple vaults with independent indexes

---

## Table of Contents

- [Core Search Methods](#core-search-methods)
  - [Semantic Search (Bi-Encoder)](#1-semantic-search-bi-encoder)
  - [Keyword Search (BM25)](#2-keyword-search-bm25)
  - [Frontmatter-Aware Search (Tag Boosting)](#25-frontmatter-aware-search-tag-boosting)
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
- [Adaptive Chunking](#adaptive-chunking)
  - [How Chunking Works](#how-chunking-works)
  - [Chunk Deduplication](#chunk-deduplication)
  - [Configuration](#chunking-configuration)
- [Search Profiles](#search-profiles)
  - [Built-in Profiles](#built-in-profiles)
  - [Custom Profiles](#custom-profiles)
- [Multi-Vault Support](#multi-vault-support)
- [Pipeline Debugging](#pipeline-debugging)
  - [Pipeline Viewer UI](#pipeline-viewer-ui)
  - [Pipeline Stages](#pipeline-stages)
  - [API Usage](#api-usage)
  - [Performance Impact](#performance-impact)
  - [Use Cases](#use-cases)
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

### 2.5. Frontmatter-Aware Search (Tag Boosting)

**Files**: `src/temoa/bm25_index.py::BM25Index.build()`, `src/temoa/synthesis.py::hybrid_search()`
**Added**: 2025-12-14 (commit d39462f)

**What it does**: Leverages curated frontmatter metadata (tags, description) to dramatically boost relevance for documents matching query tags.

**How it works**:

**BM25 Layer** (Tag Indexing):
1. Tags and description fields are extracted from frontmatter
2. Tags are repeated 2x in indexed text (increases term frequency)
3. Description is repeated 2x (similar weight to tags)
4. Combined indexed text: `title + tags(2x) + description(2x) + content`

**Tag Boosting** (BM25 scoring):
1. When query matches document tags, apply 5x score multiplier
2. Track matched tags for transparency
3. Store both base and boosted scores

**Hybrid RRF Boost** (Aggressive preservation):
1. RRF fusion averages ranks, which can bury perfect tag matches
2. Tag-matched results get 1.5-2.0x max_rrf boost to overcome averaging
3. Mark as `tag_boosted: true` to prevent downstream re-ranking

**Why we chose it**:
- **Tags are categorical**: Unlike body text, tags are user-curated keywords that deserve special handling
- **Multi-layered**: BM25 handles keyword matching, aggressive boosting preserves it through RRF fusion
- **Measured success**: 100% success rate for tag queries (before: buried in results, after: #1)
- **Description integration**: Prepended to semantic embeddings + indexed in BM25 for dual benefit

**Strengths**:
- Perfect match for tag-based queries ("zettelkasten books" → documents tagged [zettelkasten, book])
- Respects user curation (tags are intentional metadata)
- Works with hybrid search (doesn't break semantic component)

**Weaknesses**:
- Requires frontmatter with tags field
- 5x boost is aggressive (may over-promote tag matches)
- Tag-boosted results skip cross-encoder re-ranking (assumes exact match is correct)

**Performance**: No additional latency (tags indexed during BM25 build)

**Configuration**:
```json
{
  "bm25": {
    "tag_boost": 5.0  // Multiplier for tag matches
  }
}
```

**Example**:
```python
# Query: "zettelkasten books"
# Document frontmatter:
#   title: "The Zettelkasten Method"
#   tags: [zettelkasten, book, note-taking]
#
# Without tag boosting:
# - BM25 score: 2.3
# - Rank: #7 (buried by longer docs mentioning both terms)
#
# With tag boosting:
# - BM25 base score: 2.3
# - Tags matched: [zettelkasten, book]
# - BM25 boosted score: 2.3 * 5.0 = 11.5
# - Rank: #1 (perfect match!)
```

**See also**:
- CHRONICLES.md Entry 38 (Frontmatter-Aware Search)
- test-vault/BM25_TAG_BOOSTING_RESULTS.md (experimental validation)

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
- **Disabled by default** (`?expand_query=false`) as of 2025-12-06
- Can be enabled via `?expand_query=true`
- Reason for default change: Short queries are often person names, which don't benefit from expansion

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
- **Flexible**: Both allowlist and blocklist modes

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

## Adaptive Chunking

**Files**: `synthesis/src/embeddings/chunking.py`, `src/temoa/synthesis.py::deduplicate_chunks()`
**Added**: Phase 3.5.2 (2025-12-30)

**What it does**: Automatically splits large documents into overlapping chunks to ensure full content coverage in semantic search.

**Problem Solved**: Embedding models have a 512 token limit (~2,500 characters). Before chunking, files larger than this had only their first ~2,500 characters searchable - the rest was invisible to search.

### How Chunking Works

**Detection Threshold**: Files >= 4,000 characters are chunked (conservative threshold ensures we only chunk files that truly need it)

**Chunking Strategy**:
1. **Chunk size**: 2,000 characters (stays well within 512 token limit)
2. **Chunk overlap**: 400 characters (preserves context at boundaries)
3. **Sliding window**: Each chunk advances by 1,600 characters (chunk_size - overlap)

**Smart Final Chunk Handling**:
- Small trailing chunks (<1,000 chars) are merged with previous chunk
- Prevents tiny fragments that add noise without value

**Example**:
```python
# Document: 5,000 characters
# chunk_size=2000, overlap=400

Chunk 0: chars 0-2000      (2,000 chars)
Chunk 1: chars 1600-3600   (2,000 chars, overlap: 1600-2000)
Chunk 2: chars 3200-5000   (1,800 chars, overlap: 3200-3600)

# If Chunk 2 was <1,000 chars, it would be merged into Chunk 1
```

**Metadata Enrichment**:
Each chunk includes:
- `chunk_index`: 0-based position (e.g., 0, 1, 2)
- `chunk_total`: Total chunks for this file (e.g., 3)
- `start_offset`: Character position in original file
- `end_offset`: Character position in original file
- `file_path`: Original file path
- `is_chunked_file`: Boolean flag

**Performance**: Chunking happens during indexing, not search. No search-time performance impact.

### Chunk Deduplication

**Problem**: Multiple chunks from same file can clutter results

**Solution** (`src/temoa/synthesis.py::deduplicate_chunks()`):
- Groups results by file path
- For files with multiple matching chunks:
  - **Default mode**: Keep only highest-scoring chunk
  - **All mode**: Keep all chunks with metadata
- Adds `matched_chunks` field showing how many chunks matched

**Example**:
```python
# Search finds 3 chunks from "Long Article.md"
# - Chunk 1: similarity 0.75
# - Chunk 2: similarity 0.82  ← Best match
# - Chunk 3: similarity 0.68

# Deduplication returns:
{
  "relative_path": "Long Article.md",
  "similarity_score": 0.82,        # Best chunk's score
  "matched_chunks": 3,              # How many chunks matched
  "is_chunked_file": true,          # Flag for UI
  "chunk_index": 1,                 # Which chunk won
  "chunk_total": 5                  # Total chunks in file
}
```

**Why best-chunk strategy**:
- Cleaner results (one entry per file in most cases)
- Highest-scoring chunk is most relevant to query
- `matched_chunks` metadata shows breadth of match
- Users can click through to see full file context in Obsidian

### Chunking Configuration

**Enabled by**:
- Search profiles (e.g., `deep` profile enables chunking)
- Default profile has `chunking_enabled: true`
- Per-vault configuration

**CLI Flags**:
```bash
# Enable chunking during indexing
temoa index --enable-chunking

# Choose embedding model (affects chunking threshold)
temoa index --model all-mpnet-base-v2
```

**API Parameters**:
```bash
# Chunking is automatic based on profile
GET /search?profile=deep  # Uses chunking for long-form content
```

**Profile Configuration**:
```python
SearchProfile(
    chunking_enabled=True,      # Enable chunking
    chunk_size=2000,            # Characters per chunk
    chunk_overlap=400,          # Overlap between chunks
    show_chunk_context=True,    # Show chunk boundaries in UI
    max_results_per_file=3      # Keep top 3 chunks (all mode)
)
```

**When Chunking is Disabled**:
- `repos` profile (gleanings are small, <4,000 chars)
- `keywords` profile (BM25 handles full text anyway)
- Files <4,000 chars (no need to chunk)

**Impact**:
- **Before**: 9MB book with 100,000 chars → only first 2,500 chars searchable
- **After**: Same book → 50 chunks, all 100,000 chars searchable
- **Example**: 2,006 files → 8,755 searchable chunks (4.4x content coverage)

**Files Modified**:
- `synthesis/src/embeddings/chunking.py` - Core chunking logic (207 lines)
- `synthesis/src/embeddings/vault_reader.py` - Integration with file reading
- `synthesis/src/embeddings/pipeline.py` - Chunking parameters
- `src/temoa/synthesis.py` - Deduplication and search integration

**See also**:
- [docs/IMPLEMENTATION.md Phase 3.5.2](IMPLEMENTATION.md#phase-352-adaptive-chunking-complete) - Implementation details
- [docs/phases/phase-3.5-specialized-search.md](phases/phase-3.5-specialized-search.md) - Full phase plan

---

## Search Profiles

**File**: `src/temoa/search_profiles.py`
**Added**: Phase 3.5.1 (2025-12-30)

**What it does**: Provides optimized search modes tailored for different content types and use cases. Each profile configures search weights, boosting, and features to optimize for specific scenarios.

**Why we need it**: Different searches need different strategies. Finding a GitHub repo by keywords is different from finding a conceptual match in long-form writing. Profiles make this easy.

### Built-in Profiles

| Profile | Best For | Hybrid Weight | BM25 Boost | Chunking | Cross-Encoder | Key Features |
|---------|----------|---------------|------------|----------|---------------|--------------|
| **repos** | GitHub repos, tools, libraries | 30% semantic<br>70% BM25 | 2.0x | Disabled | Disabled (speed) | Stars/topics boosting |
| **recent** | What you wrote/saved recently | 50/50 balanced | 1.0x | Enabled | Enabled | 7-day half-life, 90-day cutoff |
| **deep** | Long articles, books, essays | 80% semantic<br>20% BM25 | 1.0x | Enabled | Enabled | Show chunk context, 3 chunks/file |
| **keywords** | Technical terms, names, phrases | 20% semantic<br>80% BM25 | 1.5x | Enabled | Disabled (speed) | Fast exact matching |
| **default** | General-purpose search | 50/50 balanced | 1.0x | Enabled | Enabled | Current behavior (balanced) |

**Hybrid Weight Explained**:
- `0.0` = Pure BM25 (keyword-only)
- `0.5` = Balanced (50% semantic, 50% BM25)
- `1.0` = Pure semantic (concept-only)

### Profile Details

**repos - GitHub Repositories & Tech**
```python
SearchProfile(
    hybrid_weight=0.3,              # Favor keywords over concepts
    bm25_boost=2.0,                 # Strong keyword matching
    metadata_boost={
        "github_stars": {
            "enabled": True,
            "scale": "log",          # Logarithmic (1k stars ≈ 10k stars)
            "max_boost": 0.5         # Up to 50% boost
        },
        "github_topics": {
            "match_boost": 3.0       # 3x when topic matches query
        }
    },
    cross_encoder_enabled=False,    # Speed over precision
    chunking_enabled=False,         # Gleanings are small
    default_include_types=["gleaning"]
)
```

**Use cases**:
- "python web framework" → Finds Flask/Django repos by keywords
- "machine learning library" → Boosts popular repos (scikit-learn, PyTorch)
- "obsidian plugin" → Matches GitHub topics

**recent - Recent Work (Last 90 Days)**
```python
SearchProfile(
    time_decay_config={
        "half_life_days": 7,        # Aggressive - prefer this week
        "max_boost": 0.5            # Up to 50% boost for today
    },
    max_age_days=90,                # Hard cutoff - ignore older
    default_include_types=["daily", "note", "writering"]
)
```

**Use cases**:
- "meeting notes" → Finds this week's meetings first
- "project ideas" → Shows recent brainstorming
- What did I work on this month?

**deep - Long-Form Content**
```python
SearchProfile(
    hybrid_weight=0.8,              # Strong semantic understanding
    chunking_enabled=True,
    chunk_size=2000,
    show_chunk_context=True,        # Show where in doc
    max_results_per_file=3,         # Show top 3 chunks
    default_exclude_types=["daily", "gleaning"]
)
```

**Use cases**:
- Research papers and articles
- Book notes and summaries
- Finding specific sections in long documents

**keywords - Exact Matching**
```python
SearchProfile(
    hybrid_weight=0.2,              # Strong BM25 bias
    bm25_boost=1.5,
    cross_encoder_enabled=False,    # Speed
    query_expansion_enabled=False   # No fuzzy matching
)
```

**Use cases**:
- "Philip Borenstein" → Exact name match
- "obsidian://vault" → Technical strings
- Code snippets and URLs

### Using Profiles

**Web UI** (when UI is updated):
```
[Dropdown: Select Profile]
  ○ Balanced (default)
  ○ Repos & Tech
  ○ Recent Work
  ○ Deep Reading
  ○ Keyword Search
```

**API**:
```bash
# Use specific profile
GET /search?q=obsidian&profile=repos

# List available profiles
GET /profiles
```

**CLI**:
```bash
# Search with profile
temoa search "obsidian plugin" --profile repos

# List profiles
temoa profiles
```

**Response includes profile used**:
```json
{
  "query": "obsidian",
  "profile": "repos",
  "results": [...]
}
```

### Custom Profiles

**Configuration** (in `config.json`):
```json
{
  "search_profiles": {
    "my-research": {
      "display_name": "Research Papers",
      "description": "Academic papers with citation focus",
      "hybrid_weight": 0.9,
      "bm25_boost": 1.0,
      "chunking_enabled": true,
      "chunk_size": 3000,
      "default_include_types": ["article", "paper"],
      "cross_encoder_enabled": true
    }
  }
}
```

**Loading**:
- Custom profiles loaded at server startup
- Cannot override built-in profiles (error if name conflicts)
- Validated on load (missing required fields → error)

**See also**:
- [src/temoa/search_profiles.py](../src/temoa/search_profiles.py) - Full profile definitions
- [docs/phases/phase-3.5-specialized-search.md](phases/phase-3.5-specialized-search.md) - Design rationale

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
│ Stage 2: Chunk Deduplication                        │
│ - Group results by source file                      │
│ - Keep best-scoring chunk per file                  │
│ - Preserves diverse file coverage                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Score Filtering (semantic mode only)       │
│ - Remove results with similarity < min_score (0.3)  │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 4: Status Filtering                           │
│ - Remove inactive/hidden gleanings                  │
│ - Check frontmatter status field                    │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 5: Type Filtering                             │
│ - Apply include_types (allowlist)                   │
│ - Apply exclude_types (blocklist, default: daily)   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 6: Cross-Encoder Re-Ranking (if enabled)      │
│ - Take top 100 candidates                           │
│ - Score each (query, doc) pair with cross-encoder   │
│ - Re-sort by cross-encoder scores                   │
└─────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────┐
│ Stage 7: Time-Aware Boost (if enabled)              │
│ - Get file modification times                       │
│ - Apply exponential decay boost                     │
│ - Re-sort by boosted scores                         │
│ - Return top N results                              │
└─────────────────────────────────────────────────────┘
    ↓
Final Results (sorted by relevance)
```

**Default Configuration** (most features enabled):
```
?hybrid=true          → Hybrid search (BM25 + semantic)
?expand_query=false   → Query expansion disabled (since 2025-12-06)
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

### Chunking Impact

**With chunking enabled** (Phase 3.5.2):
- **Indexing time**: ~15-25% longer (more chunks to embed)
- **Search time**: No change (~400ms) - search is still constant time
- **Storage**: 4-5x more embeddings (2,006 files → 8,755 chunks example)
- **Memory**: Slightly higher (proportional to chunk count)
- **Example**: 3,000 file vault with many large documents
  - Without chunking: ~160s indexing, 3,000 embeddings
  - With chunking: ~185-200s indexing, ~13,000 embeddings (4.4x)

**Chunk deduplication overhead**: <10ms per search (negligible)

**Trade-offs**:
- ✓ Full content searchable (100% coverage vs. ~25% before)
- ✓ No search-time penalty
- ✗ Longer initial indexing
- ✗ More disk space for embeddings
- ✗ Slightly more RAM for chunk metadata

**Recommendation**: Enable chunking for vaults with long-form content (books, articles, research papers). Disable for vaults with mostly short notes (daily notes, fleeting thoughts).

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
| **Adaptive Chunking** | Full content coverage, no search penalty | Larger embedding models (more expensive) |
| **Search Profiles** | Optimized for use cases, simple to use | Manual parameter tuning (too complex) |

---

## Configuration Reference

### Search Endpoint Parameters

```
GET /search?
  q=<query>                    # Required: Search query
  &vault=<name>                # Optional: Vault to search (default: config vault)
  &profile=<name>              # Optional: Search profile (default, repos, recent, deep, keywords)
  &limit=<int>                 # Optional: Max results (default: 10, max: 100)
  &min_score=<float>           # Optional: Min similarity (0.0-1.0, default: 0.3)
  &hybrid=<bool>               # Optional: Use hybrid search (default: true, overridden by profile)
  &rerank=<bool>               # Optional: Use re-ranking (default: true, overridden by profile)
  &expand_query=<bool>         # Optional: Expand short queries (default: false, changed 2025-12-06)
  &time_boost=<bool>           # Optional: Boost recent docs (default: true, overridden by profile)
  &include_types=<csv>         # Optional: Whitelist types (e.g., "gleaning,article")
  &exclude_types=<csv>         # Optional: Blacklist types (default: "daily")
  &pipeline_debug=<bool>       # Optional: Return pipeline state for debugging (default: false)
```

**Note**: When using `profile` parameter, profile settings take precedence over individual flags (`hybrid`, `rerank`, `time_boost`, etc.). You can still override specific settings by passing explicit parameters.

**Profile API Endpoint**:
```
GET /profiles                  # List all available search profiles
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

## Pipeline Debugging

**Added**: 2026-01-21 (Phase 3 Complete)

Temoa includes a pipeline viewer tool to visualize how results flow through the 8-stage search pipeline. This is useful for understanding why specific results appear, disappear, or change ranks during search.

### Pipeline Viewer UI

Access the pipeline viewer at: `http://localhost:8080/pipeline`

The UI provides:
- **Summary metrics**: Total time, initial/final result counts, filtering statistics
- **Stage-by-stage visualization**: See results at each pipeline stage
- **Rank change tracking**: Visualize how re-ranking and time boost affect result order
- **Filtering details**: See which results were removed and why
- **Export functionality**: Download full pipeline state as JSON

### Pipeline Stages

The search pipeline consists of 8 stages (0-7):

1. **Stage 0: Query Expansion** - TF-IDF expansion for short queries (<3 words)
   - Shows: Original query, expanded query, expansion terms added

2. **Stage 1: Primary Retrieval & Chunk Deduplication** - Semantic + BM25 hybrid search
   - Shows: Search mode (hybrid/semantic), result counts, top 20 results with scores
   - Note: Chunk deduplication happens inside `hybrid_search()` (best chunk per file)

3. **Stage 3: Score Filtering** - Remove low-scoring results (semantic-only mode)
   - Shows: Before/after counts, min score threshold, removed items
   - Only applied in semantic mode (not hybrid)

4. **Stage 4: Status Filtering** - Remove inactive/hidden gleanings
   - Shows: Before/after counts, removed items with status

5. **Stage 5: Type Filtering** - Apply include/exclude type filters
   - Shows: Before/after counts, include/exclude rules, removed items with types

6. **Stage 6: Cross-Encoder Re-Ranking** - Precision improvement via re-scoring
   - Shows: Rank changes (before→after), score deltas, tag-boosted preservation

7. **Stage 7: Time-Aware Boost** - Recency boost with exponential decay
   - Shows: Boosted items with boost amounts, rank changes

### API Usage

Enable pipeline debugging by adding `pipeline_debug=true` to the search endpoint:

```bash
GET /search?q=obsidian&pipeline_debug=true&limit=10
```

**Response Structure**:

```json
{
  "query": "obsidian",
  "results": [...],
  "total": 10,
  "pipeline": {
    "query": {
      "original": "obsidian",
      "expanded": null,
      "vault": "amoxtli",
      "profile": "default"
    },
    "config": {
      "hybrid": true,
      "rerank": true,
      "expand_query": false,
      "time_boost": true,
      "limit": 10,
      "min_score": 0.3,
      "include_types": null,
      "exclude_types": ["daily"]
    },
    "stages": [
      {
        "stage_num": 0,
        "stage_name": "Query Expansion",
        "result_count": 0,
        "results_preview": [],
        "metadata": {
          "original_query": "obsidian",
          "expanded_query": null,
          "expansion_terms": [],
          "applied": false
        },
        "timing_ms": 0.0
      },
      {
        "stage_num": 1,
        "stage_name": "Primary Retrieval & Chunk Deduplication",
        "result_count": 20,
        "results_preview": [
          {
            "relative_path": "file.md",
            "title": "File Title",
            "similarity_score": 0.8234,
            "bm25_score": 15.32,
            "rrf_score": 0.0456,
            "tag_boosted": true,
            "tags_matched": ["obsidian", "plugins"]
          }
        ],
        "metadata": {
          "search_mode": "hybrid",
          "search_limit": 20,
          "hybrid_enabled": true,
          "note": "Chunk deduplication happens inside hybrid_search (best chunk per file)"
        },
        "timing_ms": 412.3
      }
    ],
    "summary": {
      "total_time_ms": 710.5,
      "initial_results": 150,
      "final_results": 10,
      "total_filtered": 140,
      "stages_count": 7
    }
  }
}
```

### Performance Impact

Pipeline debugging adds minimal overhead:

- **Disabled** (`pipeline_debug=false`): No overhead, normal search performance
- **Enabled** (`pipeline_debug=true`): ~20-50ms overhead for state capture and formatting
- **Payload size**: ~50-200KB additional JSON (top 20 results per stage)

The overhead comes from:
- Shallow copying results for before/after comparisons
- Formatting result previews (path + scores)
- Calculating rank changes between stages

### Use Cases

1. **Understanding tag boosting**: See how BM25 tag matches get 5x boost in hybrid mode
2. **Debugging filtering**: Understand why expected results don't appear
3. **Tuning re-ranking**: See how cross-encoder changes result order
4. **Profile optimization**: Compare pipeline behavior across different profiles
5. **Performance analysis**: Identify slow stages (timing per stage)

### Related Tools

The pipeline viewer complements existing debugging tools:

- **Score Mixer (`/harness`)**: Live score weight tuning (semantic, BM25, RRF)
- **Pipeline Viewer (`/pipeline`)**: Stage-by-stage result flow visualization (this tool)
- **Search UI (`/`)**: Main search interface with profile selector

All three tools are interconnected via navigation links in the header.

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
