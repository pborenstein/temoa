# UI Cleanup Plan

**Created**: 2025-11-28
**Branch**: `ui-cleanup`
**Goal**: Reduce visual clutter, optimize vertical space, improve hierarchy

---

## Current Problems (from screenshots analysis)

### 1. **Vertical Space Waste**
- Header with subtitle takes 3 lines
- Gear icon floats alone on the right (not aligned with header)
- Vault selector is too prominent (large dropdown + info badges)
- Large search button (14px padding, full width)
- Empty stats section showing "-" placeholders when no results

### 2. **Visual Hierarchy Issues**
- Vault selector appears before search box (but search is primary action)
- Search button is enormous compared to importance
- Gear icon isolated instead of integrated with header

### 3. **Size Problems**
- Search button: `padding: 14px`, `font-size: 16px`, full width = TOO BIG
- Vault selector: `padding: 10px 12px`, full width = too prominent
- Header: 28px h1 + 8px margin + subtitle = excessive vertical space

---

## Proposed Changes

### **Change 1: Compact Header with Inline Gear Icon**

**Current** (3 lines):
```
Temoa                                    ⚙︎
Semantic search for your vault
```

**Proposed** (1 line):
```
Temoa  ⚙︎       Semantic search for your vault
```

**Implementation**:
```css
header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px; /* reduced from 24px */
}

h1 {
    font-size: 24px; /* reduced from 28px */
    margin: 0;
}

.subtitle {
    font-size: 13px; /* reduced from 14px */
    color: #888888;
}

.nav-link {
    font-size: 16px; /* reduced from 18px */
    padding: 4px 8px; /* reduced from 8px 12px */
}
```

**HTML**:
```html
<header>
    <h1>Temoa</h1>
    <a href="/manage" class="nav-link">⚙︎</a>
    <p class="subtitle">Semantic search for your vault</p>
</header>
```

**Space saved**: ~20px vertical

---

### **Change 2: Compact Vault Selector (Move Below Search)**

**Current position**: Before search box (prominent)
**Proposed position**: After search box, before Options (de-emphasized)

**Current size**:
- `padding: 10px 12px`
- Full width dropdown
- Info badges below

**Proposed size**:
- `padding: 6px 10px` (smaller)
- Compact inline layout: `Vault: [dropdown ▼] (default, 3083 files)`
- Info badges inline with dropdown

**Implementation**:
```css
.vault-selector {
    margin-bottom: 12px; /* reduced from 16px */
    font-size: 13px; /* NEW: smaller text */
}

.vault-selector-label {
    display: inline-block;
    color: #888888;
    font-size: 12px;
    margin-right: 8px;
}

.vault-select {
    display: inline-block;
    width: auto; /* NOT full width */
    min-width: 150px;
    padding: 6px 10px; /* reduced from 10px 12px */
    font-size: 13px; /* reduced from 14px */
}

.vault-info {
    display: inline-block; /* inline with dropdown */
    margin-left: 8px;
}
```

**HTML**:
```html
<div class="vault-selector">
    <label class="vault-selector-label">Vault:</label>
    <select id="vault-select" class="vault-select" onchange="onVaultChange()">
        <option value="">Loading...</option>
    </select>
    <span id="vault-info" class="vault-info"></span>
</div>
```

**Space saved**: ~30px vertical + cleaner visual hierarchy

---

### **Change 3: Compact Search Button (Small Icon Style)**

**Current**:
- Full width button
- `padding: 14px`
- `font-size: 16px`
- Text: "Search"
- Huge vertical space (24px margin-bottom)

**Proposed Option A - Inline Small Button**:
```
┌────────────────────────────────────────┐
│ Search your vault...            [→]   │
└────────────────────────────────────────┘
```

**Proposed Option B - Below Input, Compact**:
```
┌────────────────────────────────────────┐
│ Search your vault...                   │
└────────────────────────────────────────┘
         [Search →]  (small button)
```

**Recommendation**: **Option A** (inline) - saves most space

**Implementation (Option A)**:
```css
.search-box {
    position: relative;
    margin-bottom: 12px; /* reduced from 16px */
}

#query {
    width: 100%;
    padding-right: 60px; /* space for button */
}

.search-btn {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    width: auto; /* NOT full width */
    padding: 8px 14px; /* compact */
    font-size: 14px; /* smaller */
    border-radius: 6px;
    margin: 0; /* no margin */
}
```

**HTML**:
```html
<div class="search-box">
    <input type="text" id="query" placeholder="Search your vault...">
    <button class="search-btn" onclick="search()">→</button>
</div>
```

**Alternative button text**:
- `→` (arrow, minimal)
- `Go` (short text)
- `🔍` (search icon - but user said no emojis)
- `⏎` (return symbol)

**Recommendation**: `→` (clean, no emoji)

**Space saved**: ~40px vertical + visual prominence reduced

---

### **Change 4: Hide Empty Stats Section**

**Current**: Stats section always visible, shows "-" when no results

**Proposed**: Only show stats section after search executes

**Implementation**:
Already exists! Just verify it's working:
```javascript
// In search() function, after results:
statsHeader.style.display = 'flex'; // Show when results exist
```

**Also hide on clear/error**:
```javascript
function clearResults() {
    // ... existing code ...
    document.getElementById('stats-header').style.display = 'none';
    document.getElementById('stats-details').style.display = 'none';
}
```

---

### **Change 5: Reorder Page Elements**

**Current Order**:
1. Header (Temoa + subtitle + gear)
2. Vault selector
3. Search box
4. Options (collapsible)
5. Search button (huge)
6. Results / Stats

**Proposed Order**:
1. Header (Temoa + gear + subtitle - all inline)
2. Search box + inline search button
3. Vault selector (compact, below search)
4. Options (collapsible, unchanged)
5. Results / Stats (only when populated)

**Hierarchy**:
- **Primary**: Search input + button (most prominent)
- **Secondary**: Vault selector (convenient but not primary)
- **Tertiary**: Options (collapsed by default)
- **Conditional**: Stats (only with results)

---

## Summary of Changes

| Element | Current | Proposed | Space Saved |
|---------|---------|----------|-------------|
| Header | 3 lines (h1 + subtitle + icon) | 1 line (inline) | ~20px |
| Vault selector | Large dropdown + badges below | Compact inline dropdown | ~30px |
| Search button | Full width, 14px padding | Inline small button | ~40px |
| Stats (empty) | Shown with "-" placeholders | Hidden until results | ~60px |
| **Total vertical space saved** | | | **~150px** |

**Mobile Impact**: Search button visible even with keyboard up ✅

---

## Responsive Behavior

### Desktop (>700px):
- Header: Temoa [gear] subtitle (all inline)
- Search: Input with inline button
- Vault: Compact inline selector

### Mobile (<700px):
- Header: May need to stack if too cramped
- Search: Inline button stays (critical for keyboard-up scenario)
- Vault: Inline selector wraps if needed

**CSS**:
```css
@media (max-width: 500px) {
    header {
        flex-wrap: wrap; /* Allow wrapping if needed */
    }

    .subtitle {
        flex-basis: 100%; /* Force to new line on narrow screens */
        margin-top: 4px;
    }
}
```

---

## Implementation Steps

### Step 1: Header Cleanup
- [ ] Make header flex with inline items
- [ ] Move gear icon between h1 and subtitle
- [ ] Reduce h1 size (28px → 24px)
- [ ] Reduce margins (24px → 16px)

### Step 2: Search Box + Button
- [ ] Add inline search button inside search box
- [ ] Position button absolutely on right side
- [ ] Add padding-right to input for button space
- [ ] Change button text to "→"
- [ ] Reduce button size (14px → 8px padding)

### Step 3: Vault Selector Reposition
- [ ] Move vault selector HTML after search box
- [ ] Make dropdown inline (width: auto)
- [ ] Add label "Vault:" before dropdown
- [ ] Make badges inline with dropdown
- [ ] Reduce padding and font size

### Step 4: Stats Visibility
- [ ] Verify stats hidden on page load
- [ ] Verify stats shown only after search
- [ ] Hide stats on clear/error

### Step 5: Testing
- [ ] Test on mobile (with keyboard up)
- [ ] Test vault switching
- [ ] Test search with inline button
- [ ] Verify visual hierarchy
- [ ] Measure vertical space saved

---

## Mockup (Text-Based)

### Before:
```
┌─────────────────────────────────────────┐
│ Temoa                               ⚙︎  │
│ Semantic search for your vault          │
│                                          │
│ ┌──────────────────────────────────┐    │
│ │ amoxtli                          ▼│    │
│ └──────────────────────────────────┘    │
│ [default] [3083 files indexed]          │
│                                          │
│ ┌──────────────────────────────────┐    │
│ │ Search your vault...             │    │
│ └──────────────────────────────────┘    │
│                                          │
│ ▶ Options                                │
│                                          │
│ ┌──────────────────────────────────┐    │
│ │         Search                   │    │
│ └──────────────────────────────────┘    │
│                                          │
│ Model: -                                 │
│ Mode: -                                  │
│ Showing: -                               │
└─────────────────────────────────────────┘
```

### After:
```
┌─────────────────────────────────────────┐
│ Temoa ⚙︎  Semantic search for your vault │
│                                          │
│ ┌──────────────────────────────────┬──┐ │
│ │ Search your vault...             │→ │ │
│ └──────────────────────────────────┴──┘ │
│ Vault: [amoxtli ▼] default, 3083 files  │
│                                          │
│ ▶ Options                                │
│                                          │
│ (results appear here when searched)      │
└─────────────────────────────────────────┘
```

**Space saved**: ~150px vertical
**Visual hierarchy**: Search is clearly primary action ✅

---

## Files to Modify

1. **`src/temoa/ui/search.html`**
   - CSS: header, vault-selector, search-box, search-btn
   - HTML: Reorder elements, inline button
   - JS: Verify stats hiding logic

2. **`src/temoa/ui/manage.html`** (apply similar changes)
   - Header inline
   - Vault selector compact
   - Consistent styling

---

## Testing Checklist

- [ ] Header is single line on desktop
- [ ] Header wraps gracefully on mobile (<500px)
- [ ] Gear icon clickable and visible
- [ ] Search button visible with keyboard up
- [ ] Search button triggers search on click
- [ ] Enter key still triggers search
- [ ] Vault selector works (switching vaults)
- [ ] Vault badges display correctly
- [ ] Options collapse/expand works
- [ ] Stats hidden on load
- [ ] Stats shown after search
- [ ] Stats hidden on clear
- [ ] Visual hierarchy clear (search primary)
- [ ] No layout shifts during interactions

---

**Status**: Ready to implement
**Estimated time**: 2-3 hours
**Risk**: Low (mostly CSS changes)
**Rollback**: Easy (git revert)
