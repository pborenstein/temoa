# Pipeline Step Viewer Harness - Implementation Plan

## Overview

Create a new harness interface that visualizes results at each stage of the 8-stage search pipeline, allowing inspection of how results flow, transform, and get filtered/boosted through the pipeline.

## Background

### Current State
- **Existing harness** (`/harness`): Score mixer for tweaking weights after results return
- **Current capability**: Only shows final scores (semantic, bm25, rrf, cross_encoder, time_boost)
- **Missing**: No visibility into intermediate pipeline stages, filtering counts, or result transformations

### Search Pipeline (8 Stages)
1. **Query Expansion** - TF-IDF expansion for short queries (<3 words)
2. **Primary Retrieval** - Semantic + BM25 hybrid search (or semantic-only)
3. **Chunk Deduplication** - Keep best chunk per file
4. **Score Filtering** - Remove low-scoring results (semantic-only mode)
5. **Status Filtering** - Remove inactive/hidden gleanings
6. **Type Filtering** - Apply include/exclude type filters
7. **Cross-Encoder Re-Ranking** - Precision improvement via re-scoring
8. **Time-Aware Boost** - Recency boost with exponential decay

## Requirements (Inferred)

Since user cannot stop for questions, inferring intent from "see the results of each step":

1. **Visibility**: Show what happens at each pipeline stage
2. **Comparison**: See before/after states for transformations
3. **Metrics**: Result counts, filtering statistics, timing per stage
4. **Debugging**: Understand why specific results appear/disappear/reorder
5. **Non-blocking**: Separate from existing harness (don't break current functionality)

## Implementation Plan

### Phase 1: Backend - Pipeline State Capture

**File**: `src/temoa/server.py` (search endpoint, lines 696-1042)

**Changes**:

1. **Add query parameter**: `pipeline_debug=true` (separate from `harness=true`)

2. **Create pipeline state container**:
   ```python
   pipeline_state = {
       "stages": [],
       "timings": {},
       "totals": {}
   }
   ```

3. **Capture state after each stage**:

   - **Stage 0 (Query Expansion)**:
     - Original query
     - Expanded query (if applied)
     - Expansion terms added
     - Timing

   - **Stage 1 (Primary Retrieval)**:
     - Semantic results (top 20 with scores)
     - BM25 results (top 20 with scores)
     - Combined RRF results (if hybrid)
     - Result counts
     - Timing

   - **Stage 2 (Chunk Deduplication)**:
     - Before count
     - After count
     - Files with multiple chunks
     - Chunks removed per file
     - Timing

   - **Stage 3 (Score Filtering)**:
     - Before count
     - After count
     - Removed results with scores
     - Min score threshold used
     - Timing

   - **Stage 4 (Status Filtering)**:
     - Before count
     - After count
     - Removed paths with statuses
     - Timing

   - **Stage 5 (Type Filtering)**:
     - Before count
     - After count
     - Removed paths with types
     - Include/exclude rules applied
     - Timing

   - **Stage 6 (Cross-Encoder Re-Ranking)**:
     - Before order (top 20 paths + scores)
     - After order (top 20 paths + scores)
     - Score deltas
     - Rank changes
     - Timing

   - **Stage 7 (Time-Aware Boost)**:
     - Before scores (top 20)
     - After scores (top 20)
     - Boost amounts per result
     - Files boosted
     - Timing

4. **Return in response**:
   ```python
   if pipeline_debug:
       data["pipeline"] = pipeline_state
   ```

**Implementation Notes**:
- Keep existing `harness=true` behavior unchanged
- Minimal performance impact when `pipeline_debug=false` (default)
- Capture top 20 results per stage (balance detail vs payload size)
- Use shallow copies to avoid memory bloat

### Phase 2: Backend - Helper Functions

**File**: `src/temoa/server.py`

**New functions**:

1. **`capture_stage_state()`**: Generic stage snapshot
   ```python
   def capture_stage_state(
       stage_num: int,
       stage_name: str,
       results: List[SearchResult],
       metadata: dict,
       start_time: float
   ) -> dict
   ```

2. **`format_result_preview()`**: Format result for debugging (path + key scores)
   ```python
   def format_result_preview(result: SearchResult, max_results: int = 20) -> dict
   ```

3. **`calculate_rank_changes()`**: Diff two result orderings
   ```python
   def calculate_rank_changes(
       before: List[SearchResult],
       after: List[SearchResult]
   ) -> List[dict]  # [{"path": "...", "before_rank": 5, "after_rank": 2, "delta": -3}]
   ```

### Phase 3: Frontend - Pipeline Viewer UI

**New File**: `src/temoa/ui/pipeline.html`

**Layout**:

```
┌─────────────────────────────────────────┐
│ Pipeline Step Viewer                    │
│ [Search Box] [Go] [Clear]              │
│ Vault: [dropdown] Profile: [dropdown]  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 0: Query Expansion              │
│   Original: "AI"                        │
│   Expanded: "AI machine learning"       │
│   Time: 45ms                            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 1: Primary Retrieval            │
│   Semantic: 150 results                 │
│   BM25: 150 results                     │
│   RRF Merged: 150 results               │
│   Time: 412ms                           │
│   [Show Top 20] [Show All]              │
│   ┌───────────────────────────────────┐ │
│   │ 1. file.md (sem: 0.82, bm25: 15.3)│ │
│   │ 2. other.md (sem: 0.79, ...)      │ │
│   └───────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 2: Chunk Deduplication          │
│   Before: 150 → After: 122              │
│   Removed: 28 chunks                    │
│   Time: 8ms                             │
│   [Show Removed Chunks]                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 3: Score Filtering              │
│   Before: 122 → After: 98               │
│   Removed: 24 (below 0.3 threshold)     │
│   Time: 2ms                             │
│   [Show Filtered Results]               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 4: Status Filtering             │
│   Before: 98 → After: 95                │
│   Removed: 3 (inactive/hidden)          │
│   Time: 3ms                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 5: Type Filtering               │
│   Before: 95 → After: 87                │
│   Removed: 8 (type: daily)              │
│   Time: 2ms                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 6: Cross-Encoder Re-Ranking     │
│   Before: 87 → After: 87 (reordered)    │
│   Rank Changes: 23 moved up, 18 down    │
│   Time: 234ms                           │
│   [Show Rank Changes]                   │
│   ┌───────────────────────────────────┐ │
│   │ file.md: #5 → #2 (↑3)            │ │
│   │ other.md: #2 → #8 (↓6)           │ │
│   └───────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ▼ Stage 7: Time-Aware Boost             │
│   Boosted: 12 files                     │
│   Max boost: +18% (file.md)             │
│   Time: 4ms                             │
│   [Show Boosts]                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Pipeline Summary                        │
│ Total Time: 710ms                       │
│ Initial Results: 150                    │
│ Final Results: 87                       │
│ Filtered: 63 (42%)                      │
└─────────────────────────────────────────┘
```

**Features**:
- Collapsible stage sections (default: all expanded)
- Color coding: green for passed, red for filtered, yellow for reordered
- Click result to open in Obsidian
- Export full pipeline state to JSON
- Copy stage data to clipboard

### Phase 4: Frontend - JavaScript Implementation

**File**: `src/temoa/ui/pipeline.html` (inline `<script>`)

**Key Functions**:

1. **`fetchPipelineResults(query)`**: Call API with `pipeline_debug=true`
2. **`renderStages(pipelineState)`**: Build DOM for all stages
3. **`renderStage(stageData, stageNum)`**: Individual stage component
4. **`renderResultList(results, maxShow)`**: Result preview with expand
5. **`renderRankChanges(changes)`**: Diff visualization (arrows, colors)
6. **`calculatePipelineSummary(pipelineState)`**: Aggregate stats
7. **`exportPipeline(pipelineState)`**: JSON download

**Visual Indicators**:
- 🟢 Results passed through
- 🔴 Results filtered out
- 🟡 Results reordered
- ⏱️ Timing badges
- 📊 Count badges

### Phase 5: Integration

**File**: `src/temoa/ui/search.html`

**Add link**: "Pipeline Viewer" button in header (next to "Harness")

**File**: `src/temoa/ui/harness.html`

**Add link**: "Pipeline Viewer" button (next to "Search")

**Result**: Three interconnected tools:
1. **/search** - Main search interface
2. **/harness** - Score mixer (existing)
3. **/pipeline** - Pipeline step viewer (new)

### Phase 6: Documentation

**File**: `docs/SEARCH-MECHANISMS.md`

**Add section**: "Pipeline Debugging" (after "Search Profiles")
- Describe `pipeline_debug=true` parameter
- Explain stage data structure
- Document pipeline viewer UI

**File**: `docs/chronicles/experimentation-harness.md`

**Add entry**: Pipeline viewer implementation
- Motivation (understand stage-by-stage transformations)
- Design decisions (top 20 limit, timing capture)
- Usage patterns

## Critical Files to Modify

### Backend
1. **`src/temoa/server.py`** (lines 696-1042)
   - Add `pipeline_debug` parameter handling
   - Insert state capture after each stage
   - Add helper functions for state formatting

2. **`src/temoa/synthesis.py`** (lines 506-724, `hybrid_search()`)
   - May need to return deduplication metadata (before/after counts)

### Frontend
3. **`src/temoa/ui/pipeline.html`** (new file)
   - Full pipeline viewer implementation (~400-500 lines)

4. **`src/temoa/ui/search.html`** (header section)
   - Add navigation link

5. **`src/temoa/ui/harness.html`** (header section)
   - Add navigation link

### Documentation
6. **`docs/SEARCH-MECHANISMS.md`**
   - Pipeline debugging section

7. **`docs/chronicles/experimentation-harness.md`**
   - Implementation log entry

## Verification

### Unit Testing
- **NOT REQUIRED** for this feature (experimental/debugging tool)
- Manual testing sufficient

### Manual Testing

1. **Basic Flow**:
   ```bash
   # Start server
   uv run temoa server

   # Open in browser
   open http://localhost:8521/pipeline

   # Run test query: "obsidian plugins"
   # Verify all 8 stages appear
   # Check result counts decrease through stages
   # Verify timing data present
   ```

2. **Stage-Specific Tests**:
   - **Query Expansion**: Short query (<3 words) → verify expansion shown
   - **Chunk Dedup**: Query matching long files → verify dedup counts
   - **Score Filter**: Lower threshold → verify removals shown
   - **Status Filter**: Query matching inactive gleanings → verify removals
   - **Type Filter**: Enable type exclusions → verify removals
   - **Re-Ranking**: Verify rank changes highlighted
   - **Time Boost**: Recent files → verify boosts applied

3. **Edge Cases**:
   - Empty query → graceful error
   - No results → show "0 results" through pipeline
   - All stages disabled → minimal pipeline
   - Large result set (500+) → verify top 20 limit works

4. **Performance**:
   - `pipeline_debug=false` → no overhead (baseline timing)
   - `pipeline_debug=true` → <50ms overhead acceptable
   - Large payload (<2MB) for 150 results → acceptable

5. **Integration**:
   - Links from `/search` and `/harness` work
   - Vault selector syncs with other pages
   - Profile selector works
   - Dark mode styling consistent

## Success Criteria

1. ✅ All 8 pipeline stages visible in UI
2. ✅ Result counts accurate at each stage
3. ✅ Timing data captured per stage
4. ✅ Filtering visualized (what was removed and why)
5. ✅ Re-ranking visualized (rank changes, score deltas)
6. ✅ Expandable/collapsible stage sections
7. ✅ Export pipeline state to JSON
8. ✅ <50ms overhead when debug enabled
9. ✅ Mobile-friendly layout
10. ✅ Navigation between search/harness/pipeline tools

## Implementation Order

1. **Backend state capture** (most complex, ~2 hours)
   - Add `pipeline_debug` parameter
   - Capture state after each stage
   - Format output structure

2. **Helper functions** (~30 min)
   - `capture_stage_state()`
   - `format_result_preview()`
   - `calculate_rank_changes()`

3. **Frontend HTML skeleton** (~30 min)
   - Page structure
   - Stage containers
   - Search form

4. **Frontend rendering** (~2 hours)
   - Stage rendering
   - Result lists
   - Rank change visualization
   - Pipeline summary

5. **Integration links** (~15 min)
   - Add links in search.html
   - Add links in harness.html

6. **Testing & refinement** (~1 hour)
   - Manual testing
   - Edge case handling
   - Mobile layout fixes

7. **Documentation** (~30 min)
   - SEARCH-MECHANISMS.md update
   - Chronicles entry

**Total estimated effort**: ~6-7 hours

## Notes

- **No questions mode**: Plan assumes standard pipeline viewer with all stages shown
- **Separation**: Keep separate from existing harness (don't break current functionality)
- **Performance**: Minimal overhead when disabled, acceptable overhead when enabled
- **Mobile-first**: Collapsible sections critical for mobile usability
- **Extensibility**: Easy to add more metadata per stage in future

## Open Design Decisions (Made Without User Input)

1. **Top 20 limit per stage**: Balance detail vs payload size (can increase if needed)
2. **All stages expanded by default**: Maximize visibility (can change to collapsed)
3. **Separate page**: `/pipeline` instead of tabs in existing harness (cleaner separation)
4. **No persistent state**: Don't save queries (keep lightweight, unlike harness profiles)
5. **No live mixing**: Pure read-only viewer (unlike harness's live recomputation)

These can be adjusted post-implementation based on usage feedback.
