# Management Page Implementation Plan

**Created**: 2025-11-24
**Status**: Ready for implementation
**Target**: Phase 3 (Enhanced Features)

---

## Overview

Add a second page to the Temoa web UI for management operations (reindexing, gleaning extraction, health monitoring, and vault statistics).

## Current State

- **Endpoints already exist**: `/reindex`, `/extract`, `/health`, `/stats`
- **Single HTML file**: `src/temoa/ui/search.html` (search UI)
- **Server routing**: `@app.get("/")` serves search.html

## Requirements

1. Reindexing capability (trigger via web)
2. Gleaning extraction (trigger via web)
3. Health and stats display
4. NOT gleaning status management (mark active/inactive) - out of scope

## Design Decisions

1. **Navigation**: Gear icon (⚙︎ U+2699 U+FE0E) in header, always visible
   - Must use variation selector U+FE0E to force text/glyph presentation (not emoji)
   - Example: `⚙︎` (gear + VS15)

2. **URL path**: `/manage`

3. **Reindex confirmation**: Always confirm before running

4. **Stats refresh**: Refresh after actions complete (not auto-refresh timer)

## Proposed Implementation

### 1. Create Management UI (`src/temoa/ui/manage.html`)

**Layout:**
```
+----------------------------------+
| Temoa Management      [← Search] |
+----------------------------------+
| System Health                    |
| - Status: healthy                |
| - Files indexed: 2,942           |
| - Model: all-MiniLM-L6-v2        |
+----------------------------------+
| Vault Statistics                 |
| - Embeddings: 2,942              |
| - Tags: 2,006                    |
| - Directories: 31                |
+----------------------------------+
| Actions                          |
| [Reindex Vault]                  |
| [Extract Gleanings]              |
|   ☑ Incremental (new files only)|
|   ☑ Auto-reindex after          |
+----------------------------------+
```

**Features:**

- Real-time health/stats display (fetch on load)
- Action buttons for reindex/extract
- Progress indicators during operations
- Success/error messages
- Mobile-responsive design matching search.html
- Dark theme consistency

### 2. Add Server Route

**File**: `src/temoa/server.py`

Add new endpoint:
```python
@app.get("/manage", response_class=HTMLResponse)
async def manage():
    """Serve management UI"""
    ui_path = Path(__file__).parent / "ui" / "manage.html"
    # Similar to root() endpoint
```

### 3. Add Navigation

**Update both pages:**

- `search.html`: Add navigation to header structure
  ```html
  <header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
              <h1>Temoa</h1>
              <p class="subtitle">Semantic search for your vault</p>
          </div>
          <a href="/manage" class="nav-link">⚙︎</a>
      </div>
  </header>
  ```
  Note: Use U+2699 U+FE0E (⚙︎) for gear icon with text presentation

- `manage.html`: Add back navigation link in header
  ```html
  <header>
      <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
              <h1>Temoa Management</h1>
              <p class="subtitle">System health, stats, and operations</p>
          </div>
          <a href="/" class="nav-link">← Search</a>
      </div>
  </header>
  ```

### 4. Management Page Components

**Health Status Section:**

- Fetches `/health` endpoint
- Displays: status, model, files_indexed, uptime
- Color-coded status indicator (green=healthy, red=unhealthy)

**Stats Section:**

- Fetches `/stats` endpoint
- Displays: embeddings count, tags, directories
- Collapsible/expandable like search page stats

**Reindex Action:**

- Button: "Reindex Vault"
- Confirmation dialog: "This will rebuild all embeddings. Continue?"
- POST to `/reindex?force=true`
- Shows progress spinner
- Displays result: "Successfully reindexed X files"

**Extract Gleanings Action:**

- Button: "Extract Gleanings"
- Options checkboxes:
  - ☑ Incremental (only new files)
  - ☑ Auto-reindex after extraction
- POST to `/extract?incremental=true&auto_reindex=true`
- Shows progress spinner
- Displays result: "Found X gleanings, created Y new, skipped Z duplicates"

## Files to Modify

1. **New file**: `src/temoa/ui/manage.html` (~400 lines, similar to search.html)
2. **Update**: `src/temoa/server.py` (add `/manage` endpoint, ~10 lines)
3. **Update**: `src/temoa/ui/search.html` (add navigation link, ~10 lines)

## Implementation Strategy

### Phase 1: Basic Structure

1. Create `manage.html` with layout and dark theme
2. Add `/manage` route to server
3. Add navigation links between pages

### Phase 2: Health & Stats Display

1. Implement health status fetch and display
2. Implement stats fetch and display
3. Add auto-refresh mechanism (if chosen)

### Phase 3: Action Buttons

1. Implement reindex button + confirmation
2. Implement extract button + options
3. Add progress indicators
4. Add success/error messaging

### Phase 4: Polish

1. Mobile responsiveness testing
2. Error handling edge cases
3. Loading states
4. Consistent styling with search page

## Technical Notes

- Reuse CSS/styling patterns from `search.html` for consistency
- Use same state management approach (localStorage if needed)
- Follow existing DOM manipulation patterns (safe innerHTML vs createElement)
- Match mobile-first responsive design
- Keep JavaScript vanilla (no frameworks)
- Use `⚙︎` (U+2699 U+FE0E) for gear icon - NOT emoji version

## JavaScript Functionality

**Health/Stats Display:**
```javascript
async function loadHealth() {
    const response = await fetch('/health');
    const data = await response.json();
    displayHealth(data);  // Update DOM with status, model, files_indexed
}

async function loadStats() {
    const response = await fetch('/stats');
    const data = await response.json();
    displayStats(data);  // Update DOM with embeddings, tags, directories
}

// Call on page load
window.addEventListener('load', () => {
    loadHealth();
    loadStats();
});
```

**Reindex Action:**
```javascript
async function reindex() {
    // Show confirmation dialog
    if (!confirm('This will rebuild all embeddings. Continue?')) {
        return;
    }

    // Show progress indicator
    const button = document.getElementById('reindex-btn');
    button.disabled = true;
    button.textContent = 'Reindexing...';

    try {
        const response = await fetch('/reindex?force=true', { method: 'POST' });
        const data = await response.json();

        // Show success message
        showMessage(`Successfully reindexed ${data.files_indexed} files`, 'success');

        // Refresh stats
        await loadHealth();
        await loadStats();
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Reindex Vault';
    }
}
```

**Extract Action:**
```javascript
async function extract() {
    const incremental = document.getElementById('incremental').checked;
    const autoReindex = document.getElementById('auto-reindex').checked;

    const button = document.getElementById('extract-btn');
    button.disabled = true;
    button.textContent = 'Extracting...';

    try {
        const url = `/extract?incremental=${incremental}&auto_reindex=${autoReindex}`;
        const response = await fetch(url, { method: 'POST' });
        const data = await response.json();

        showMessage(
            `Found ${data.total_gleanings} gleanings, ` +
            `created ${data.new_gleanings} new, ` +
            `skipped ${data.duplicates} duplicates`,
            'success'
        );

        // Refresh stats
        await loadHealth();
        await loadStats();
    } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Extract Gleanings';
    }
}
```

## Out of Scope

- Gleaning status management UI (marking active/inactive/hidden)
- User authentication
- Multi-user support
- Advanced scheduling (cron, etc.)

## Summary

This implementation adds a lightweight management interface to Temoa that:

1. Allows triggering reindex and extraction operations from mobile
2. Displays system health and vault statistics
3. Maintains UI consistency with existing search page
4. Uses confirmation dialogs to prevent accidental operations
5. Refreshes stats after operations complete
6. Requires minimal changes to existing code (~500 total lines)

---

**Next Steps**: Review plan, then implement in phases as outlined above.
