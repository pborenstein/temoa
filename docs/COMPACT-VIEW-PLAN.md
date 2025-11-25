# Compact Collapsible Results View Implementation Plan

**Created**: 2025-11-24
**Status**: 🔵 IN PROGRESS
**Target**: Phase 2.5 UI Enhancement

---

## Overview

Implement collapsible result cards with state management improvements, addressing UI-REVIEW.md recommendations while adding the compact view feature.

## Goals

1. **Compact default view**: Results collapse to single line + tags by default
2. **Expandable on demand**: Click to expand, multiple can be expanded
3. **State management**: Fix scattered state issues (UI-REVIEW.md Priority #2)
4. **DOM safety**: Replace innerHTML with createElement (UI-REVIEW.md Priority #3)
5. **Error handling**: Add error boundaries (UI-REVIEW.md Priority #4)
6. **Future-proof**: Don't paint ourselves into a corner

---

## Current State Analysis

**Existing patterns we can leverage:**
- Stats panel uses collapsible pattern with localStorage persistence (lines 294-346, 766-770)
- Advanced options uses similar pattern (lines 176-226, 757-764)
- Results currently rendered with innerHTML (lines 891-967) - **needs refactoring**

**Current result card structure:**
- Title + badges (project, type, score)
- Path + created date
- Description (if present)
- Tags (if present)

**Collapsed view will show:**
- Title + badges (top line)
- Tags (optional second line)

**Expanded view shows:**
- Everything (current display)

---

## Implementation Phases

### ✅ Phase 0: Planning & Documentation
- [x] Create this plan document
- [x] Analyze current code structure
- [x] Get user approval

### ✅ Phase 1: State Management Foundation

**Status**: COMPLETE (2025-11-24)

**Tasks**:
- [x] Create central state object
- [x] Implement versioned localStorage (avoid UI-REVIEW.md Section 2.5 issue)
- [x] Add loadState/saveState functions
- [x] Wire up state updates
- [x] Add race condition protection
- [x] Update existing collapsible sections to use state

**Details**:

```javascript
const state = {
  query: '',
  results: [],
  filters: {
    minScore: 0.3,
    limit: 20,
    hybrid: false,
    includeTypes: [],
    excludeTypes: ['daily']
  },
  ui: {
    expandedResults: new Set(),  // Track which results are expanded
    statsExpanded: false,
    advancedExpanded: false,
    showJson: false
  },
  currentRequestId: 0  // Prevent race conditions
}

const STORAGE_VERSION = 1
const STORAGE_KEY = `temoa_v${STORAGE_VERSION}_ui_state`
```

**Files affected**:
- `src/temoa/ui/search.html` (JavaScript section)

**Estimated time**: 2-3 hours

---

### ✅ Phase 2: Safe DOM Manipulation

**Status**: COMPLETE (2025-11-24)

**Tasks**:
- [x] Create component factory functions
  - [x] `createResultCard(result, expanded)`
  - [x] `createResultHeader(result)`
  - [x] `createResultDetails(result)`
  - [x] `createBadge(type, content)`
  - [x] `createTag(tag)`
  - [x] `createErrorCard()` for fallback
- [x] Replace innerHTML in `displayResults()`
- [x] Add event delegation for clicks
- [x] Test all render paths

**Current problem (UI-REVIEW.md Section 2.2)**:
```javascript
// UNSAFE: String concatenation with innerHTML
resultsDiv.innerHTML = `<div class="result-row">...</div>`
```

**New pattern**:
```javascript
// SAFE: createElement with textContent
function createResultCard(result, expanded) {
  const card = document.createElement('div')
  card.className = 'result-row'
  card.dataset.resultId = result.relative_path

  const header = createResultHeader(result)
  card.appendChild(header)

  if (expanded) {
    const details = createResultDetails(result)
    card.appendChild(details)
  }

  return card
}
```

**Event delegation**:
```javascript
resultsDiv.addEventListener('click', (e) => {
  const card = e.target.closest('.result-row')
  if (!card) return

  const resultId = card.dataset.resultId
  toggleResultExpanded(resultId)
})
```

**Files affected**:
- `src/temoa/ui/search.html` (JavaScript section)

**Estimated time**: 3-4 hours

---

### ✅ Phase 3: Collapsible Results Feature

**Status**: COMPLETE (2025-11-24)

**Tasks**:
- [x] Add CSS for collapsed/expanded states
- [x] Implement `toggleResultExpanded(resultId)`
- [x] Add "Collapse All" and "Expand All" buttons
- [x] Default all results to collapsed
- [x] Test expand/collapse behavior
- [x] Add arrow indicators (▶/▼)
- [x] Event delegation for clicks

**CSS changes**:

```css
.result-row {
  cursor: pointer;
  padding: 12px 20px;  /* Reduced padding when collapsed */
}

.result-row.expanded {
  padding: 20px;  /* Full padding when expanded */
}

.result-header::before {
  content: '▶';
  font-size: 12px;
  color: #888;
  margin-right: 8px;
  transition: transform 0.2s;
}

.result-row.expanded .result-header::before {
  transform: rotate(90deg);
}

.result-details {
  display: none;
  margin-top: 12px;
}

.result-row.expanded .result-details {
  display: block;
}

/* Compact collapsed state */
.result-row:not(.expanded) .result-header {
  margin-bottom: 0;
}
```

**Toggle logic**:

```javascript
function toggleResultExpanded(resultId) {
  if (state.ui.expandedResults.has(resultId)) {
    state.ui.expandedResults.delete(resultId)
  } else {
    state.ui.expandedResults.add(resultId)
  }

  updateState({ ui: state.ui })

  // Update just this card's DOM
  const card = document.querySelector(`[data-result-id="${CSS.escape(resultId)}"]`)
  card.classList.toggle('expanded')
}
```

**Collapse all button**:

```html
<div class="results-controls">
  <button class="collapse-all-btn" onclick="collapseAllResults()">
    Collapse All
  </button>
  <div id="results-header" class="results-header"></div>
</div>
```

**Files affected**:
- `src/temoa/ui/search.html` (CSS and JavaScript sections)

**Estimated time**: 2-3 hours

---

### ✅ Phase 4: Error Boundaries

**Status**: COMPLETE (2025-11-24)

**Tasks**:
- [x] Create `safeRender(renderFn, fallback)` wrapper
- [x] Apply to all component factory functions
- [x] Add error card fallback
- [x] Test error handling

**Implementation**:

```javascript
function safeRender(renderFn, fallback) {
  try {
    return renderFn()
  } catch (err) {
    console.error('Render error:', err)
    showError('Something went wrong. Please refresh.')
    return fallback || createErrorCard()
  }
}

function createErrorCard() {
  const card = document.createElement('div')
  card.className = 'result-row error'
  card.textContent = 'Failed to render result'
  return card
}

// Usage
function displayResults(data) {
  resultsDiv.replaceChildren(
    ...results.map(result =>
      safeRender(
        () => createResultCard(result, state.ui.expandedResults.has(result.relative_path)),
        createErrorCard()
      )
    )
  )
}
```

**Files affected**:
- `src/temoa/ui/search.html` (JavaScript section)

**Estimated time**: 1 hour

---

### ✅ Phase 5: Polish & Additional Improvements

**Status**: COMPLETE (2025-11-24)

**Tasks**:
- [x] Prevent race conditions (UI-REVIEW.md Section 2.1) - Done in Phase 1
- [x] Add keyboard shortcuts (c = collapse all, e = expand all)
- [ ] Test on mobile device (ready for next session)
- [ ] Update CHRONICLES.md with entry (ready for next session)

**Debounce fix**:

```javascript
function debounce(func, delay) {
  let timer

  const debounced = function(...args) {
    clearTimeout(timer)
    timer = setTimeout(() => func.apply(this, args), delay)
  }

  debounced.cancel = () => clearTimeout(timer)
  return debounced
}

const debouncedSearch = debounce(search, 300)
queryInput.addEventListener('input', debouncedSearch)
```

**Race condition prevention**:

```javascript
async function search() {
  const requestId = ++state.currentRequestId

  // ... fetch ...

  const data = await response.json()

  // Ignore if newer request already started
  if (requestId !== state.currentRequestId) {
    console.log('Ignoring stale response')
    return
  }

  displayResults(data)
}
```

**Keyboard shortcuts**:

```javascript
document.addEventListener('keydown', (e) => {
  if (e.target.matches('input, textarea')) return

  if (e.key === 'c') {
    e.preventDefault()
    collapseAllResults()
  }

  if (e.key === 'e') {
    e.preventDefault()
    expandAllResults()
  }
})
```

**Files affected**:
- `src/temoa/ui/search.html` (JavaScript section)
- `docs/CHRONICLES.md` (new entry)

**Estimated time**: 1-2 hours

---

## Progress Tracking

### Session 1 (2025-11-24)

**Completed**:
- [x] Created plan document (`docs/COMPACT-VIEW-PLAN.md`)
- [x] Analyzed current code structure
- [x] **Phase 1: State Management Foundation**
  - [x] Central state object with filters, UI state, request tracking
  - [x] Versioned localStorage (`temoa_v1_ui_state`)
  - [x] loadState/saveState/updateState functions
  - [x] Race condition protection with requestId
  - [x] Updated existing collapsible sections (stats, advanced options)
  - [x] State restoration on page load
- [x] **Phase 2: Safe DOM Manipulation**
  - [x] Created 7 component factory functions (createElement-based)
  - [x] Replaced innerHTML with safe DOM APIs (XSS protection)
  - [x] Event delegation for result card clicks
  - [x] All rendering now uses textContent (auto-escaping)
- [x] **Phase 3: Collapsible Results**
  - [x] CSS for collapsed/expanded states
  - [x] Arrow indicators (▶ collapsed, ▼ expanded)
  - [x] toggleResultExpanded/collapseAllResults/expandAllResults functions
  - [x] Collapse All and Expand All buttons
  - [x] Results default to collapsed (single line view)
  - [x] State persists in localStorage
- [x] **Phase 4: Error Boundaries**
  - [x] safeRender wrapper function
  - [x] Applied to all result card creation
  - [x] Graceful error handling with fallback cards
- [x] **Phase 5: Polish**
  - [x] Keyboard shortcuts (c = collapse all, e = expand all)
  - [x] Race conditions prevented (Phase 1)

**Remaining for Next Session**:
- [ ] Test on actual mobile device (Phase 2.5 validation)
- [ ] Update CHRONICLES.md with implementation entry
- [ ] Commit changes with detailed message
- [ ] User testing and feedback

**Status**: Implementation 95% complete, ready for testing

---

## Success Criteria

- [ ] All results default to collapsed (single line + tags)
- [ ] Click any result to expand/collapse
- [ ] Multiple results can be expanded simultaneously
- [ ] "Collapse All" button works
- [ ] Expanded state persists in localStorage (versioned)
- [ ] No innerHTML usage (XSS safe)
- [ ] Race conditions prevented
- [ ] Renders work without crashes (error boundaries)
- [ ] Mobile-friendly (tested on actual device)
- [ ] No performance regression (search still fast)

---

## Files to Modify

1. **src/temoa/ui/search.html** (primary file)
   - CSS section: Add collapsed/expanded styles
   - HTML section: Add collapse all button
   - JavaScript section: All logic changes

2. **docs/CHRONICLES.md** (documentation)
   - Add new entry for compact view implementation

3. **docs/IMPLEMENTATION.md** (status update)
   - Update Phase 2.5 status when complete

---

## Dependencies & Constraints

**Must maintain**:
- Zero external dependencies (vanilla JS only)
- Mobile-first approach
- Dark mode aesthetic
- Fast performance (~400ms search time)

**Cannot break**:
- Existing collapsible patterns (stats, advanced options)
- Search functionality
- Type filtering
- obsidian:// URI links

**Must address from UI-REVIEW.md**:
- ✅ State management (Section 2.1)
- ✅ DOM manipulation safety (Section 2.2)
- ✅ Error boundaries (Section 2.4)
- ✅ localStorage versioning (Section 2.5)
- ✅ Debounce issues (Section 2.6)

---

## Future Enhancements (Not in Scope)

These are mentioned in UI-REVIEW.md but not part of this implementation:

- PWA support (manifest + service worker)
- Component architecture (Web Components)
- Search history
- Keyboard shortcuts panel (beyond collapse/expand)
- Light mode toggle
- ARIA labels for screen readers

These can be added in later phases without conflicting with this work.

---

## Notes & Decisions

**Why createElement over template literals?**
- XSS safety (textContent auto-escapes)
- Performance (no HTML parsing)
- Maintainability (easier to debug)
- Future-proof (can add Web Components later)

**Why Set for expandedResults?**
- Fast lookups (O(1) instead of O(n))
- Native add/delete/has methods
- Easy to serialize to array for localStorage

**Why default collapsed?**
- User request: "default = everything collapsed"
- Reduces visual clutter (mobile optimization)
- Matches mental model of "scan then dig"
- Can still expand multiple at once when needed

**Why persist expanded state?**
- User expectation: state survives refresh
- Matches existing pattern (stats, advanced options)
- Low cost (small Set stored in localStorage)

---

**Plan Created**: 2025-11-24
**Last Updated**: 2025-11-24
**Next Review**: After Phase 1 completion
