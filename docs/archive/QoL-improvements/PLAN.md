# Quality of Life Improvements Plan

**Branch**: `qol-improvements`
**Estimated Duration**: 3-4 days
**Goal**: Bridge web UI / CLI feature gap and improve search result UX

---

## Overview

Phase 3.5 added powerful features (profiles, chunking) but they're CLI-only. The web UI lags behind in both features and information density. This plan brings them into parity while improving the mobile search experience.

---

## Problem Statement

### Feature Gaps (CLI → Web UI)
1. **Search profiles** - 5 optimized modes (repos, recent, deep, keywords, default) exist but not in web UI
2. **Index chunking options** - Chunking parameters (enable, size, overlap, threshold) CLI-only
3. **Model selection** - Can't choose embedding model from web UI
4. **Gleaning management** - Mark active/inactive, check links - CLI-only
5. **Advanced stats** - Limited vault statistics compared to what's available

### UX Issues
1. **Search results waste space** - Score is prominent but content description is buried
2. **Dates are missing** - No creation/modification dates visible in results
3. **Options panel too crowded** - Too many toggles, hard to use on mobile
4. **Management page too basic** - Just reindex + extract, missing capabilities

---

## User Requirements (from Q&A)

### Search Results Display
**Priority**: Content > Score

**User quote**: "More important than the score is 'what is in this note'. The fact that it appears in the results means that it has a high score, so that's secondary information really."

**Required fields** (visible without expanding):
- Title (existing, good)
- Description (currently hidden or truncated)
- Tags (currently visible but small)
- Dates (MISSING):
  - Note creation date (`frontmatter.created`)
  - Note modification date (`frontmatter.modified`)
  - Article publication date (NOT AVAILABLE - future enhancement)

**Secondary fields** (visible on expand):
- Scores (semantic, BM25, RRF, cross-encoder)
- Path/type
- Boost flags (tag_boosted, time_boost)
- Content snippet

### Management Page
**Required additions**:
1. Gleaning maintenance (HIGH PRIORITY)
   - Mark as active/inactive/hidden
   - Check for broken links
   - Update descriptions

2. Model selection for indexing (HIGH PRIORITY)
   - Dropdown: all-mpnet-base-v2, all-MiniLM-L6-v2, etc.
   - Show current model in use

3. Advanced index statistics (HIGH PRIORITY)
   - Chunk counts (if chunking enabled)
   - Average file sizes
   - Tag distribution
   - Index health metrics

4. ~~Archaeology~~ (SKIP - old, untested)

### Search Profiles
**Integration**: Profile dropdown above search box (prominent placement)

**Behavior**:
- Dropdown with 5 options: repos, recent, deep, keywords, default
- Profile sets multiple search parameters automatically
- Advanced users can still toggle individual options in Options panel
- Default to "default" profile on page load

### Index Generation Options
**Integration**: Expand "Reindex Vault" section with collapsible "Advanced Options"

**Options to expose**:
- Model selector dropdown
- Enable chunking checkbox
- Chunk size input (default 2000)
- Chunk overlap input (default 400)
- Chunk threshold input (default 4000)

---

## Implementation Plan

### Phase 1: Search Result Redesign (1 day)

**Goal**: Show content first, scores second

**Files to modify**:
- `src/temoa/ui/search.html` (result card layout)

**Changes**:

#### Result Card Structure (Collapsed State)
```
┌─────────────────────────────────────────┐
│ TITLE                           [expand]│
│ Description text here that can span up  │
│ to three lines before truncating with   │
│ an ellipsis at the end...               │
│ tag1  tag2  tag3                        │
│ Created: 2025-12-25 • Modified: 3d ago  │
│                                         │
│ 🎯 0.82 semantic • 45.2 BM25 • 7d old   │ <- Compact score row
└─────────────────────────────────────────┘
```

#### Result Card Structure (Expanded State)
```
┌──────────────────────────────────────────┐
│ TITLE                         [collapse] │
│ Description text here with...            │
│ tag1  tag2  tag3                         │
│ Created: 2025-12-25 • Modified: 3d ago   │
│                                          │
│ Scores:                                  │
│   Semantic: 0.82                         │
│   BM25: 45.2 (tag boosted ✓)             │
│   RRF: 0.102                             │
│   Cross-encoder: 0.65                    │
│   Time boost: 0.12 (7 days old)          │
│                                          │
│ Type: gleaning                           │
│ Path: Reference/Tech/file.md             │
│ Source: Daily/2025/12-25.md (if gleaning)│
└──────────────────────────────────────────┘
```

**Key improvements**:
1. Description prominent (2 lines, truncate with ellipsis)
2. Dates visible without expanding (relative format: "3d ago", "2w ago")
3. Single compact score row when collapsed (most relevant metrics)
4. Full score breakdown on expand
5. Gleaning-specific fields (source, URL) shown when expanded

**Technical details**:
- Use CSS `line-clamp: 3` for description truncation (~120-150 chars)
- Format dates with relative time (use simple JS: today/yesterday/Nd ago/Nw ago/Nmo ago)
- Show `created` date from frontmatter, `modified` as relative
- Conditional rendering for gleaning-specific fields (`frontmatter.source`, `frontmatter.url`)
- Tag chips limited to 5, show "+N more" on expand
- Profile persistence in localStorage (key: `temoa_search_profile`)

---

### Phase 2: Search Profiles Integration (0.5 days)

**Goal**: Expose 5 search profiles in web UI

**Files to modify**:
- `src/temoa/ui/search.html` (add profile selector)

**Changes**:

#### Profile Selector UI
```html
<!-- Insert above search box -->
<div class="profile-selector">
  <label>Search Mode:</label>
  <select id="profile-select">
    <option value="default" selected>Default (Balanced)</option>
    <option value="repos">Repos (GitHub, tech docs)</option>
    <option value="recent">Recent (Last 90 days)</option>
    <option value="deep">Deep (Long-form content)</option>
    <option value="keywords">Keywords (Exact matching)</option>
  </select>
  <button id="profile-info" title="Learn about search profiles">ⓘ</button>
</div>
```

#### Profile Change Behavior
1. When profile selected, update search parameters:
   - Set hybrid weight
   - Toggle rerank/expand/time-boost
   - Set min score
   - Update URL params: `?profile=repos`

2. Profile info button shows modal:
   - Explain each profile
   - Show what parameters it sets
   - Link to docs

3. Manual override:
   - User can still expand Options and toggle individual settings
   - This overrides the profile (show warning: "Custom settings active")

**API integration**:
- GET `/profiles` - List available profiles with descriptions
- Add `&profile=<name>` to search API call
- Server applies profile settings automatically

---

### Phase 3: Management Page Enhancements (1.5 days)

**Goal**: Add gleaning management, model selection, advanced stats

**Files to modify**:
- `src/temoa/ui/manage.html` (layout + new sections)
- `src/temoa/server.py` (new API endpoints)

#### 3A: Gleaning Management Section

**New section in manage.html**:
```
┌─────────────────────────────────────────┐
│ Gleaning Management                     │
├─────────────────────────────────────────┤
│ Active gleanings: 482                   │
│ Inactive gleanings: 23                  │
│ Hidden gleanings: 0                     │
│                                         │
│ [Check for Broken Links]                │
│ [Update Descriptions from URLs]         │
│ [View Inactive Gleanings]               │
└─────────────────────────────────────────┘
```

**New API endpoints needed**:
- GET `/gleaning/stats?vault=<name>` - Count by status
- POST `/gleaning/check-links?vault=<name>` - Check broken links, return list
- POST `/gleaning/update-descriptions?vault=<name>` - Fetch and update descriptions
- GET `/gleaning/list?vault=<name>&status=inactive` - List by status
- POST `/gleaning/set-status?vault=<name>&id=<id>&status=<status>` - Update status

**UI flow**:
1. Click "Check for Broken Links" → Shows progress bar → Shows results table
2. Results table: URL | Status | Action (Mark Inactive button)
3. Click "View Inactive Gleanings" → Shows filterable list → Can mark as active

#### 3B: Advanced Index Options

**Expand "Reindex Vault" section**:
```
┌─────────────────────────────────────────┐
│ Reindex Vault                           │
│ [Reindex] ▼ Advanced Options            │ <- Collapsible
│                                         │
│ Model: [all-mpnet-base-v2 ▾]            │
│                                         │
│ □ Enable chunking for large files       │
│   Chunk size: [2000] chars              │
│   Overlap: [400] chars                  │
│   Threshold: [4000] chars               │
│                                         │
│ □ Full rebuild (process all files)      │
└─────────────────────────────────────────┘
```

**Changes**:
- Fetch available models: GET `/models`
- Pass parameters to `/reindex`:
  - `?model=<name>`
  - `&enable_chunking=true`
  - `&chunk_size=2000`
  - `&chunk_overlap=400`
  - `&chunk_threshold=4000`

#### 3C: Advanced Statistics Section

**New section**:
```
┌─────────────────────────────────────────┐
│ Advanced Statistics                     │
├─────────────────────────────────────────┤
│ Content Coverage:                       │
│   Files indexed: 12,305                 │
│   Chunks created: 8,755 (chunking on)   │
│   Chunks per file: 4.4x avg             │
│   Avg file size: 3.2 KB                 │
│                                         │
│ Tag Distribution: (top 10)              │
│   python: 234  obsidian: 189            │
│   ai: 156      networking: 134          │
│   ...                                   │
│                                         │
│ Content Types:                          │
│   gleaning: 482  article: 156           │
│   tool: 89       daily: 365             │
│                                         │
│ Index Health:                           │
│   Status: ● Healthy                     │
│   Last indexed: 2025-12-31 10:30        │
│   Stale files: 0                        │
└─────────────────────────────────────────┘
```

**New API endpoint**:
- GET `/stats/advanced?vault=<name>` - Extended statistics

**Backend changes**:
- Add chunking stats to `synthesis/src/stats.py`
- Add type distribution counting
- Add tag frequency analysis (top N tags)
- Add index freshness check (files modified after last index)

---

### Phase 4: Index Options Integration (0.5 days)

**Goal**: Make chunking/model options available in web UI

**Covered in Phase 3B above** (Advanced Index Options section)

---

### Phase 5: Testing & Documentation (0.5 days)

**Testing checklist**:
- [ ] Profile selector updates search params correctly
- [ ] Profile changes reflected in URL params
- [ ] Manual option overrides work with profiles
- [ ] Result cards show all required fields
- [ ] Date formatting works correctly (relative time)
- [ ] Gleaning-specific fields only show for gleanings
- [ ] Expand/collapse works smoothly
- [ ] Model selector populates from API
- [ ] Chunking options pass to reindex endpoint
- [ ] Advanced stats load correctly
- [ ] Gleaning management actions work
- [ ] All features work on mobile (primary target)

**Documentation updates**:
- [ ] Update CLAUDE.md with new web UI features
- [ ] Update README.md with profile descriptions
- [ ] Add screenshots to docs/QoL-improvements/
- [ ] Update SEARCH-MECHANISMS.md with profile info
- [ ] Add comments to search.html explaining layout

---

## API Endpoints to Add

### Profiles
- `GET /profiles` - List available search profiles (EXISTS)

### Models
- `GET /models` - List available embedding models (NEW)

### Gleaning Management
- `GET /gleaning/stats?vault=<name>` - Status counts (NEW)
- `POST /gleaning/check-links?vault=<name>` - Check URLs (NEW)
- `POST /gleaning/update-descriptions?vault=<name>` - Fetch descriptions (NEW)
- `GET /gleaning/list?vault=<name>&status=<status>` - List by status (NEW)
- `POST /gleaning/set-status` - Update gleaning status (NEW)

### Advanced Stats
- `GET /stats/advanced?vault=<name>` - Extended statistics (NEW)

### Reindex (Extend Existing)
- `POST /reindex` - Add params:
  - `?model=<name>`
  - `&enable_chunking=true|false`
  - `&chunk_size=N`
  - `&chunk_overlap=N`
  - `&chunk_threshold=N`

---

## File Modification Summary

### Core Files to Modify
1. **src/temoa/ui/search.html** (~300 line changes)
   - Add profile selector UI
   - Redesign result card layout
   - Add date formatting JS
   - Update expand/collapse logic

2. **src/temoa/ui/manage.html** (~400 line changes)
   - Add gleaning management section
   - Add advanced stats section
   - Expand reindex section with options
   - Add model selector

3. **src/temoa/server.py** (~200 line changes)
   - Add 6 new API endpoints (gleaning, models, stats)
   - Extend /reindex endpoint parameters
   - Add profile parameter passthrough

### New Files to Create
1. **src/temoa/gleaning_manager.py** (NEW)
   - Link checking logic
   - Description fetching from URLs
   - Status management helpers

2. **src/temoa/stats_advanced.py** (NEW)
   - Chunking statistics calculator
   - Tag distribution analysis
   - Type distribution analysis
   - Index health checker

### Files to Leave Alone
- All CLI code (already feature-complete)
- Core search logic (server.py search endpoint)
- Synthesis integration (working well)
- Profile definitions (already exist in search_profiles.py)

---

## Design Decisions

### Progressive Disclosure Strategy
**Principle**: Show content first, technical details on demand

1. **Collapsed state** = User cares about "what is this note?"
   - Title, description, tags, dates = content signals
   - Minimal score info (single line, most relevant metrics)

2. **Expanded state** = User wants details
   - Full score breakdown
   - Technical metadata (path, type, source)
   - All boost flags and metrics

### Date Formatting
**User-friendly relative time**:
- Today → "Today"
- Yesterday → "Yesterday"
- 2-6 days → "3d ago"
- 7-30 days → "2w ago"
- 31-365 days → "3mo ago"
- 365+ days → "2025-12-25" (absolute)

**Modification dates**:
- Always relative ("Modified 3d ago")
- Hover shows absolute timestamp

### Mobile-First Constraints
- Touch targets ≥44px
- No hover-only interactions
- Single-column layout
- Collapsible sections to save vertical space
- Chunky buttons for management actions

---

## Success Criteria

### Feature Parity
- [x] All CLI search features available in web UI
- [x] All CLI index options available in web UI
- [x] Gleaning management available in web UI (subset of CLI)

### UX Improvements
- [x] Search results prioritize content over scores
- [x] Dates visible without expanding
- [x] Profile selection is obvious and easy
- [x] Management page has useful capabilities

### Technical Quality
- [x] No breaking changes to existing API
- [x] Backward compatible (old clients still work)
- [x] Mobile-tested on iOS/Android
- [x] All new endpoints tested
- [x] Documentation updated

---

## Risk Assessment

### Low Risk
- Result card redesign (pure UI, no API changes)
- Profile selector (API exists, just wiring)
- Date formatting (pure client-side JS)

### Medium Risk
- Gleaning management endpoints (new backend logic)
- Advanced stats calculations (performance considerations)
- Model selector (needs validation)

### High Risk
- None identified

### Mitigation Strategies
1. **Gleaning operations**: Add timeout protection, progress indicators
2. **Stats calculations**: Cache results, run asynchronously
3. **Model validation**: Check model exists before indexing
4. **Mobile testing**: Test on actual devices before merge

---

## Future Enhancements (NOT in this plan)

These are good ideas but out of scope for QoL improvements:

1. **Article publication dates**
   - Would need to extract from gleaning URLs (crawl HTML)
   - Or add manual frontmatter field
   - Defer to Phase 4 or later

2. **Tag distribution charts**
   - Nice to have but not essential
   - Text list is sufficient for now

3. **Gleaning bulk actions**
   - "Mark all inactive from domain X"
   - Useful but complex UX
   - Defer until user feedback shows need

4. **Profile customization**
   - Let users create/edit profiles
   - Good for power users
   - Not needed for MVP

5. **Search history improvements**
   - Group by date
   - Delete individual items
   - Export search history
   - Nice to have, not critical

---

## Timeline

```
Day 1 (Morning):   Phase 1 - Result card redesign
Day 1 (Afternoon): Phase 2 - Profile integration
Day 2 (Morning):   Phase 3A - Gleaning management endpoints
Day 2 (Afternoon): Phase 3B - Advanced index options
Day 3 (Morning):   Phase 3C - Advanced statistics
Day 3 (Afternoon): Phase 4 - Final integration
Day 4 (Morning):   Phase 5 - Testing on mobile
Day 4 (Afternoon): Phase 5 - Documentation updates
```

**Total: 3-4 days** (depends on testing/refinement needs)

---

## Design Decisions (Finalized)

### Gleaning Link Checking
**Decision**: Async with progress bar
- Start job in background
- Show progress: "120/482 checked"
- User can navigate away
- Results appear when done or on page refresh
- Implementation: POST `/gleaning/check-links` returns job_id, GET `/gleaning/check-links/<job_id>` polls status

### Model Switching
**Decision**: Show warning + offer reindex
- Changing model shows confirmation dialog
- Message: "Changing embedding model requires vault reindex. This will process all files. Continue?"
- If confirmed, save new model + trigger reindex
- Show progress during reindex

### Description Truncation
**Decision**: 3 lines (~120-150 chars)
- CSS: `display: -webkit-box; -webkit-line-clamp: 3;`
- Good balance for gleanings with curated descriptions
- Click to expand for full text

### Profile Persistence
**Decision**: Remember last profile in localStorage
- Key: `temoa_search_profile`
- Restored on page load (like vault selection)
- URL param overrides: `?profile=repos`
- Manual option changes don't affect saved profile

---

**Status**: ✅ Ready to implement

**Notes for Claude**:
- Don't modify CLI code (it's the reference implementation)
- Keep backward compatibility (old API clients must work)
- Test on mobile first (it's the primary use case)
- Follow existing UI patterns (dark theme, compact design)
- Document all new endpoints in docstrings
