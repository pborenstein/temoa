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
