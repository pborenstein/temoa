# Implementation Plan: Obsidian-Style Filtering for Temoa Explorer View

**Created**: 2026-02-01
**Branch**: `filters-and-combs`
**Target**: Add Obsidian-style search filtering to Explorer view with configurable tag logic
**Reference**: [Obsidian Search Syntax](https://help.obsidian.md/plugins/search)

**Note**: We will implement a subset of Obsidian's search operators, not the full syntax.

---

## Overview

Add an Obsidian-style filtering system to Temoa's Explorer view that supports:
- Filter operators: `tag:`, `type:`, `status:`, `path:`, `file:`, `[property:value]`, date ranges
- Configurable AND/OR tag matching logic
- Hybrid filtering: server-side (type, status) + client-side (tags, properties, dates)
- Instant filter feedback with visual filter chips

**User's Core Question**: "Do we filter on fetch or after?"
**Answer**: **Both** - Hybrid approach optimizes for performance (server pre-filters) and UX (client instant filters)

---

## Key Architectural Decision: Hybrid Filter Strategy

### Pre-Fetch Filters (Server-Side)
Run before fetching results to reduce data transfer:
- `type:gleaning` - Already implemented via `filter_by_type()` (server.py:365-448)
- `status:active` - Already implemented via `filter_inactive_gleanings()` (server.py:328-362)
- Result limit - Controls fetch size

### Post-Fetch Filters (Client-Side, Instant)
Filter already-fetched results in browser for instant feedback:
- `tag:python tag:obsidian` - Fast experimentation with AND/OR toggle
- `[property:value]`, e.g., `[project:temoa]` - Custom property matching
- `path:L/Gleanings`, `file:README` - Path/filename string matching
- Date ranges: `created:>2025-01-01`, `modified:<30d`

**Rationale**:
- Server-side: Reduces bandwidth (mobile-friendly), leverages existing caching
- Client-side: Instant experimentation (fits "Knobs and Dials" philosophy), no server changes needed
- No network overhead for tag/property/date filters

---

## Filter Syntax Specification

**Reference**: See [Obsidian Search Syntax](https://help.obsidian.md/plugins/search) for full operator list.

**Implemented in Temoa**:

```
tag:python              → Filter by tag (exact match)
tag:python,obsidian     → Multiple tags (comma-separated, OR by default)
type:gleaning           → Filter by type (server-side pre-fetch)
status:active           → Filter by status (server-side pre-fetch)
path:L/Gleanings        → Path contains string (case-insensitive)
file:README             → Filename contains string (case-insensitive)
[property:value]        → Custom property exact match (Phase 2)
[project:temoa]         → Example: project property filter
created:>2025-01-01     → Date range (ISO format YYYY-MM-DD) (Phase 3)
created:<30d            → Relative date (days ago) (Phase 3)
modified:>7d            → Modified within last 7 days (Phase 3)
```

**Combining filters**: Space-separated, implicit AND between different filter types
```
semantic search tag:python type:gleaning created:>2025-01-01
→ Query: "semantic search" + tag:python + type:gleaning + created after 2025-01-01
```

**Not Implemented** (from Obsidian):
- Boolean operators: `OR`, `AND`, `-` (negation)
- Regex search: `/pattern/`
- Line/section search: `line:`, `section:`
- Block search: `block:`
- Task operators: `task:`, `task-todo:`, `task-done:`

---

## UI Integration (Explorer View Controls Pane)

### Current Controls Pane Structure
```
Controls Pane (280px width)
├── Fetch (server round-trip)
│   ├── Hybrid balance slider (semantic ↔ BM25)
│   ├── Result limit (number input)
│   ├── Cross-encoder checkbox
│   └── Expand query checkbox
│
└── Live (instant re-mixing, client-side)
    ├── Semantic/BM25 balance slider
    ├── Tag multiplier slider
    └── Time weight slider
```

### New Structure (Add Filter Section)
```
Controls Pane (280px width)
├── Fetch (server round-trip)
│   └── [existing controls]
│
├── Filters (NEW - instant, client-side)       ← ADD THIS SECTION
│   ├── Filter syntax input (monospace textarea)
│   ├── Active filter chips (visual feedback)
│   ├── Tag match mode toggle (ANY/ALL)
│   └── Filter help (collapsible)
│
└── Live (instant re-mixing, client-side)
    └── [existing controls]
```

**Visual Design**:
- Monospace input for filter syntax clarity (60px height, auto-expand)
- Blue filter chips below input showing active filters with × remove buttons
- Toggle buttons for ANY/ALL tag matching (radio button style)
- Collapsible help text with filter syntax examples
- Mobile: Accordion-style, collapsed by default

---

## Implementation Phases

### Phase 1: Core Filtering UI (MVP) - ✅ COMPLETE

**Goal**: Basic filter parsing and client-side filtering in Explorer view

**Status**: Implemented 2026-02-01, commit 70479b2

**Completed**:
1. Added "Filters" section to Controls pane in search.html
2. Implemented filter parser: `parseFilterSyntax(input)`
3. Implemented client-side filter application: `applyFilters(results, filters, tagMatchMode)`
4. Implemented filter chips UI: `updateFilterChips(filters)`
5. Wired up to search flow

**Files Modified**: `src/temoa/ui/search.html` (~450 lines)

**Known Issues**:
- ~~Keyboard shortcuts interfere with typing~~ (Fixed: removed all keyboard shortcuts)

---

### Phase 2: Property Discovery - NEXT

**Goal**: Enable custom property filtering with discovery/autocomplete

**Tasks**:
1. Add `/properties` endpoint in server.py
   - Read metadata.json from vault storage
   - Extract all frontmatter properties and their values
   - Return property value distributions for autocomplete
   - Query param: `?property=project` for specific property
   - Cache results for 5 minutes (avoid repeated file I/O)

2. Extend filter parser to handle `[property:value]` syntax
   - Parse custom property filters: `[project:temoa]`, `[status:active]`
   - Add to filters object: `properties: {project: "temoa", ...}`

3. Implement property matching in `applyFilters()`
   - Check result.frontmatter[property] === value
   - Handle missing properties (fail-open)

4. Optional: Basic autocomplete
   - Fetch `/properties` on input focus
   - Show dropdown with property names as user types `[`
   - Show values when user types `[property:`

**Files Modified**:
- `src/temoa/server.py` (~80 lines: new endpoint)
- `src/temoa/ui/search.html` (~100 lines: property parsing, autocomplete)

**Success Criteria**:
- Can filter by any frontmatter property
- `/properties` endpoint returns property distributions
- Autocomplete suggests property names (optional)

---

### Phase 3: Date Filtering - Future

**Goal**: Support date range filtering for created/modified fields

**Tasks**:
1. Extend filter parser for date syntax
2. Implement date parsing utility: `parseDateConstraint(constraint)`
3. Implement date matching in `applyFilters()`
4. Update filter chips to show date ranges

**Files Modified**: `src/temoa/ui/search.html` (~150 lines)

---

### Phase 4: Polish & Documentation - Future

**Goal**: Edge cases, mobile optimization, documentation

**Tasks**:
1. Edge case handling
2. Mobile optimizations
3. Performance validation
4. Documentation updates
5. Testing

---

## Critical Files

### Client-Side (Primary Work)
- **src/temoa/ui/search.html** (lines 1178-1400) - Explorer view HTML structure
- **src/temoa/ui/search.html** (lines 2183-2393) - Filter parsing and application functions

### Server-Side (Phase 2 Only)
- **src/temoa/server.py** (lines 2202-2320) - `/stats/advanced` endpoint (reference for `/properties`)
- **src/temoa/server.py** (lines 365-448) - `filter_by_type()` (pattern for server-side filtering)

---

## Performance Characteristics

### Filter Parsing
- **Regex parsing**: < 5ms for typical input (10 filters)
- **No network overhead**: Pure client-side JavaScript

### Client-Side Filtering
- **50 results, 5 active filters**: < 50ms
- **100 results, 10 active filters**: < 100ms
- **No server round-trip**: Instant feedback

### Server-Side Filtering (Existing)
- **Type filtering**: ~10-20ms (cached frontmatter)
- **Status filtering**: ~10-20ms (cached frontmatter)
- **Total search latency**: 400-600ms (unchanged)

### Property Discovery (Phase 2)
- **First call**: ~200-300ms (read metadata.json)
- **Cached calls**: < 5ms (5 min cache)

**Mobile Impact**: Zero additional network traffic for tag/property/date filters - critical for <2s response time goal

---

## Open Questions for User

1. **Autocomplete in Phase 1 or Phase 2?**
   - Phase 1: Better UX from start, more complex initial implementation
   - Phase 2: Simpler MVP, add autocomplete with `/properties` endpoint
   - **Recommendation**: Phase 2 (simpler start)

2. **Filter persistence across searches?**
   - Clear filters on new search (current plan)
   - Persist filters until explicitly removed
   - **Recommendation**: Clear on new search (cleaner UX)

3. **Server-side tag filtering for large result sets?**
   - Client-only: Works for typical 20-50 results, instant feedback
   - Server endpoint: Better scaling for 100+ results, adds latency
   - **Recommendation**: Start client-only, add server if needed

4. **AND/OR toggle applies to all multi-value filters or just tags?**
   - Just tags (current plan)
   - All multi-value (tags, types, properties)
   - **Recommendation**: Just tags initially (KISS)

---

## Related Documentation

- **Phase 1 Summary**: PHASE1-IMPLEMENTATION-SUMMARY.md
- **Testing Guide**: FILTER-TESTING-GUIDE.md
- **Syntax Reference**: FILTER-SYNTAX-REFERENCE.md
- **Obsidian Reference**: https://help.obsidian.md/plugins/search

---

**Last Updated**: 2026-02-01
**Status**: Phase 1 complete, Phase 2 ready to implement
