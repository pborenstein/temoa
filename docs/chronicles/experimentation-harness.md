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

---

## Entry 53: Pipeline Step Viewer (2026-01-21)

**What**: Built `/pipeline` viewer to visualize results at each stage of the 8-stage search pipeline.

**Why**: While the harness shows final scores and allows weight tuning, it doesn't show how results transform through the pipeline. Need visibility into intermediate stages to understand:
- Why specific results appear/disappear/reorder
- How filtering affects result counts at each stage
- Which results get tag-boosted vs cross-encoder re-ranked
- Performance bottlenecks (timing per stage)

**How**:

1. **Backend (server.py)**:
   - Added `pipeline_debug=true` query parameter
   - Created helper functions: `capture_stage_state()`, `format_result_preview()`, `calculate_rank_changes()`
   - Inserted state capture after each pipeline stage (0, 1, 3-7)
   - Stage data includes: result count, top 20 results preview, stage-specific metadata, timing

2. **Frontend (pipeline.html)**:
   - Standalone page at `/pipeline` with vault/profile selectors
   - Collapsible stage sections (default expanded) showing:
     - Summary metrics (total time, initial/final counts, filtering %)
     - Stage-by-stage results with scores (semantic, BM25, RRF, cross_encoder, time_boost)
     - Rank changes (before→after with arrows and deltas)
     - Removed items (filtering stages show what was filtered and why)
   - Export to JSON functionality
   - Mobile-friendly collapsible layout

3. **Integration**:
   - Added "Pipeline" nav links to `/search` and `/harness` headers
   - All three tools now interconnected (Search ↔ Harness ↔ Pipeline)

**Pipeline Stages Captured**:

- **Stage 0**: Query Expansion (original→expanded query, expansion terms)
- **Stage 1**: Primary Retrieval & Chunk Deduplication (semantic/BM25 results, search mode)
- **Stage 3**: Score Filtering (removed low-scoring results, threshold applied)
- **Stage 4**: Status Filtering (removed inactive/hidden gleanings)
- **Stage 5**: Type Filtering (removed by include/exclude rules)
- **Stage 6**: Cross-Encoder Re-Ranking (rank changes, preserved tag-boosted)
- **Stage 7**: Time-Aware Boost (boosted items, rank changes)

**Performance**: <50ms overhead when enabled, 0ms when disabled (default)

**Files**:
- src/temoa/server.py (pipeline_debug param, helper functions, state capture)
- src/temoa/ui/pipeline.html (new viewer page)
- src/temoa/ui/search.html (added nav link)
- src/temoa/ui/harness.html (added nav link)
- docs/SEARCH-MECHANISMS.md (new Pipeline Debugging section)

**Testing**: Manual verification of all 7 stages with query "test" shows correct counts, timing, rank changes, and metadata.

**Commits**: 2508210, fb8be51

---

## Entry 54: Unified Explorer Interface - Planning (2026-01-23)

**What**: Designed comprehensive plan for consolidating Search/Harness/Pipeline into single unified interface.

**Why**: Three separate tools require context switching, can't explore pipeline while tuning mixer, can't inspect result details while viewing stages. User requested ability to "explore the whole pipeline, inspect individual results, and play with the things" in one place.

**How**:

1. **Three-pane layout**:
   - Left: Controls pane (Fetch/Live mixer from harness)
   - Center: Results pane (List mode or Pipeline mode)
   - Right: Inspector pane (new - detailed result inspection)

2. **Two view modes**:
   - List mode: Current search.html results with selection
   - Pipeline mode: Stage-by-stage accordion from pipeline.html

3. **Inspector** (new component):
   - Scores tab: All score types with visual bars
   - Metadata tab: Tags, type, status, file info
   - Journey tab: Pipeline stage progression for selected result

4. **Responsive design**:
   - Desktop: Three columns (280px | 1fr | 320px)
   - Mobile: Vertical stack with accordions + bottom drawer

5. **Implementation phases**: 5 phases, 14-20h estimate
   - Phase 1: Core layout & infrastructure
   - Phase 2: Inspector implementation
   - Phase 3: Pipeline mode integration
   - Phase 4: Live remix & polish
   - Phase 5: Migration & cleanup

**Plan**: `docs/plans/unified-search-interface.md` (wireframes, API strategy, open questions, risk analysis)

**Status**: Planning complete, awaiting user approval to begin implementation

**Commits**: [documentation only - no code commits]

---

## Entry 55: Phase 1 Implementation - Core Layout (2026-01-23)

**What**: Started Phase 1 implementation of Explorer interface - completed 4/7 tasks

**Why**: Build unified three-pane interface to consolidate search/harness/pipeline tools into single workflow

**How**:
- Created `src/temoa/ui/explorer.html` with responsive three-pane grid layout (280px | 1fr | 320px on desktop, vertical stack on mobile)
- Implemented full state management with `explorerState` object + localStorage persistence (view mode, fetch/live params, search history)
- Built Controls pane with Fetch section (hybrid balance, limit, rerank, expand) and Live section (mix balance, tag multiplier, time weight)
- Added `/explorer` route to `src/temoa/server.py` (serves explorer.html via FileResponse)
- Wired up all mixer controls with dirty tracking, instant Live remix, state persistence

**Decisions**: Used recommendations from plan - global view mode persistence, last-used default, Scores tab default

**Status**: 4/7 Phase 1 tasks complete (layout, state, controls, route) - 3 remaining (Results pane, Inspector layout, search flow)

**Files**: `src/temoa/ui/explorer.html`, `src/temoa/server.py`

---

## Entry 56: Unified Search Interface Complete (2026-01-25)

**What**: Consolidated search.html, explorer.html, harness.html, and pipeline.html into single unified interface with view toggle.

**Why**: User requested single page for both simple search and parameter exploration without context switching. Multiple separate tools were "scaffolding" to be burned after learning what works.

**How**:
- Merged search.html (2,507 lines) + explorer.html (2,093 lines) → unified search.html (2,456 lines)
- Added view toggle in header: List ⟷ Explorer (keyboard shortcut: `t`)
- Single state object with shared localStorage (query, results, history, fetch/live params persist across views)
- List view: simple result cards + search history sidebar
- Explorer view: three-pane layout (Controls | Results | Inspector) with full mixer controls
- Deleted obsolete files: harness.html, pipeline.html, explorer.html
- Removed routes: /harness, /pipeline, /explorer from server.py

**Testing**: Verified at http://localhost:8080/ - view toggle working, search functional in both modes, state persistence confirmed

**Files**: src/temoa/ui/search.html (unified), src/temoa/server.py (routes removed)

**Commits**: dd11668

---

## Entry 57: Graph Exploration Research (2026-01-25)

**What**: Researched libraries for parsing Obsidian wikilinks and building note relationship graphs.

**Why**: Current search treats notes as isolated islands. Wikilinks represent human-curated relationships that Temoa ignores. User wants to explore note neighborhoods, not just search results.

**Key Insight**: Two layers of relatedness:
1. **Explicit links** (wikilinks) - high signal, human-curated
2. **Implicit similarity** (embeddings) - model-inferred, works on any text

**Research Findings**:

| Library | Status | Notes |
|---------|--------|-------|
| **obsidiantools** | Recommended | v0.11.0, 502 stars, NetworkX integration, production-ready |
| obsidianmd-parser | Alternative | Python 3.12+, modern but smaller community |
| Obsidian-Markdown-Parser | Basic | Limited docs, link extraction only |

**obsidiantools capabilities**:
- Parse `[[wikilinks]]` and `[[link|alias]]`
- Build NetworkX graph for traversal (shortest path, clustering, centrality)
- Get backlinks/forward links for any note
- Detect orphaned notes
- Frontmatter and tag extraction

**Plain text fallback**: For non-Obsidian vaults, use pure semantic similarity (current behavior) or build implicit links from embedding neighborhoods.

**Potential features**:
- "Show neighborhood" - notes 1-2 hops from selected result
- Graph-boosted search - boost results that share link neighborhoods with top matches
- Cluster visualization - identify connected groups around query

**Files**: docs/CONTEXT.md (updated), docs/chronicles/experimentation-harness.md (this entry)

**Status**: Research complete, ready to prototype

---

## Entry 58: Graph Exploration Implementation (2026-01-26)

**What**: Implemented wikilink graph exploration in Explorer Inspector using obsidiantools.

**Why**: Search treats notes as islands; wikilinks represent human-curated relationships that Temoa was ignoring. User wants to explore note neighborhoods, not just search results.

**How**:

1. Added `obsidiantools` dependency (v0.11.0) - parses wikilinks, builds NetworkX graph
2. Created `src/temoa/vault_graph.py`:
   - `VaultGraph` class with lazy loading per vault
   - `get_neighbors(note, hops)` - returns incoming/outgoing links + N-hop neighborhood
   - `get_hub_notes()` - finds well-connected notes
   - `_normalize_note_name()` - handles path variations (L/foo.md -> foo)
3. Added server endpoints:
   - `GET /graph/neighbors?note=X&vault=Y&hops=2`
   - `GET /graph/stats?vault=Y`
   - `GET /graph/hubs?vault=Y`
4. Added "Linked Notes" section to Inspector pane (after title, before Scores)
5. Graph cached in `app.state.vault_graphs` dict

**Performance**: ~90s to load 6000-note vault graph (lazy, on first request)

**Files**:
- src/temoa/vault_graph.py (new)
- src/temoa/server.py (endpoints, imports, app.state)
- src/temoa/ui/search.html (Inspector section)
- tests/test_server.py (3 new tests)
- pyproject.toml (obsidiantools dependency)

**Status**: Implementation complete, needs server restart to test end-to-end
