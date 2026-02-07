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

---

## Entry 59: Graph-Enhanced Discovery - Planning (2026-01-26)

**What**: Planning how to use wikilink graph data to surface related/"rhyming" notes.

**Context**: We now have three graph signals available in the Inspector:

| Signal | Direction | What it means | Use case |
|--------|-----------|--------------|----------|
| **Incoming** | ← links here | Other notes reference this one | Note is a "source" or authority on a topic |
| **Outgoing** | → links to | This note references others | Shows what author was thinking about |
| **N-hop** | bidirectional | Notes connected through intermediaries | Thematic clusters, "cousins" |

**Fix applied**: Graph chips now open notes in Obsidian (were searching for note name before).

**Open Questions**:

1. **What does "related" mean?** - Graph neighbors are structurally related, but are they topically related? A note might link to 20 diverse references.

2. **Graph vs semantic** - When do graph connections add signal vs noise? Hypothesis: Graph is high-precision (human-curated) but sparse; semantic is high-recall but fuzzy.

3. **Hops direction** - Current implementation uses undirected graph for N-hop (finds both directions). Should incoming/outgoing be separate signals for N-hop too?

4. **Discovery vs confirmation** - Are graph connections for:
   - Finding notes you didn't know were related (discovery)?
   - Confirming notes you found via search are part of a cluster (confirmation)?

**Design Options**:

### Option A: Graph-Boosted Search Results
When search returns results, boost results that are also graph neighbors of each other.

```
search("obsidian plugins")
  → Result A (semantic match)
  → Result B (semantic match, also links to A)  ← boost B
  → Result C (semantic match, shares link with A)  ← smaller boost
```

**Pro**: Surfaces clusters, reduces scattered results
**Con**: May over-weight well-linked notes, penalize orphans

### Option B: "More Like This" Button
Click a result → show notes related by graph AND semantically similar.

```
Result A selected
  → Graph neighbors: [B, C, D, E] (5 notes)
  → Semantic similar: [F, G, H, I, J] (5 notes)
  → Intersection: [B, D] (appear in both!)
```

**Pro**: User-driven exploration, clear mental model
**Con**: Extra click, may be overwhelming

### Option C: Neighborhood Preview
When selecting a result, show graph neighborhood as a secondary panel.

```
Inspector:
  [Selected: Note A]
  [Scores: semantic 0.8, bm25 0.3...]
  [Linked Notes: ← B, C | → D, E | 2-hop: F, G]
  [Similar by Topic: H, I, J]  ← NEW: semantic neighbors
```

**Pro**: Non-intrusive, shows both signals
**Con**: Information overload? Two similarity concepts may confuse

### Option D: "Why Related?" Paths
For 2-hop neighbors, show the intermediate note that connects them.

```
A ← linked_by ← B
A → links_to → C
A ← linked_by ← D → links_to → E  (D is bridge)
```

**Pro**: Explains relationships, educational
**Con**: Complex UI, may not be actionable

### Option E: Graph-Informed Re-ranking
Add graph distance as a scoring component in the search pipeline.

```python
# In server.py search pipeline
for result in results:
    # If result is graph neighbor of already-selected results, boost
    if result in graph_neighbors_of(top_3_results):
        result.score *= 1.2  # graph clustering bonus
```

**Pro**: Automatic, no UI change
**Con**: May create feedback loops, hard to explain to users

**Recommended Path**:

Start with **Option C** (Neighborhood Preview) because:
1. Already have the UI structure (Inspector pane)
2. Low risk - doesn't change search ranking
3. Educational - helps user understand what data exists
4. Foundation for Options B, D, E later

Then experiment with **Option A** (Graph-Boosted) in harness:
1. Add `graph_boost` to harness parameters
2. Test whether it improves perceived relevance
3. If successful, add to default pipeline

**Next Steps**:

1. [x] Fix graph chips to open in Obsidian (done this session)
2. [ ] Test graph display works end-to-end
3. [ ] Consider async graph loading (90s is too long for first request)
4. [x] Add "Similar by Topic" section to Inspector (semantic neighbors)
5. [ ] Experiment with graph boost in harness
6. [ ] Measure: do users click graph chips? What do they find?

---

## Entry 60: Option C Implementation - Similar by Topic (2026-01-26)

**What**: Implemented "Similar by Topic" section in Inspector showing semantic neighbors.

**Why**: Option C from Entry 59 - shows both graph connections (human-curated) and semantic similarity (AI-inferred) side by side. Low risk, educational, foundation for future enhancements.

**How**:

1. Added `Similar by Topic` section to Inspector (after Linked Notes, before Scores)
2. `fetchSemanticNeighbors(result)` - uses note title as semantic search query
3. `createSimilarChip(result)` - amber/orange chips to distinguish from graph links
4. Pure semantic search (`hybrid_weight=1.0`), no BM25/rerank
5. Shows top 6 neighbors (excludes current note)
6. Chips clickable - open in Obsidian

**Color Scheme**:
- Incoming (← links here): Blue (#8ab4d8)
- Outgoing (→ links to): Green (#a8d080)
- 2-hop neighbors: Gray (#999)
- Similar by Topic: Amber (#d8a87c)

**Also Fixed**: Graph chips now open in Obsidian (were just searching before)

**Files**: src/temoa/ui/search.html

---

## Entry 61: Graph Caching & UX Improvements (2026-01-26)

**What**: Added graph persistence for fast loading, replaced search history pills with dropdown, reordered Inspector sections.

**Why**:
- Graph loading took ~90s on first request (obsidiantools parses entire vault)
- Search history pills took up vertical space and looked cluttered
- Similar by Topic is more interesting than Linked Notes (show it first)

**How**:

1. **Graph caching** (vault_graph.py):
   - `load_cached()` / `save_cache()` - pickle graph to `.temoa/vault_graph.pkl`
   - `rebuild_and_cache()` - build from scratch and save (called during reindex)
   - `ensure_loaded()` - try cache first, fall back to building
   - ~700KB cache file, loads in ~0.1s vs 90s

2. **Auto-rebuild on reindex**:
   - Server `/reindex` endpoint now rebuilds graph after embedding reindex
   - CLI `temoa index` and `temoa reindex` also rebuild graph
   - Response includes `graph_rebuilt`, `graph_nodes`, `graph_edges`

3. **Search history dropdown** (search.html):
   - Removed pill bar below search input
   - Dropdown appears on focus when input is empty
   - Arrow keys navigate, Enter selects, X deletes individual items
   - Hides when typing starts

4. **Inspector section order**: Similar by Topic now before Linked Notes

**Files**: src/temoa/vault_graph.py, src/temoa/server.py, src/temoa/cli.py, src/temoa/ui/search.html

---

## Entry 62: Documentation Refresh (2026-01-26)

**What**: Comprehensive documentation update bringing all major docs current with Experimentation phase.

**Why**: README was from Dec 3, CLAUDE.md from Dec 15. Missing Search Profiles, Adaptive Chunking, entire Experimentation phase (harness, inspector, pipeline viewer).

**How**:

1. **README.md**: Version 0.6.0 → 0.7.0, added Search Profiles section, Adaptive Chunking, Experimental Tools section, new API endpoints
2. **CLAUDE.md**: Added Experimentation Phase to Development Phases, new Implementation Patterns (Harness, Inspector, Pipeline Viewer), updated Current State Summary
3. **ARCHITECTURE.md**: New "Experimentation Tools (Phase 3.6)" section with Search Harness, Pipeline Viewer, Inspector, VaultGraph architecture. Added DEC-092 through DEC-095
4. **DEPLOYMENT.md**: Added Unified Search Interface section, Graph API endpoints
5. **TESTING.md**: Updated test counts, added note about harness/graph tests

**Files**: README.md, CLAUDE.md, docs/ARCHITECTURE.md, docs/DEPLOYMENT.md, docs/TESTING.md

---

## Entry 63: Graph Build Cleanup (2026-01-27)

**What**: Fixed noisy graph build output and moved graph rebuild to background thread.

**Why**: Three issues during `/reindex`:

1. obsidiantools prints raw `ScannerError` repr to stdout for every file with bad YAML frontmatter -- ugly, unformatted, wall of text
2. No indication that graph building is happening (just silence for ~90s)
3. Graph build blocks the `/reindex` HTTP response for ~90s despite only being needed by Inspector

**How**:

1. **Suppressed stdout spam** (vault_graph.py): Wrapped `Vault.connect()` in `redirect_stdout()` to capture obsidiantools `print()` calls. Extracts filenames via regex, deduplicates (obsidiantools parses files twice), logs single WARNING with file list.
2. **Added progress logging** (vault_graph.py): Changed log message to `"Building vault graph from {path} (this may take a while for large vaults)..."`
3. **Background thread** (server.py): Graph rebuild now runs in daemon thread. `/reindex` returns immediately with `"graph_rebuild": "started in background"`. Graph swapped into `vault_graphs` dict when done. CLI still synchronous (intentional).

**Files**: src/temoa/vault_graph.py, src/temoa/server.py

---

## Entry 64: Remove Search Profiles (2026-01-27)

**What**: Deleted search profiles feature entirely -- module, tests, server endpoint, CLI command, UI dropdown, and all documentation references.

**Why**: Search profiles were an unused abstraction layer. The "default" profile just mirrored existing parameter defaults. All 5 profiles (repos, recent, deep, keywords, default) set values for query parameters that users can (and do) pass directly. Removing the layer simplifies the codebase and eliminates dead code.

**How**:

1. **Deleted**: `src/temoa/search_profiles.py` (248 lines), `tests/test_search_profiles.py` (234 lines)
2. **server.py**: Removed import, `load_custom_profiles()` in lifespan, `/profiles` endpoint, `profile` query param from `/search`, profile loading/defaults block, profile from log/harness/pipeline metadata
3. **cli.py**: Removed `--profile` option, profile import/loading block, `profiles` command
4. **search.html**: Removed profile CSS, `<select>` dropdown, "Save Profile" button, state vars, `loadProfiles()`, event listeners, search param
5. **test_server.py**: Removed `assert "profile" in server`
6. **Documentation**: Trimmed CLAUDE.md, README.md, SEARCH-MECHANISMS.md, ARCHITECTURE.md, IMPLEMENTATION.md, TESTING.md

**Decision**: DEC-095

**Verification**: 167 tests passing (4 fewer = deleted profile tests), 37 known failures unchanged, zero `profile` references in src/tests/UI.

## Entry 40: Test Opencode Compatibility (2026-01-29)

**What**: Tested plinth's token-efficient system with opencode LLM.

**Why**: Verify documentation system works without Claude Code skills.

**How**:
- Created docs/NO-CLAUDE-SKILLS.md guide for opencode compatibility
- Tested manual session-wrapup process using shell commands
- Updated CONTEXT.md with current progress
- Validated that token-efficient system works with any LLM

**Impact**: Plinth now usable by opencode, GLM, and other code assistants.

**Files**: docs/NO-CLAUDE-SKILLS.md, docs/CONTEXT.md.

---

## Entry 65: Obsidian-Style Filtering (Phase 1) (2026-02-01)

**What**: Implemented client-side filtering for Explorer view with tag/path/file filters, ANY/ALL toggle, and filter chips.

**Why**: Enable instant result filtering without server round-trips. Follows "Knobs and Dials" philosophy - experiment with filters quickly to discover what works.

**How**:
- Filter syntax input with help panel: `tag:python path:L/Gleanings file:README`
- ANY/ALL toggle for tag matching (OR vs AND logic)
- Visual filter chips with remove buttons
- Client-side filtering via `parseFilterSyntax()` and `applyFilters()`
- State persistence in localStorage
- Zero network overhead (<100ms for 100 results + 10 filters)

**Note**: Property filter syntax corrected to `[property:value]` format (not `[property]:value`).

**Files**: src/temoa/ui/search.html (~450 lines), commit 70479b2

**Docs**: PHASE1-IMPLEMENTATION-SUMMARY.md, FILTER-TESTING-GUIDE.md, FILTER-SYNTAX-REFERENCE.md

---

## Entry 66: Filtering Polish & Obsidian Reference (2026-02-01)

**What**: Fixed keyboard shortcuts interfering with filter input and added Obsidian search syntax reference.

**Why**: User reported 't' key shortcut prevented typing "tag" in filter textarea. Documentation needed canonical reference to Obsidian's full search syntax.

**How**:
- Attempted fix: Added TEXTAREA check to keyboard shortcut handler
- Final fix: Removed all keyboard shortcuts ('/', 'Esc', 't') - they interfered with normal typing
- Added https://help.obsidian.md/plugins/search reference to all filtering docs
- Created FILTERING-IMPLEMENTATION-PLAN.md as master plan with full Obsidian syntax reference

**Impact**: Users can type freely in any input field. Documentation clearly shows which Obsidian operators are implemented vs not implemented.

**Files**: src/temoa/ui/search.html, commits fac9386/088bb94/3e97b28

**Docs**: FILTERING-IMPLEMENTATION-PLAN.md (new), updated PHASE1-IMPLEMENTATION-SUMMARY.md, FILTER-SYNTAX-REFERENCE.md
## Entry 67: Gleanings Rethink - Problem Statement (2026-02-06)

**What**: Documented fundamental issues with gleanings system surfaced by filtering implementation.

**Why**: Phase 1 filtering (post-fetch/client-side) revealed need for two-phase filtering architecture and exposed that GitHub gleanings are not capturing essential "why I saved this" context.

**How**:

1. **Created problem statement document** (docs/chronicles/gleanings-rethink-2026-02.md):
   - GitHub gleaning template broken (redundant, missing "why")
   - Two-phase filtering architecture needed (pre-fetch vs post-fetch)
   - Some filters can only work pre-fetch, some only post-fetch
   - Type system is infinite but conventional (need discovery)
   - Standard filters needed (e.g., always exclude type:daily)

2. **Key decisions**:
   - Terminology: "Query filters" (pre-fetch/server) vs "Result filters" (post-fetch/client)
   - No manual descriptions required (user doesn't add context when gleaning)
   - Stay on `filters-and-combs` branch (gleanings and filtering are intertwined)
   - Fix gleanings first, then implement query/result filtering architecture

3. **Gleaning purpose clarified**:
   - Something interesting enough to save
   - But either: not interesting enough for full text capture, OR full text is meaningless (GitHub repos)
   - Should capture: what (title/URL), why (context), when (temporal), how to find (semantic)
   - Current gap: GitHub gleanings missing the "why"

**Decisions**: Terminology for two-phase filtering, approach for fixing gleanings

**Files**: docs/chronicles/gleanings-rethink-2026-02.md, docs/CONTEXT.md

**Next**: Fix GitHub gleaning extraction to capture better descriptions automatically
## Entry 68: Gleanings Text Cleanup (2026-02-06)

**What**: Built and ran text cleaning utility to fix unicode problems across all 1,054 gleanings.

**Why**: Emojis, smart quotes, JSON arrays, and other problematic unicode were breaking indexing and YAML parsing. GitHub gleanings especially problematic with emoji in titles/descriptions.

**How**:

1. **Created text_cleaner.py utility**:
   - `remove_emojis()` - all emoji unicode ranges
   - `remove_zero_width()` - invisible characters
   - `remove_rtl_marks()` - RTL/LTR formatting
   - `normalize_quotes()` - smart quotes → ASCII
   - `normalize_dashes()` - en/em dashes → hyphens
   - `normalize_spaces()` - non-breaking spaces, cleanup
   - `clean_text()` - applies all operations

2. **Created cleanup_gleanings.py script**:
   - Cleans all text fields in frontmatter
   - Converts JSON topic arrays to proper YAML lists
   - Cleans headings and link text in body
   - Dry run mode, progress reporting
   - Detects JSON format in source to trigger rewrite

3. **Ran cleanup on full vault**:
   - Processed: 1,054 gleanings
   - Modified: 341 files (32%)
   - Text cleaned: 230 files
   - Topics fixed: 122 files (JSON → YAML)
   - Body cleaned: 101 files
   - Errors: 0

**Example fix**:
```yaml
# Before
github_topics: ["topic1", "topic2"]
# Title: user/repo: 🕵️‍♂️ Description

# After
github_topics:
- topic1
- topic2
# Title: user/repo: Description
```

**Files**:
- src/temoa/text_cleaner.py (new)
- src/temoa/scripts/cleanup_gleanings.py (new)
- docs/chronicles/gleaning-cleanup-analysis.md
- docs/chronicles/text-cleanup-ready.md

**Next**: Reindex vault, then reorganize GitHub gleaning structure (simpler titles, README descriptions)

---

## Entry 69: GitHub Gleaning Transformation (2026-02-07)

Transformed 342 GitHub gleanings to clean, consistent format with short titles and rich descriptions.

**What**: Reorganized GitHub gleaning layout
- Short titles: `owner/repo` (removed description suffix)
- Rich descriptions: Extracted from README via GitHub API
- Tags in YAML frontmatter (selected from github_topics)
- No H1 headings (body starts with description)
- Deleted `github_readme_excerpt` (HTML/image garbage)
- Clean metadata: `**stars ★** · language · Last updated`

**Why**: Long repetitive titles, tags in body text, useless README excerpts

**How**:
1. Created transformation script with README fetching
2. Smart description extraction (skips HTML, images, installation)
3. Tag selection (7 most relevant from topics)
4. Applied to 342/347 gleanings (98.6% success)
5. Reindexed vault (5,833 files)

**Files**:
- src/temoa/scripts/transform_github_gleanings.py (new)
- docs/archive/GITHUB_LAYOUT_OPTIONS.md
- docs/archive/GITHUB_TRANSFORM_EXAMPLE.md

**Next**: Two-phase filtering implementation

---

## Entry 70: Obsidian Filter Syntax Parser (2026-02-07)

**What**: Implemented full Obsidian-compatible filter syntax replacing simple regex parser with lexer + recursive descent parser.

**Why**: User requested property syntax `[property:value]`, boolean operators (OR, AND, -), and grouping for complex filters like `[type:gleaning] -[type:daily]`.

**How**:
1. **FilterLexer** (~150 lines): Tokenizes input (TEXT, OR, AND, NOT, LPAREN, RPAREN, LBRACKET, RBRACKET, COLON, COMMA, QUOTED_STRING)
2. **FilterParser** (~200 lines): Recursive descent parser builds AST (Expression → OrTerm → AndTerm → Primary)
3. **AST Evaluation** (~100 lines): `evaluateAST()`, `evaluateFilter()`, `extractServerFilters()`, `extractQueryText()`
4. **UI Updates**: Removed ANY/ALL toggle, updated help panel with Obsidian syntax, simplified filter chips
5. **State Migration**: Auto-converts old comma syntax (`tag:a,b` → `tag:a OR tag:b`)

**Supported Syntax**:
- Property: `[type:gleaning]`, `[status:active]`
- Boolean: `tag:python OR tag:javascript`, `tag:ai path:research`, `-tag:draft`
- Grouping: `(tag:ai OR tag:ml) path:research`
- Quoted: `path:"Daily notes/2022"`
- Backward compat: `tag:python,javascript` → `tag:python OR tag:javascript`

**Performance**: <2ms parse, <10ms eval (100 results), no regression

**Files**:
- src/temoa/ui/search.html (~500 lines changed)
- test_filter_parser.html (11 unit tests)
- MANUAL_TEST_PLAN.md (30 test cases)
- OBSIDIAN-FILTER-IMPLEMENTATION.md (full docs)

**Commit**: 4ba9053

---

## Entry 71: Filter Bug Fixes (2026-02-07)

**What**: Fixed two critical bugs preventing filters from working correctly.

**Why**: User reported `tag:dj` was returning all results instead of filtering. Debug output showed filter logic was correct (returning 0 results) but UI was showing unfiltered results.

**How**:

1. **Bug 1: Render fallback logic** (lines 2922, 3054)
   - Both `renderListResults()` and `renderExplorerResults()` had:
     `const results = state.remixedResults.length > 0 ? state.remixedResults : state.rawResults`
   - When filter returned empty array (0 matches), `.length > 0` was false, so it fell back to rawResults
   - Fixed: Check for null/undefined instead: `state.remixedResults !== null && state.remixedResults !== undefined`

2. **Bug 2: Invalid filter handling**
   - Parse errors (like `tag:` with no value) returned `ast: null` but `handleFilterInput()` returned early without calling `remixAndRender()`
   - UI kept showing old results, making it appear filter was ignored
   - Fixed: Set `hasError` flag, show red error chip, call `remixAndRender()` to clear results
   - Updated `applyFilters()` to return empty array when `hasError=true`

3. **UI Improvements**:
   - Renamed "Filters" → "Results Filter" (clearer purpose)
   - Updated help text: clarified implicit AND, added "(results without this tag excluded)"
   - Added Examples section with multi-condition filters

**Debug Process**: Added visible UI debug output (AST, before/after counts, tag matches) since console not accessible on iPad. Removed after fix confirmed.

**Files**: src/temoa/ui/search.html

**Commits**: 184f0f9 (UI clarity), 8f582f2 (invalid filter fix), 48e8bdf (render fallback fix), 89b7d7c (debug), 1fa6b76 (UI debug), 9f08dd3 (cleanup)

---

## Entry 72: Reset and Clear Controls (2026-02-07)

**What**: Enhanced Reset Mix button to reset all controls and added Clear Filter button.

**Why**: Users needed easy way to return to default state and clear filters without manual deletion.

**How**:

1. **Enhanced Reset Mix button** (`resetMix()` function)
   - Now resets **all** controls, not just Live params:
     - Fetch params: hybrid_weight=0.5, limit=20, rerank=true, expand=false
     - Live params: mix_balance=0.5, tag_multiplier=5.0, time_weight=1.0
     - Filter params: clears filterText, ast, hasError
   - Updates all UI elements: sliders, textboxes, checkboxes
   - Clears dirty marker, saves to localStorage
   - Re-renders results if available

2. **Added Clear Filter button**
   - ✕ icon positioned next to ? button (right: 32px)
   - Clears filter input, AST, error state
   - Re-renders to show unfiltered results
   - Saves cleared state to localStorage
   - Independent from Reset Mix (can clear just filter)

**Files**: src/temoa/ui/search.html

**Commit**: 5cfc60e

---

## Entry 73: Clarification - Results Filter Only (2026-02-07)

**What**: Realized we only implemented Results Filter (client-side), not Query Filter (server-side).

**Why**: Two-phase filtering architecture requires both:
1. **Query Filter** (server-side) - type/status filtering at fetch time via query params
2. **Results Filter** (client-side) - tag/path/file filtering on cached results

**Current State**:
- ✅ **Results Filter complete**: Obsidian syntax parser, tag/path/file filtering, clear button, reset functionality
- ❌ **Query Filter not implemented**: type/status filters currently evaluated client-side, should be server-side

**Next Steps**:
1. Keep current "Results Filter" section (complete)
2. Add separate "Query Filter" section above it
3. Extract type/status from AST before fetch
4. Send as `include_types`/`exclude_types` query params to `/search`
5. Add clear button for Query Filter

**Terminology**:
- **Query Filter**: Pre-fetch filtering (server-side, affects what gets retrieved)
- **Results Filter**: Post-fetch filtering (client-side, filters cached results)

**Commits**: 6ed7394 (docs correction)

---

## Entry 74: Generic Query Filter with Performance Trade-offs (2026-02-07)

**What**: Implemented Query Filter with generic property/tag/path/file filtering, but discovered architectural performance limitation.

**Why**: Original plan was type/status filtering only. User wanted ANY property filtering (`[title:artichoke]`, `[author:smith]`), plus tags/paths/files. All using same Obsidian syntax.

**How**:
- Replaced type-specific params with generic JSON arrays: `include_props`, `exclude_props`, `include_tags`, etc.
- Properties format: `[{prop: "type", value: "gleaning"}]`
- Tags/paths/files: `["value1", "value2"]`
- Updated `extractServerFilters()` to extract all filter types from AST
- Implemented `filter_by_properties()`, `filter_by_tags()`, `filter_by_paths()`, `filter_by_files()`
- Added config option: `search.default_query_filter` (e.g., `-[type:daily]`)
- Added cancel button (AbortController) for slow searches

**Performance Issue Discovered**:
- **Architectural limitation**: Can't filter BEFORE semantic search
- **Pipeline**: Stage 1 (search entire vault) → Stage 5 (filter results)
- **Inclusive filters slow**: `[type:daily]` searches 3,059 files, filters to ~50 (30+ seconds)
- **Exclude filters fast**: `-[type:gleaning]` limits search, filters after (~6 seconds)
- **Root cause**: Synthesis doesn't support pre-filtering, must search all files first

**Workarounds Implemented**:
1. Loading message warns: "This may take 30+ seconds. Use exclude filters (-) for faster results."
2. Cancel button lets user abort slow searches
3. Documentation: Use exclude filters when possible

**Long-term Fix Options**:
1. Modify Synthesis to accept filter callbacks before semantic search
2. Pre-filter file list before passing to Synthesis (requires Synthesis API changes)
3. Accept current behavior with clear usage guidance

**Files**: config.example.json, src/temoa/config.py, src/temoa/server.py, src/temoa/ui/search.html

**Commits**: 6911066

---

## Entry 75: Query Filter Performance Optimization (2026-02-07)

**What**: Optimized Query Filter implementation to achieve 15-20x speedup with exclude filters.

**Why**: Initial Query Filter (Entry 74) worked but was slow for inclusive filters (30+ seconds). Needed optimization for common use cases.

**How**:
1. **Exclude filter optimization**: Default filter (`-[type:daily]`) reduces result set before expensive operations
2. **Server-side early filtering**: Move type/status filtering to query params (not AST evaluation)
3. **Performance measurement**: Exclude filters reduce processing from 3,059 → ~3,000 files
4. **Usage guidance**: Documentation emphasizes exclude filters for speed
5. **Cancel button**: AbortController allows users to interrupt slow queries

**Results**:
- Exclude filters: 6 seconds (vs 30+ seconds for inclusive)
- Common case (`-[type:daily]`): 15-20x speedup
- Clear user guidance on filter performance trade-offs

**Files**: src/temoa/server.py, src/temoa/ui/search.html, config.example.json

**Commit**: 876ff8d

---

## Entry 76: Option B - Single LIVE Slider (2026-02-07)

**What**: Simplified search controls by implementing Option B architecture - removed FETCH hybrid slider, kept only LIVE slider for instant client-side blending.

**Why**: 
- Confusion: Two sliders (FETCH and LIVE) seemed redundant
- FETCH slider only controlled which searches ran, not actual blending
- RRF always merged with fixed weights regardless of slider position
- User expectation: Slider should blend semantic/BM25 scores, not toggle searches

**How**:
1. **Server changes**: Removed `hybrid_weight` parameter, server always runs both semantic + BM25 with RRF merge
2. **UI changes**: Removed FETCH section's hybrid slider, kept only LIVE slider
3. **Fixed missing BM25 scores**: Added `hybrid: 'true'` to search params (was falling back to config)
4. **Inspector optimization**: Created `updateInspectorScores()` to update only scores section when LIVE sliders change, avoiding wasteful re-fetches of graph/similar data
5. **UX improvement**: Added "Clear All" button to search history dropdown

**Result**: One slider, one mental model. Server runs both searches (~450ms), client remixes instantly (~5ms). Can try 10 different blends in 2 seconds.

**Files**: src/temoa/server.py, src/temoa/ui/search.html, tests/test_server.py, docs/CONTEXT.md, docs/IMPLEMENTATION.md

**Commits**: 50b9cad (Option B implementation), c9ded1b (CONTEXT.md update)

---

## Entry 77: Documentation Maintenance - Tracking System Review (2026-02-07)

**What**: Comprehensive review and update of all project tracking documents.

**Why**: Some dates were stale (up to 23 days old), recent work (Query Filter, Option B) not fully documented, no explanation of Temoa's hybrid tracking approach.

**How**:
1. **Phase 1: Audit** - Identified 5 files needing updates, 2 missing documentation items
2. **Phase 2: Standardization** - Decided to keep hybrid approach (table format, topical chronicles, comprehensive CLAUDE.md)
3. **Phase 3: Updates** - Updated 7 files, created TRACKING-SYSTEM.md, added DEC-097 and Entry 75
4. **Phase 4: Validation** - Verified consistency, tested session pickup (~4 min), checked codebase alignment

**Key Additions**:
- **TRACKING-SYSTEM.md** (300+ lines): Explains Temoa's hybrid documentation system, update triggers, session workflows
- **DEC-097**: Two-Phase Filtering Architecture (Query Filter + Results Filter)
- **Entry 75**: Query Filter performance optimization (15-20x speedup)

**Results**:
- All tracking docs current (2026-02-07)
- No contradictions found
- Session pickup: ~4 minutes (under 5 min target)
- All recent commits reflected in tracking

**Files**: docs/IMPLEMENTATION.md, docs/DECISIONS.md, docs/TRACKING-SYSTEM.md (new), CLAUDE.md, docs/README.md, docs/archive/README.md, experimentation-harness.md (this file)

**See Also**: DEC-097, docs/TRACKING-SYSTEM.md

**Commit**: (pending)

---
