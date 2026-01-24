# Unified Search Interface - Implementation Plan

**Status**: Draft for Approval
**Created**: 2026-01-21
**Branch**: `knobs-and-dials`
**Phase**: Experimentation (Harness UI)

---

## Problem Statement

Currently have three separate search interfaces:

1. **`/search`** (search.html) - Production search UI, simple and focused
2. **`/harness`** (harness.html) - Score mixer for experimenting with weights
3. **`/pipeline`** (pipeline.html) - Pipeline step viewer for debugging

This separation means:
- Context switching between tools breaks flow
- Can't see pipeline stages while tuning mixer weights
- Can't inspect individual results while viewing pipeline
- Need to re-run same query across 3 different pages
- Settings don't persist across tools (except via localStorage)

**User request**: "I want to be able to explore the whole pipeline, inspect individual results, and play with the things" - all in one place.

---

## Vision: The Explorer

A unified, multi-pane interface that consolidates all three tools into a single cohesive experience.

### Core Concept: Three-Pane Layout

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER: Query + Vault + Profile + Run                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐   │
│  │              │  │                 │  │              │   │
│  │   CONTROLS   │  │    RESULTS      │  │   INSPECT    │   │
│  │              │  │                 │  │              │   │
│  │   (Mixer)    │  │   (List/Flow)   │  │  (Details)   │   │
│  │              │  │                 │  │              │   │
│  │              │  │                 │  │              │   │
│  └──────────────┘  └─────────────────┘  └──────────────┘   │
│   Fetch/Live       Results w/          Pipeline view,      │
│   params           scores + tags        scores, metadata   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Left Pane: **Controls** (from Harness)
- **Fetch section** (server params - triggers new search)
  - Hybrid balance slider (Semantic ↔ BM25)
  - Result limit
  - Cross-encoder toggle
  - Query expansion toggle

- **Live section** (client params - instant remix)
  - Semantic/BM25 balance slider
  - Tag multiplier
  - Time weight

- **Actions**
  - Reset Mix
  - Save Profile
  - Export JSON

### Center Pane: **Results** (enhanced from Search)
- **View Modes** (toggle button)
  - **List mode**: Current search.html style (default)
    - Collapsible cards with scores
    - Click to select → shows in Inspector
  - **Pipeline mode**: Stage-by-stage flow
    - All 7 stages as vertical accordion
    - Each stage shows counts, timing, top results
    - Click result in any stage → shows in Inspector

### Right Pane: **Inspector** (new)
- **Empty state**: "Select a result to inspect"
- **When result selected**:
  - Title + path + Obsidian link
  - **All Scores** tab:
    - Semantic, BM25, RRF, Cross-Encoder, Mixed
    - Time boost, Tag boosted indicator
    - Visual score bars
  - **Metadata** tab:
    - Tags (matched highlighted)
    - Type, Status, Description
    - Days old, modification date
    - File size, word count
  - **Pipeline Journey** tab (if in pipeline mode):
    - Shows which stages this result appeared in
    - Rank changes at each stage
    - Why it was filtered (if applicable)

---

## Design Decisions

### Layout Strategy: Adaptive Grid

**Desktop (>1024px)**:
```css
.explorer-grid {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 16px;
}
```

**Tablet (768-1024px)**:
```css
.explorer-grid {
  grid-template-columns: 240px 1fr 280px;
}
```

**Mobile (<768px)**: Stack vertically, use accordions
- Controls accordion (collapsed by default)
- Results (always visible)
- Inspector drawer (slides up from bottom when result selected)

### State Management

**Single source of truth**:
```javascript
const explorerState = {
  // Search state
  query: '',
  vault: null,
  profile: null,

  // Results
  rawResults: [],        // from server
  remixedResults: [],    // after client-side remix
  pipelineData: null,    // pipeline stages (if pipeline mode)

  // UI state
  viewMode: 'list',      // 'list' | 'pipeline'
  selectedResult: null,  // currently inspected result
  selectedStage: null,   // if viewing pipeline

  // Mixer state
  fetchParams: { ... },
  liveParams: { ... },

  // Persistence
  searchHistory: [],
}
```

### API Strategy

**Single endpoint call** with both harness and pipeline data:
```javascript
const params = {
  q: query,
  vault: vault,
  profile: profile,
  harness: 'true',        // get structured scores
  pipeline_debug: 'true', // get stage-by-stage data
  // ... other params
}
```

This avoids multiple requests. Backend already supports both flags.

### Component Reuse

**Controls Pane**: Copy from harness.html
- Fetch/Live mixer sections
- Balance sliders
- Tooltips
- State persistence

**Results List**: Enhanced search.html
- Add selection state (highlight selected)
- Click handler to populate Inspector
- Keep collapse/expand functionality

**Pipeline View**: Adapted pipeline.html
- Same stage accordion
- Click result → populate Inspector (instead of inline display)
- Keep timing/metadata sections

**Inspector**: New component
- Tabbed interface (Scores | Metadata | Journey)
- Responsive drawer on mobile
- Deep-link support (URL param for selected result)

---

## Implementation Phases

### Phase 1: Core Layout & Infrastructure
**Goal**: Get the three-pane layout working with basic data flow

**Tasks**:
- [ ] Create `explorer.html` with responsive grid layout
- [ ] Implement state management system (`explorerState` object)
- [ ] Build Controls pane (copy from harness.html)
- [ ] Build Results pane - List mode (adapted from search.html)
- [ ] Build empty Inspector pane (just layout, no content yet)
- [ ] Wire up search flow: Controls → API → Results
- [ ] Add route `/explorer` to server.py

**Success Criteria**:
- Can run search with mixer controls
- Results display in center pane
- Layout responsive on desktop/mobile
- State persists to localStorage

---

### Phase 2: Inspector Implementation
**Goal**: Make result inspection fully functional

**Tasks**:
- [ ] Implement result selection in List mode
- [ ] Build Inspector "Scores" tab
  - All score types with visual bars
  - Tag boosted indicator
  - Time boost visualization
- [ ] Build Inspector "Metadata" tab
  - Tags (matched highlighted)
  - Type, status, description
  - File info (size, dates, counts)
- [ ] Build Inspector mobile drawer (slide up from bottom)
- [ ] Add keyboard shortcuts (arrow keys to navigate results, Enter to inspect)

**Success Criteria**:
- Click result → Inspector shows all scores and metadata
- Inspector responsive on mobile (drawer)
- Can navigate results with keyboard
- Clear visual indication of selected result

---

### Phase 3: Pipeline Mode
**Goal**: Add pipeline visualization as alternate view mode

**Tasks**:
- [ ] Implement view mode toggle (List ↔ Pipeline)
- [ ] Build Pipeline view in center pane (adapted from pipeline.html)
  - Stage accordion (7 stages)
  - Counts, timing, metadata per stage
  - Click result in any stage → Inspector
- [ ] Build Inspector "Journey" tab
  - Show which stages result appeared in
  - Rank changes per stage
  - Filtering reasons (if filtered)
- [ ] Add stage-level summaries (total time, filtering %)
- [ ] Preserve view mode in localStorage

**Success Criteria**:
- Toggle between List and Pipeline modes
- Click result in any pipeline stage → Inspector shows full details
- Journey tab shows stage-by-stage progression
- Pipeline timing and metadata visible

---

### Phase 4: Live Remix & Polish
**Goal**: Client-side remix working, final UX polish

**Tasks**:
- [ ] Wire up Live mixer to instant remix
  - Balance slider → re-sort results in real-time
  - Tag/time weights → recalculate mixed scores
  - Update Inspector scores when remix happens
- [ ] Implement Fetch dirty tracking (yellow border when params changed)
- [ ] Add Export JSON (exports full state: query, params, results, pipeline)
- [ ] Add Save Profile (saves mixer settings to localStorage)
- [ ] Add search history dropdown (shared with other tools)
- [ ] Keyboard shortcuts guide (`?` key)
- [ ] Mobile UX testing and refinements

**Success Criteria**:
- Mixer changes → instant re-sort (no API call)
- Fetch changes → clear indication re-search needed
- Export produces complete JSON snapshot
- Mobile UX smooth and intuitive

---

### Phase 5: Migration & Cleanup
**Goal**: Decide fate of old tools, update docs

**Tasks**:
- [ ] User testing: Is Explorer a full replacement?
- [ ] Decision: Keep old tools or redirect to Explorer?
  - **Option A**: Explorer becomes `/` (main UI), archive old tools
  - **Option B**: Keep all 4 tools, Explorer as advanced mode
  - **Option C**: Explorer becomes `/`, keep `/search` as simple mode
- [ ] Update navigation links across all pages
- [ ] Update CLAUDE.md with new UI structure
- [ ] Add Explorer section to SEARCH-MECHANISMS.md
- [ ] Chronicle entry for unified interface
- [ ] Tests: Add Explorer route tests to test_server.py

**Success Criteria**:
- Clear navigation strategy decided
- Documentation updated
- All links working
- Tests passing

---

## Technical Considerations

### Performance

**Concern**: Rendering pipeline + results + inspector could be slow

**Mitigation**:
- Pipeline mode only renders when active (not default)
- Results use virtual scrolling if >100 items (future)
- Inspector lazy-loads Journey tab (only when clicked)
- State updates batched (React-style, but vanilla JS)

### Mobile Experience

**Challenges**:
- Three panes don't fit on mobile
- Touch targets need to be larger
- Inspector needs modal/drawer UX

**Solutions**:
- Vertical stack on mobile: Controls (accordion) → Results → Inspector (drawer)
- Controls collapsed by default (expand to adjust)
- Inspector slides up from bottom when result tapped
- Large touch targets (48px minimum)
- Swipe gestures (future): swipe result left/right to navigate

### Accessibility

**Requirements**:
- Keyboard navigation (arrow keys, Enter, Esc)
- Screen reader support (ARIA labels, roles)
- Focus management (Inspector opens → focus moves there)
- High contrast mode support
- Reduced motion support (prefers-reduced-motion)

### Browser Support

**Target**: Modern evergreen browsers (last 2 versions)
- Chrome, Firefox, Safari, Edge
- iOS Safari 14+
- Android Chrome

**Avoid**: IE11, old mobile browsers

---

## Open Questions

### 1. View Mode Persistence
**Question**: Should view mode (List vs Pipeline) persist per vault, globally, or not at all?

**Options**:
- **A**: Global (same mode for all vaults)
- **B**: Per-vault (some vaults default to Pipeline, others to List)
- **C**: Session only (reset to List on reload)

**Recommendation**: **A** (Global) - simpler state, users likely have one preferred mode

---

### 2. Default View Mode
**Question**: Should Explorer default to List or Pipeline mode?

**Options**:
- **A**: List (simpler, faster, most users just want results)
- **B**: Pipeline (power users love it, shows all stages)
- **C**: Last used (restore from localStorage)

**Recommendation**: **C** (Last used) - gives power users their preference, new users see List first

---

### 3. Inspector Default Tab
**Question**: Which tab should Inspector open to by default?

**Options**:
- **A**: Scores (most relevant for debugging)
- **B**: Metadata (most useful for understanding the doc)
- **C**: Last used tab

**Recommendation**: **A** (Scores) - aligns with Explorer's debugging purpose

---

### 4. Old Tool Strategy
**Question**: What happens to /search, /harness, /pipeline after Explorer launches?

**Options**:
- **A**: Redirect all to /explorer (Explorer becomes the UI)
- **B**: Keep /search as simple mode, redirect /harness and /pipeline to /explorer
- **C**: Keep all 4 tools (choice is good, some users prefer simplicity)

**Recommendation**: **B** - Preserve simple /search for production use, consolidate debugging tools into /explorer

---

## File Structure

```
src/temoa/ui/
├── search.html         # Keep as simple search UI
├── explorer.html       # NEW: Unified interface (this plan)
├── harness.html        # Redirect to /explorer?mode=mixer (Phase 5)
├── pipeline.html       # Redirect to /explorer?mode=pipeline (Phase 5)
└── components/         # NEW: Shared JS modules (future refactor)
    ├── mixer.js
    ├── results.js
    ├── inspector.js
    └── pipeline.js
```

---

## Success Metrics

### Functional
- [ ] Can search with mixer controls
- [ ] Results display in both List and Pipeline modes
- [ ] Inspector shows all score types and metadata
- [ ] Client-side remix works instantly
- [ ] Mobile UX smooth (accordion + drawer)
- [ ] State persists across sessions
- [ ] Export JSON contains all data

### Performance
- [ ] Search response < 2s (same as current)
- [ ] Client remix < 50ms
- [ ] View mode switch < 100ms
- [ ] Inspector opens < 50ms
- [ ] Total page size < 150KB (uncompressed HTML/CSS/JS)

### UX
- [ ] User can explore pipeline without context switching
- [ ] Inspector provides all needed detail for debugging
- [ ] Mixer changes feel instant (no loading spinners)
- [ ] Mobile UX feels native (drawer, accordions, touch-friendly)

---

## Timeline Estimate

**Phase 1**: 4-6 hours (core layout + data flow)
**Phase 2**: 3-4 hours (inspector implementation)
**Phase 3**: 3-4 hours (pipeline mode)
**Phase 4**: 2-3 hours (live remix + polish)
**Phase 5**: 2-3 hours (migration + docs)

**Total**: 14-20 hours (2-3 focused work sessions)

---

## Risks & Mitigations

### Risk: Too Complex for Mobile
**Impact**: Mobile users can't use Explorer effectively
**Likelihood**: Medium
**Mitigation**: Vertical stack + drawer UX, extensive mobile testing

### Risk: Performance Degradation
**Impact**: Explorer slower than current tools
**Likelihood**: Low (pipeline only renders when active)
**Mitigation**: Lazy loading, virtual scrolling (future), profiling

### Risk: Scope Creep
**Impact**: Implementation takes 3x longer than estimated
**Likelihood**: Medium
**Mitigation**: Strict phase boundaries, defer nice-to-haves to future

### Risk: User Prefers Separate Tools
**Impact**: Explorer not adopted, wasted effort
**Likelihood**: Low (user requested this)
**Mitigation**: Keep /search as fallback, user testing after Phase 3

---

## Next Steps

1. **Approval**: User reviews this plan, provides feedback
2. **Kickoff**: Create `explorer.html` stub, start Phase 1
3. **Iteration**: Build phase by phase, user testing after each
4. **Launch**: Phase 5 migration, update docs, deprecate old tools (or not)

---

## Appendix: Wireframes

### Desktop Layout (List Mode)
```
┌────────────────────────────────────────────────────────────────────┐
│ [Query Input]  [Vault ▾] [Profile ▾]                      [Run]    │
├──────────────────┬─────────────────────────────┬──────────────────┤
│ FETCH            │ RESULTS (List)              │ INSPECTOR        │
│                  │                             │                  │
│ Sem ●────────○ BM│ 1. Result Title             │ No result        │
│ [20] Results     │    path/to/file.md          │ selected         │
│ ☑ Cross-encoder  │    sem:85% bm25:12 rrf:0.42 │                  │
│ ☐ Expand query   │    [tags] [matched]         │ Select a result  │
│                  │                             │ to see details   │
│ LIVE             │ 2. Another Result           │                  │
│                  │    another/file.md          │                  │
│ Sem ●────○ BM    │    sem:78% bm25:25 rrf:0.38 │                  │
│ [5.0] Tags       │    [tag1]                   │                  │
│ [1.0] Time       │                             │                  │
│                  │ 3. Third Result             │                  │
│ [Reset Mix]      │    third/file.md            │                  │
│ [Save Profile]   │    sem:72% bm25:8 rrf:0.35  │                  │
│ [Export JSON]    │                             │                  │
│                  │                             │                  │
└──────────────────┴─────────────────────────────┴──────────────────┘
```

### Desktop Layout (Pipeline Mode)
```
┌────────────────────────────────────────────────────────────────────┐
│ [Query Input]  [Vault ▾] [Profile ▾]           [List|Pipeline]     │
├──────────────────┬─────────────────────────────┬──────────────────┤
│ FETCH            │ PIPELINE STAGES             │ INSPECTOR        │
│                  │                             │                  │
│ Sem ●────────○ BM│ ▼ 0. Query Expansion (0ms)  │ Result Title     │
│ [20] Results     │    Original: "test"         │ path/to/file.md  │
│ ☑ Cross-encoder  │    Expanded: "test testing" │                  │
│ ☐ Expand query   │                             │ ── Scores ────   │
│                  │ ▼ 1. Primary Retrieval (45ms│ Semantic: 0.85   │
│ LIVE             │    120 results              │ [████████░]      │
│                  │    1. Result Title ←SELECTED│ BM25: 12.4       │
│ Sem ●────○ BM    │    2. Another Result        │ [████░░░░░]      │
│ [5.0] Tags       │    3. Third Result          │ RRF: 0.42        │
│ [1.0] Time       │    ...                      │ [████████░]      │
│                  │                             │                  │
│ [Reset Mix]      │ ▶ 3. Score Filtering (12ms) │ Tag Boosted: ✓   │
│ [Save Profile]   │    95 results (-25)         │ Time Boost: +8%  │
│ [Export JSON]    │                             │                  │
│                  │ ▶ 6. Cross-Encoder (218ms)  │ ── Metadata ──   │
│                  │    95 results (rank changes)│ Tags: [tag1]     │
│                  │                             │ Type: note       │
└──────────────────┴─────────────────────────────┴──────────────────┘
```

### Mobile Layout (Vertical Stack)
```
┌──────────────────────────┐
│ [Query Input]      [Run] │
│ [Vault ▾] [Profile ▾]    │
├──────────────────────────┤
│ ▶ Controls (tap to open) │  ← Collapsed accordion
├──────────────────────────┤
│ RESULTS                  │
│                          │
│ 1. Result Title          │
│    path/to/file.md       │
│    sem:85% bm25:12       │
│    [tags] [matched]      │
│                          │  ← Tap result → drawer slides up
│ 2. Another Result        │
│    another/file.md       │
│    sem:78% bm25:25       │
│                          │
│ 3. Third Result          │
│    third/file.md         │
│    sem:72% bm25:8        │
│                          │
└──────────────────────────┘
         ▲ Drawer slides up when result tapped
┌──────────────────────────┐
│ INSPECTOR         [×]    │  ← Swipe down to close
│                          │
│ Result Title             │
│ path/to/file.md          │
│                          │
│ [Scores|Metadata|Journey]│
│                          │
│ Semantic: 0.85           │
│ [████████░]              │
│ BM25: 12.4               │
│ [████░░░░░]              │
│                          │
└──────────────────────────┘
```

---

## Conclusion

The Explorer interface consolidates three separate tools into one cohesive experience, enabling users to:

- **Search** with full mixer control (from Harness)
- **Explore** results in list or pipeline view (from Search + Pipeline)
- **Inspect** individual results with full score/metadata detail (new)

All without context switching between pages.

This aligns with the user's request to "explore the whole pipeline, inspect individual results, and play with the things" in a single unified interface.

**Ready for approval and implementation.**
