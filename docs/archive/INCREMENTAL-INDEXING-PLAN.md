# Incremental Indexing Implementation Plan

**Created**: 2025-11-25
**Status**: Proposed
**Goal**: Implement true incremental reindexing to make `temoa reindex` fast for daily use

---

## Overview

Currently, both `temoa index` and `temoa reindex` do full rebuilds of the entire embedding index, processing every file in the vault. This takes the same amount of time (**~2.6 minutes** for the current 3,059-file vault) regardless of how many files actually changed.

This plan implements **true incremental reindexing** where `temoa reindex` only processes new and modified files, making it much faster for daily use.

### Current Production Stats (Measured 2025-11-25)

- **Files indexed**: 3,059
- **Model**: `all-mpnet-base-v2`
- **Embedding dimensions**: 768
- **Index size**: ~18.7 MB (embeddings.npy) + ~2-3 MB (metadata.json)
- **Full index time**: **154 seconds (2m 34s)** on MacBook
  - Reading vault: ~2s (fast)
  - Embedding batches: ~152s (slow - this is what we optimize)

---

## Design Goals

### CLI Commands (User-Facing)

**`temoa index [--vault PATH]`**
- Full rebuild from scratch
- Use when: First time setup, switching models, or troubleshooting
- Always clears existing index and reprocesses everything
- No other flags (clean, simple)

**`temoa reindex [--vault PATH]`**
- Incremental update (only new/modified files)
- Use when: After adding gleanings, modifying notes, daily maintenance
- Falls back to full index if no existing index found (no error)
- No other flags (clean, simple)

### Backend API

**`POST /reindex?force=false`** (default)
- Incremental update
- `force=true` → full rebuild
- Keeps existing endpoint name

### Management UI

**"Reindex Vault" section**
- Button labeled: "Reindex Vault"
- Checkbox/toggle: "Full rebuild" (unchecked by default)
- Unchecked = incremental update
- Checked = full rebuild from scratch

---

## Current State vs Desired State

### Current Behavior

```python
# synthesis.py:664
def reindex(self, force: bool = True):
    if force:
        self.pipeline.store.clear()  # Only difference!

    # Both paths do the same work:
    vault_content = self.pipeline.reader.read_vault()  # Read ALL files
    texts = [content.content for content in vault_content]
    embeddings = self.pipeline.engine.embed_texts(texts)  # Embed ALL
    self.pipeline.store.save_embeddings(embeddings, metadata)  # Save ALL
```

**Problem**: Whether `force=True` or `force=False`, it processes every file.

### Desired Behavior

```python
def reindex(self, force: bool = True):
    if force:
        # Full rebuild
        self.pipeline.store.clear()
        vault_content = self.pipeline.reader.read_vault()
        # ... embed all and save
    else:
        # Incremental update
        changed_files = self._find_changed_files()
        if not changed_files:
            return {"status": "success", "message": "No changes detected"}

        # Only embed changed files
        embeddings = self.pipeline.engine.embed_texts(changed_files)
        # Merge with existing embeddings
        self._merge_embeddings(embeddings, metadata)
```

---

## Implementation Details

### 1. File Change Detection

**Track modification times in metadata**:

```python
# Current metadata structure (per file):
{
    "relative_path": "path/to/file.md",
    "title": "Note Title",
    "tags": ["tag1", "tag2"],
    "created_date": "2025-01-15",
    "modified_date": "2025-01-20",  # ← Already tracked!
    "content_length": 1234,
    "frontmatter": {...}
}
```

**Add index-time tracking**:

```python
# New: index.json includes file tracking
{
    "model_info": {"model_name": "all-mpnet-base-v2"},
    "created_at": "2025-11-25T10:30:00",
    "num_embeddings": 3050,
    "embedding_dim": 768,
    "files": {...},
    "file_tracking": {  # ← NEW
        "path/to/file.md": {
            "modified_date": "2025-01-20",
            "content_hash": "abc123...",  # Optional: more reliable than mtime
            "index_position": 0  # Position in embeddings array
        },
        ...
    }
}
```

### 2. Memory Implications of Array-to-List Conversion

**The NumPy → Python List Challenge**:

NumPy arrays are fixed-size contiguous memory blocks. To add/remove/update elements, we must:
1. Load the NumPy array into memory
2. Convert to Python list (flexible, can grow/shrink)
3. Modify the list (add/update/delete)
4. Convert back to NumPy array
5. Save to disk

**Memory usage breakdown** (with current vault: 3,059 files × 768 dims):

```python
# Step 1: Load NumPy array
old_embeddings = np.load("embeddings.npy")
# Memory: 3,059 × 768 × 8 bytes = 18,795,264 bytes ≈ 18.8 MB

# Step 2: Convert to Python list
embedding_list = list(old_embeddings)
# Memory: NumPy array (18.7 MB) + Python list (18.7 MB data + ~50 KB overhead)
# Peak: ~37.5 MB

# Step 3: Modify list (append/delete/update)
embedding_list.append(new_embedding)
# Memory: Still ~37.5 MB (maybe 38 MB with a few new embeddings)

# Step 4: Convert back to NumPy
final_embeddings = np.array(embedding_list)
# Memory: Python list (37.5 MB) + new NumPy array (18.7 MB)
# Peak: ~56 MB (briefly during conversion)

# Step 5: Python GC reclaims list memory, save array
np.save("embeddings.npy", final_embeddings)
# Memory: Back to ~18.7 MB after GC
```

**Why this approach is acceptable**:
- Peak memory: ~56 MB (trivial on modern systems with GB of RAM)
- Duration: Conversion takes ~50-100ms (not noticeable)
- Alternative (NumPy slicing/concatenation): More complex, similar memory usage
- Benefit: Simple, readable code that's easy to test and debug

**If memory becomes a concern** (e.g., vault grows to 50K files):
- 50,000 × 768 × 8 = ~307 MB per array
- Peak during conversion: ~614 MB (still acceptable)
- Could optimize with numpy.concatenate() for appends only
- But list approach should scale to 100K+ files before issues arise

### 3. Change Detection Algorithm

```python
def _find_changed_files(self) -> Dict[str, List[VaultContent]]:
    """Find new, modified, and deleted files.

    Returns:
        {
            "new": [VaultContent objects for new files],
            "modified": [VaultContent objects for changed files],
            "deleted": [paths of deleted files]
        }
    """
    # Load existing index tracking
    _, _, index_info = self.pipeline.store.load_embeddings()
    if not index_info or "file_tracking" not in index_info:
        # No previous index, do full rebuild
        return None

    file_tracking = index_info["file_tracking"]

    # Read current vault state
    current_vault = self.pipeline.reader.read_vault()
    current_files = {c.relative_path: c for c in current_vault}

    new_files = []
    modified_files = []
    deleted_paths = []

    # Find new and modified files
    for path, content in current_files.items():
        if path not in file_tracking:
            new_files.append(content)
        else:
            tracked = file_tracking[path]
            # Compare modification dates
            if content.modified_date != tracked["modified_date"]:
                modified_files.append(content)
            # Optional: Also compare content hash for reliability
            # if content_hash(content.content) != tracked["content_hash"]:
            #     modified_files.append(content)

    # Find deleted files
    for path in file_tracking.keys():
        if path not in current_files:
            deleted_paths.append(path)

    return {
        "new": new_files,
        "modified": modified_files,
        "deleted": deleted_paths
    }
```

### 3. Embedding Merge Strategy

**Challenge**: NumPy arrays are fixed-size. We need to add/update/remove embeddings.

**CRITICAL: Order of Operations Matters!**

When merging embeddings, the order in which we apply changes is critical to avoid index corruption:

1. **DELETE first** (in reverse index order)
2. **UPDATE second** (using pre-deletion indices)
3. **APPEND last** (new files go at end)

**Why this order?**
- Deleting shifts all subsequent indices down
- Updating requires stable indices
- Appending doesn't affect existing indices

**Wrong order = data corruption!**

```python
# WRONG - DO NOT DO THIS
for new_file in new_files:
    embeddings_list.append(new_embedding)  # Adds at end
for deleted_idx in deleted_indices:
    del embeddings_list[deleted_idx]  # ❌ Index is wrong now!

# RIGHT - ALWAYS DO THIS
# Step 1: DELETE (reverse order to avoid index shifting issues)
for idx in sorted(deleted_indices, reverse=True):
    del embeddings_list[idx]
# Step 2: UPDATE (indices still valid after deletions)
for update in updates:
    embeddings_list[update.idx] = update.embedding
# Step 3: APPEND (safe to add at end)
for new_embedding in new_embeddings:
    embeddings_list.append(new_embedding)
```

**Approach**:

```python
def _merge_embeddings(
    self,
    new_embeddings: np.ndarray,
    new_metadata: List[Dict],
    changes: Dict
) -> None:
    """Merge new/updated embeddings with existing index.

    CRITICAL: This function modifies array indices. The order of operations
    is EXTREMELY important to avoid data corruption:

    1. DELETE files first (in REVERSE index order)
    2. UPDATE files second (using original indices from before deletion)
    3. APPEND new files last (at end of array)

    Do NOT change this order without careful testing!

    Args:
        new_embeddings: Embeddings for new/modified files
        new_metadata: Metadata for new/modified files
        changes: Dict with "new", "modified", "deleted" file lists
    """
    # Load existing embeddings
    old_embeddings, old_metadata, index_info = self.pipeline.store.load_embeddings()

    if old_embeddings is None:
        # No existing index, just save new ones
        self.pipeline.store.save_embeddings(new_embeddings, new_metadata, model_info)
        return

    file_tracking = index_info.get("file_tracking", {})

    # Build mapping: path → index position (from BEFORE any changes)
    # This is our source of truth for where things currently are
    path_to_idx = {}
    for i, meta in enumerate(old_metadata):
        path_to_idx[meta["relative_path"]] = i

    # Convert to Python lists (allows dynamic sizing)
    embeddings_list = list(old_embeddings)
    metadata_list = list(old_metadata)

    # =========================================================================
    # STEP 1: DELETE files (REVERSE order - CRITICAL!)
    # =========================================================================
    # WHY REVERSE? When you delete index 5, index 6 becomes 5, 7 becomes 6, etc.
    # If we delete in forward order, our stored indices become invalid.
    # Reverse order means we delete from the end first, keeping earlier indices stable.

    indices_to_delete = []
    for path in changes["deleted"]:
        if path in path_to_idx:
            indices_to_delete.append(path_to_idx[path])

    # Sort descending (largest index first) to maintain index validity
    for idx in sorted(indices_to_delete, reverse=True):
        del embeddings_list[idx]
        del metadata_list[idx]

    # =========================================================================
    # STEP 2: UPDATE modified files (use ORIGINAL indices from path_to_idx)
    # =========================================================================
    # IMPORTANT: path_to_idx was built BEFORE deletions. After deleting files,
    # some indices may have shifted. This is OK for updates because:
    # - We're using the OLD position to find the file
    # - We're replacing it in-place (no shifting)
    # - The positions are still valid relative to the list structure
    #
    # GOTCHA: If a file was both modified AND its position shifted due to
    # deletions before it, we need to account for that shift!

    # Rebuild position map after deletions
    path_to_idx_after_delete = {}
    for i, meta in enumerate(metadata_list):
        path_to_idx_after_delete[meta["relative_path"]] = i

    new_idx = 0
    for content in changes["modified"]:
        path = content.relative_path
        if path in path_to_idx_after_delete:  # Use post-deletion indices
            current_idx = path_to_idx_after_delete[path]
            embeddings_list[current_idx] = new_embeddings[new_idx]
            metadata_list[current_idx] = new_metadata[new_idx]
            new_idx += 1

    # =========================================================================
    # STEP 3: APPEND new files (always safe - goes at end)
    # =========================================================================
    for content in changes["new"]:
        embeddings_list.append(new_embeddings[new_idx])
        metadata_list.append(new_metadata[new_idx])
        new_idx += 1

    # Convert back to numpy array
    merged_embeddings = np.array(embeddings_list)

    # Save merged result (save_embeddings will rebuild file_tracking with correct positions)
    self.pipeline.store.save_embeddings(merged_embeddings, metadata_list, model_info)
```

### 4. BM25 Index Handling

The BM25 keyword index is fast to rebuild (takes seconds), so we can just rebuild it entirely each time:

```python
# In reindex() method:
if not force:
    # Incremental semantic embeddings (slow)
    changes = self._find_changed_files()
    if changes:
        # ... merge embeddings logic

    # But rebuild BM25 from scratch (fast)
    vault_content = self.pipeline.reader.read_vault()
    self.bm25_index.build(documents)
```

**Rationale**:
- BM25 indexing is fast (< 5 seconds for 2000 files)
- Simplifies implementation (no need to merge BM25 index)
- Still saves time by avoiding re-embedding unchanged files

---

## Changes Required

### 1. CLI Changes (`src/temoa/cli.py`)

**Before**:
```python
@click.option('--force', is_flag=True, help='Force full rebuild of index')
def reindex(vault, force):
    result = client.reindex(force=force)
```

**After**:
```python
def reindex(vault):
    """Re-index vault incrementally (only new/modified files)."""
    result = client.reindex(force=False)
```

**`index` command** (no changes needed):
```python
def index(vault):
    """Build complete index from scratch."""
    result = client.reindex(force=True)
```

### 2. Backend Changes (`src/temoa/synthesis.py`)

Add three new methods to `SynthesisClient`:

1. `_find_changed_files()` - Detect new/modified/deleted files
2. `_merge_embeddings()` - Merge new embeddings with existing index
3. Update `reindex(force=False)` - Use incremental logic when `force=False`

### 3. Storage Changes (`synthesis/src/embeddings/store.py`)

**Update `save_embeddings()` to track files**:

```python
def save_embeddings(
    self,
    embeddings: np.ndarray,
    metadata: List[Dict[str, Any]],
    model_info: Dict[str, str]
) -> None:
    """Save embeddings and metadata with file tracking."""

    # Build file tracking map
    file_tracking = {}
    for i, meta in enumerate(metadata):
        file_tracking[meta["relative_path"]] = {
            "modified_date": meta.get("modified_date"),
            "content_length": meta.get("content_length"),
            "index_position": i
        }

    # Save index.json with tracking
    index_data = {
        "model_info": model_info,
        "created_at": datetime.now().isoformat(),
        "num_embeddings": len(embeddings),
        "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
        "file_tracking": file_tracking,  # ← NEW
        "files": {
            "embeddings": str(self.embeddings_file.name),
            "metadata": str(self.metadata_file.name)
        }
    }

    # ... save as before
```

### 4. API Endpoint Changes (`src/temoa/server.py`)

**Current**:
```python
@app.post("/reindex")
async def reindex(force: bool = False):
    result = synthesis_client.reindex(force=force)
```

**No changes needed** - already has the right signature! Just update docstring:

```python
@app.post("/reindex")
async def reindex(force: bool = False):
    """
    Re-index the vault.

    By default, only processes new/modified files (incremental).
    Use ?force=true for full rebuild from scratch.

    Examples:
        POST /reindex           # Incremental update
        POST /reindex?force=true   # Full rebuild
    """
```

### 5. Management UI Changes (`src/temoa/ui/manage.html`)

**Before**:
```html
<button onclick="reindex()">Reindex Vault</button>

<script>
async function reindex() {
    const response = await fetch('/reindex?force=true', { method: 'POST' });
}
</script>
```

**After**:
```html
<div class="reindex-section">
    <h3>Reindex Vault</h3>
    <p>Update the search index with new and modified files.</p>

    <label>
        <input type="checkbox" id="fullRebuild">
        Full rebuild (process all files)
    </label>

    <button onclick="reindex()">Reindex Vault</button>
</div>

<script>
async function reindex() {
    const fullRebuild = document.getElementById('fullRebuild').checked;
    const url = `/reindex?force=${fullRebuild}`;

    const response = await fetch(url, { method: 'POST' });
    // ... handle response
}
</script>
```

---

## Testing Strategy

### 1. Unit Tests

**Test change detection**:
```python
def test_find_changed_files_new():
    # Create index with 3 files
    # Add 1 new file to vault
    # Assert: changes["new"] has 1 file

def test_find_changed_files_modified():
    # Create index with 3 files
    # Modify 1 file (update mtime)
    # Assert: changes["modified"] has 1 file

def test_find_changed_files_deleted():
    # Create index with 3 files
    # Delete 1 file from vault
    # Assert: changes["deleted"] has 1 file path
```

**Test embedding merge**:
```python
def test_merge_embeddings_add():
    # Start with 100 embeddings
    # Add 5 new files
    # Assert: result has 105 embeddings

def test_merge_embeddings_update():
    # Start with 100 embeddings
    # Update 3 files
    # Assert: result has 100 embeddings, 3 are updated

def test_merge_embeddings_delete():
    # Start with 100 embeddings
    # Delete 2 files
    # Assert: result has 98 embeddings
```

### 2. Integration Tests

```python
def test_reindex_incremental():
    # Build full index
    initial = client.reindex(force=True)

    # Add 1 new file
    # Run incremental reindex
    result = client.reindex(force=False)

    # Assert: Only 1 file was processed
    # Assert: Search still finds all files

def test_reindex_falls_back_to_full():
    # Delete index files
    # Run reindex (force=False)
    # Assert: Does full index without error
```

### 3. Performance Testing

**Benchmark scenarios**:

```bash
# Scenario 1: No changes
temoa reindex  # Should be < 2 seconds

# Scenario 2: 10 new files added
temoa reindex  # Should be ~2-3 seconds

# Scenario 3: 1 file modified
temoa reindex  # Should be < 2 seconds

# Scenario 4: Full rebuild (baseline)
temoa index    # ~154 seconds (unchanged)
```

**Success criteria**:
- Incremental reindex with no changes: < 3 seconds
- Incremental reindex with 10 new files: < 8 seconds
- Full rebuild: Same as current (~154 seconds)

---

## Implementation Order

### Phase 1: Backend Foundation
1. ✅ Add `file_tracking` to `store.py::save_embeddings()`
2. ✅ Implement `SynthesisClient._find_changed_files()`
3. ✅ Implement `SynthesisClient._merge_embeddings()`
4. ✅ Write unit tests for change detection and merging

### Phase 2: Incremental Logic
1. ✅ Update `SynthesisClient.reindex(force=False)` to use incremental logic
2. ✅ Add fallback to full index if no previous index exists
3. ✅ Write integration tests
4. ✅ Test with real vault (1000+ files)

### Phase 3: CLI & API Updates
1. ✅ Remove `--force` flag from `temoa reindex` command
2. ✅ Update API endpoint docstring
3. ✅ Update CLI help text and documentation

### Phase 4: UI Updates
1. ✅ Add "Full rebuild" checkbox to management page
2. ✅ Update button click handler to respect checkbox
3. ✅ Add user feedback (show what was processed)
4. ✅ Test on mobile

### Phase 5: Documentation & Deployment
1. ✅ Update README.md with new command behavior
2. ✅ Update DEPLOYMENT.md with reindexing guidance
3. ✅ Add entry to CHRONICLES.md documenting this change
4. ✅ Deploy and test in production

---

## Edge Cases & Error Handling

### 1. No Previous Index
**Scenario**: User runs `temoa reindex` but no index exists yet

**Behavior**: Automatically fall back to full index (no error)

```python
def reindex(self, force: bool = True):
    if not force:
        # Check if index exists
        if not self.pipeline.store.exists():
            logger.info("No existing index found, performing full rebuild")
            force = True

    # ... rest of logic
```

### 2. Model Mismatch
**Scenario**: Previous index used different model than current config

**Behavior**:
- Detect model mismatch from `index.json`
- Log warning
- Recommend full rebuild with `temoa index`
- Continue with incremental (user's choice)

```python
# In _find_changed_files():
if index_info["model_info"]["model_name"] != self.model_name:
    logger.warning(
        f"Model mismatch: index uses {index_info['model_info']['model_name']}, "
        f"but config specifies {self.model_name}. "
        f"Consider running 'temoa index' for full rebuild."
    )
```

### 3. Corrupted Index
**Scenario**: `index.json` exists but embeddings/metadata files are missing

**Behavior**: Fall back to full index

```python
try:
    embeddings, metadata, index_info = self.pipeline.store.load_embeddings()
    if embeddings is None or metadata is None:
        raise SynthesisError("Corrupted index")
except Exception as e:
    logger.warning(f"Could not load index: {e}, performing full rebuild")
    force = True
```

### 4. Empty Change Set
**Scenario**: User runs `temoa reindex` but no files changed

**Behavior**: Return success immediately (no work needed)

```python
changes = self._find_changed_files()
if not changes or (
    not changes["new"] and
    not changes["modified"] and
    not changes["deleted"]
):
    return {
        "status": "success",
        "message": "No changes detected, index is up to date"
    }
```

---

## Migration Notes

### Backward Compatibility

**Existing indexes** (created before this change):
- Do not have `file_tracking` in `index.json`
- First `temoa reindex` will detect this and fall back to full rebuild
- Subsequent runs will use incremental logic

**No manual migration needed** - system handles it gracefully.

### User Communication

**Update help text**:
```
$ temoa index --help
Usage: temoa index [OPTIONS]

  Build complete embedding index from scratch.

  Use this for: first-time setup, switching models, troubleshooting.

$ temoa reindex --help
Usage: temoa reindex [OPTIONS]

  Re-index vault incrementally (only new/modified files).

  Use this for: after adding gleanings, modifying notes, daily maintenance.
  Falls back to full index if no existing index is found.
```

**Update README.md**:
```markdown
## Indexing Commands

- `temoa index` - Full rebuild (processes all files, ~15-20 seconds)
- `temoa reindex` - Incremental update (only changed files, ~2-5 seconds)

After extracting gleanings or modifying notes, run `temoa reindex` to update the search index.
```

---

## DANGER ZONES: Where Bugs Will Hide

This section documents the critical failure modes and "gotchas" that will cause subtle data corruption if not handled correctly. Read this before implementing or debugging merge logic.

### Danger Zone #1: List Index Shifting

**Problem**: When you delete an item from a Python list, all subsequent indices shift down by 1.

```python
# Example of the problem
items = ['a', 'b', 'c', 'd', 'e']  # indices: 0, 1, 2, 3, 4
del items[1]  # Delete 'b'
# Now: ['a', 'c', 'd', 'e']  # indices: 0, 1, 2, 3
# Former index 2 ('c') is now index 1
# Former index 3 ('d') is now index 2
# etc.
```

**Consequences**:
- If you store indices before deletion, they become INVALID after deletion
- Using old indices after deletion = accessing wrong data = corruption

**Solution**: Always delete in REVERSE order (highest index first)

```python
indices_to_delete = [1, 3, 7, 12]
for idx in sorted(indices_to_delete, reverse=True):  # [12, 7, 3, 1]
    del items[idx]
# Deleting 12 doesn't affect indices 7, 3, 1
# Deleting 7 doesn't affect indices 3, 1
# Deleting 3 doesn't affect index 1
# All deletions use correct indices
```

### Danger Zone #2: Stale Index Maps

**Problem**: After deletions, any `path → index` mapping built BEFORE deletion is stale.

```python
# Built before deletions
path_to_idx = {"file1.md": 0, "file2.md": 1, "file3.md": 2}

# After deleting index 1 ("file2.md")
# "file3.md" is now at index 1, not 2!
# But path_to_idx still says it's at 2 (WRONG!)
```

**Consequences**:
- Using stale map for updates = updating wrong file
- Using stale map for lookups = accessing wrong data

**Solution**: Rebuild the index map after deletions

```python
# After deletions, rebuild map
path_to_idx_after_delete = {}
for i, meta in enumerate(metadata_list):
    path_to_idx_after_delete[meta["relative_path"]] = i
# Now updates use correct current positions
```

### Danger Zone #3: Wrong Order of Operations

**Problem**: Applying changes in wrong order corrupts indices.

```python
# WRONG - Appending before deleting
embeddings_list.append(new_embedding)  # Adds at end
del embeddings_list[5]  # This should delete old file, but...
# We just deleted what we added! Or deleted wrong file!

# WRONG - Updating before deleting
embeddings_list[5] = updated_embedding  # Update position 5
del embeddings_list[3]  # Delete shifts indices
# Position 5 is now position 4, update went to wrong place!
```

**Consequences**:
- Embeddings don't match metadata
- Search returns wrong files
- Silent data corruption (hard to detect)

**Solution**: ALWAYS use this order:
1. DELETE (reverse order)
2. UPDATE (using rebuilt index map)
3. APPEND (new files at end)

### Danger Zone #4: Forgetting to Rebuild file_tracking

**Problem**: After merge, `file_tracking` positions are stale.

```python
# Before: file_tracking says "file3.md" is at position 10
# After deleting positions 2, 5, 8
# "file3.md" is now at position 7
# But file_tracking still says 10 (WRONG!)
```

**Consequences**:
- Next incremental reindex uses wrong positions
- Cumulative corruption over multiple reindexes

**Solution**: `save_embeddings()` ALWAYS rebuilds file_tracking

```python
# This happens automatically in save_embeddings()
file_tracking = {}
for i, meta in enumerate(metadata):
    file_tracking[meta["relative_path"]] = {
        "modified_date": meta["modified_date"],
        "index_position": i  # Fresh, correct position
    }
```

### Danger Zone #5: Off-By-One in new_embeddings Index

**Problem**: When processing modified and new files, tracking position in `new_embeddings` array.

```python
# new_embeddings contains: [embedding_for_modified1, embedding_for_modified2, embedding_for_new1, embedding_for_new2]
# If you restart new_idx for each loop, you'll reuse embeddings!

# WRONG
for modified_file in modified_files:
    embeddings_list[idx] = new_embeddings[0]  # Always uses first!

for new_file in new_files:
    embeddings_list.append(new_embeddings[0])  # Always uses first!

# RIGHT
new_idx = 0
for modified_file in modified_files:
    embeddings_list[idx] = new_embeddings[new_idx]
    new_idx += 1  # Increment!

for new_file in new_files:
    embeddings_list.append(new_embeddings[new_idx])
    new_idx += 1  # Keep incrementing!
```

### Testing for These Dangers

**Critical test cases**:
1. Delete first file (index 0) → verify all positions shift correctly
2. Delete last file → verify no off-by-one errors
3. Delete multiple non-contiguous files → verify all shifts tracked
4. Modify file that comes AFTER a deletion → verify position corrected
5. Mix all three operations → verify order is correct

**Invariants to check**:
- `len(embeddings) == len(metadata)` (always)
- `embeddings[i]` matches `metadata[i]["relative_path"]` (always)
- `file_tracking[path]["index_position"] == actual_position_in_array` (always)
- After reindex, search for known file returns correct file (end-to-end)

---

## Success Metrics

### Performance Targets

**Current vault**: 3,059 files with `all-mpnet-base-v2` (768-dim embeddings)

**Before** (current behavior - both do full rebuild):
- `temoa index`: **154 seconds** (2m 34s) - embed all 3,059 files
- `temoa reindex`: **154 seconds** (2m 34s) - identical, embed all 3,059 files

**After** (target with incremental reindexing):
- `temoa index`: **154 seconds** (unchanged - still full rebuild)
- `temoa reindex` (no changes): **< 3 seconds** (just change detection)
- `temoa reindex` (10 new files): **~5-8 seconds** (embed 10 + merge)
- `temoa reindex` (100 new files): **~30-40 seconds** (embed 100 + merge)
- `temoa reindex` (1000 new files): **~90-100 seconds** (embed 1000 + merge)

**Time savings for typical daily use** (5-10 new gleanings):
- Current: 154 seconds (2m 34s)
- Target: 6 seconds
- **Speedup: 25x faster**

### User Experience Improvements

1. **Faster daily workflow**: Reindexing after adding gleanings goes from 154s → 6s (25x faster)
2. **Clearer semantics**: `index` vs `reindex` names match their behavior
3. **Simpler CLI**: No flags to remember (except `--vault`)
4. **Smarter defaults**: UI checkbox defaults to incremental (faster)
5. **Scales with vault growth**: Even with 5K+ files, incremental reindex stays fast

---

## Questions & Decisions

### Q1: Content hash vs modification time?

**Modification time** (simpler):
- ✅ Fast to check (no file reading)
- ✅ Already tracked in metadata
- ❌ Can be unreliable (git checkout, file sync, etc.)

**Content hash** (more reliable):
- ✅ Guaranteed to detect changes
- ❌ Requires reading entire file
- ❌ Slower for large vaults

**Decision**: Start with modification time, add content hash as optional enhancement later if needed.

### Q2: Should we support "force reindex specific files"?

**Use case**: User modified a few specific files and wants to reindex just those.

**API**: `POST /reindex?files=path/to/file1.md,path/to/file2.md`

**Decision**: Not in initial implementation. Can add later if users request it.

### Q3: Should incremental reindex update BM25 incrementally too?

**Full rebuild each time**:
- ✅ Simple to implement
- ✅ BM25 is fast (< 5 seconds)
- ❌ Still processes all files

**Incremental BM25**:
- ✅ Could be faster
- ❌ More complex (need BM25 merge logic)
- ❌ Marginal benefit (BM25 already fast)

**Decision**: Rebuild BM25 fully each time. It's fast enough and keeps implementation simple.

---

## Risk Assessment

### Low Risk
- ✅ Backward compatible (falls back gracefully)
- ✅ Doesn't change full index behavior
- ✅ Easy to test (clear inputs/outputs)

### Medium Risk
- ⚠️ Embedding merge logic is complex (numpy array manipulation)
- ⚠️ File tracking adds data to index.json (could grow large)
- **Mitigation**: Thorough testing, limit tracking to essential fields

### High Risk
- ❌ None identified

---

## Future Enhancements

Beyond initial implementation, consider:

1. **Content hashing** - More reliable change detection
2. **Partial file reindex** - API to reindex specific files
3. **Incremental BM25** - If BM25 becomes bottleneck
4. **Progress reporting** - Show which files are being processed
5. **Reindex statistics** - Show "10 new, 5 modified, 2 deleted" in output

---

## Summary

This plan implements true incremental reindexing by:
1. Tracking file modification times in `index.json`
2. Detecting new/modified/deleted files before embedding
3. Only embedding changed files
4. Merging new embeddings with existing index (via list conversion)
5. Falling back to full index when no previous index exists

**The result**: `temoa reindex` goes from **154 seconds** → **6 seconds** for typical daily use (25x faster).

**Memory overhead**: Peak ~56 MB during merge (acceptable on modern systems)

**Current production scale**:
- 3,059 files
- 768-dimensional embeddings (`all-mpnet-base-v2`)
- ~18.8 MB index size
- Full index: 154 seconds (measured)
- Scales comfortably to 50K+ files

**CLI Design**:
- `temoa index [--vault PATH]` = full rebuild (no other flags)
- `temoa reindex [--vault PATH]` = incremental (no other flags)

**UI Design**:
- Button: "Reindex Vault"
- Checkbox: "Full rebuild" (off by default)

Clean, simple, fast, and scalable. ✓
