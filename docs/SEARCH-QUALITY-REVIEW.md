# Search Quality Code Review

**Date**: 2025-12-03
**Scope**: Cross-encoder re-ranking, query expansion, and time-aware scoring
**Status**: Review complete, fixes pending

---

## Overview

This document captures the code review findings for the Phase 3 search quality features:

1. **Cross-Encoder Re-Ranking** (`src/temoa/reranker.py`) - Two-stage retrieval for better precision
2. **Query Expansion** (`src/temoa/query_expansion.py`) - TF-IDF based expansion for short queries
3. **Time-Aware Scoring** (`src/temoa/time_scoring.py`) - Exponential decay boost for recent documents

**Overall Assessment**: Functionally solid with good separation of concerns and comprehensive documentation. However, there are 3 critical issues and several opportunities for simplification.

---

## Critical Issues (Fix Now)

### 1. Data Mutation Bug in Pipeline Order ⚠️

**File**: `src/temoa/server.py` lines 667-684
**Severity**: CRITICAL (incorrect data flow)

**Problem**: Time boost is applied *before* re-ranking, which mutates the `similarity_score` field in place:

```python
# Current order (WRONG):
# Line 667-671: Apply time-aware boost
if time_boost and filtered_results:
    time_scorer = request.app.state.time_scorer
    filtered_results = time_scorer.apply_boost(filtered_results, vault_path)

# Line 673-684: Apply cross-encoder re-ranking
if rerank and filtered_results:
    reranker = request.app.state.reranker
    filtered_results = reranker.rerank(query=q, results=filtered_results, ...)
```

In `time_scoring.py` line 82:
```python
result['similarity_score'] = boosted_score  # OVERWRITES original score
```

**Why this matters**:
- The cross-encoder should re-rank based on semantic relevance, not artificially boosted scores
- Creates confusion about what scores mean
- The cross-encoder doesn't use `similarity_score` anyway (it uses content), but the mutation is still problematic

**Fix**: Swap the order - apply time boost AFTER re-ranking:

```python
# Apply cross-encoder re-ranking if enabled
if rerank and filtered_results:
    reranker = request.app.state.reranker
    rerank_count = min(100, len(filtered_results))
    logger.info(f"Re-ranking top {rerank_count} results with cross-encoder")
    filtered_results = reranker.rerank(
        query=q,
        results=filtered_results,
        top_k=limit,
        rerank_top_n=rerank_count
    )

# Apply time-aware boost AFTER re-ranking
if time_boost and filtered_results:
    time_scorer = request.app.state.time_scorer
    logger.info(f"Applying time-aware boost to {len(filtered_results)} results")
    filtered_results = time_scorer.apply_boost(filtered_results, vault_path)
```

**Impact**: Clean separation - reranker uses original scores, time boost affects final ranking only.

---

### 2. Path Traversal Vulnerability 🔒

**File**: `src/temoa/time_scoring.py` line 61
**Severity**: CRITICAL (security)

**Problem**: User-controlled `relative_path` is joined to `vault_path` without validation:

```python
file_path = vault_path / result['relative_path']  # Line 61
```

An attacker could craft a result with `relative_path: "../../../etc/passwd"` to read file metadata outside the vault.

**Why this matters**:
- While results come from Synthesis (trusted), if Synthesis has a bug or vault contains maliciously crafted files with weird paths, this could leak file metadata (modification times) from outside vault
- Defense in depth principle - validate at every boundary

**Fix**: Validate that resolved path stays within vault:

```python
file_path = vault_path / result['relative_path']

# Ensure path is within vault (prevent path traversal)
try:
    file_path = file_path.resolve()
    vault_path_resolved = vault_path.resolve()
    if not str(file_path).startswith(str(vault_path_resolved)):
        logger.warning(f"Path traversal attempt detected: {result['relative_path']}")
        continue
except Exception as e:
    logger.warning(f"Path resolution failed for {result['relative_path']}: {e}")
    continue

if not file_path.exists():
    logger.debug(f"File not found for time boost: {file_path}")
    continue
```

**Impact**: Prevents potential information disclosure outside vault.

---

### 3. Silent Failure in Query Expansion 🤫

**File**: `src/temoa/server.py` lines 605-617
**Severity**: HIGH (observability)

**Problem**: If initial search for expansion fails or returns no results, query expansion silently falls back to original query without logging why:

```python
if expand_query:
    query_expander = request.app.state.query_expander
    if query_expander.should_expand(q):
        # Get initial results for expansion
        logger.info(f"Query '{q}' is short, fetching initial results for expansion")
        initial_data = synthesis.search(query=q, limit=5)
        initial_results = initial_data.get("results", [])

        # Expand query (silently fails if no results)
        q = query_expander.expand(q, initial_results, top_k=5)
```

If `synthesis.search()` returns 0 results, expansion silently skips and user doesn't know why short query wasn't expanded.

**Fix**: Add logging and error handling:

```python
if expand_query:
    query_expander = request.app.state.query_expander
    if query_expander.should_expand(q):
        try:
            # Get initial results for expansion
            logger.info(f"Query '{q}' is short, fetching initial results for expansion")
            initial_data = synthesis.search(query=q, limit=5)
            initial_results = initial_data.get("results", [])

            if not initial_results:
                logger.info(f"Query '{q}' needs expansion but initial search returned no results")

            # Expand query
            q = query_expander.expand(q, initial_results, top_k=5)
            if q != original_query:
                expanded_query = q
                logger.info(f"Query expanded: '{original_query}' → '{q}'")
        except SynthesisError as e:
            logger.warning(f"Initial search for expansion failed: {e}, proceeding with original query")
            # Continue with original query
```

**Impact**: Better observability for debugging expansion behavior.

---

## High Priority Issues (Fix Soon)

### 4. Redundant Sort After Time Boost

**File**: `src/temoa/time_scoring.py` line 95
**Severity**: MEDIUM (performance)

**Problem**: Time scorer sorts results at line 95, but if re-ranking is enabled, the reranker will sort again by cross-encoder score. Wasted O(n log n) work.

**Current flow**:
```
1. Time boost mutates scores
2. Time scorer sorts by boosted similarity_score (line 95)
3. Reranker sorts by cross_encoder_score (line 118 in reranker.py)
```

**Fix**: Make sorting optional in `TimeAwareScorer.apply_boost()`:

```python
def apply_boost(
    self,
    results: List[Dict[str, Any]],
    vault_path: Path,
    sort: bool = True  # Add parameter
) -> List[Dict[str, Any]]:
    # ... existing code ...

    if boosted_count > 0:
        logger.debug(f"Applied time boost to {boosted_count}/{len(results)} results")

    # Only sort if requested (skip if re-ranking will sort anyway)
    if sort:
        results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

    return results
```

Then in `server.py`:
```python
# Don't sort if we're about to re-rank (re-ranker will sort)
filtered_results = time_scorer.apply_boost(
    filtered_results,
    vault_path,
    sort=not rerank  # Only sort if NOT re-ranking
)
```

**Benefit**: Saves ~O(n log n) sort when re-ranking is enabled (typical case).

---

### 5. Empty Text Handling in Reranker

**File**: `src/temoa/reranker.py` lines 104-111
**Severity**: MEDIUM (correctness)

**Problem**: If result has no content, no title, AND no relative_path:
- `doc_text = "" or " "` → `" "` (single space)
- Cross-encoder gets `["query", " "]` pair
- Model processes empty document (wasted compute, may give weird score)

**Fix**: Skip results with no meaningful text:

```python
# Build (query, document) pairs
pairs = []
valid_candidates = []
for result in candidates:
    doc_text = result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"
    if doc_text.strip():  # Only add if has actual text
        pairs.append([query, doc_text])
        valid_candidates.append(result)
    else:
        logger.debug(f"Skipping result with no text content: {result}")

if not pairs:
    logger.debug("No valid candidates with text content for re-ranking")
    return results[:top_k]

# Score with cross-encoder
logger.debug(f"Re-ranking {len(pairs)} candidates with cross-encoder")
scores = self.model.predict(pairs)

# Attach cross-encoder scores to results
for result, score in zip(valid_candidates, scores):
    result['cross_encoder_score'] = float(score)

# Sort by cross-encoder score (descending)
reranked = sorted(
    valid_candidates,
    key=lambda x: x.get('cross_encoder_score', 0),
    reverse=True
)
```

**Impact**: Avoids wasting cross-encoder compute on empty results.

---

### 6. Empty Query Handling in Expansion

**File**: `src/temoa/query_expansion.py` lines 41-42
**Severity**: MEDIUM (robustness)

**Problem**: Whitespace-only queries trigger expansion but will fail:

```python
word_count = len(query.split())
return word_count < 3
```

Edge case: `query = "   "` (only whitespace)
- `"   ".split()` → `[]`
- `len([])` → `0`
- `0 < 3` → `True` (should expand)
- But expansion will fail because empty query won't match anything

**Fix**: Reject empty queries early:

```python
def should_expand(self, query: str) -> bool:
    """Determine if query should be expanded.

    Short queries (< 3 words) are ambiguous and benefit from expansion.

    Args:
        query: Original search query

    Returns:
        True if query is short and would benefit from expansion
    """
    words = query.split()
    # Don't expand empty queries
    if not words:
        return False
    # Only expand short queries (< 3 words)
    return len(words) < 3
```

**Impact**: Prevents pointless expansion attempt on empty queries.

---

## Medium Priority (Nice to Have)

### 7. Extract Duplicate Doc Text Logic

**Files**: `src/temoa/reranker.py` line 106, `src/temoa/query_expansion.py` lines 81-83
**Severity**: LOW (code quality)

**Problem**: Same pattern duplicated in two places:

In `reranker.py` line 106:
```python
doc_text = result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"
```

In `query_expansion.py` lines 81-83:
```python
text = result.get('content') or \
       f"{result.get('title', '')} {result.get('description', '')} " \
       f"{result.get('relative_path', '')}"
```

**Fix**: Extract to utility function:

```python
# In new file: src/temoa/search_utils.py
def extract_result_text(result: dict[str, Any], include_description: bool = True) -> str:
    """Extract searchable text from a result dict.

    Args:
        result: Search result from Synthesis
        include_description: Whether to include description field

    Returns:
        Combined text for semantic processing
    """
    if result.get('content'):
        return result['content']

    parts = [result.get('title', '')]
    if include_description:
        parts.append(result.get('description', ''))
    parts.append(result.get('relative_path', ''))

    return ' '.join(p for p in parts if p)
```

Then use in both places:
```python
from .search_utils import extract_result_text

# In reranker.py:
doc_text = extract_result_text(result, include_description=False)

# In query_expansion.py:
text = extract_result_text(result, include_description=True)
```

**Benefit**: Single source of truth for text extraction logic.

---

### 8. Reduce Logging Verbosity

**File**: `src/temoa/query_expansion.py` line 110
**Severity**: LOW (observability)

**Problem**: Query expansion logs at INFO level for every expanded query:

```python
logger.info(f"Expanded query: '{query}' → '{expanded}'")  # Line 110
```

Users don't need to see every query expansion in production logs.

**Fix**: Change to DEBUG:

```python
logger.debug(f"Expanded query: '{query}' → '{expanded}'")
```

**Impact**: Cleaner production logs.

---

### 9. Simplify Reranker Pairs Construction

**File**: `src/temoa/reranker.py` lines 104-107
**Severity**: LOW (code style)

**Current code**:
```python
pairs = []
for result in candidates:
    doc_text = result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"
    pairs.append([query, doc_text])
```

**Simplified**:
```python
pairs = [
    [query, result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"]
    for result in candidates
]
```

**Benefit**: More Pythonic, reduces 4 lines to 3.

---

## Low Priority (Polish)

### 10. Lazy Load Cross-Encoder Model

**File**: `src/temoa/server.py` line 85
**Severity**: LOW (performance)

**Problem**: Model (~90MB) loads at startup even if user never enables re-ranking. Wastes 2-3 seconds on startup and ~800MB RAM.

**Fix**: Lazy load on first use:
```python
# In lifespan():
app.state.reranker = None  # Don't load yet

# In search endpoint:
if rerank and filtered_results:
    if request.app.state.reranker is None:
        logger.info("Loading cross-encoder model (first use)...")
        request.app.state.reranker = CrossEncoderReranker()

    reranker = request.app.state.reranker
    # ... use reranker
```

**Benefit**: Faster startup, lower memory if feature unused.

**Downside**: First query with re-ranking will be 2-3s slower.

**Recommendation**: Keep current behavior (eager loading) since re-ranking is enabled by default and is a core feature. Document that `rerank=false` query param exists if users want to skip it.

---

### 11. Consider Simpler Term Frequency

**File**: `src/temoa/query_expansion.py` line 93
**Severity**: LOW (simplification)

**Problem**: TF-IDF refits vocabulary and IDF weights for every query. For 5 documents, this is expensive (sklearn overhead).

**Alternative**: For pseudo-relevance feedback with only 5 docs, TF-IDF might be overkill. Consider simpler term frequency:

```python
from collections import Counter
import re

def get_top_terms(docs: list[str], n: int = 3, stopwords: set = None) -> list[str]:
    """Extract top terms by frequency from documents."""
    if stopwords is None:
        # Basic English stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}

    # Tokenize and count
    words = []
    for doc in docs:
        words.extend(re.findall(r'\b\w+\b', doc.lower()))

    # Filter stopwords and count
    counts = Counter(w for w in words if w not in stopwords and len(w) > 2)

    # Return top N
    return [word for word, count in counts.most_common(n)]
```

This is simpler, faster, and easier to understand than TF-IDF for this use case.

**However**: Current implementation works and is tested. Only change if performance becomes an issue.

---

### 12. Standardize Type Hints

**Files**: All Python files
**Severity**: LOW (consistency)

**Problem**: Inconsistent typing:
- `reranker.py` uses `List[Dict[str, Any]]` (PEP 585 old style)
- `query_expansion.py` uses `List[Dict[str, Any]]` (PEP 585 old style)
- `server.py` uses `list[str] | None` (PEP 604 new style)

**Fix**: Use modern Python 3.10+ syntax everywhere:

```python
# Change from:
from typing import List, Dict, Any
def rerank(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

# To:
def rerank(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
```

Check `pyproject.toml` for minimum Python version first.

---

## Positive Observations ✅

What's already well done:

1. **Clear separation of concerns**: Each module does one thing well (reranking, expansion, time scoring)

2. **Comprehensive docstrings**: Every function has clear docstrings with args, returns, and examples

3. **Defensive programming**: Good use of `.get()` with defaults throughout

4. **Fail-open error handling**: `time_scoring.py` continues processing if one file fails (line 87-89)

5. **Logging discipline**: Good use of DEBUG vs INFO levels (except one case noted above)

6. **Test coverage**: `tests/test_reranker.py` has good edge case coverage (empty results, single result, ranking changes)

7. **Performance awareness**: `rerank_top_n` parameter limits cross-encoder work (line 65 in `reranker.py`)

8. **Preservation of data**: Reranker preserves all original fields

9. **Configuration flexibility**: Time scorer parameters are configurable via config file

10. **Pipeline composability**: Each stage can be enabled/disabled independently via query params

---

## Implementation Plan

### Phase 1: Critical Fixes (Do First)

1. Fix pipeline order - move time boost after re-ranking
2. Add path traversal validation in time scoring
3. Improve error handling for query expansion

**Estimated effort**: 1-2 hours
**Impact**: HIGH (fixes bugs and security issue)

### Phase 2: High Priority Improvements (Do Soon)

4. Make time scorer sort optional (performance)
5. Skip empty text in reranker
6. Validate empty query in expansion

**Estimated effort**: 1 hour
**Impact**: MEDIUM (improves robustness and performance)

### Phase 3: Nice-to-Have Polish (Do When Time Permits)

7. Extract duplicate doc text logic
8. Reduce logging verbosity
9. Simplify reranker pairs construction

**Estimated effort**: 1 hour
**Impact**: LOW (code quality improvements)

### Phase 4: Optional Enhancements (Consider Later)

10. Lazy load cross-encoder (probably not worth it)
11. Simpler term frequency (only if TF-IDF becomes bottleneck)
12. Standardize type hints (cleanup)

**Estimated effort**: 2-3 hours
**Impact**: LOW (marginal gains)

---

## File-Specific Summary

**`src/temoa/reranker.py`**:
- Line 104-107: Can simplify to list comprehension (LOW)
- Line 106: Should skip results with no meaningful text (MEDIUM)

**`src/temoa/query_expansion.py`**:
- Line 41-42: Should handle empty/whitespace-only queries (MEDIUM)
- Line 93: TF-IDF might be overkill for 5 docs (LOW, nice-to-have)
- Line 110: Logging too verbose INFO → DEBUG (LOW)

**`src/temoa/time_scoring.py`**:
- Line 61: Path traversal vulnerability - needs validation (CRITICAL)
- Line 95: Unnecessary sort if re-ranking enabled (MEDIUM)
- Line 82: Mutates similarity_score - causes confusion (CRITICAL)

**`src/temoa/server.py` (lines 602-684)**:
- Line 667-684: Time boost applied before re-ranking - wrong order (CRITICAL)
- Line 605-617: Silent failure if expansion search returns no results (HIGH)
- Line 85: Eager loading of cross-encoder (LOW, probably keep as-is)

---

## Testing Strategy

After implementing fixes:

1. **Unit tests**: Add tests for path traversal validation, empty query handling, empty text handling
2. **Integration tests**: Test pipeline with all combinations of flags (rerank, expand, time_boost)
3. **Performance tests**: Verify sort optimization improves latency
4. **Manual testing**: Search production vault with various query types

---

**Review completed**: 2025-12-03
**Next action**: Implement Phase 1 critical fixes
