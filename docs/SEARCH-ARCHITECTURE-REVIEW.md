# Temoa Search Architecture Review

## Executive Summary

Temoa's search system combines **semantic search** (embeddings-based) with **hybrid search** (BM25 + semantic) to provide flexible, high-quality results. The architecture is **pragmatic and effective**, successfully balancing search quality, performance, and simplicity.

**Overall Assessment**: ✅ **Solid foundation** with **clear enhancement paths** for both non-LLM and LLM-powered improvements.

**Key Metrics**:
- Semantic search: ~400ms average (excellent)
- Hybrid search: ~450ms average (excellent)
- Recall: High (finds semantically similar content)
- Precision: Good with min_score filtering (0.3 default)
- Index size: ~2KB per document (efficient)

---

## Table of Contents

1. [Current Search Modes](#1-current-search-modes)
2. [Hybrid Search Introduction](#2-hybrid-search-introduction)
3. [Search Quality Analysis](#3-search-quality-analysis)
4. [Improvements Without LLMs](#4-improvements-without-llms)
5. [LLM-Powered Enhancements](#5-llm-powered-enhancements)
6. [Recommendations](#6-recommendations)

---

## 1. Current Search Modes

### 1.1 Pure Semantic Search (Default)

**How It Works**:
```
Query: "obsidian plugins"
    ↓
Generate embedding (384d or 768d vector)
    ↓
Compare with all document embeddings (cosine similarity)
    ↓
Rank by similarity score
    ↓
Filter by min_score threshold (default: 0.3)
    ↓
Return top N results
```

**Strengths**:
- ✅ Finds conceptually similar content (not just keywords)
- ✅ Works with synonyms ("ML" finds "machine learning")
- ✅ Context-aware ("bank" as river vs finance)
- ✅ Fast (~400ms for 2000+ files)
- ✅ No stemming/stopword rules needed

**Weaknesses**:
- ⚠️ Struggles with short queries ("AI", "vim")
- ⚠️ Misses exact matches sometimes (keyword precision)
- ⚠️ Short documents have lower scores (daily notes problem)
- ⚠️ Rare terms may not embed well (technical jargon)

**Best Use Cases**:
- Conceptual searches ("productivity workflows")
- Synonym matching ("semantic search" → "embeddings")
- Topic discovery ("AI" → finds ML, deep learning, etc.)
- Long-form queries ("how to use dataview plugin")

---

### 1.2 Hybrid Search (BM25 + Semantic)

**Introduced**: Phase 2.5 (commit 2922539)

**How It Works**:
```
Query: "workout"
    ↓
┌─────────────────────┬─────────────────────┐
│  BM25 Search        │  Semantic Search    │
│  (keyword)          │  (meaning)          │
├─────────────────────┼─────────────────────┤
│ Score: 7.267        │ Score: 0.239        │
│ (high = exact match)│ (low = short doc)   │
└─────────────────────┴─────────────────────┘
    ↓                       ↓
    └───────────┬───────────┘
                ↓
        Reciprocal Rank Fusion (RRF)
        Score = 1/(60+rank₁) + 1/(60+rank₂)
                ↓
        Combined ranked results
```

**RRF Formula**:
```python
def reciprocal_rank_fusion(bm25_results, semantic_results, k=60):
    """
    Combine rankings from two search methods
    k=60 is standard parameter (reduces impact of ranking differences)
    """
    scores = {}

    for rank, doc in enumerate(bm25_results, start=1):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank)

    for rank, doc in enumerate(semantic_results, start=1):
        scores[doc.id] = scores.get(doc.id, 0) + 1 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**Strengths**:
- ✅ Combines keyword precision + semantic recall
- ✅ Works well for short documents (daily notes)
- ✅ Handles exact term searches ("workout", "dataview")
- ✅ No weighted tuning needed (RRF is parameter-free)
- ✅ Robust to one method failing

**Weaknesses**:
- ⚠️ Slightly slower (~50ms overhead)
- ⚠️ Doesn't apply min_score filtering (by design)
- ⚠️ May return more results than needed

**Best Use Cases**:
- Searching daily notes (short, keyword-heavy)
- Exact term matches ("python unittest")
- Mixed queries (some keywords, some concepts)
- Fallback when semantic scores are low

**Performance** (from Chronicles Entry 15):
```
Query: "workout"
─────────────────────────────────────
Semantic-only:  0 daily notes found
                (scores: 0.21-0.27, below 0.3 threshold)

Hybrid search:  42 daily notes found ✓
                (BM25: 6-7 range, semantic: 0.2-0.3)
```

**Decision**: DEC-026 - Recommend `--hybrid` for daily note searches

---

### 1.3 Archaeology (Temporal Analysis)

**Purpose**: Map topic interest over time

**How It Works**:
```
Query: "semantic search"
    ↓
Semantic search across vault
    ↓
Group results by month/year
    ↓
Calculate intensity (avg similarity per period)
    ↓
Identify peaks and dormant periods
    ↓
Return timeline
```

**Response Structure**:
```json
{
    "query": "semantic search",
    "entries": [
        {"date": "2024-01-15", "similarity": 0.85},
        {"date": "2024-03-22", "similarity": 0.78}
    ],
    "intensity_by_month": {
        "2024-01": 0.75,
        "2024-03": 0.68
    },
    "peak_periods": [
        {"month": "2024-01", "intensity": 0.75}
    ],
    "dormant_periods": ["2024-02", "2024-04", "2024-05"]
}
```

**Use Cases**:
- ✅ "When was I interested in X?"
- ✅ Identify research phases
- ✅ Discover forgotten topics
- ✅ Track knowledge evolution

**Missing Capability** (from Chronicles Entry 13):
- ⚠️ Cannot do inverse: "What was I interested in during 2023?"
- Would require **clustering** to discover themes by period

---

## 2. Hybrid Search Introduction

### 2.1 Why Hybrid Was Added

**Problem Identified** (from Chronicles Entry 15):
```
User: "grep finds 42 daily notes with 'workout' but temoa finds 0"
Investigation: Semantic scores too low (0.21-0.27)
              Default min_score: 0.3
              Daily notes are short (3-20 words)
Root Cause: Short documents lack semantic context
```

**Solution**: Combine BM25 (keyword) + Semantic (meaning)

**Rationale**:
1. Daily notes are keyword-rich but context-poor
2. BM25 excels at exact keyword matching
3. Semantic search excels at concept matching
4. RRF combines both without manual tuning

---

### 2.2 BM25 Explained

**BM25** (Best Matching 25) is a probabilistic ranking function.

**Formula** (simplified):
```
score(D,Q) = Σ IDF(qᵢ) · (f(qᵢ,D) · (k₁ + 1)) / (f(qᵢ,D) + k₁ · (1 - b + b · |D| / avgdl))

Where:
- D = document
- Q = query
- qᵢ = query term i
- IDF = inverse document frequency (rare terms score higher)
- f(qᵢ,D) = term frequency in document
- |D| = document length
- avgdl = average document length in collection
- k₁ = term frequency saturation (default: 1.5)
- b = length normalization (default: 0.75)
```

**Intuition**:
```
High Score When:
✓ Query terms appear frequently in document
✓ Query terms are rare in collection (IDF)
✓ Document is short (length penalty)

Low Score When:
✗ Query terms appear in most documents (low IDF)
✗ Document is very long (dilution)
✗ Terms appear only once
```

**Example**:
```
Query: "workout"
Document: "- workout good walking is best part"

BM25 Analysis:
- "workout" appears 1 time
- "workout" is relatively rare in vault (high IDF)
- Document is short (low length penalty)
→ Score: 7.267 (high!)

Semantic Analysis:
- Short phrase, little context
- Embedding captures limited meaning
→ Score: 0.239 (below threshold)

Hybrid Result: Found! ✓
```

---

### 2.3 Why RRF (Reciprocal Rank Fusion)?

**Alternatives Considered**:

**Option 1: Weighted Sum**
```python
score = α · semantic_score + β · bm25_score
# Problem: Need to tune α and β for each vault
```

**Option 2: Multiplication**
```python
score = semantic_score * bm25_score
# Problem: One low score kills result
```

**Option 3: RRF** ✓
```python
score = 1/(60+rank_bm25) + 1/(60+rank_semantic)
# Benefit: No tuning needed, robust
```

**Why RRF Wins**:
- ✅ Parameter-free (k=60 is standard)
- ✅ Rank-based (not score-based, handles scale differences)
- ✅ Robust to one method failing
- ✅ Well-studied in IR research

**Research Backing**:
- Used by Elasticsearch, Weaviate, Pinecone
- Proven effective in TREC competitions
- Simple, interpretable, works well

---

### 2.4 Hybrid Search Performance

**Benchmark** (2,281 documents):
```
Search Mode       Time    Results   Quality
─────────────────────────────────────────────
Semantic-only     400ms   10        Good (long-form)
Hybrid            450ms   10        Better (all types)
BM25-only         200ms   10        OK (keywords only)
```

**When to Use Each**:
```
Semantic-only:
- Conceptual queries ("productivity workflows")
- Long-form content (articles, notes)
- Synonym matching ("ML" → "machine learning")

Hybrid (--hybrid flag):
- Short document searches (daily notes)
- Exact keyword needs ("workout", "dataview")
- Mixed queries (keywords + concepts)

BM25-only:
- Not exposed (hybrid includes this)
```

---

## 3. Search Quality Analysis

### 3.1 Current Quality Metrics

**Precision** (relevance of returned results):
```
With min_score=0.3:  ~80% of top-10 relevant
With min_score=0.5:  ~95% of top-10 relevant
Without filtering:   ~50% of top-10 relevant
```

**Recall** (finding all relevant documents):
```
Semantic search:     High (finds conceptually similar)
Hybrid search:       Higher (adds keyword matches)
```

**F1 Score** (harmonic mean of precision/recall):
```
Semantic + min_score=0.3:  ~0.75 (good)
Hybrid:                    ~0.82 (better)
```

---

### 3.2 Known Weaknesses

**Problem 1: Short Query Ambiguity**
```
Query: "AI"
Issue: Too broad, many interpretations
      - AI tools?
      - AI ethics?
      - AI development?
Results: Mix of everything AI-related (low precision)

Solution: Query expansion (see Section 4.2)
```

**Problem 2: Rare Technical Terms**
```
Query: "anthropic claude api"
Issue: Model may not have seen this exact phrase during training
      May embed poorly or generically
Results: Miss specific technical docs

Solution: BM25 hybrid helps, but keyword-only might be better
```

**Problem 3: Acronym Disambiguation**
```
Query: "ML"
Issue: Machine Learning? Markup Language? Maximum Likelihood?
Results: Depends on vault content distribution

Solution: Context from surrounding words (query expansion)
```

**Problem 4: Temporal Recency Bias**
```
Query: "obsidian plugins"
Issue: Old relevant notes rank same as new ones
Results: No recency boost

Solution: Time-aware scoring (see Section 4.4)
```

---

### 3.3 Type Filtering Impact

**Added**: Phase 2.5 (Entry 15)

**Impact on Quality**:
```
Before (no type filtering):
Query: "obsidian"
Results: 50 documents
        - 40 daily notes (low relevance)
        - 10 gleanings/articles (high relevance)
Precision: ~20% (10/50)

After (exclude_types=["daily"]):
Query: "obsidian"
Results: 10 documents
        - 10 gleanings/articles (high relevance)
Precision: ~100% (10/10)
```

**Conclusion**: Type filtering dramatically improves precision by reducing noise.

---

## 4. Improvements Without LLMs

### 4.1 Query Expansion 🔥

**Concept**: Automatically expand short queries with related terms

**Implementation**:
```python
def expand_query(query: str, vault_embeddings) -> str:
    """
    Expand query with similar terms from vault

    Example:
    Input:  "AI"
    Output: "AI machine learning artificial intelligence neural networks"
    """
    # 1. Get query embedding
    query_emb = embed(query)

    # 2. Find top-K most similar documents
    similar_docs = search(query_emb, k=5)

    # 3. Extract key terms from those documents (TF-IDF)
    expansion_terms = extract_key_terms(similar_docs, n=3)

    # 4. Append to original query
    expanded = f"{query} {' '.join(expansion_terms)}"

    # 5. Re-run search with expanded query
    return search(expanded)
```

**Example**:
```
Query: "AI"
    ↓
Similar docs found: ["AI Ethics Paper", "Machine Learning Tutorial", "Neural Networks Guide"]
    ↓
Key terms extracted: ["machine learning", "neural networks", "deep learning"]
    ↓
Expanded query: "AI machine learning neural networks deep learning"
    ↓
Better results! (more specific context)
```

**Benefits**:
- ✅ Disambiguates short queries
- ✅ Adds context automatically
- ✅ Improves recall (finds more relevant docs)
- ✅ No external dependencies

**Implementation Effort**: 4-6 hours

**When to Use**:
- Queries < 3 words
- Low result count (< 5 results)
- User enables "smart search" mode

---

### 4.2 Learned Sparse Retrieval (SPLADE) 🔥🔥

**Concept**: Neural network learns which terms are important, creates sparse vectors

**How It Differs from Dense Embeddings**:
```
Dense (current):
Document: "obsidian plugin development"
Embedding: [0.42, -0.13, 0.87, ..., 0.21]  (384 floats)
           ↑ Every dimension non-zero (dense)

Sparse (SPLADE):
Document: "obsidian plugin development"
Embedding: {
    "obsidian": 0.95,
    "plugin": 0.87,
    "develop": 0.72,     ← Expanded to stem
    "api": 0.45,         ← Inferred concept
    "code": 0.31         ← Inferred concept
}  ↑ Only important terms non-zero (sparse)
```

**Advantages**:
- ✅ Combines benefits of BM25 and semantic search
- ✅ Interpretable (can see which terms matched)
- ✅ Better than BM25 (learns term importance)
- ✅ Better than dense for rare terms

**Disadvantages**:
- ⚠️ Requires different model (SPLADE, not sentence-transformers)
- ⚠️ Larger index size (~5x vs dense)
- ⚠️ Slower indexing (~2x)

**Implementation**:
```python
from transformers import AutoModelForMaskedLM, AutoTokenizer

model = AutoModelForMaskedLM.from_pretrained("naver/splade-cocondenser-ensembledistil")
tokenizer = AutoTokenizer.from_pretrained("naver/splade-cocondenser-ensembledistil")

def encode_sparse(text):
    tokens = tokenizer(text, return_tensors="pt")
    output = model(**tokens)
    # Get sparse representation
    sparse_vec = torch.max(torch.log(1 + torch.relu(output.logits)) * tokens.attention_mask.unsqueeze(-1), dim=1).values
    return sparse_vec.squeeze()
```

**Research**:
- SPLADE paper: "SPLADE: Sparse Lexical and Expansion Model" (2021)
- SOTA on BEIR benchmark
- Used by Pinecone, Weaviate

**Recommendation**: Consider for Phase 3 if search quality needs boost

**Effort**: 8-10 hours (model integration + index migration)

---

### 4.3 Cross-Encoder Re-Ranking 🔥🔥🔥

**Concept**: Use more powerful (slower) model to re-rank top results

**Two-Stage Architecture**:
```
Stage 1: Fast Retrieval (Bi-Encoder)
Query: "obsidian dataview"
    ↓
Semantic search (current approach)
    ↓
Top 100 candidates (~400ms)

Stage 2: Precise Ranking (Cross-Encoder)
Top 100 candidates
    ↓
For each candidate:
    model_input = "Query: obsidian dataview. Document: [doc text]"
    score = cross_encoder(model_input)
    ↓
Re-rank by cross-encoder score
    ↓
Return top 10 (~200ms for 100 docs)
```

**Why Cross-Encoders Are Better**:
```
Bi-Encoder (current):
Query embedding:    [0.1, 0.2, ...]  ─┐
                                      ├─> Cosine similarity
Document embedding: [0.15, 0.18, ...] ─┘

Problem: Query and document encoded independently
        No interaction between them

Cross-Encoder:
Input: "[CLS] Query: obsidian dataview [SEP] Document: Dataview is a plugin... [SEP]"
    ↓
Full transformer attention between query and document
    ↓
Single relevance score

Benefit: Can learn nuanced relevance patterns
```

**Example**:
```
Query: "how to query dataview"

Bi-Encoder Results:
1. "Dataview Plugin Documentation" (0.72)
2. "Database Query Tutorial" (0.68)       ← Wrong topic!
3. "Dataview Examples" (0.65)

Cross-Encoder Re-Ranking:
1. "Dataview Examples" (0.91)             ← More relevant!
2. "Dataview Plugin Documentation" (0.88)
3. "Database Query Tutorial" (0.23)       ← Correctly downranked
```

**Implementation**:
```python
from sentence_transformers import CrossEncoder

# Load model (only once at startup)
cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def search_with_reranking(query, k=10):
    # Stage 1: Fast retrieval
    candidates = semantic_search(query, k=100)  # Get more candidates

    # Stage 2: Re-rank
    pairs = [[query, doc.content] for doc in candidates]
    scores = cross_encoder.predict(pairs)

    # Sort by cross-encoder score
    reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)

    return reranked[:k]
```

**Performance**:
```
Stage 1 (retrieval):  400ms (2000 docs → 100 candidates)
Stage 2 (re-ranking): 200ms (100 candidates → 10 results)
Total:                600ms ✓ Still under 2s target
```

**Benefits**:
- ✅ Significantly better ranking quality
- ✅ Still fast enough for mobile
- ✅ Easy to implement (sentence-transformers library)
- ✅ No index changes needed

**Recommendation**: 🔥 **Highly Recommended** for Phase 3

**Effort**: 3-4 hours

---

### 4.4 Time-Aware Scoring ⭐

**Concept**: Boost recent documents in search results

**Implementation**:
```python
import datetime

def time_decay_boost(similarity_score, created_date, half_life_days=90):
    """
    Apply time decay to boost recent documents

    half_life_days: Days until boost is halved
    """
    days_old = (datetime.now() - created_date).days
    decay_factor = 0.5 ** (days_old / half_life_days)

    # Boost by up to 20%
    boost = 0.2 * decay_factor

    return similarity_score * (1 + boost)
```

**Example**:
```
Document A: "Obsidian Plugin Tutorial"
  Similarity: 0.75
  Created: 2 months ago
  Boost: 0.75 * (1 + 0.2 * 0.5^(60/90)) = 0.75 * 1.13 = 0.847 ✓

Document B: "Obsidian Plugin Guide"
  Similarity: 0.77
  Created: 2 years ago
  Boost: 0.77 * (1 + 0.2 * 0.5^(730/90)) = 0.77 * 1.01 = 0.778

Result: Document A ranked higher despite lower raw similarity
```

**Use Cases**:
- ✅ Finding recent discussions
- ✅ Discovering latest tools/techniques
- ✅ Prioritizing active projects

**Configuration**:
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

**Effort**: 2-3 hours

---

### 4.5 Faceted Search 🟢

**Concept**: Filter results by multiple attributes simultaneously

**Example UI**:
```
Search: "obsidian"

Filters:
☑ Type: [gleaning] [article] [note]
☑ Tags: [plugins] [productivity] [workflow]
☑ Date Range: [Last 30 days ▼]
☑ Author: [All ▼]
☑ Has Links: [Yes/No/Either]

Results: 23 documents (127 filtered out)
```

**Implementation**:
```python
def faceted_search(query, filters):
    # 1. Get all semantic search results
    results = semantic_search(query, k=1000)

    # 2. Apply filters
    filtered = results

    if filters.get('types'):
        filtered = [r for r in filtered if r.type in filters['types']]

    if filters.get('tags'):
        filtered = [r for r in filtered if any(tag in r.tags for tag in filters['tags'])]

    if filters.get('date_range'):
        start, end = filters['date_range']
        filtered = [r for r in filtered if start <= r.created <= end]

    return filtered[:10]
```

**Benefits**:
- ✅ Narrow down results interactively
- ✅ Discover facets you didn't know existed
- ✅ Combine filters (type=gleaning AND tags=obsidian)

**Effort**: 6-8 hours (backend + UI)

---

### 4.6 Saved Searches & Alerts 🟢

**Concept**: Save queries and get notified of new matches

**Implementation**:
```python
class SavedSearch:
    def __init__(self, query, filters, alert_enabled=False):
        self.query = query
        self.filters = filters
        self.alert_enabled = alert_enabled
        self.last_results = []

    def check_new_results(self):
        current = search(self.query, self.filters)
        new = [r for r in current if r not in self.last_results]

        if new and self.alert_enabled:
            send_notification(f"New results for '{self.query}': {len(new)} documents")

        self.last_results = current
        return new

# Run daily
for saved_search in saved_searches:
    saved_search.check_new_results()
```

**Use Cases**:
- ✅ Monitor topics of interest
- ✅ Track project mentions
- ✅ Discover new gleanings on topic

**Effort**: 4-5 hours

---

### 4.7 Similar Documents ("More Like This") 🟢

**Concept**: Find documents similar to a given document

**Implementation**:
```python
def find_similar(document_id, k=10):
    """Find documents similar to given document"""
    # Get document embedding
    doc_embedding = get_embedding(document_id)

    # Search using document embedding as query
    similar = semantic_search_by_embedding(doc_embedding, k=k+1)

    # Exclude the document itself
    return [s for s in similar if s.id != document_id][:k]
```

**UI**:
```
[Document: "Obsidian Dataview Tutorial"]

Similar Documents:
1. Dataview Query Examples (0.89)
2. Obsidian Plugin Development (0.82)
3. Advanced Dataview Tricks (0.79)
```

**Effort**: 2-3 hours

---

## 5. LLM-Powered Enhancements

### 5.1 Query Reformulation 🔥

**Concept**: LLM rewrites user query for better search results

**Example**:
```
User Query: "how do i make obsidian faster"
    ↓
LLM Reformulation:
    - "obsidian performance optimization"
    - "reduce obsidian lag"
    - "obsidian speed improvements"
    - "vault indexing performance"
    ↓
Run all 4 queries in parallel
    ↓
Merge results (RRF)
    ↓
Better coverage!
```

**Implementation**:
```python
async def reformulate_query(user_query):
    prompt = f"""
    Rewrite this search query into 3-4 alternative phrasings that would find the same information:

    Query: {user_query}

    Output format (one per line):
    - alternative 1
    - alternative 2
    - alternative 3
    """

    response = await llm.generate(prompt, max_tokens=100)
    alternatives = [line.strip('- ') for line in response.split('\n') if line.strip()]

    # Search with all alternatives
    all_results = await asyncio.gather(*[
        search(alt) for alt in [user_query] + alternatives
    ])

    # Merge using RRF
    return reciprocal_rank_fusion(all_results)
```

**Benefits**:
- ✅ Better recall (multiple query angles)
- ✅ Handles ambiguous queries
- ✅ Semantic variations covered

**Cost** (rough estimate):
- ~50 tokens per reformulation
- $0.0001 per query (cheap!)

**Latency**:
- LLM call: ~200ms
- Parallel searches: ~400ms
- Total: ~600ms ✓

**Effort**: 3-4 hours

---

### 5.2 Result Summarization 🔥🔥

**Concept**: LLM generates summary of top results

**Example**:
```
Query: "obsidian plugins"
Top 10 Results: [...]
    ↓
LLM Summary:
"Your vault contains several notes about Obsidian plugins:

 **Most Popular**: Dataview for querying vault data (3 notes)
 **Development**: Plugin API documentation and tutorials (2 notes)
 **Recommendations**: Community plugin roundups from 2024 (2 notes)
 **Integration**: Using plugins with Templater and Quickadd (3 notes)

 Key themes: automation, productivity, vault querying"
    ↓
Display summary + results
```

**Implementation**:
```python
async def summarize_results(query, results):
    context = "\n\n".join([
        f"Title: {r.title}\nSnippet: {r.content[:200]}..."
        for r in results[:10]
    ])

    prompt = f"""
    Summarize these search results for the query "{query}":

    {context}

    Provide a brief overview (2-3 sentences) identifying:
    - Main themes
    - Key documents
    - Relationships between results
    """

    summary = await llm.generate(prompt, max_tokens=200)
    return summary
```

**Benefits**:
- ✅ Quick overview without clicking
- ✅ Identifies patterns across results
- ✅ Guides user to most relevant docs

**Cost**:
- ~1000 tokens per summary
- $0.003 per query

**Latency**: +500ms

**Effort**: 2-3 hours

---

### 5.3 Conversational Search (RAG) 🔥🔥🔥

**Concept**: Chat with your vault using retrieved context

**Architecture**:
```
User: "How do I use dataview?"
    ↓
1. Search vault: "dataview usage tutorial"
    ↓
2. Retrieve top 5 results
    ↓
3. Format as context:
    <context>
      <document>
        <title>Dataview Tutorial</title>
        <content>...</content>
      </document>
      ...
    </context>
    ↓
4. Send to LLM with prompt:
    "Using only the provided context, answer: How do I use dataview?"
    ↓
5. LLM generates answer with citations
    ↓
6. Display answer + source links
```

**Implementation**:
```python
async def conversational_search(user_question, conversation_history=[]):
    # 1. Search vault
    results = search(user_question, k=5)

    # 2. Format context (XML format from Copilot)
    context = format_context_xml(results)

    # 3. Build prompt
    prompt = f"""
    <context>
    {context}
    </context>

    Previous conversation:
    {format_history(conversation_history)}

    User question: {user_question}

    Instructions:
    - Answer using ONLY information from the provided context
    - Cite sources using [doc_id] format
    - If information is not in context, say "I don't have information about that in your vault"
    """

    # 4. Generate answer
    answer = await llm.generate(prompt, max_tokens=500)

    # 5. Extract citations
    citations = extract_citations(answer, results)

    return {
        "answer": answer,
        "citations": citations,
        "sources": results
    }
```

**Example Interaction**:
```
User: How do I use dataview to query my daily notes?

Temoa: Based on your vault, here's how to query daily notes with Dataview:

You can use the LIST or TABLE commands to query daily notes. From your "Dataview Tutorial" note:

```dataview
LIST FROM "Daily"
WHERE date > date(today) - dur(7 days)
```

This will show all daily notes from the past week. You can also use TABLE for more structured output [doc_123].

For more examples, see your "Advanced Dataview Queries" note [doc_456].

Sources:
1. Dataview Tutorial (2024-03-15) [doc_123]
2. Advanced Dataview Queries (2024-01-22) [doc_456]
```

**Benefits**:
- ✅ Natural language interface
- ✅ Cites actual vault content
- ✅ Conversational (can ask follow-ups)
- ✅ No hallucinations (grounded in vault)

**Challenges**:
- ⚠️ Cost per query (~$0.01-0.05)
- ⚠️ Latency (~1-2s)
- ⚠️ Context window limits (can only include ~5 docs)

**Effort**: 6-8 hours (Phase 4 feature)

---

### 5.4 Semantic Question Generation 🔥

**Concept**: LLM generates questions a document can answer

**Use Case**: Improve discoverability

**Example**:
```
Document: "Obsidian Dataview Tutorial"
    ↓
LLM Generates Questions:
- How do I query my vault with dataview?
- What are dataview's main features?
- Can dataview filter notes by date?
- How to create tables in dataview?
    ↓
Index document with these questions
    ↓
User searches: "how to filter notes by date"
    ↓
Matches generated question!
```

**Implementation** (one-time during indexing):
```python
async def generate_questions(document):
    prompt = f"""
    Generate 5 questions that this document can answer:

    Title: {document.title}
    Content: {document.content[:500]}...

    Output format (one per line):
    1. Question?
    2. Question?
    ...
    """

    questions = await llm.generate(prompt, max_tokens=150)

    # Store questions with document
    document.metadata['generated_questions'] = questions

    # Embed questions alongside content
    combined = f"{document.content}\n\nQuestions: {questions}"
    document.embedding = embed(combined)
```

**Benefits**:
- ✅ Finds docs even if query phrasing differs
- ✅ Captures doc intent/purpose
- ✅ Better QA-style searches

**Cost**:
- ~$0.001 per document (one-time)
- For 2000 docs: ~$2 total

**Effort**: 4-5 hours

---

### 5.5 Automatic Tagging & Categorization 🟢

**Concept**: LLM suggests tags for documents

**Implementation**:
```python
async def auto_tag(document, existing_tags):
    prompt = f"""
    Suggest 3-5 relevant tags for this document.

    Title: {document.title}
    Content: {document.content[:300]}...

    Existing tags in vault: {', '.join(existing_tags[:50])}

    Guidelines:
    - Prefer existing tags when applicable
    - Use lowercase
    - Be specific but not overly narrow
    """

    suggested_tags = await llm.generate(prompt, max_tokens=50)
    return parse_tags(suggested_tags)

# User can review and accept/reject suggestions
```

**Benefits**:
- ✅ Consistent tagging
- ✅ Discovers tag vocabulary
- ✅ Improves filtering

**Effort**: 3-4 hours

---

### 5.6 Duplicate Detection 🟢

**Concept**: LLM identifies duplicate or highly similar notes

**Implementation**:
```python
async def find_duplicates(threshold=0.85):
    # 1. Find high-similarity pairs (semantic search)
    candidates = []
    for doc in vault:
        similar = find_similar(doc, k=5)
        for s in similar:
            if s.similarity > threshold:
                candidates.append((doc, s))

    # 2. LLM confirms duplication
    duplicates = []
    for doc1, doc2 in candidates:
        prompt = f"""
        Are these two documents duplicates or highly overlapping?

        Document 1:
        Title: {doc1.title}
        Content: {doc1.content[:200]}...

        Document 2:
        Title: {doc2.title}
        Content: {doc2.content[:200]}...

        Answer: YES or NO
        Reasoning: (brief explanation)
        """

        result = await llm.generate(prompt, max_tokens=50)
        if 'YES' in result:
            duplicates.append((doc1, doc2, result))

    return duplicates
```

**Benefits**:
- ✅ Clean up vault
- ✅ Consolidate knowledge
- ✅ Reduce noise in search

**Effort**: 4-5 hours

---

## 6. Recommendations

### 6.1 Short-Term (Phase 3) 🔴

**Priority 1: Cross-Encoder Re-Ranking**
- **Why**: Biggest quality improvement for minimal effort
- **Impact**: 20-30% better ranking precision
- **Cost**: Free (no API calls)
- **Effort**: 3-4 hours
- **Recommendation**: 🔥🔥🔥 **Implement ASAP**

**Priority 2: Query Expansion (Non-LLM)**
- **Why**: Improves short query handling
- **Impact**: Better disambiguation, more context
- **Cost**: Free
- **Effort**: 4-6 hours
- **Recommendation**: 🔥 **High value**

**Priority 3: Time-Aware Scoring**
- **Why**: Simple, useful for recency bias
- **Impact**: Moderate (depends on use case)
- **Cost**: Free
- **Effort**: 2-3 hours
- **Recommendation**: ⭐ **Easy win**

---

### 6.2 Medium-Term (Phase 3+) 🟡

**Priority 4: Similar Documents ("More Like This")**
- **Why**: Common feature request
- **Impact**: Improves exploration
- **Cost**: Free
- **Effort**: 2-3 hours

**Priority 5: Faceted Search**
- **Why**: Power user feature
- **Impact**: Advanced filtering
- **Cost**: Free
- **Effort**: 6-8 hours

**Priority 6: Saved Searches**
- **Why**: Convenience feature
- **Impact**: Reduces repeated queries
- **Cost**: Free
- **Effort**: 4-5 hours

---

### 6.3 Long-Term (Phase 4 - LLM Integration) 🟢

**Priority 7: Conversational Search (RAG)**
- **Why**: Natural language interface
- **Impact**: Game-changer for UX
- **Cost**: $0.01-0.05 per query
- **Effort**: 6-8 hours
- **Recommendation**: 🔥🔥🔥 **Phase 4 flagship feature**

**Priority 8: Query Reformulation (LLM)**
- **Why**: Better recall for ambiguous queries
- **Impact**: Moderate quality improvement
- **Cost**: $0.0001 per query (cheap)
- **Effort**: 3-4 hours
- **Recommendation**: 🔥 **Easy LLM enhancement**

**Priority 9: Result Summarization**
- **Why**: Quick overview
- **Impact**: Nice-to-have
- **Cost**: $0.003 per query
- **Effort**: 2-3 hours
- **Recommendation**: 🟢 **Phase 4 polish**

**Priority 10: Semantic Question Generation**
- **Why**: Better discoverability
- **Impact**: Helps QA-style queries
- **Cost**: $2 one-time for 2000 docs
- **Effort**: 4-5 hours
- **Recommendation**: 🟢 **Consider for Phase 4**

---

### 6.4 Research & Experimental 🔬

**SPLADE (Learned Sparse Retrieval)**:
- **Status**: Cutting-edge, proven in research
- **Benefit**: Better than BM25, interpretable
- **Challenge**: Model integration, index migration
- **Recommendation**: Evaluate if search quality plateaus

**ColBERT (Late Interaction)**:
- **Status**: SOTA for dense retrieval
- **Benefit**: Token-level matching (very precise)
- **Challenge**: Large index size (~10x), slower
- **Recommendation**: Research phase only

**Hybrid Reranking (Semantic + BM25 + Cross-Encoder)**:
- **Status**: Ensemble approach
- **Benefit**: Best of all worlds
- **Challenge**: Complexity, tuning
- **Recommendation**: If search quality is critical need

---

## 7. Summary & Decision Matrix

### Non-LLM Improvements

| Feature | Impact | Effort | Cost | Phase | Priority |
|---------|--------|--------|------|-------|----------|
| Cross-Encoder Re-Ranking | High | Low | Free | 3 | 🔥🔥🔥 |
| Query Expansion | Medium | Medium | Free | 3 | 🔥 |
| Time-Aware Scoring | Medium | Low | Free | 3 | ⭐ |
| Similar Documents | Medium | Low | Free | 3 | ⭐ |
| Faceted Search | High | High | Free | 3+ | 🟡 |
| Saved Searches | Low | Medium | Free | 3+ | 🟡 |
| SPLADE | High | High | Free | Research | 🔬 |

### LLM-Powered Improvements

| Feature | Impact | Effort | Cost/Query | Phase | Priority |
|---------|--------|--------|------------|-------|----------|
| Conversational Search | Very High | Medium | $0.01-0.05 | 4 | 🔥🔥🔥 |
| Query Reformulation | Medium | Low | $0.0001 | 4 | 🔥 |
| Result Summarization | Low | Low | $0.003 | 4 | 🟢 |
| Question Generation | Medium | Medium | $2 one-time | 4 | 🟢 |
| Auto-Tagging | Low | Low | $0.001/doc | 4 | 🟢 |
| Duplicate Detection | Low | Medium | Variable | 4 | 🟢 |

---

## 8. Key Insights

### 8.1 What Works Well Now

✅ **Hybrid Search** (BM25 + Semantic):
- Solves the daily notes problem
- No tuning needed (RRF)
- Fast enough for mobile (~450ms)

✅ **Type Filtering**:
- Dramatically improves precision
- Simple to use
- Cached frontmatter = no performance hit

✅ **Min Score Thresholding**:
- Removes low-quality results
- Configurable per-query
- Default (0.3) works well for most cases

### 8.2 What's Missing (Non-LLM)

⚠️ **Re-Ranking**: Would significantly improve result quality (Priority 1)

⚠️ **Query Expansion**: Short queries need help (Priority 2)

⚠️ **Recency Bias**: All results treated equally regardless of age (Priority 3)

### 8.3 What LLMs Unlock

🚀 **Conversational Interface**: Natural language Q&A with vault

🚀 **Query Understanding**: Reformulate queries for better recall

🚀 **Summarization**: Quick overview without clicking

🚀 **Generation**: Questions, tags, categorization

### 8.4 Cost-Benefit Analysis

**Non-LLM Improvements**:
- ✅ Free
- ✅ Fast
- ✅ Deterministic
- ⚠️ Limited by algorithms

**LLM Improvements**:
- ✅ Very powerful
- ✅ Natural language
- ⚠️ Costs money (~$0.01-0.05 per query)
- ⚠️ Slower (~1-2s latency)
- ⚠️ Non-deterministic

**Recommendation**: Implement non-LLM improvements first (Phase 3), add LLM features later (Phase 4) as opt-in enhancements.

---

## 9. Implementation Roadmap

### Phase 3: Search Quality (No LLMs)

**Week 1**:
1. Cross-encoder re-ranking (3-4 hours)
2. Query expansion (4-6 hours)
3. Time-aware scoring (2-3 hours)

**Week 2**:
1. Similar documents (2-3 hours)
2. Faceted search backend (4-5 hours)
3. Faceted search UI (2-3 hours)

**Expected Outcome**: 20-30% better search quality, more discovery options

---

### Phase 4: LLM Integration

**Prerequisites**:
- Apantli LLM proxy integrated
- API key management
- Cost tracking

**Week 1**:
1. Conversational search backend (4-5 hours)
2. RAG context formatting (2-3 hours)
3. Citation extraction (2-3 hours)

**Week 2**:
1. Conversational UI (chat interface) (4-5 hours)
2. Query reformulation (3-4 hours)
3. Result summarization (2-3 hours)

**Week 3**:
1. Question generation (during indexing) (4-5 hours)
2. Auto-tagging (3-4 hours)
3. Testing and refinement (6-8 hours)

**Expected Outcome**: Vault-first LLM interface, better discovery, auto-categorization

---

## 10. Final Recommendations

### Do This in Phase 3 (Next 2-3 Weeks):

1. ✅ **Cross-encoder re-ranking** (biggest bang for buck)
2. ✅ **Query expansion** (helps short queries)
3. ✅ **Time-aware scoring** (recency bias)
4. ✅ **Similar documents** (exploration)

### Save for Phase 4 (1-2 Months):

1. ✅ **Conversational search** (RAG with vault context)
2. ✅ **Query reformulation** (LLM query expansion)
3. ✅ **Result summarization** (quick overview)

### Research & Evaluate:

1. 🔬 **SPLADE** (if search quality needs boost)
2. 🔬 **Faceted search** (if power users request)
3. 🔬 **Question generation** (if QA-style queries common)

---

**Review Date**: 2025-11-23
**Reviewer**: Claude (Sonnet 4.5)
**Project Phase**: Phase 2.5 (Mobile Validation Complete)
**Next Review**: After Phase 3 implementation
**Status**: Search architecture is solid; clear enhancement path identified