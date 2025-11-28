# Phase 3: Enhanced Features - Chronicles

> **Timeline**: 2025-11-26 onwards
> **Status**: In Progress
> **Goal**: Fix technical debt, improve search quality, polish UX

---

## Entry 20: Multi-Vault Support - Preventing Data Loss (2025-11-26)

**Problem**: The `--vault` flag was broken and dangerous.

**What was broken**:
```bash
# This command was SUPPOSED to index vault2:
temoa index --vault ~/vaults/vault2

# But ACTUALLY stored the index in vault1's .temoa/:
# vault1/.temoa/index.json  ← OVERWRITTEN with vault2 data!
```

**Root cause** (in `src/temoa/cli.py`):
```python
# CLI accepted --vault override:
vault_path = Path(vault) if vault else config.vault_path  ✅

# But always used config's storage:
storage_dir = config.storage_dir  ❌ ALWAYS vault1/.temoa/!

# Created client with mismatched paths:
client = SynthesisClient(
    vault_path=vault2,        # Index vault2's files
    storage_dir=vault1/.temoa  # But store in vault1's directory!
)
```

**Impact**:
- **Data loss**: Indexing vault2 overwrote vault1's embeddings
- **Corruption**: File tracking mixed up between vaults
- **Incremental reindex broken**: Tracked wrong files
- **Silent failure**: No warning, user unaware of problem

### The Fix: Vault-Aware Storage Derivation

**Core strategy**: Storage directory must follow vault path.

**New module**: `src/temoa/storage.py` (195 lines)

**Key functions**:

1. **`derive_storage_dir(vault_path, config_vault_path, config_storage_dir)`**
   ```python
   if vault_path == config_vault_path:
       return config_storage_dir  # Honor user's config
   else:
       return vault_path / ".temoa"  # Auto-derive for other vaults
   ```

2. **`validate_storage_safe(storage_dir, vault_path, operation, force=False)`**
   ```python
   # Read existing index.json
   if index_file.exists():
       stored_vault = index_data["vault_path"]
       if stored_vault != vault_path and not force:
           raise ConfigError(f"""
Storage directory mismatch detected!

Operation: {operation}
Target vault: {vault_path}
Existing index vault: {stored_vault}
Storage dir: {storage_dir}

This would overwrite the index for a different vault.

Solutions:
  1. Use correct vault: --vault {stored_vault}
  2. Delete old index: rm -rf {storage_dir}
  3. Force overwrite: {operation} --vault {vault_path} --force
           """)
   ```

3. **Auto-migration for old indexes**:
   ```python
   if "vault_path" not in index_data:
       # Old index without metadata - add it
       index_data["vault_path"] = str(vault_path.resolve())
       index_data["vault_name"] = vault_path.name
       index_data["migrated_at"] = datetime.now().isoformat()
       # Write back
       index_file.write_text(json.dumps(index_data, indent=2))
   ```

### CLI Updates (All 5 Commands)

**Pattern applied to**: `index`, `reindex`, `search`, `archaeology`, `stats`

```python
# Before (BROKEN):
def command(vault):
    config = Config()
    vault_path = Path(vault) if vault else config.vault_path
    client = SynthesisClient(
        vault_path=vault_path,
        storage_dir=config.storage_dir  # ❌ WRONG
    )

# After (FIXED):
def command(vault, force=False):  # Added --force flag for index/reindex
    from .storage import derive_storage_dir, validate_storage_safe

    config = Config()

    # Derive vault and storage together
    if vault:
        vault_path = Path(vault)
        storage_dir = derive_storage_dir(
            vault_path, config.vault_path, config.storage_dir
        )
    else:
        vault_path = config.vault_path
        storage_dir = config.storage_dir

    # Validate before write operations
    if operation_is_write:  # index, reindex
        validate_storage_safe(storage_dir, vault_path, "command", force)

    client = SynthesisClient(
        vault_path=vault_path,
        storage_dir=storage_dir  # ✅ CORRECT
    )
```

**New flags**:
- `--force` added to `index` and `reindex` for override (with warning)
- `--vault` added to `search`, `archaeology`, `stats` (read-only ops)

### Vault Metadata in Index

**Added to `index.json`** (in `src/temoa/synthesis.py:950`):
```python
model_info = {
    "model_name": self.pipeline.engine.model_name,
    "embedding_dim": embeddings.shape[1],
    "vault_path": str(self.vault_path.resolve()),  # ← NEW
    "vault_name": self.vault_path.name,            # ← NEW
    "indexed_at": datetime.now().isoformat()       # ← NEW
}
```

**Purpose**:
- **Validation**: Detect vault mismatches before operations
- **Logging**: Better error messages with vault names
- **Future**: Multi-vault search, vault switching

### Testing

**Unit tests** (`tests/test_storage.py` - 13 tests, all passing):
- ✅ Storage derivation for config vault vs other vaults
- ✅ Vault mismatch detection raises ConfigError
- ✅ Force flag bypasses validation
- ✅ Auto-migration of old indexes
- ✅ Corrupted index doesn't crash validation
- ✅ Metadata retrieval functions

**Integration tests** (`tests/test_multi_vault_integration.py`):
- Marked as requiring Synthesis (manual testing)
- Provides test structure for future CI/CD

**Manual testing** (2025-11-26):
```bash
# Test 1: Config vault unchanged
$ temoa stats
Vault path: /Users/philip/Obsidian/amoxtli
Storage: /Users/philip/Obsidian/amoxtli/.temoa
Files indexed: 3067  ✅ Still works

# Test 2: Other vault derives storage
$ temoa stats --vault /tmp/temoa-test-vault-2
Vault path: /tmp/temoa-test-vault-2
Storage: /tmp/temoa-test-vault-2/.temoa  ✅ Auto-derived!

# Test 3: Each vault independent
$ ls /Users/philip/Obsidian/amoxtli/.temoa/
index.json  all-mpnet-base-v2/  ✅ Config vault's index

$ ls /tmp/temoa-test-vault-2/.temoa/
all-mpnet-base-v2/  ✅ Separate directory
```

### User Experience

**For single-vault users** (99% of users):
- ✅ No changes needed
- ✅ Works exactly as before
- ✅ Auto-migration adds metadata (one-time, automatic)

**For multi-vault users**:
- ✅ Each vault gets independent `.temoa/` directory
- ✅ Can switch vaults with `--vault` flag
- ✅ Validation prevents accidental overwrites
- ✅ Clear error messages with solutions

**Error messages** (example):
```
Storage directory mismatch detected!

Operation: index
Target vault: /Users/philip/vaults/vault2
Existing index vault: /Users/philip/vaults/vault1
Storage dir: /Users/philip/vaults/vault1/.temoa

This would overwrite the index for a different vault, causing data loss.

Solutions:
  1. Use correct vault path:
     temoa index --vault /Users/philip/vaults/vault1

  2. Delete existing index (if you're sure):
     rm -rf /Users/philip/vaults/vault1/.temoa

  3. Force overwrite (DANGER - will lose existing index):
     temoa index --vault /Users/philip/vaults/vault2 --force
```

### Design Decisions

**DEC-036: Multi-Vault Storage Strategy**
- **Decision**: Auto-derive storage as `vault/.temoa/` for non-config vaults
- **Alternative considered**: Centralized storage (e.g., `~/.config/temoa/indexes/`)
- **Rationale**:
  - Co-location is intuitive (index lives with vault)
  - Simpler for users (no additional path management)
  - Easier to backup/sync (vault + index together)
  - Matches Obsidian's .obsidian/ pattern
- **Trade-off**: Index not portable across machines (but embeddings aren't either)

**DEC-037: Validation Before Operations**
- **Decision**: Validate vault match before write operations, fail early
- **Alternative considered**: Warn but allow (soft validation)
- **Rationale**:
  - Data loss is catastrophic (can't undo)
  - Better to block and require --force
  - Clear error messages guide users to solution
  - Prevents accidental mistakes

**DEC-038: Auto-Migration of Old Indexes**
- **Decision**: Automatically add metadata to old indexes on first access
- **Alternative considered**: Require manual reindex
- **Rationale**:
  - Seamless upgrade experience
  - No user action required
  - One-time cost (only missing metadata)
  - Logged for visibility

### Backward Compatibility

**100% backward compatible**:
- ✅ Existing configs work without changes
- ✅ Old indexes auto-migrate on first use
- ✅ Single-vault users see no difference
- ✅ Storage location unchanged for config vault
- ✅ All existing CLI commands work

**Breaking changes**: None

**Deprecations**: None

### Files Changed

1. **`src/temoa/storage.py`** (195 lines) - NEW FILE
   - Core vault-aware storage utilities
   - Validation and auto-migration logic

2. **`src/temoa/cli.py`** (5 commands updated)
   - `index()` - Added --force, storage derivation, validation
   - `reindex()` - Added --force, storage derivation, validation
   - `search()` - Added --vault support
   - `archaeology()` - Added --vault support
   - `stats()` - Added --vault support

3. **`src/temoa/synthesis.py`** (3 lines added)
   - Added vault metadata to `model_info` dict (line 953-955)

4. **`tests/test_storage.py`** (282 lines) - NEW FILE
   - 13 unit tests, all passing

5. **`tests/test_multi_vault_integration.py`** (188 lines) - NEW FILE
   - Integration test structure (manual testing)

6. **`pyproject.toml`** (1 line added)
   - Added pytest as dev dependency

7. **`uv.lock`** (updated dependencies)

### Commit

```
feat: implement multi-vault support with safe storage derivation

This fixes the critical bug where `temoa index --vault /other/vault`
would store the index in the config vault's .temoa/, causing data loss.

Closes: Phase 3 Part 0 - Multi-Vault Support
Resolves: Data loss bug from IMPLEMENTATION.md line 1149
```

### What's Next

**Phase 3 Part 1: Technical Debt** (next up):
- Fix module-level initialization
- Remove sys.path manipulation
- Introduce service layer

**Phase 3 Part 2: Search Quality**:
- Cross-encoder re-ranking
- Query expansion
- Time-aware scoring

**Phase 3 Part 3: UI/UX Polish**:
- PWA support
- Keyboard shortcuts
- Search history

### Key Insight

**From PHASE-3-READY.md**:
> This bug was a **time bomb**. Anyone using `--vault` for testing or multi-vault workflows risked silent data corruption. The fix is surgical: validate before operations, fail with clear solutions, provide escape hatch via --force.

**Lesson learned**: Optional flags that change behavior (like `--vault`) must be comprehensively tested across all code paths. Path derivation must be atomic (vault + storage together, not separately).

---

## Entry 21: Multi-Vault Webapp UI (2025-11-27)

**Goal**: Extend multi-vault support to the webapp with a vault selector UI.

### What Was Built

**Vault Selector Component** (added to both search.html and manage.html):
- Dropdown showing all configured vaults by name
- Info badges below showing: "default" status, "N files indexed" or "not indexed"
- State management: URL param > localStorage > default vault
- Shareable URLs with `?vault=...` parameter

**Backend Fixes**:
1. Fixed `/health` endpoint to accept vault parameter
2. Fixed `get_vault_metadata()` to check model-specific subdirectory (`storage_dir/model/index.json`)
3. Fixed `/vaults` endpoint to correctly report indexed status

### Key Discovery: Storage Structure

**Problem**: `/vaults` endpoint reported all vaults as "not indexed" even though they were.

**Root cause**: Synthesis stores indexes in model-specific subdirectories:
```
.temoa/                    ← storage_dir (what we were checking)
  └── all-mpnet-base-v2/   ← actual location
      └── index.json       ← here!
```

**Fix**: Updated `get_vault_metadata()` to accept model parameter:
```python
def get_vault_metadata(storage_dir: Path, model: str) -> Optional[Dict]:
    index_file = storage_dir / model / "index.json"  # ← Now correct!
    ...
```

### Config Format

Multi-vault support requires adding a `vaults` array to config:
```json
{
  "vaults": [
    {"name": "amoxtli", "path": "~/Obsidian/amoxtli", "is_default": true},
    {"name": "rodeo", "path": "~/Obsidian/rodeo", "is_default": false},
    {"name": "small-vault", "path": "~/Obsidian/small-vault", "is_default": false}
  ],
  "vault_path": "~/Obsidian/amoxtli",
  ...
}
```

Backward compatible: If no `vaults` array, auto-generates single-vault list from `vault_path`.

### UI Design Decisions

**DEC-039: Clean Dropdown, Info in Badges**
- Dropdown shows just vault names (clean, scannable)
- Badges below show metadata (default status, file count)
- Avoids cluttered dropdown with redundant info

**DEC-040: State Priority (URL > localStorage > default)**
- URL params enable shareable links (`?vault=rodeo`)
- localStorage remembers last-used vault
- Falls back to default vault from config

**DEC-041: Removed Status Link from Footer**
- Health info now in vault badges
- Management page shows detailed status
- Cleaner footer, less redundancy

### Files Changed

1. **`src/temoa/storage.py`** - Fixed `get_vault_metadata()` to accept model parameter
2. **`src/temoa/server.py`** - Fixed `/health` and `/vaults` endpoints
3. **`src/temoa/ui/search.html`** - Added vault selector with full state management
4. **`src/temoa/ui/manage.html`** - Added vault selector, updated all API calls

### Testing

Verified with 3 vaults:
- **amoxtli**: 3067 files indexed ✅
- **rodeo**: 9056 files indexed ✅
- **small-vault**: not indexed ✅

All endpoints working with vault parameter:
- `/vaults` - Lists all vaults with status
- `/health?vault=...` - Health check for specific vault
- `/search?vault=...` - Search specific vault
- `/stats?vault=...` - Stats for specific vault
- `/reindex?vault=...` - Reindex specific vault
- `/extract?vault=...` - Extract gleanings from specific vault

---

## Entry 22: UI Cleanup - Mobile-First Space Optimization (2025-11-28)

**Goal**: Optimize vertical space, improve visual hierarchy, ensure search button visible with mobile keyboard up

### The Problem

During testing, user identified several UI issues:
1. **Vertical space waste** - Header too large, vault selector too prominent, huge search button
2. **Wrong hierarchy** - Vault selector appeared before search box (but search is primary)
3. **Navigation misplaced** - Gear icon floating alone instead of integrated with header
4. **Common settings buried** - Hybrid search checkbox inside collapsible Options panel
5. **Management page backwards** - Actions section at bottom despite being most important

**Key insight**: "Vertical space is precious" on mobile. Search button wasn't visible with keyboard up.

### Changes Implemented

#### 1. Compact Inline Header
**Before** (3 lines):
```
Temoa                    ⚙︎
Semantic search for your vault
```

**After** (1 line):
```
Temoa  Semantic search for your vault    Manage
```

**Changes**:
- Removed `.header-content` wrapper, made header flexbox with `gap: 12px`
- h1 size reduced: 28px → 24px
- Margins reduced: 24px → 16px
- Gear icon `⚙︎` replaced with "Manage" text
- Navigation link aligned right with `margin-left: auto`
- Subtitle has `flex: 1` to expand and push nav link right
- Mobile responsive: subtitle wraps on screens < 500px

**Space saved**: ~20px vertical

#### 2. Inline Search Button
**Before**:
```
┌─────────────────────────────────┐
│ Search your vault...            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│           Search                │  ← Full width, 14px padding
└─────────────────────────────────┘
```

**After**:
```
┌─────────────────────────────┬──┐
│ Search your vault...        │→ │  ← Inline, 8px padding
└─────────────────────────────┴──┘
```

**Changes**:
- Button positioned absolute inside search box: `position: absolute; right: 6px; top: 50%; transform: translateY(-50%);`
- Text changed: "Search" → "→" (arrow)
- Padding reduced: 14px → 8px
- Input has `padding-right: 60px` for button space
- Button width: auto (not 100%)

**Space saved**: ~40px vertical + button visible with keyboard up ✅

#### 3. Vault Selector: Compact + Repositioned
**Before** (top of page, after header):
```
┌──────────────────────────────────┐
│ amoxtli                          ▼│  ← Full width
└──────────────────────────────────┘
[default] [3083 files indexed]
```

**After** (bottom of page, before footer):
```
Vault: [amoxtli ▼] default, 3083 files  ← Inline, compact
```

**Changes**:
- Moved from after header to **before footer** (bottom of page)
- Layout: inline flexbox with `gap: 8px`
- Added label: `<label class="vault-selector-label">Vault:</label>`
- Dropdown: `width: auto; min-width: 150px` (not 100%)
- Padding reduced: 10px 12px → 6px 10px
- Font size reduced: 14px → 13px
- Badges inline: `display: inline-flex` (not block)

**Rationale**: Vault switching is infrequent, doesn't need top position. Search is primary action.

**Space saved**: ~30px vertical + better hierarchy

#### 4. Hybrid Checkbox: Moved Outside Options
**Before**: Inside collapsible Options panel (requires expanding to access)
**After**: Immediately below search box (always visible)

```
Search box + button
Hybrid (BM25+semantic) ☐  ← Quick access
▶ Options
```

**Rationale**: User noted "that's a way more common change than the other settings". Hybrid search is toggled frequently, shouldn't be buried.

**Impact**: Common setting now easily accessible without expanding Options.

#### 5. Management Page: Actions First
**Before order**:
1. System Health
2. Vault Statistics
3. Actions ← Most important, but at bottom

**After order**:
1. **Actions** ← Reindex, Extract (most important)
2. System Health
3. Vault Statistics

**Rationale**: User said "the most important thing is the action panel but it's at the bottom". Primary use case is triggering reindex/extract.

### Space Saved Summary

| Change | Vertical Space Saved |
|--------|---------------------|
| Header inline | ~20px |
| Search button inline | ~40px |
| Vault selector compact | ~30px |
| **Total** | **~90px** |

**Mobile impact**: Search button now visible even with keyboard up ✅

### Visual Hierarchy (New Order)

**Search page**:
1. Header (compact, 1 line)
2. **Search box + button** ← PRIMARY
3. **Hybrid checkbox** ← Quick access (common setting)
4. Options (collapsible) - Min Score, Limit, Type filters
5. Results/Stats (only when populated)
6. **Vault selector** ← Bottom (infrequent setting)
7. Footer

**Management page**:
1. Header
2. **Actions** ← PRIMARY (Reindex, Extract)
3. System Health
4. Vault Statistics
5. Footer

### Design Decisions

**DEC-042: Search is Primary, Vault is Infrequent**
- **Decision**: Move vault selector to bottom of page
- **Rationale**: Vault switching happens rarely (setup, testing). Search happens constantly. Top of page should focus on primary action.
- **Alternative considered**: Keep vault at top but make more compact
- **Why rejected**: Even compact, it pushes search down. Search must be first thing user sees.

**DEC-043: Common Settings Above the Fold**
- **Decision**: Move hybrid checkbox outside Options panel
- **Rationale**: User explicitly noted hybrid search is toggled "way more" than other settings. Burying in collapsible section adds friction.
- **Alternative considered**: Keep all settings in Options for cleanliness
- **Why rejected**: UI cleanliness < usability. Common actions should be immediately accessible.

**DEC-044: Inline Search Button for Mobile**
- **Decision**: Position search button inside search box (absolute positioned)
- **Rationale**: Solves mobile keyboard issue - button always visible. Also saves ~40px vertical space.
- **Alternative considered**: Small button below input
- **Why rejected**: Still takes vertical space. Inline is more compact and follows modern UI patterns (Gmail, GitHub, etc.)

**DEC-045: Actions First on Management Page**
- **Decision**: Reorder sections to put Actions at top
- **Rationale**: User goes to management page specifically to trigger actions (reindex, extract). Stats are informational, less frequently needed.
- **Alternative considered**: Keep informational sections first (traditional "dashboard" layout)
- **Why rejected**: Management page isn't a dashboard, it's an action panel. Optimize for primary use case.

**DEC-046: Replace Gear Icon with Text**
- **Decision**: Change `⚙︎` to "Manage" text, align right
- **Rationale**: User requested clearer navigation. Text is more explicit than icons. Right alignment follows convention (account/settings usually top-right).
- **Alternative considered**: Keep gear icon but align right
- **Why rejected**: Text is clearer. "Manage" explicitly describes what you'll find.

### Files Modified

1. **`src/temoa/ui/search.html`** (~100 lines modified)
   - Header HTML: removed wrapper, inline layout
   - Header CSS: flexbox with gap, mobile responsive
   - Search button: moved inside search box
   - Vault selector: moved to bottom, added label, made inline
   - Hybrid checkbox: moved outside Options panel

2. **`src/temoa/ui/manage.html`** (~50 lines modified)
   - Header HTML: same changes as search.html
   - Section reorder: Actions → Health → Statistics
   - Navigation: "← Search" → "Search" (removed arrow, aligned right)

3. **`pyproject.toml`** (1 line)
   - Version bump: 0.2.0 → 0.3.0

4. **`docs/UI-CLEANUP-PLAN.md`** (418 lines) - NEW FILE
   - Comprehensive implementation plan
   - Before/after mockups
   - CSS and HTML changes documented
   - Testing checklist

### Testing

**Verified**:
- [x] Header is single line on desktop
- [x] Header wraps gracefully on mobile (<500px)
- [x] Navigation link clickable and aligned right
- [x] Search button visible with keyboard up
- [x] Search button triggers search on click
- [x] Enter key still triggers search
- [x] Vault selector works at bottom
- [x] Vault badges display correctly
- [x] Hybrid checkbox accessible without expanding Options
- [x] Management Actions section at top
- [x] Visual hierarchy clear (search is primary)

**User feedback**: "awesome" - all changes implemented as requested

### Key Insight

**Mobile-first means ruthless prioritization of vertical space**. Every pixel counts when keyboard takes half the screen. The question isn't "where does this fit?" but "does the user need this immediately, frequently, or rarely?"

- **Immediately**: Search box, search button
- **Frequently**: Hybrid toggle
- **Occasionally**: Options (min score, limit, type filters)
- **Rarely**: Vault selector

Organize top-to-bottom by frequency of use, not by what looks balanced on desktop.

**Corollary**: Don't let "infrequent but important" settings claim prime real estate. Vault selector is important (for multi-vault users) but rarely changed. Bottom placement is correct.

---

**Entry created**: 2025-11-28
**Author**: Claude (Sonnet 4.5)
**Status**: UI cleanup complete, v0.3.0
