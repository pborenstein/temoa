# Phase 3 Part 2: Search Quality Improvements

**Created**: 2025-11-29
**Branch**: `phase-3-part-2-search-quality`
**Status**: Planning
**Prerequisites**: Phase 3 Part 1 ✅ Complete (Technical debt fixed)

---

## Why This Matters

You've been using Temoa daily from mobile. The core hypothesis is validated: **fast vault search changes behavior**. But search quality is the bottleneck preventing it from being indispensable.

**Real-world problem**: Semantic search alone has limitations:
- **Short queries** ("AI", "obsidian") are ambiguous - what aspect?
- **Ranking precision** - relevant results buried in position 5-10
- **Recency bias** - recent notes often more relevant, but similarity score doesn't know that

Phase 3 Part 2 fixes these issues with proven techniques that add minimal latency.

---

## What We're Building

Three search quality improvements in priority order:

1. **Cross-Encoder Re-Ranking** (TOP PRIORITY)
   - Better ranking precision (20-30% improvement)
   - Minimal latency cost (~200ms)
   - Proven effective (used by Elasticsearch, Weaviate, Pinecone)

2. **Query Expansion** (MEDIUM)
   - Better handling of short/ambiguous queries
   - Extract key terms from initial results to expand query
   - No LLM needed (TF-IDF based)

3. **Time-Aware Scoring** (EASY WIN)
   - Boost recent documents with configurable decay
   - Simple math, zero latency cost
   - Useful for vaults with temporal patterns

---

## Part 1: Cross-Encoder Re-Ranking (PRIORITY 1)

### The Problem

**Bi-encoder semantic search** (what we use now):
- Fast: Encode query once, compare with pre-computed embeddings
- Good recall: Finds semantically similar documents
- **Weak precision**: Ranking order often suboptimal

**Example**:
```
Query: "how to set up obsidian sync"
Results:
1. Score 0.81 - "Obsidian plugins I use" (mentions sync plugin)
2. Score 0.79 - "Setting up Obsidian Sync step-by-step" ← SHOULD BE #1
3. Score 0.76 - "Sync issues troubleshooting"
```

Result #2 is clearly most relevant but ranked #2 due to bi-encoder limitations.

### The Solution: Two-Stage Retrieval

**Stage 1: Bi-Encoder (Fast Recall)**
- Use current semantic search
- Retrieve top 100 candidates
- Time: ~400ms

**Stage 2: Cross-Encoder (Precise Re-Ranking)**
- Score each (query, document) pair together
- Better at understanding relevance
- Re-rank top 100 → return top 10
- Time: ~200ms for 100 pairs

**Total time**: ~600ms (still well under 2s target ✅)

### Why Cross-Encoders Are Better at Ranking

**Bi-Encoder** (current):
```
Query embedding:     [0.2, 0.8, -0.1, ...]
Document embedding:  [0.3, 0.7,  0.0, ...]
Score: cosine_similarity = 0.79
```
- Encodes query and document separately
- Compares embeddings with simple math
- Fast but loses interaction information

**Cross-Encoder**:
```
Input: "[CLS] how to set up obsidian sync [SEP] This guide shows how to configure Obsidian Sync..."
Output: 0.92 (relevance score)
```
- Processes query and document together
- Learns relevance patterns from training data
- Slow but very accurate

### Implementation Plan

**1. Add Cross-Encoder Dependency**

Update `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "sentence-transformers>=2.2.0",  # Already have this
]
```

**Model to use**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Size: ~90MB
- Speed: ~2ms per pair (200ms for 100 pairs)
- Quality: Trained on MS MARCO dataset (millions of query-document pairs)

**2. Create Reranker Module**

File: `src/temoa/reranker.py`

```python
from sentence_transformers import CrossEncoder
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    """Re-ranks search results using cross-encoder for better precision."""

    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """Initialize cross-encoder model.

        Args:
            model_name: HuggingFace model identifier
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        logger.info("Cross-encoder loaded successfully")

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
        rerank_top_n: int = 100
    ) -> List[Dict[str, Any]]:
        """Re-rank search results using cross-encoder.

        Args:
            query: Search query string
            results: List of search results from bi-encoder
            top_k: Number of results to return after re-ranking
            rerank_top_n: Number of top results to re-rank (default: 100)

        Returns:
            Re-ranked results (top_k items)
        """
        if not results:
            return results

        # Only re-rank top N candidates (performance optimization)
        candidates = results[:rerank_top_n]

        # Build (query, document) pairs
        pairs = []
        for result in candidates:
            # Use content if available, otherwise title + path
            doc_text = result.get('content') or f"{result['title']} {result['relative_path']}"
            pairs.append([query, doc_text])

        # Score with cross-encoder
        logger.debug(f"Re-ranking {len(pairs)} candidates")
        scores = self.model.predict(pairs)

        # Attach cross-encoder scores
        for result, score in zip(candidates, scores):
            result['cross_encoder_score'] = float(score)

        # Sort by cross-encoder score
        reranked = sorted(candidates, key=lambda x: x['cross_encoder_score'], reverse=True)

        logger.debug(f"Re-ranking complete, returning top {top_k}")
        return reranked[:top_k]
```

**3. Integrate with Server**

Update `src/temoa/server.py`:

```python
# In lifespan initialization
cross_encoder_reranker = CrossEncoderReranker()
app.state.reranker = cross_encoder_reranker

# In /search endpoint
@app.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    use_reranker: bool = Query(True, description="Use cross-encoder re-ranking"),
    # ... other params
):
    # Stage 1: Bi-encoder semantic search
    # (retrieve more candidates for re-ranking)
    rerank_count = 100 if use_reranker else limit
    results = synthesis.search(query=q, limit=max(limit, rerank_count))

    # Apply existing filters (status, type, etc.)
    filtered_results = filter_by_status(...)
    filtered_results = filter_by_type(...)

    # Stage 2: Cross-encoder re-ranking (optional)
    if use_reranker and len(filtered_results) > limit:
        reranker = request.app.state.reranker
        filtered_results = reranker.rerank(
            query=q,
            results=filtered_results,
            top_k=limit,
            rerank_top_n=100
        )

    return SearchResponse(
        query=q,
        results=filtered_results,
        # ... other fields
    )
```

**4. Update Web UI**

Add toggle for re-ranking in `src/temoa/ui/search.html`:

```html
<!-- In Options section -->
<label>
    <input type="checkbox" id="use-reranker" checked>
    Use smart re-ranking (better precision, ~200ms slower)
</label>
```

```javascript
// In search() function
const useReranker = document.getElementById('use-reranker').checked;
const url = `/search?q=${q}&limit=${limit}&use_reranker=${useReranker}&...`;
```

**5. Add CLI Flag**

Update `src/temoa/cli.py`:

```python
@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Number of results")
@click.option("--rerank/--no-rerank", default=True, help="Use cross-encoder re-ranking")
def search(query: str, limit: int, rerank: bool):
    """Search vault with semantic search."""
    # ... existing code

    if rerank:
        reranker = CrossEncoderReranker()
        results = reranker.rerank(query, results, top_k=limit)
```

### Performance Impact

**Before** (bi-encoder only):
- Search: ~400ms
- Total: ~400ms

**After** (bi-encoder + cross-encoder):
- Bi-encoder search (retrieve 100): ~400ms
- Cross-encoder re-rank (100 pairs): ~200ms
- Total: ~600ms

**Still under 2s target** ✅ (with plenty of headroom for mobile network latency)

### Testing Plan

**Unit Tests** (`tests/test_reranker.py`):
```python
def test_reranker_initialization():
    """Test cross-encoder loads successfully."""
    reranker = CrossEncoderReranker()
    assert reranker.model is not None

def test_rerank_empty_results():
    """Test reranking with no results."""
    reranker = CrossEncoderReranker()
    results = reranker.rerank("test", [])
    assert results == []

def test_rerank_improves_ranking():
    """Test that re-ranking changes order."""
    reranker = CrossEncoderReranker()
    results = [
        {"title": "Unrelated doc", "content": "Something else", "score": 0.8},
        {"title": "Very relevant", "content": "Exactly what was asked", "score": 0.7},
    ]
    reranked = reranker.rerank("what was asked", results, top_k=2)
    assert reranked[0]['title'] == "Very relevant"
```

**Integration Test**:
```bash
# Compare results with/without re-ranking
temoa search "obsidian sync" --no-rerank > without.json
temoa search "obsidian sync" --rerank > with.json

# Manually verify top 5 results are better in with.json
```

**Manual Mobile Test**:
1. Search for ambiguous query ("AI")
2. Verify results make sense
3. Verify response time still < 1s from mobile
4. Compare with `use_reranker=false` - should see difference in ordering

### Success Criteria

- [ ] Cross-encoder model loads at startup (~2-3 seconds)
- [ ] Re-ranking adds ~200ms to search time
- [ ] Total search time still < 1s from mobile
- [ ] `/search?use_reranker=true` returns better ranked results than `false`
- [ ] UI checkbox controls re-ranking behavior
- [ ] CLI `--rerank` flag works
- [ ] Tests pass

### Expected Improvement

**Precision@5** (how many of top 5 results are relevant):
- Before: ~60-70%
- After: ~80-90%

**Ranking quality**:
- Before: Relevant result might be #5-10
- After: Relevant result typically in #1-3

This is a **qualitative improvement** you'll notice during daily use.

---

## Part 2: Query Expansion (MEDIUM PRIORITY)

### The Problem

**Short queries lack context**:
```
Query: "AI"
→ Too broad. Could mean:
  - AI ethics
  - AI tools/apps
  - AI research papers
  - AI implementation guides
```

**Current behavior**: Returns top 10 results based on "AI" alone, often misses relevant docs that use different terminology.

### The Solution: Pseudo-Relevance Feedback

**Technique**: Use initial search results to infer user intent and expand query.

**Algorithm**:
1. Run initial search with short query
2. Extract key terms from top-5 results (TF-IDF)
3. Append expansion terms to query
4. Re-run search with expanded query

**Example**:
```
Original query: "AI"
Top-5 results contain: "machine learning", "neural networks", "ethics", "chatgpt"
Expanded query: "AI machine learning neural networks"
→ Better results ✅
```

### Implementation Plan

**1. Create Query Expander Module**

File: `src/temoa/query_expansion.py`

```python
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class QueryExpander:
    """Expands short/ambiguous queries using pseudo-relevance feedback."""

    def __init__(self, max_expansion_terms: int = 3):
        """Initialize query expander.

        Args:
            max_expansion_terms: Maximum number of terms to add to query
        """
        self.max_expansion_terms = max_expansion_terms
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)  # unigrams and bigrams
        )

    def should_expand(self, query: str) -> bool:
        """Determine if query should be expanded.

        Args:
            query: Original search query

        Returns:
            True if query is short and would benefit from expansion
        """
        # Only expand short queries (< 3 words)
        word_count = len(query.split())
        return word_count < 3

    def expand(
        self,
        query: str,
        initial_results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> str:
        """Expand query using top-k initial results.

        Args:
            query: Original search query
            initial_results: Initial search results
            top_k: Number of top results to use for expansion

        Returns:
            Expanded query string
        """
        if not self.should_expand(query):
            logger.debug(f"Query '{query}' doesn't need expansion")
            return query

        if not initial_results:
            return query

        # Extract text from top-k results
        docs = []
        for result in initial_results[:top_k]:
            text = result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"
            docs.append(text)

        # TF-IDF to find important terms
        try:
            tfidf_matrix = self.vectorizer.fit_transform(docs)
            feature_names = self.vectorizer.get_feature_names_out()

            # Get top terms by TF-IDF score
            avg_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
            top_indices = avg_tfidf.argsort()[-self.max_expansion_terms:][::-1]
            expansion_terms = [feature_names[i] for i in top_indices]

            # Filter out terms already in query
            query_lower = query.lower()
            expansion_terms = [
                term for term in expansion_terms
                if term.lower() not in query_lower
            ]

            if expansion_terms:
                expanded = f"{query} {' '.join(expansion_terms)}"
                logger.info(f"Expanded query: '{query}' → '{expanded}'")
                return expanded

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")

        return query
```

**2. Integrate with Search Endpoint**

Update `src/temoa/server.py`:

```python
# In lifespan
query_expander = QueryExpander(max_expansion_terms=3)
app.state.query_expander = query_expander

# In /search endpoint
@app.get("/search")
async def search(
    request: Request,
    q: str = Query(..., min_length=1),
    expand_query: bool = Query(True, description="Expand short queries"),
    # ... other params
):
    original_query = q

    # Stage 0: Query expansion (if needed and enabled)
    if expand_query and request.app.state.query_expander.should_expand(q):
        # Get initial results with original query
        initial_results = synthesis.search(query=q, limit=5)

        # Expand query
        q = request.app.state.query_expander.expand(q, initial_results)

    # Stage 1: Bi-encoder search (with expanded query)
    results = synthesis.search(query=q, limit=...)

    # Stage 2: Re-ranking (if enabled)
    # ...

    return SearchResponse(
        query=original_query,  # Show original to user
        expanded_query=q if q != original_query else None,
        results=results,
        # ...
    )
```

**3. Update Web UI**

Show expanded query in UI:

```javascript
// In displayResults()
if (data.expanded_query) {
    const expansion = document.createElement('div');
    expansion.className = 'query-expansion';
    expansion.innerHTML = `
        <small style="color: #888;">
            Expanded to: "${data.expanded_query}"
        </small>
    `;
    resultsDiv.insertBefore(expansion, resultsDiv.firstChild);
}
```

**4. Add CLI Support**

```python
@cli.command()
@click.argument("query")
@click.option("--expand/--no-expand", default=True, help="Expand short queries")
def search(query: str, expand: bool, ...):
    # ...
```

### Performance Impact

**Additional latency**:
- Initial search (for expansion): ~400ms
- TF-IDF computation: ~50ms
- Expanded search: ~400ms
- **Total (if expanded)**: ~850ms

**Mitigation**: Only trigger for short queries (< 3 words), so most searches unaffected.

### Testing

**Unit Tests**:
```python
def test_should_expand_short_query():
    expander = QueryExpander()
    assert expander.should_expand("AI") == True
    assert expander.should_expand("AI ethics research") == False

def test_expand_query():
    expander = QueryExpander()
    results = [
        {"content": "Machine learning and neural networks are types of AI"},
        {"content": "AI ethics is important for responsible development"},
    ]
    expanded = expander.expand("AI", results)
    assert "machine learning" in expanded.lower() or "neural networks" in expanded.lower()
```

### Success Criteria

- [ ] Short queries (< 3 words) get expanded automatically
- [ ] Expansion terms come from top-5 initial results
- [ ] Expanded query shown in UI
- [ ] Option to disable expansion (checkbox or flag)
- [ ] Tests pass

### When NOT to Use

**Skip expansion if**:
- Query is already specific (>= 3 words)
- Initial results count is low (< 5 docs)
- User explicitly disables it

---

## Part 3: Time-Aware Scoring (EASY WIN)

### The Problem

**Recency matters**:
- Recent notes often more relevant to current interests
- Old notes might be outdated
- Semantic similarity doesn't know when document was created

**Example**:
```
Query: "best AI tools"
Results:
1. Score 0.85 - "AI Tools Review" (2021) - Mentions GPT-2
2. Score 0.83 - "My AI Toolkit 2024" (2024) - Mentions GPT-4, Claude ← More relevant!
```

Result #2 is more relevant but ranked lower due to slightly lower similarity.

### The Solution: Time Decay Boost

**Formula**:
```python
boosted_score = similarity_score * (1 + boost_factor)

boost_factor = max_boost * (0.5 ** (days_old / half_life_days))
```

**Example** (half_life = 90 days, max_boost = 0.2):
- Document from today: boost = 0.2 (20% boost)
- Document from 90 days ago: boost = 0.1 (10% boost)
- Document from 180 days ago: boost = 0.05 (5% boost)
- Document from 1 year ago: boost = 0.02 (2% boost)

**Effect**: Gently favors recent docs without completely discarding old ones.

### Implementation Plan

**1. Update Config Schema**

`config.json`:
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
  }
}
```

**2. Create Time Scoring Module**

File: `src/temoa/time_scoring.py`

```python
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import os

class TimeAwareScorer:
    """Applies time-decay boost to search results."""

    def __init__(
        self,
        half_life_days: int = 90,
        max_boost: float = 0.2,
        enabled: bool = True
    ):
        """Initialize time-aware scorer.

        Args:
            half_life_days: Number of days for boost to decay by 50%
            max_boost: Maximum boost factor for most recent docs
            enabled: Whether to apply time-aware scoring
        """
        self.half_life_days = half_life_days
        self.max_boost = max_boost
        self.enabled = enabled

    def apply_boost(self, results: List[Dict[str, Any]], vault_path: Path) -> List[Dict[str, Any]]:
        """Apply time-decay boost to results.

        Args:
            results: Search results
            vault_path: Path to vault (to get file modification times)

        Returns:
            Results with boosted scores
        """
        if not self.enabled:
            return results

        now = datetime.now()

        for result in results:
            # Get file modification time
            file_path = vault_path / result['relative_path']
            if not file_path.exists():
                continue

            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            days_old = (now - modified_time).days

            # Calculate boost factor
            decay_factor = 0.5 ** (days_old / self.half_life_days)
            boost = self.max_boost * decay_factor

            # Apply boost to similarity score
            original_score = result.get('similarity_score', 0)
            boosted_score = original_score * (1 + boost)

            result['original_score'] = original_score
            result['time_boost'] = boost
            result['similarity_score'] = boosted_score

        # Re-sort by boosted score
        results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

        return results
```

**3. Integrate with Search**

```python
# In lifespan
time_scorer = TimeAwareScorer(
    half_life_days=config.search.get('time_decay', {}).get('half_life_days', 90),
    max_boost=config.search.get('time_decay', {}).get('max_boost', 0.2),
    enabled=config.search.get('time_decay', {}).get('enabled', True)
)
app.state.time_scorer = time_scorer

# In /search endpoint
results = synthesis.search(...)
results = filter_by_status(...)
results = filter_by_type(...)

# Apply time-aware boost (before re-ranking)
if use_time_boost:
    results = request.app.state.time_scorer.apply_boost(results, config.vault_path)

# Then re-rank if enabled
if use_reranker:
    results = reranker.rerank(...)
```

**4. Add UI Toggle**

```html
<label>
    <input type="checkbox" id="use-time-boost" checked>
    Boost recent documents
</label>
```

### Performance Impact

**Latency**: < 5ms (simple math on already-fetched results)

**Negligible** - this is essentially free.

### Testing

```python
def test_time_boost_recent_doc():
    scorer = TimeAwareScorer(half_life_days=90, max_boost=0.2)
    # Mock results with dates
    results = [
        {"similarity_score": 0.8, "relative_path": "old.md"},  # 1 year old
        {"similarity_score": 0.75, "relative_path": "recent.md"},  # 1 day old
    ]
    # Set up mock file mtimes...
    boosted = scorer.apply_boost(results, vault_path)
    # Recent doc should be boosted to #1
    assert boosted[0]['relative_path'] == "recent.md"
```

### Success Criteria

- [ ] Recent docs get boosted in ranking
- [ ] Configurable via config.json
- [ ] Toggleable in UI
- [ ] No noticeable latency impact
- [ ] Tests pass

---

## Implementation Order

**Day 1: Cross-Encoder Re-Ranking**
1. Add `CrossEncoderReranker` class (2h)
2. Integrate with server endpoint (1h)
3. Add UI toggle (30min)
4. Test and validate (1h)

**Day 2: Query Expansion**
1. Add `QueryExpander` class (2h)
2. Integrate with server (1h)
3. Add UI display of expanded query (30min)
4. Test (1h)

**Day 3: Time-Aware Scoring**
1. Add `TimeAwareScorer` class (1h)
2. Integrate with server (30min)
3. Add config and UI toggle (30min)
4. Test (1h)

**Day 4: Integration & Polish**
1. Ensure all three work together correctly
2. Performance testing on mobile
3. Update documentation
4. Write Chronicles entry

---

## Success Criteria (Overall)

**Performance**:
- [ ] Search with all features enabled: < 1s on average
- [ ] Mobile response time: < 2s (with network latency)
- [ ] No regressions in existing functionality

**Quality**:
- [ ] Precision@5 improves 20-30% (cross-encoder)
- [ ] Short queries return better results (expansion)
- [ ] Recent docs ranked higher when appropriate (time boost)

**Usability**:
- [ ] All features have UI toggles
- [ ] All features have CLI flags
- [ ] Defaults make sense (all enabled)
- [ ] Clear feedback when features are active

**Code Quality**:
- [ ] Modular design (separate classes for each feature)
- [ ] Well-tested (unit + integration tests)
- [ ] Documented (docstrings + Chronicles entry)
- [ ] No technical debt introduced

---

## Dependencies

**Python packages** (add to `pyproject.toml`):
```toml
dependencies = [
    # ... existing
    "sentence-transformers>=2.2.0",  # Already have this
    "scikit-learn>=1.3.0",  # For TF-IDF in query expansion
]
```

**Model downloads** (automatic on first use):
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~90MB)

**Disk space**: ~100MB for models (negligible)

---

## What NOT to Build

**From original Phase 3 plan, explicitly SKIP**:

- ❌ **LLM-based query reformulation** - Save for Phase 4
- ❌ **Hybrid search (BM25 + semantic)** - Already have this
- ❌ **Result clustering** - Not needed for vault size
- ❌ **Advanced filters beyond current** - YAGNI

**Rationale**: These three features (re-ranking, expansion, time-boost) are proven, simple, and address real friction. Don't over-engineer.

---

## Open Questions

**Q: Should cross-encoder be enabled by default?**
A: YES - the quality improvement is significant and latency is acceptable. User can disable if needed.

**Q: Should query expansion run on every short query automatically?**
A: YES, but only if initial results count >= 5. If vault too small, skip expansion.

**Q: What default half_life for time decay?**
A: Start with 90 days (3 months). User can adjust in config.

**Q: Should we cache cross-encoder results?**
A: NOT YET - measure first. Caching adds complexity. Only add if needed.

---

## References

**Research**:
- [Cross-Encoders for Re-Ranking](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- [Query Expansion Techniques](https://en.wikipedia.org/wiki/Query_expansion)
- [Time-Aware Search Ranking](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-script-score-query.html#time-decay-functions)

**Related Docs**:
- `docs/PHASE-3-READY.md` - Overall Phase 3 plan
- `docs/ARCHITECTURE.md` - System architecture
- `docs/IMPLEMENTATION.md` - Progress tracking

---

**Status**: READY TO DISCUSS
**Next Action**: Review plan with user, get approval, then implement
**Estimated Duration**: 3-4 days
