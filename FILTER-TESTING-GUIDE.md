# Filter Testing Guide - Phase 1

**Branch**: `filters-and-combs`
**Date**: 2026-02-01

---

## Quick Start

1. **Open Temoa**: Navigate to `http://localhost:8080`
2. **Switch to Explorer View**: Click "Explorer" in top-right view toggle
3. **Run a search**: Enter any query (e.g., "python") and click Run
4. **Find the Filters section**: In the Controls pane (left side), between "Fetch" and "Live"

---

## UI Components

### Filters Section Location

```
Controls Pane (left side)
├── Fetch (server round-trip)
│   └── [Hybrid balance, limit, checkboxes]
│
├── Filters ← NEW SECTION HERE
│   ├── Filter syntax input (monospace textarea)
│   ├── Active filter chips (blue pills with ×)
│   ├── Tag match mode toggle (ANY / ALL)
│   └── Help panel (collapsible)
│
└── Live (instant re-mixing)
    └── [Balance sliders, multipliers]
```

---

## Test Scenarios

### Test 1: Single Tag Filter

**Steps**:
1. Search for: `python`
2. In filter input, type: `tag:python`
3. Press any key to trigger filtering

**Expected**:
- Results instantly filter to show only docs with `python` tag
- Blue chip appears: `tag:python` with × button
- Result count updates

**Verify**:
- [ ] Filter chip appears
- [ ] Results contain only python-tagged docs
- [ ] No server round-trip (instant)

---

### Test 2: Multiple Tags (OR mode)

**Steps**:
1. Search for: `programming`
2. In filter input, type: `tag:python,javascript`
3. Ensure ANY toggle is active (blue highlight)

**Expected**:
- Results show docs with EITHER python OR javascript tags
- Two chips appear: `tag:python` and `tag:javascript`
- More results than single tag (OR logic)

**Verify**:
- [ ] Two separate chips appear
- [ ] Results include docs with python OR javascript
- [ ] ANY button is highlighted

---

### Test 3: Multiple Tags (AND mode)

**Steps**:
1. Same search as Test 2: `tag:python,javascript`
2. Click **ALL** toggle button

**Expected**:
- Results instantly filter to show ONLY docs with BOTH tags
- Fewer results than OR mode
- ALL button is highlighted

**Verify**:
- [ ] Results contain ONLY docs with both tags
- [ ] Toggle updates instantly (no server call)
- [ ] ALL button is highlighted

---

### Test 4: Path Filtering

**Steps**:
1. Search for: `gleaning`
2. In filter input, type: `path:L/Gleanings`

**Expected**:
- Results filter to show only files in L/Gleanings directory
- Chip appears: `path:L/Gleanings`
- Case-insensitive matching

**Verify**:
- [ ] Only files with path containing "L/Gleanings" appear
- [ ] Works case-insensitively (try `path:l/gleanings`)

---

### Test 5: File Name Filtering

**Steps**:
1. Search for: `readme`
2. In filter input, type: `file:README`

**Expected**:
- Results filter to show only files with "README" in filename
- Chip appears: `file:README`
- Case-insensitive matching

**Verify**:
- [ ] Only files with "readme" in name appear
- [ ] Works case-insensitively

---

### Test 6: Combined Filters

**Steps**:
1. Search for: `semantic search`
2. In filter input, type: `tag:python path:L/Gleanings file:gleaning`

**Expected**:
- Results match ALL filters (AND logic between filter types)
- Three chips appear
- Very specific results (intersection of all filters)

**Verify**:
- [ ] Three chips appear
- [ ] Results match semantic query AND all filters
- [ ] Empty result set is possible (and OK)

---

### Test 7: Remove Filter Chip

**Steps**:
1. Create filters: `tag:python,obsidian path:L/Gleanings`
2. Click × on `tag:python` chip

**Expected**:
- `tag:python` chip disappears
- Input updates to: `tag:obsidian path:L/Gleanings`
- Results re-filter instantly
- Only obsidian tag remains

**Verify**:
- [ ] Chip removed
- [ ] Input text updated correctly
- [ ] Results re-filtered
- [ ] Remaining filters still active

---

### Test 8: Help Panel Toggle

**Steps**:
1. Click **?** button in top-right of filter input box

**Expected**:
- Help panel slides down/up
- Shows filter syntax examples
- Styled in dark theme

**Verify**:
- [ ] Help panel toggles on/off
- [ ] Syntax examples are visible
- [ ] Examples use monospace font with highlighting

---

### Test 9: State Persistence

**Steps**:
1. Enter filters: `tag:python path:L/Gleanings`
2. Set tag mode to **ALL**
3. Refresh page (F5)

**Expected**:
- Filter input shows: `tag:python path:L/Gleanings`
- Tag mode is still **ALL**
- Chips appear
- If results were fetched, they're re-filtered

**Verify**:
- [ ] Filter text persists
- [ ] Tag mode persists
- [ ] Chips re-appear
- [ ] State saved in localStorage

---

### Test 10: Server-Side Filters (Informational)

**Steps**:
1. In filter input, type: `type:gleaning status:active`

**Expected**:
- Chips appear showing these filters
- These filters don't affect client results (they're server-side)
- When you click **Run** next time, they'll be parsed and sent to server

**Note**: In Phase 1, type/status filters are parsed and shown as chips, but they need server integration in future phases.

**Verify**:
- [ ] Chips appear for type/status
- [ ] No error occurs
- [ ] Parsing works correctly

---

## Edge Cases

### Empty Filter Input

**Steps**:
1. Enter filters, then delete all text

**Expected**:
- All results shown (no filtering)
- Chips disappear
- State saves empty filter

---

### Missing Frontmatter

**Steps**:
1. Filter by: `tag:nonexistent`

**Expected**:
- Results without tags field are excluded (fail-open)
- Empty result set is possible
- No errors

---

### Case Sensitivity

**Steps**:
1. Try: `path:L/gleanings` (lowercase)
2. Try: `path:L/GLEANINGS` (uppercase)

**Expected**:
- Both match `L/Gleanings` directory
- Case-insensitive matching works

---

### Extra Spaces

**Steps**:
1. Type: `tag:python    path:L/Gleanings` (extra spaces)

**Expected**:
- Filters parse correctly
- Chips appear normally
- Extra spaces cleaned up in input

---

## Performance Testing

### 50 Results, 5 Filters

**Steps**:
1. Search returning ~50 results
2. Add 5 filters: `tag:a,b,c path:L file:gleaning`

**Expected**:
- Filter application < 50ms
- Instant UI update
- Smooth performance

---

### Toggle Tag Mode Rapidly

**Steps**:
1. Add filters: `tag:python,obsidian,javascript`
2. Click ANY → ALL → ANY → ALL rapidly

**Expected**:
- UI responds instantly each time
- Results update smoothly
- No lag or errors

---

## Visual Verification

### Filter Section Styling

**Check**:
- [ ] Monospace font in input (SF Mono, Monaco, etc.)
- [ ] Dark theme (#2a2a2a input background)
- [ ] Blue chips (#2a5a8a background)
- [ ] Help button (?) in top-right of input
- [ ] Toggle buttons have active state (blue highlight)
- [ ] Chips have hover effect on × button

---

### Mobile View (Optional)

If testing on mobile:
- [ ] Filter section is accessible
- [ ] Input is usable with virtual keyboard
- [ ] Chips are touch-friendly
- [ ] Toggle buttons work with touch

---

## Browser Console

Open browser console (F12) and check for:
- [ ] No JavaScript errors
- [ ] State logged on init: `Temoa initialized {...}`
- [ ] No warnings about missing elements

---

## Testing Checklist Summary

Core Functionality:
- [ ] Single tag filter works
- [ ] Multiple tags with ANY mode works
- [ ] Multiple tags with ALL mode works
- [ ] Path filtering works
- [ ] File filtering works
- [ ] Combined filters work
- [ ] Remove chip works
- [ ] Help panel toggles
- [ ] State persists on reload

Edge Cases:
- [ ] Empty input works
- [ ] Missing frontmatter handled
- [ ] Case-insensitive matching works
- [ ] Extra spaces handled

Performance:
- [ ] Instant filtering (<100ms)
- [ ] Smooth toggle switching
- [ ] No lag with many filters

Visual:
- [ ] Monospace input font
- [ ] Blue chips
- [ ] Active toggle state
- [ ] Dark theme consistent

---

## Known Limitations (Phase 1)

1. **Property filtering**: Not yet implemented (Phase 2)
   - `[property]:value` syntax will be parsed but not applied

2. **Date filtering**: Not yet implemented (Phase 3)
   - `created:>2025-01-01` will be parsed but not applied

3. **Server-side type/status**: Chips shown but not sent to server
   - These work as query params in `/search` but not wired to filter input yet

4. **Autocomplete**: Not yet implemented (Phase 2)
   - No suggestions while typing

---

## Reporting Issues

If you find bugs, note:
- Filter input text
- Expected behavior
- Actual behavior
- Browser console errors
- Screenshot if visual issue

---

## Next: Phase 2

After Phase 1 testing passes, Phase 2 will add:
- Property filtering: `[project]:temoa`
- `/properties` endpoint for discovery
- Autocomplete suggestions
- Property value chips

---

**Testing Date**: __________
**Tester**: __________
**Browser**: __________
**Test Result**: ☐ Pass ☐ Fail

**Notes**:
