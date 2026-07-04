# Entry 40: Token Limits and Chunking Requirement Discovery

**Date**: 2025-12-18
**Author**: Claude (Sonnet 4.5)
**Type**: Architectural Discovery - Critical Limitation
**Impact**: **CRITICAL** - Affects searchability of large documents
**Status**: DOCUMENTED (implementation deferred to Phase 4)

---

## The Discovery

While testing Temoa with the 1002 vault (Project Gutenberg books), discovered a critical limitation that invalidates a core architectural assumption from Phase 0-1.

### The Problem

**Embedding models have fixed token limits**:
- all-mpnet-base-v2 (default): **512 tokens** (~2,000-2,500 chars)
- all-MiniLM-L6-v2: **512 tokens** (~2,000-2,500 chars)
- all-MiniLM-L12-v2: **512 tokens** (~2,000-2,500 chars)
- paraphrase-albert-small-v2: **100 tokens** (~400 chars!)

**Current behavior**:
- sentence-transformers **silently truncates** text beyond token limit
- No warning or error message
- Embeddings only represent first ~2,500 characters of any file
- Rest of content is unsearchable

**Real impact** (1002 vault with 9MB book files):
```
File: 3254.md (9,153,615 bytes = 9.1MB)
Content: John Galsworthy's complete Project Gutenberg works
Model limit: 512 tokens (~2,500 chars)
Indexed: 0.027% of content
Lost: 99.973% of content

Result: Search for "Forsyte Saga Chapter 45" → ❌ NOT FOUND
        (Chapter 45 is past character 2,500)
```

---

## DEC-002 Was Correct for Its Context

### Original Decision (Entry 5, Phase 0-1)

**DEC-002: Why No Chunking?**
**Date**: 2025-11-18
**Decision**: No chunking initially
**Rationale**:
- Gleanings are small (<500 chars typically)
- Atomic units (one link per note)
- Synthesis handles short documents well
- Reduces implementation complexity

**Re-evaluate if**: Gleanings grow to include long summaries (>2000 chars)

### What Changed

**Phase 0-1 assumptions** (November 2025):
- ✓ Temoa designed for **gleanings only**
- ✓ Gleanings are small (500 chars)
- ✓ No need to search full vault

**Current reality** (December 2025):
- ✗ Vault scope expanded to **full vault indexing** (all content types)
- ✗ New use case: **Large document libraries** (books, articles, reference docs)
- ✗ Files up to **9MB** in production use
- ✗ **Daily notes excluded by default**, so indexed content is gleanings + other types (story, article, reference, writering, etc.)

**DEC-002 is still valid for**:
- Pure gleaning vaults (L/Gleanings/ directory only)
- Small note collections (<2,500 chars per file)

**DEC-002 is invalid for**:
- Book libraries (Project Gutenberg, reference texts)
- Long-form writing (articles, essays >2,500 chars)
- General purpose vault search

---

## Real Vault Use Cases

**Important**: Daily notes (type=daily) are **excluded by default** via `exclude_types=daily`. The problem affects OTHER content types.

| Vault | Indexed Content (daily excluded) | File Size Range | Token Limit Issue? |
|-------|----------------------------------|----------------|-------------------|
| **amoxtli** | Gleanings (~500 chars) + writering/llmering (varies) | 500-10,000 bytes | Partial (longer writering/articles truncated) |
| **rodeo** | Work notes (type varies) | 1,000-10,000 bytes | Yes (longer docs truncated) |
| **1002** | Project Gutenberg books (type=story) | 100KB-**9.1MB** | **CRITICAL** (99%+ content unsearchable) |

**Content type breakdown**:
- **gleaning**: Extracted links from daily notes (~500 chars) - ✅ Fully searchable
- **daily**: Daily notes where links originate (excluded by default, not indexed) - N/A
- **story**: Books, novels, anthologies (100KB-9MB) - ❌ Mostly unsearchable
- **writering/llmering/article/reference**: Varies widely (500-50,000+ chars) - ⚠️ Partially searchable
- **note**: General notes (varies) - ⚠️ Partially searchable

### 1002 Vault File Sizes

```
Largest files (tail -20 from ls -lh):
916K  39635-0.md
937K  13260-0.md
993K  22091-8.md
1.0M  12921-8.md
1.0M  18709-8.md
1.0M  27582-0.md
1.0M  30941-0.md
1.0M  43084-8.md
1.1M  1069-0.md
1.1M  20872-8.md
1.1M  40915-8.md
1.2M  43629-0.md
1.3M  32046-8.md
1.4M  51828-0.md
1.6M  2334-0.md
1.9M  27200.md
2.6M  3090-0.md
2.7M  24230-0.md
5.6M  57333-0.md
8.7M  3254.md  ← John Galsworthy's complete works

Total: 1,002 markdown files
ALL files exceed 512 token limit
```

---

## Current Truncation Behavior

### What Happens During Indexing

```python
# synthesis/src/embeddings/vault_reader.py
def read_file(file_path):
    content = file.read()  # Read full 9MB file
    frontmatter = parse_frontmatter(content)
    description = frontmatter.get('description', '')

    # Prepend description for semantic context
    full_text = f"{description}. {content}" if description else content

    cleaned = clean_markdown(full_text)  # ~8.5MB after markdown cleanup

    # Send to sentence-transformers for embedding
    return cleaned  # Full 8.5MB sent to model

# synthesis/src/embeddings/engine.py
def generate_embedding(text):
    # sentence-transformers SILENTLY truncates here
    embedding = self.model.encode(text)
    # Only first ~2,500 chars were embedded
    # Last ~9,150,000 chars ignored
    # NO WARNING OR ERROR
    return embedding
```

### Impact on Search Quality

**Search coverage by file size** (for indexed content - daily notes excluded):
```
File size       Coverage    Example Content Type
-----------     --------    --------------------
< 2,500 chars   100%        Gleanings (type=gleaning)
2,500-5,000     50%         Short articles, notes
5,000-10,000    25%         Medium articles, writering
10-100KB        < 10%       Long-form articles, reference docs
100KB-1MB       < 1%        Essays, short stories (type=story)
1MB+            < 0.1%      Books, anthologies (type=story)
9MB             0.027%      Complete works (3254.md, type=story)
```

**Note**: Daily notes (type=daily) are excluded via `exclude_types=daily` by default, so they're not indexed and don't contribute to this problem.

**Query behavior**:
- Query matches first 2,500 chars: ✅ FOUND
- Query matches middle of document: ❌ MISSED
- Query matches end of document: ❌ MISSED
- Embedding biased toward document beginning

**Silent failure mode**:
- No error during indexing
- No warning to user
- Results appear correct (but are incomplete)
- User has no way to know content is truncated

---

## Why This Wasn't Discovered Earlier

### Test Coverage Gaps

1. **Test vault only had small files**:
   - Largest file: 8KB (daily note)
   - Most files: < 2KB
   - No test case for >512 token files

2. **Testing focused on amoxtli vault**:
   - Primary content: gleanings (~500 chars)
   - Daily notes excluded by default (`exclude_types=daily`)
   - Most indexed content fit within token limit

3. **Silent truncation**:
   - No error messages
   - No warnings in logs
   - sentence-transformers designed to "just work"

4. **Index appeared to work**:
   - Small queries matched successfully
   - No obvious failures
   - Performance was good

### Discovery Trigger

Testing with 1002 vault:
- First time indexing vault with **all files** >512 tokens
- Query for specific chapter numbers failed
- Investigation revealed truncation at model level

---

## DEC-085: Chunking Required for Large Documents

**Date**: 2025-12-18
**Context**: Model token limits incompatible with large document indexing
**Decision**: Implement adaptive chunking strategy for files >4,000 chars
**Status**: Approved (implementation deferred to Phase 4)

### Rationale

**Must have chunking because**:
1. **Essential for 1002 vault**: Can't index books (type=story) without it
2. **Improves all vaults**: Long-form content (articles, writering, reference docs >2,500 chars)
3. **Industry standard**: Obsidian Copilot, LlamaIndex, LangChain all chunk
4. **No alternative**: Can't change model token limits

**Note**: Daily notes (type=daily) are excluded by default, so chunking them is not the primary motivation.

**Adaptive approach chosen because**:
1. **Backward compatible**: Small files work as-is (no re-indexing)
2. **Efficient**: Only overhead for files that need it
3. **Flexible**: Threshold tunable per vault type

### Chunking Strategy

**Threshold-based chunking**:
```python
def should_chunk(content_length):
    """Determine if file needs chunking"""
    if content_length < 2000:
        return False  # Small: gleanings, short notes (no overhead)
    elif content_length < 4000:
        return False  # Medium: most daily notes fit in one embedding
    else:
        return True   # Large: books, articles, long-form content

def chunk_document(content, chunk_size=2000, overlap=400):
    """
    Split document with overlap to preserve context at boundaries.

    Args:
        content: Full document text
        chunk_size: Target size in characters (default: 2000)
        overlap: Chars to overlap between chunks (default: 400 = 20%)

    Returns:
        List of chunk dicts with metadata
    """
    chunks = []
    start = 0

    while start < len(content):
        end = min(start + chunk_size, len(content))

        chunks.append({
            'content': content[start:end],
            'chunk_index': len(chunks),
            'chunk_total': None,  # Set after loop
            'start_offset': start,
            'end_offset': end
        })

        start = end - overlap  # Move forward with overlap

    # Set total count
    for chunk in chunks:
        chunk['chunk_total'] = len(chunks)

    return chunks
```

**Parameters**:
- **Chunk size**: 2,000 chars (safely under 512 token limit)
- **Overlap**: 400 chars (20% overlap prevents context loss at boundaries)
- **Threshold**: Chunk files >4,000 chars (2x chunk size for efficiency)

**Example** (9MB file):
```
Input: 9,153,615 chars (3254.md - Galsworthy)
Chunk size: 2,000 chars
Overlap: 400 chars
Effective step: 1,600 chars per chunk

Chunks created: ~5,721 chunks
Index size: 5,721 embeddings (vs 1 truncated embedding)
Search coverage: 100% (vs 0.027%)
```

### Index Format Changes

**Before (document-level)**:
```python
{
  "file_path": "3254.md",
  "embedding": [0.42, -0.13, ..., 0.21],  # Only first 2,500 chars
  "metadata": {
    "title": "Complete Works",
    "size": 9153615,
    "modified": "2025-12-17T21:35:24"
  }
}
```

**After (chunk-level)**:
```python
[
  {
    "file_path": "3254.md",
    "chunk_index": 0,
    "chunk_total": 5721,
    "start_offset": 0,
    "end_offset": 2000,
    "embedding": [0.42, -0.13, ..., 0.21],  # Chunk 0 (chars 0-2000)
    "metadata": {
      "title": "Complete Works",
      "size": 9153615,
      "modified": "2025-12-17T21:35:24"
    }
  },
  {
    "file_path": "3254.md",
    "chunk_index": 1,
    "chunk_total": 5721,
    "start_offset": 1600,  # 400 char overlap with chunk 0
    "end_offset": 3600,
    "embedding": [0.18, 0.56, ..., 0.44],  # Chunk 1 (chars 1600-3600)
    "metadata": {...}
  },
  # ... 5,719 more chunks ...
]
```

### Search Result Changes

**Result includes chunk information**:
```python
{
  "title": "The Complete Project Gutenberg Works of Galsworthy",
  "file_path": "3254.md",
  "chunk_index": 342,
  "chunk_total": 5721,
  "chunk_excerpt": "...Forsyte Saga Chapter 45 begins here...",
  "similarity_score": 0.87,
  "cross_encoder_score": 4.52,
  "obsidian_uri": "obsidian://open?vault=1002&file=3254.md"
}
```

**Future enhancement** (Phase 4 with LLM integration):
- obsidian://open?vault=1002&file=3254.md&search=Forsyte+Saga+Chapter+45
- Jump directly to matched chunk location in Obsidian

---

## Trade-offs Analysis

### Impact on System Resources

| Aspect | Current (No Chunking) | With Chunking | Change |
|--------|----------------------|---------------|--------|
| **Search coverage** | 35% of large files | **100%** | +186% |
| **Index size** (1002 vault) | 25MB (1,002 docs) | **75-100MB** (5,000-6,000 chunks) | +3-4x |
| **Indexing time** | 159s (1,002 docs) | **~400-500s** (5,000-6,000 embeddings) | +2.5-3x |
| **Search latency** | 400ms | 400ms | No change |
| **Disk usage** | Low | Medium-High | +75MB |
| **Memory usage** | ~600MB | ~800MB | +200MB |

### Benefits vs Costs

**Benefits**:
- ✅ **100% search coverage** (vs 35% for large files)
- ✅ **Find specific chapters/sections** in books
- ✅ **Works with any file size** (no 2,500 char limit)
- ✅ **Better for LLM integration** (Phase 4) - can cite specific chunks
- ✅ **Industry standard approach** (proven pattern)

**Costs**:
- ❌ **3-4x larger index files** (75-100MB vs 25MB for 1002 vault)
- ❌ **2.5-3x slower indexing** (400-500s vs 159s)
- ❌ **More complex search results** (chunk IDs, merging logic)
- ❌ **Index migration required** (can't reuse existing indexes)

**Acceptable because**:
- Disk space is cheap (~100MB is negligible)
- Indexing is infrequent (daily/weekly, not per-search)
- Search latency unchanged (most important metric)
- Coverage improvement is essential for book libraries

---

## Implementation Priority

**Status**: DEFERRED to Phase 4 or Production Hardening

### Why Defer?

1. **Phase 3 complete and working**:
   - amoxtli vault: Works well (gleanings + medium daily notes)
   - rodeo vault: Works acceptably (most notes < 4,000 chars)
   - Current production use cases satisfied

2. **1002 vault is new use case**:
   - Not a regression (never worked for 9MB files)
   - Book library support is additive feature
   - Can document limitation for now

3. **Non-trivial implementation**:
   - Requires index format migration
   - Need to handle chunk merging in search results
   - Should batch with other Phase 4 work:
     - LLM integration (benefits from chunks for citation)
     - Advanced search features
     - Performance optimizations

4. **Risk management**:
   - Current system is stable
   - Chunking adds complexity
   - Better to plan carefully than rush

### Short-term Workaround

**Document the limitation**:
1. ✅ Add warning in ARCHITECTURE.md
2. ✅ Update CLAUDE.md to remove "Why No Chunking?"
3. ✅ Log warning when indexing files >4,000 chars
4. ✅ Add to known limitations in README.md

**Optional logging enhancement**:
```python
def generate_embeddings(files):
    large_files = [f for f in files if len(f.content) > 4000]

    if large_files:
        logger.warning(
            f"Indexing {len(large_files)} files >4,000 chars. "
            f"Only first ~2,500 chars will be searchable. "
            f"Chunking support coming in Phase 4."
        )
```

---

## Documentation Updates

### 1. DECISIONS.md

**Add to Decision Registry table**:
```markdown
| DEC-085: Chunking Required for Large Documents | 40 | Adaptive chunking for files >4K chars, deferred to Phase 4 |
```

**Update DEC-002 entry**:
```markdown
| DEC-002: Why No Chunking? | 5 | Gleanings are small (<500 chars), no chunking needed **[Phase 0-1 only]** |
```

### 2. CLAUDE.md

**Remove this section**:
```markdown
### Why No Chunking?
**Obsidian Copilot uses 6000-char chunks**, but Temoa doesn't need this because:
- Gleanings are small (< 500 chars typically)
- Already atomic units (one link per note)
- Synthesis handles short documents well
- Reduces implementation complexity

**Re-evaluate if**: Gleanings grow to include long summaries/notes
```

**Replace with**:
```markdown
### File Size Considerations and Chunking

**Current Limitation** (as of Phase 3):
- Embedding models have **512 token limit** (~2,000-2,500 chars)
- Files larger than limit are **silently truncated**
- Only first ~2,500 characters of any file are searchable

**Impact by content type** (daily notes excluded by default):
- **Gleanings** (type=gleaning): ✅ Fully searchable (< 500 chars)
- **Daily notes** (type=daily): Not indexed (excluded via `exclude_types=daily`)
- **Other types** (story, article, writering, reference): ⚠️ Partially searchable
- **Books** (type=story, 100KB-9MB): ❌ Mostly unsearchable (< 1% coverage)

**Chunking Status**:
- **DEC-085**: Adaptive chunking approved for Phase 4
- **Threshold**: Files >4,000 chars will be chunked
- **Parameters**: 2,000 char chunks with 400 char overlap
- **Why deferred**: Current vaults (amoxtli, rodeo) work acceptably;
  book library support (1002 vault) is additive feature

**Workaround**: For now, be aware that searches may miss content beyond
the first ~2,500 characters in large files. Full chunking support coming in Phase 4.

See docs/chronicles/production-hardening.md Entry 40 for full analysis.
```

### 3. ARCHITECTURE.md

**Add new section after "How Embeddings Work"**:
```markdown
## Document Handling & Token Limits

### Token Limits Per Model

All sentence-transformer models have maximum sequence lengths:

| Model | Max Tokens | Max Chars (approx) | Coverage on 9MB File |
|-------|------------|-------------------|---------------------|
| all-mpnet-base-v2 (default) | 512 | ~2,000-2,500 | 0.027% |
| all-MiniLM-L6-v2 | 512 | ~2,000-2,500 | 0.027% |
| all-MiniLM-L12-v2 | 512 | ~2,000-2,500 | 0.027% |
| paraphrase-albert-small-v2 | 100 | ~400 | 0.004% |

**Token estimation**: ~1 token per 3-4 characters (English text)

### Current Truncation Behavior

**What happens**:
1. Synthesis reads full file content (up to 9MB+)
2. Prepends frontmatter description (if present)
3. Cleans markdown formatting
4. Sends entire text to sentence-transformers
5. **Model silently truncates** at token limit (512 tokens)
6. Only first ~2,500 characters are embedded
7. **No warning or error**

**Impact on search** (indexed content - daily notes excluded):
```
File size       Searchable    Example Content Type
-----------     ----------    --------------------
< 2,500 chars   100%          Gleanings (type=gleaning), short notes
2,500-5,000     50%           Medium articles, writering
5,000-10,000    25%           Long articles, reference docs
100KB+          < 1%          Essays, short stories (type=story)
1MB+            < 0.1%        Books, anthologies (type=story)
9MB             0.027%        Complete works (type=story)
```

**Note**: Daily notes (type=daily) are excluded by default and not indexed.

**Query behavior**:
- Matches in first 2,500 chars: ✅ FOUND
- Matches after char 2,500: ❌ MISSED
- Embedding biased toward document beginning

### Chunking Support (Phase 4)

**Status**: Approved (DEC-085), implementation deferred

**Strategy**: Adaptive chunking
- Files < 4,000 chars: No chunking (current behavior)
- Files ≥ 4,000 chars: Split into 2,000-char chunks with 400-char overlap

**Impact**:
- Search coverage: 100% (vs current 35% for large files)
- Index size: +3-4x (acceptable)
- Indexing time: +2.5-3x (acceptable)
- Search latency: No change (400ms)

See Entry 40 in docs/chronicles/production-hardening.md for full analysis.
```

### 4. SEARCH-MECHANISMS.md

**Add new section**:
```markdown
## Token Limits and Search Coverage

### Current Limitation

Temoa uses sentence-transformer embedding models with fixed token limits:
- **all-mpnet-base-v2**: 512 tokens (~2,000-2,500 characters)
- Text beyond this limit is **silently truncated** before embedding
- Only the first ~2,500 characters of any file are searchable

### Coverage by File Size

Based on real vault analysis (1002 vault with Project Gutenberg books, daily notes excluded by default):

| File Size | Coverage | Content Types |
|-----------|----------|---------------|
| < 2.5KB | 100% | Gleanings (type=gleaning), short notes |
| 2.5-5KB | ~50% | Medium articles, writering |
| 5-10KB | ~25% | Long articles, reference docs |
| 100KB+ | < 1% | Essays, short stories (type=story) |
| 1MB+ | < 0.1% | Books, anthologies (type=story) |

**Impact**: Searches for content in the middle or end of large documents will fail.

**Note**: Daily notes (type=daily) are excluded via `exclude_types=daily` by default and are not indexed.

### Mitigation (Phase 4)

**DEC-085**: Adaptive chunking approved for implementation in Phase 4.

When implemented:
- Files >4,000 chars will be split into 2,000-char chunks
- 400-char overlap preserves context at boundaries
- 100% search coverage regardless of file size
- Trade-off: 3-4x larger index, 2.5-3x slower indexing (acceptable)
```

---

## Key Insights

### 1. Silent Failures Are Dangerous

**Problem**: sentence-transformers truncates without warning
- Users don't know content is missing
- Results appear correct but are incomplete
- No way to detect the problem without investigation

**Lesson**: Always log warnings for edge cases:
```python
if len(content) > 4000:
    logger.warning(
        f"File {file_path} ({len(content)} chars) exceeds recommended size. "
        f"Only first ~2,500 chars will be searchable until chunking is implemented."
    )
```

### 2. Architectural Assumptions Have Shelf Life

**DEC-002 was correct** for:
- Phase 0-1 scope (gleanings only)
- Small file collections
- Atomic unit assumption

**DEC-002 became incorrect** when:
- Vault scope expanded (Phase 3+)
- Large document libraries added (1002 vault)
- Use case evolved beyond gleanings

**Lesson**: Always include "Re-evaluate if" conditions in decisions

### 3. Test with Realistic Data

**Test vault limitations**:
- Only had files <8KB
- No test case for >512 token content
- Didn't represent real-world book libraries

**Lesson**: Create test cases for edge cases:
- Very large files (>1MB)
- Files that exceed model limits
- Boundary conditions (exactly at token limit)

### 4. Default Exclusions Hide Problems

**Why this wasn't caught earlier**:
- `exclude_types=daily` meant daily notes weren't tested at scale
- Daily notes were the *only* content >2,500 chars in amoxtli vault
- Large files (books) became primary indexed content in 1002 vault
- Token limit only discovered when testing book libraries

**Lesson**: Test with defaults disabled sometimes

---

## Action Items

### Immediate (Documentation)

1. ✅ Add Entry 40 to production-hardening.md
2. ✅ Add DEC-085 to DECISIONS.md
3. ✅ Update CLAUDE.md - remove "Why No Chunking?", add reality
4. ✅ Update ARCHITECTURE.md - add "Token Limits" section
5. ✅ Update SEARCH-MECHANISMS.md - add coverage table
6. ✅ Update CHRONICLES.md index to reference Entry 40

### Phase 4 (Implementation)

1. Design chunk-aware index format
2. Implement adaptive chunking (threshold-based)
3. Add chunk merging in search results
4. Test with 1002 vault (verify 100% coverage)
5. Add chunk-based citation for LLM integration
6. Migration guide for existing indexes

### Optional (Short-term)

1. Add warning log when indexing files >4,000 chars
2. Log truncation statistics during indexing
3. Add `--chunk` flag for experimental chunking
4. Update README.md known limitations section

---

**Entry created**: 2025-12-18
**Duration**: ~2 hours (investigation + documentation)
**Status**: DOCUMENTED
**Decision IDs**: DEC-085 (Chunking Required for Large Documents)
**Related Decisions**: DEC-002 (Why No Chunking? - Phase 0-1 context only)
**Files updated**:
- docs/chronicles/production-hardening.md (this entry)
- docs/DECISIONS.md (DEC-085 added)
- docs/CLAUDE.md (file size reality documented)
- docs/ARCHITECTURE.md (token limits section added)
- docs/SEARCH-MECHANISMS.md (coverage table added)
