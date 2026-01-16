# Experimentation Phase: Search Harness

Chronicle entries for the Search Harness implementation - an interactive score mixer for experimenting with search parameter weights.

---

## Entry 50: Search Harness Foundation (2026-01-15)

**What**: Fixed bugs and implemented `?harness=true` API parameter for structured score output.

**Why**: Need to see all raw component scores to experiment with different weight combinations and understand how parameters affect ranking.

**How**:
1. **Fixed cross_encoder_score bug** - UI looked for `rerank_score` but backend sends `cross_encoder_score`
2. **Fixed pipeline diagram** - Added Stage 2 (Chunk Deduplication), corrected stage order (re-rank before time boost)
3. **Added harness API** - `?harness=true` returns `result.scores` object with semantic/bm25/rrf/cross_encoder/time_boost/tag_boosted, plus `harness.mix` and `harness.server` metadata

**Files**: src/temoa/server.py, src/temoa/ui/search.html, docs/SEARCH-MECHANISMS.md, tests/test_server.py

**Tests**: 12/12 server tests passing (added test_search_harness_parameter, test_search_without_harness)

---

## Entry 51: Harness UI Complete (2026-01-15)

**What**: Built standalone `/harness` page (Phase 2) with client-side score remixing.

**Why**: Keep production search UI stable while experimenting with scoring weights. Separate page allows iterating without disrupting normal use.

**How**:
1. Created `harness.html` - standalone score mixer page
2. Client-side remix function re-sorts results instantly when weights change
3. Server params section tracks when re-fetch needed
4. Added info tooltips (?) explaining every parameter
5. Semantic/BM25 balance slider (single control instead of two inputs)
6. Compact layout: slider(2fr) + tags(1fr) + time(1fr)

**Features**:
- Vault/profile selectors
- State persistence (localStorage)
- Export JSON, save profiles
- 13/13 tests passing

**Files**: src/temoa/ui/harness.html, src/temoa/server.py (route), tests/test_server.py

**Commits**: cfaf048, 49e813a, 2a1a7df, 83faefb, e73b2c6

---

## Entry 52: Harness UI Refinements (2026-01-15)

**What**: Improved harness clarity with Fetch/Live terminology, visual feedback, and slider fixes.

**Why**: User testing revealed confusion about which params affect retrieval vs ranking, and score indicators weren't visually distinct.

**Changes**:
1. **Fetch/Live split** - Swapped section order (Fetch first, Live second); renamed "Server Parameters" to "Fetch", "Mix Weights" to "Live"
2. **Fetch balance slider** - Converted from number input to slider matching Live slider style
3. **Visual feedback** - Time-boosted dates glow purple; matched tags glow green (passed `tags_matched` through from BM25)
4. **Tags=0 behavior** - Disables tag boosting (1x multiplier) instead of zeroing scores
5. **Slider persistence** - Fixed bug where Live slider reset to 50/50 after search (was overwriting from server response)
6. **Removed redundant "tags: boosted"** - Green tag glow shows same info

**Files**: src/temoa/ui/harness.html, src/temoa/synthesis.py (added tags_matched to results)
