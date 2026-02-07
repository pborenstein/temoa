# Synthesis Pre-Filtering Plan

**Created**: 2026-02-07
**Status**: Planning
**Goal**: Enable Query Filter to filter files BEFORE semantic search to eliminate 30+ second waits

---

## Problem Statement

**Current Behavior** (Slow):
```
Query: [type:daily] + search "AI"
Pipeline:
1. Synthesis searches ALL 3,059 vault files (30+ seconds)
2. Temoa filters to ~50 daily notes
3. Return 20 results

Result: 30+ seconds to search 50 files
```

**Desired Behavior** (Fast):
```
Query: [type:daily] + search "AI"
Pipeline:
1. Temoa determines ~50 files match [type:daily]
2. Synthesis searches ONLY those 50 files (2-3 seconds)
3. Return 20 results

Result: 2-3 seconds to search 50 files
```

---

## Architecture Options

### Option A: File List Pre-Filter (Recommended)

**Approach**: Pass a list of file paths to Synthesis, only search those files.

**Synthesis Changes**:
```python
# synthesis/src/embeddings/pipeline.py

class EmbeddingPipeline:
    def search(
        self,
        query: str,
        limit: int = 10,
        file_filter: Optional[List[str]] = None  # NEW PARAMETER
    ) -> Dict:
        """
        Search embeddings with optional file filter.

        Args:
            query: Search query
            limit: Max results
            file_filter: Optional list of relative paths to search
                        If provided, only search these files
        """
        # Load all embeddings
        data = self.store.load()

        # NEW: Apply file filter if provided
        if file_filter is not None:
            # Convert file_filter to set for O(1) lookup
            allowed_paths = set(file_filter)

            # Filter embeddings and metadata
            filtered_indices = [
                i for i, path in enumerate(data['paths'])
                if path in allowed_paths
            ]

            if not filtered_indices:
                return {"results": [], "query": query}

            # Create filtered views
            embeddings = data['embeddings'][filtered_indices]
            paths = [data['paths'][i] for i in filtered_indices]
            metadata = [data['metadata'][i] for i in filtered_indices]
        else:
            # Use all embeddings (current behavior)
            embeddings = data['embeddings']
            paths = data['paths']
            metadata = data['metadata']

        # Rest of search logic unchanged
        query_embedding = self.engine.encode(query)
        similarities = self._compute_similarities(query_embedding, embeddings)
        # ... etc
```

**Temoa Changes**:
```python
# src/temoa/synthesis.py

class SynthesisClient:
    def search(
        self,
        query: str,
        limit: int = 10,
        file_filter: Optional[List[str]] = None  # NEW PARAMETER
    ) -> Dict:
        """Search with optional file pre-filter."""
        return self.pipeline.search(
            query=query,
            limit=limit,
            file_filter=file_filter
        )

# src/temoa/server.py

# In search endpoint, BEFORE Stage 1 (Primary Retrieval):

# NEW: Stage 0.5: Build file filter from Query Filter
file_filter = None
if include_props_list or include_tags_list or include_paths_list or include_files_list:
    # Get all vault files
    all_files = list(vault_client.vault_reader.vault_files)

    # Apply filters to get allowed file list
    file_filter = []
    for file_path in all_files:
        # Read frontmatter (cached by VaultReader)
        content = vault_client.vault_reader.read_file(file_path)

        # Apply property filters
        if include_props_list:
            if not matches_properties(content.frontmatter, include_props_list):
                continue

        # Apply tag filters
        if include_tags_list:
            if not matches_tags(content.frontmatter, include_tags_list):
                continue

        # Apply path filters
        if include_paths_list:
            if not matches_paths(file_path, include_paths_list):
                continue

        # Apply file filters
        if include_files_list:
            if not matches_files(file_path, include_files_list):
                continue

        file_filter.append(str(file_path.relative_to(vault_path)))

# Stage 1: Primary retrieval with file filter
if use_hybrid:
    data = synthesis.hybrid_search(
        query=q,
        limit=search_limit,
        file_filter=file_filter  # NEW
    )
else:
    data = synthesis.search(
        query=q,
        limit=search_limit,
        file_filter=file_filter  # NEW
    )
```

**Pros**:
- Simple API: just pass list of paths
- No Synthesis internal changes needed
- Temoa controls filtering logic
- Works with existing embeddings

**Cons**:
- Requires reading frontmatter for ALL files upfront (~3,059 files)
- Might be slow if frontmatter reading isn't cached
- Memory overhead to build file list

**Performance Estimate**:
- File list building: 1-2 seconds (if frontmatter cached)
- Semantic search: 2-3 seconds (only filtered files)
- **Total: 3-5 seconds** (vs current 30+ seconds)

---

### Option B: Filter Callback Function

**Approach**: Pass a callback function to Synthesis that decides which files to search.

**Synthesis Changes**:
```python
from typing import Callable

class EmbeddingPipeline:
    def search(
        self,
        query: str,
        limit: int = 10,
        filter_func: Optional[Callable[[str, Dict], bool]] = None
    ) -> Dict:
        """
        Search with optional filter callback.

        Args:
            filter_func: Function(path, metadata) -> bool
                        Return True to include file in search
        """
        data = self.store.load()

        if filter_func is not None:
            # Apply filter to each file
            filtered_indices = [
                i for i, (path, meta) in enumerate(zip(data['paths'], data['metadata']))
                if filter_func(path, meta)
            ]
            # ... (same as Option A)
```

**Temoa Changes**:
```python
# Define filter function
def query_filter_func(path: str, metadata: Dict) -> bool:
    # Check properties
    if include_props_list:
        frontmatter = metadata.get('frontmatter', {})
        if not matches_properties(frontmatter, include_props_list):
            return False
    # ... etc
    return True

# Pass to Synthesis
data = synthesis.search(
    query=q,
    limit=search_limit,
    filter_func=query_filter_func
)
```

**Pros**:
- More flexible (callback can do anything)
- Synthesis handles iteration
- Could be faster if metadata is already in Synthesis

**Cons**:
- More complex API
- Callback coupling between Temoa and Synthesis
- Harder to debug

---

### Option C: Hybrid Approach (Best of Both Worlds)

**Approach**: Support both file list AND callback, use whichever is provided.

```python
def search(
    self,
    query: str,
    limit: int = 10,
    file_filter: Optional[List[str]] = None,
    filter_func: Optional[Callable[[str, Dict], bool]] = None
) -> Dict:
    """Search with optional filtering.

    Exactly one of file_filter or filter_func should be provided.
    If neither provided, search all files (current behavior).
    """
    if file_filter is not None and filter_func is not None:
        raise ValueError("Cannot specify both file_filter and filter_func")

    # ... rest as in Option A or B
```

**Pros**:
- Maximum flexibility
- Can choose best approach per use case

**Cons**:
- More API surface area
- Slightly more complex implementation

---

## Implementation Plan

### Phase 1: Proof of Concept (1-2 hours)

**Goal**: Validate that pre-filtering works and is fast

1. **Implement Option A in Synthesis** (file list filter)
   - Modify `EmbeddingPipeline.search()` to accept `file_filter`
   - Test with small file list (10-20 files)
   - Measure performance

2. **Test from Temoa**
   - Manually create file list of daily notes
   - Pass to Synthesis
   - Measure end-to-end time
   - Should be 3-5 seconds vs 30+ seconds

3. **Decision Point**: If PoC works, proceed to Phase 2

### Phase 2: Integration (2-3 hours)

**Goal**: Full integration with Query Filter

1. **Add file list building to Temoa**
   - Implement `build_file_filter()` function
   - Cache frontmatter reads (use VaultReader)
   - Add timing logs

2. **Update search pipeline**
   - Add Stage 0.5: Build file filter
   - Pass file_filter to Synthesis
   - Update pipeline_state logging

3. **Test with real queries**
   - `[type:daily]` - should be fast now
   - `[type:gleaning]` - should be fast
   - No filters - should work as before

### Phase 3: Optimization (1-2 hours)

**Goal**: Make it production-ready

1. **Cache frontmatter**
   - Ensure VaultReader caches frontmatter
   - Measure file list building time
   - Should be <1 second

2. **Handle edge cases**
   - Empty file list (no matches)
   - All files match (same as no filter)
   - Mixed include/exclude filters

3. **Update documentation**
   - Update ARCHITECTURE.md
   - Add performance notes
   - Remove "slow inclusive filter" warnings

### Phase 4: Hybrid Search Support (30 minutes)

**Goal**: Make it work with BM25 + semantic

1. **Update `hybrid_search()` method**
   - Add `file_filter` parameter
   - Pass to both BM25 and semantic search
   - Test that RRF fusion still works

---

## Testing Strategy

### Performance Tests

**Before Implementation**:
```bash
# Measure current times
time curl "localhost:8080/search?q=AI&include_props=%5B%7B%22prop%22%3A%22type%22%2C%22value%22%3A%22daily%22%7D%5D"
# Expected: 30+ seconds
```

**After Implementation**:
```bash
# Same query should be much faster
time curl "localhost:8080/search?q=AI&include_props=%5B%7B%22prop%22%3A%22type%22%2C%22value%22%3A%22daily%22%7D%5D"
# Expected: 3-5 seconds
```

### Functional Tests

1. **Inclusive property filter**: `[type:daily]`
2. **Inclusive tag filter**: `tag:python`
3. **Mixed filters**: `[type:gleaning] tag:ai path:Reference`
4. **Exclusive filters**: `-[type:daily]` (should still work fast)
5. **No filters**: Empty Query Filter (should work as before)

---

## Risk Assessment

### Low Risk
- ✅ No breaking changes to Synthesis API (just adding optional parameter)
- ✅ Backward compatible (no filter = current behavior)
- ✅ Easy to revert if needed

### Medium Risk
- ⚠️ Frontmatter reading performance (mitigated by caching)
- ⚠️ File list building overhead (measured in Phase 1)

### High Risk
- ❌ None identified

---

## Success Criteria

1. **Performance**: Inclusive filters complete in <5 seconds (vs 30+ seconds now)
2. **Correctness**: Same results as current slow method
3. **Backward Compatibility**: Searches without filters work as before
4. **No Regressions**: Exclude filters still fast, hybrid search still works

---

## Future Enhancements

### Post-MVP Improvements

1. **Cache file lists**: Cache the result of `build_file_filter()` for repeated queries
2. **Incremental filtering**: If only adding exclusions, filter existing list instead of rebuilding
3. **Smart defaults**: Auto-detect common slow patterns and suggest exclude filters
4. **Filter statistics**: Show "Searching X files" in loading message

### Advanced Features

1. **Multi-stage filtering**: Filter in stages (properties → tags → paths) to fail fast
2. **Bloom filters**: Use bloom filters for fast membership testing
3. **Index pre-filtering**: Build inverted indexes for common filter patterns

---

## Alternative: Accept Current Behavior

**If pre-filtering proves too complex**, document the trade-off:

- **Inclusive filters**: Slow (search all → filter) but exhaustive
- **Exclude filters**: Fast (search limited → filter) but may miss edge cases
- **Guidance**: Use exclude filters (`-[type:daily]`) when possible

This is a valid product decision if implementation cost is too high.

---

## Recommendation

**Implement Option A (File List Pre-Filter)** because:

1. **Simple API**: Just pass list of paths
2. **Clear separation**: Temoa owns filtering logic, Synthesis owns search
3. **Easy to test**: Can verify file list correctness before search
4. **Low risk**: Backward compatible, easy to revert
5. **Big impact**: 6-10x performance improvement

**Time Estimate**: 4-6 hours total (PoC → Integration → Testing)

**ROI**: High - eliminates major UX issue with minimal risk
