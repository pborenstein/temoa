# Phase 3: Ready to Build - Consolidated Plan

**Created**: 2025-11-24
**Updated**: 2025-11-25 (Added Part 0: Multi-Vault Support)
**Status**: Ready for implementation
**Prerequisites**: Phase 2.5 ✅ Complete (Mobile validated, real-world usage confirmed)

---

## Executive Summary

Phase 2.5 validation is complete. You've been using Temoa from mobile, it works, and the core hypothesis is validated. Now we enhance based on **actual usage patterns** and **technical debt** identified during real-world testing.

This plan consolidates findings from three comprehensive reviews:
- Architecture Review (technical debt priorities)
- Search Architecture Review (quality improvements)
- UI Review (interface enhancements)

**Guiding Principle**: Build what removes friction you experienced, not what sounds cool.

**NEW**: Part 0 added to fix critical multi-vault support bug discovered during incremental reindexing implementation (Entry 19).

---

## Part 0: Multi-Vault Support Fix (CRITICAL)

> **Priority**: MUST FIX FIRST - Data corruption risk
> **Duration**: 1-2 hours
> **Discovered**: During incremental reindexing implementation (2025-11-25)

### Problem

When using `--vault` flag to index a different vault, `storage_dir` comes from config (pointing to config's vault), not the vault being indexed:

```python
# Current code in cli.py:514-526
vault_path = Path(vault) if vault else config.vault_path  # ✅ Correct

client = SynthesisClient(
    synthesis_path=config.synthesis_path,
    vault_path=vault_path,  # ✅ Uses custom vault
    model=config.default_model,
    storage_dir=config.storage_dir  # ❌ Uses config vault's .temoa/!
)
```

**Consequences**:
- Index for different vault overwrites config vault's index
- File_tracking from wrong vault used for change detection
- Incremental reindex corrupts data (mixing vaults)

### Solution

Derive `storage_dir` from the vault being indexed, not from config:

```python
# Proposed fix
if vault:
    vault_path = Path(vault)
    # Derive storage_dir from the vault path, not config
    storage_dir = vault_path / ".temoa" / config.default_model
else:
    vault_path = config.vault_path
    storage_dir = config.storage_dir
```

### Implementation

**Files to modify**:
1. `src/temoa/cli.py` - Update `index()` and `reindex()` commands (lines ~514, ~561)
2. Test with multiple vaults to verify independence

**Testing**:
```bash
# Index vault A
temoa index --vault ~/vaults/vault-a

# Index vault B
temoa index --vault ~/vaults/vault-b

# Verify:
# - vault-a/.temoa/ exists with vault A's index
# - vault-b/.temoa/ exists with vault B's index
# - Neither overwrites the other
```

**Success Criteria**:
- [ ] Each vault has its own independent `.temoa/` directory
- [ ] `--vault` flag works correctly without data corruption
- [ ] Incremental reindex uses correct file_tracking for vault being indexed

**Effort**: 1-2 hours

---

## Part 1: Fix Technical Debt (Foundation)

> **Priority**: CRITICAL - Do this first, before adding features
> **Duration**: 1-2 days
> **Source**: Architecture Review

### 1.1 Fix Module-Level Initialization (CRITICAL)

**Problem**: `server.py` loads config and Synthesis at module import time, making testing difficult and violating best practices.

**Current Code** (server.py:36-58):
```python
# Module-level initialization - BAD
config = Config()
synthesis = SynthesisClient(...)
```

**Fix**: Move to lifespan context
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config = Config()
    synthesis = SynthesisClient(...)

    app.state.config = config
    app.state.synthesis = synthesis

    yield

    # Shutdown cleanup
    await synthesis.cleanup()  # if needed
```

**Impact**:
- ✅ Testable (can mock config/synthesis)
- ✅ Proper resource management
- ✅ Follows FastAPI best practices
- ✅ Prevents import-time side effects

**Effort**: 2-3 hours

---

### 1.2 Remove sys.path Manipulation (CRITICAL)

**Problem**: Multiple files modify `sys.path` at runtime, causing fragile imports.

**Locations**:
- `server.py` lines 24-27 (scripts path)
- `synthesis.py` lines 140-143 (synthesis path)
- `cli.py` line 663 (scripts path)

**Fix**: Make scripts a proper package
```bash
# Add scripts/__init__.py
touch scripts/__init__.py

# Use relative imports
from ..scripts import extract_gleanings
```

**Or**: Define entry points in `pyproject.toml`

**Impact**:
- ✅ Portable (no hardcoded paths)
- ✅ Robust imports
- ✅ Standard Python structure
- ✅ Easier to debug

**Effort**: 1-2 hours

---

### 1.3 Introduce Service Layer (HIGH)

**Problem**: Business logic mixed with HTTP handlers in `server.py`, leading to duplication in CLI.

**Current**: Filtering logic in both `server.py` and `cli.py`

**Fix**: Create `SearchService` class
```python
# src/temoa/search_service.py
class SearchService:
    def __init__(self, synthesis_client, gleaning_manager):
        self.synthesis = synthesis_client
        self.gleaning_manager = gleaning_manager

    def search(self, query, filters=None):
        results = self.synthesis.search(query)
        return self._apply_filters(results, filters)

    def _apply_filters(self, results, filters):
        # All filtering logic here
        ...
```

**Benefits**:
- ✅ Reusable (server and CLI both use it)
- ✅ Testable (no HTTP client needed)
- ✅ Single responsibility
- ✅ SOLID principles

**Effort**: 4-6 hours

---

## Part 2: Search Quality Improvements (High Value)

> **Priority**: HIGH - Directly improves core functionality
> **Duration**: 1-2 days
> **Source**: Search Architecture Review

### 2.1 Cross-Encoder Re-Ranking (TOP PRIORITY)

**Impact**: 20-30% better ranking precision
**Effort**: 3-4 hours
**Cost**: Free (no API calls)

**Implementation**:
```python
from sentence_transformers import CrossEncoder

cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def search_with_reranking(query, k=10):
    # Stage 1: Fast retrieval (current method)
    candidates = semantic_search(query, k=100)

    # Stage 2: Re-rank with cross-encoder
    pairs = [[query, doc.content] for doc in candidates]
    scores = cross_encoder.predict(pairs)

    # Sort by cross-encoder score
    reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return reranked[:k]
```

**Performance**: 600ms total (400ms retrieval + 200ms re-ranking) - still under 2s target ✅

**Why This First**:
- Biggest quality improvement for minimal effort
- No architecture changes needed
- Proven effective in research
- Used by Elasticsearch, Weaviate, Pinecone

---

### 2.2 Query Expansion (Non-LLM)

**Impact**: Better handling of short/ambiguous queries
**Effort**: 4-6 hours
**Cost**: Free

**Implementation**:
```python
def expand_query(query: str, vault_embeddings) -> str:
    # 1. Get query embedding
    query_emb = embed(query)

    # 2. Find top-5 most similar documents
    similar_docs = search(query_emb, k=5)

    # 3. Extract key terms (TF-IDF)
    expansion_terms = extract_key_terms(similar_docs, n=3)

    # 4. Append to original query
    return f"{query} {' '.join(expansion_terms)}"
```

**Example**:
```
Query: "AI" (ambiguous)
→ Finds: ["AI Ethics Paper", "ML Tutorial", "Neural Networks"]
→ Expands to: "AI machine learning neural networks ethics"
→ Better results ✅
```

**When to Use**:
- Queries < 3 words
- Low result count (< 5 results)
- User enables "smart search" mode

---

### 2.3 Time-Aware Scoring (EASY WIN)

**Impact**: Boost recent documents (recency bias)
**Effort**: 2-3 hours
**Cost**: Free

**Implementation**:
```python
def time_decay_boost(similarity_score, created_date, half_life_days=90):
    days_old = (datetime.now() - created_date).days
    decay_factor = 0.5 ** (days_old / half_life_days)
    boost = 0.2 * decay_factor
    return similarity_score * (1 + boost)
```

**Configurable**:
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

---

## Part 3: UI/UX Enhancements (Polish)

> **Priority**: MEDIUM - Nice-to-haves that improve experience
> **Duration**: 2-3 days
> **Source**: UI Review

### 3.1 PWA Support (HIGH VALUE)

**Impact**: Install to home screen, app-like experience
**Effort**: 2-3 hours

**Files to Add**:

1. **manifest.json**:
```json
{
    "name": "Temoa",
    "short_name": "Temoa",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#1a1a1a",
    "theme_color": "#1a1a1a",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
    ]
}
```

2. **service-worker.js** (basic):
```javascript
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open('temoa-v1').then(cache => {
            return cache.addAll(['/', '/search.html', '/offline.html']);
        })
    );
});
```

**Benefits**:
- ✅ One tap to launch from home screen
- ✅ Fullscreen mode (no browser chrome)
- ✅ Offline fallback
- ✅ Feels like native app

---

### 3.2 Keyboard Shortcuts

**Impact**: Power user efficiency
**Effort**: 1-2 hours

**Implementation**:
```javascript
document.addEventListener('keydown', (e) => {
    // '/' to focus search (like GitHub)
    if (e.key === '/' && document.activeElement === document.body) {
        e.preventDefault();
        document.getElementById('query').focus();
    }

    // Escape to clear and blur
    if (e.key === 'Escape') {
        document.getElementById('query').value = '';
        document.getElementById('query').blur();
    }

    // 'c' = collapse all, 'e' = expand all (already implemented)
});
```

---

### 3.3 Search History

**Impact**: Quick re-run of common searches
**Effort**: 2-3 hours

**Implementation**:
```javascript
const searchHistory = {
    max: 10,

    add(query) {
        let history = this.get();
        history = [query, ...history.filter(q => q !== query)].slice(0, this.max);
        localStorage.setItem('temoa_search_history', JSON.stringify(history));
    },

    get() {
        return JSON.parse(localStorage.getItem('temoa_search_history')) || [];
    }
};

// Show autocomplete dropdown with recent searches
```

---

## Implementation Timeline

### Week 1: Foundation & Search Quality

**Day 1-2: Fix Technical Debt**
- Morning: Module-level initialization fix (2-3h)
- Afternoon: Remove sys.path manipulation (1-2h)

**Day 3-4: Search Improvements**
- Morning: Cross-encoder re-ranking (3-4h)
- Afternoon: Query expansion (4-6h)

**Day 5: Polish & Test**
- Morning: Time-aware scoring (2-3h)
- Afternoon: Service layer refactor (start)

### Week 2: UI/UX Polish

**Day 1-2: Service Layer**
- Complete service layer refactor (remaining 2-3h)
- Update server and CLI to use service

**Day 3-4: UI Enhancements**
- PWA support (2-3h)
- Keyboard shortcuts (1-2h)
- Search history (2-3h)

**Day 5: Testing & Deployment**
- Integration testing
- Mobile testing
- Performance validation
- Documentation updates

---

## Success Criteria

### Technical Debt Fixed
- [ ] No module-level config/synthesis initialization
- [ ] No sys.path manipulation anywhere
- [ ] Service layer used by both server and CLI
- [ ] All tests still passing

### Search Quality Improved
- [ ] Cross-encoder re-ranking working (20-30% better precision)
- [ ] Query expansion for short queries (< 3 words)
- [ ] Time-aware scoring configurable
- [ ] Search still responds in < 1s on average

### UI Enhanced
- [ ] PWA installable on mobile home screen
- [ ] Keyboard shortcuts working ('/', Esc, c, e)
- [ ] Search history saves and shows autocomplete
- [ ] No performance regression

### User Experience
- [ ] Still using daily from mobile (habit maintained)
- [ ] Search quality noticeably better
- [ ] UI more efficient (fewer taps/keystrokes)
- [ ] Installation on home screen used regularly

---

## What NOT to Build (Scope Control)

**From original Phase 3 plan, SKIP these**:

- ❌ Archaeology UI (endpoint exists, UI not needed yet)
- ❌ Faceted search (power user feature, not validated need)
- ❌ Result previews (not useful on mobile, no hover)
- ❌ Advanced filters beyond what exists (YAGNI)

**Rationale**: These are hypothetical features. Build based on real friction from actual usage.

**Future consideration**: If you find yourself wanting these during daily use, add them then.

---

## Phase 4 Preview (LLM Integration)

After Phase 3, if vault-first habit is solid:

**LLM-Powered Enhancements** (from Search Architecture Review):
- Conversational search (RAG with vault context)
- Query reformulation (LLM rewrites query for better recall)
- Result summarization (quick overview)

**Cost**: $0.01-0.05 per query
**Effort**: 6-8 hours

**Decision Point**: Only proceed if Phase 3 usage validates need for LLM features.

---

## References

**Consolidated from**:
- `docs/archive/reviews/ARCHITECTURAL-REVIEW.md`
- `docs/archive/reviews/SEARCH-ARCHITECTURE-REVIEW.md`
- `docs/archive/reviews/UI-REVIEW.md`

**Related**:
- `docs/IMPLEMENTATION.md` - Phase tracking
- `docs/ARCHITECTURE.md` - System architecture
- `docs/CHRONICLES.md` - Decision history

---

**Status**: Ready to implement
**Prerequisites**: Phase 2.5 complete ✅
**Next Action**: Fix technical debt (Part 1)
**Estimated Duration**: 2 weeks (10 working days)
