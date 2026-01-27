# Phase 3.5: Specialized Search Modes

**Status**: PLANNING 🔵
**Branch**: TBD (will create `phase-3.5-search-modes`)
**Duration**: 10-14 days
**Version**: 0.7.0

---

## Overview

**Goal**: Enable optimized search experiences for different content types and use cases through user-selectable search profiles, adaptive chunking, and metadata-aware ranking.

**Problem**: Current search treats all content uniformly. Searching for GitHub repos needs different weighting than searching daily notes or reading long articles. Large documents (>2,500 chars) are silently truncated, making most content unsearchable.

**Solution**:
1. **Search Profiles** - Pre-configured modes optimized for different use cases (Repos, Recent Work, Deep Reading, Keywords)
2. **Adaptive Chunking** - Split large documents into searchable chunks with overlap
3. **Metadata-Based Boosting** - Use GitHub metadata (stars, topics, language) in ranking
4. **Smart Recommendations** - Auto-suggest which profile to use based on query/filters

---

## Table of Contents

- [Motivation](#motivation)
- [Architecture](#architecture)
  - [Search Profiles System](#search-profiles-system)
  - [Chunking System](#chunking-system)
  - [Metadata Boosting](#metadata-boosting)
  - [Profile Recommendation](#profile-recommendation)
- [Implementation Plan](#implementation-plan)
- [Configuration](#configuration)
- [UI/UX Changes](#uiux-changes)
- [Testing Strategy](#testing-strategy)
- [Migration Path](#migration-path)
- [Success Criteria](#success-criteria)

---

## Motivation

### Use Cases

**1. Repo Search** ("Find that Python library I saved")
- **Content**: GitHub gleanings with rich metadata
- **Need**: Keyword-heavy matching, boost by stars/topics/language
- **Current Problem**: Semantic search dilutes exact matches, metadata ignored
- **Optimal**: 70% BM25, 30% semantic, boost popular repos

**2. Recent Work** ("What did I write this week?")
- **Content**: Daily notes, recent articles/notes
- **Need**: Heavy time-weighting, filter to recent only
- **Current Problem**: 90-day half-life too long, old stuff clutters results
- **Optimal**: 7-day half-life, exclude content >90 days old

**3. Deep Reading** ("Find where I wrote about X concept")
- **Content**: Long-form articles, essays, book notes
- **Need**: Semantic understanding, chunking for long docs, precision ranking
- **Current Problem**: Long docs truncated at 2,500 chars, most content unsearchable
- **Optimal**: 80% semantic, chunking enabled, cross-encoder re-ranking

**4. Keyword Search** ("Find 'React hooks' exactly")
- **Content**: Technical notes, API references, framework docs
- **Need**: Exact keyword matching, minimal semantic interpretation
- **Current Problem**: Semantic search finds conceptually related but not exact matches
- **Optimal**: 80% BM25, 20% semantic, skip cross-encoder for speed

### Current Limitations

**Silent Truncation** (Critical Issue):
- Files >2,500 chars → only first 2,500 searchable
- 9MB book file → 0.027% coverage
- No warning to user
- **Impact**: 1002 vault (books), long articles, reference docs mostly unsearchable

**One-Size-Fits-All**:
- Same weights for all queries
- Same time-decay for all content types
- Metadata (GitHub stars, topics) ignored
- No way to optimize for specific use cases

---

## Architecture

### Search Profiles System

**Core Concept**: Pre-configured search parameter bundles optimized for specific use cases.

#### Profile Definition

```python
# src/temoa/search_profiles.py

@dataclass
class SearchProfile:
    """Configuration for a search mode"""
    name: str
    display_name: str
    description: str

    # Core search weights
    hybrid_weight: float  # 0.0-1.0, where 0=pure BM25, 1=pure semantic
    bm25_boost: float = 1.0  # Multiplier for BM25 scores

    # Metadata boosting
    metadata_boost: Dict[str, Any] = field(default_factory=dict)

    # Time weighting
    time_decay_config: Optional[Dict[str, Any]] = None
    max_age_days: Optional[int] = None  # Filter out older content

    # Quality/speed tradeoffs
    cross_encoder_enabled: bool = True
    query_expansion_enabled: bool = False

    # Content filtering
    default_include_types: Optional[List[str]] = None
    default_exclude_types: Optional[List[str]] = None

    # Chunking
    chunking_enabled: bool = True
    chunk_size: int = 2000
    chunk_overlap: int = 400

    # Result presentation
    show_chunk_context: bool = False
    max_results_per_file: int = 1  # For chunked results


# Built-in profiles
SEARCH_PROFILES = {
    "repos": SearchProfile(
        name="repos",
        display_name="Repos & Tech",
        description="Find GitHub repos, libraries, tools by keywords and popularity",
        hybrid_weight=0.3,  # 30% semantic, 70% BM25
        bm25_boost=2.0,
        metadata_boost={
            "github_stars": {
                "enabled": True,
                "scale": "log",  # log(stars) for diminishing returns
                "max_boost": 0.5  # Up to 50% boost
            },
            "github_topics": {
                "enabled": True,
                "match_boost": 3.0  # 3x boost when query matches topic
            },
            "github_language": {
                "enabled": True,
                "match_boost": 1.5  # 1.5x boost when language matches query
            }
        },
        time_decay_config=None,  # Recency doesn't matter for repos
        cross_encoder_enabled=False,  # Speed over precision
        default_include_types=["gleaning"],
        chunking_enabled=False  # Gleanings are small
    ),

    "recent": SearchProfile(
        name="recent",
        display_name="Recent Work",
        description="Find what you wrote or saved recently (last 90 days)",
        hybrid_weight=0.5,  # Balanced
        time_decay_config={
            "half_life_days": 7,  # Aggressive - prefer this week
            "max_boost": 0.5  # Up to 50% boost for today
        },
        max_age_days=90,  # Hard cutoff - ignore older content
        default_include_types=["daily", "note", "writering"],
        cross_encoder_enabled=True,
        chunking_enabled=True  # Daily notes can be long
    ),

    "deep": SearchProfile(
        name="deep",
        display_name="Deep Reading",
        description="Search long-form content with full context (articles, books, essays)",
        hybrid_weight=0.8,  # 80% semantic, 20% BM25
        cross_encoder_enabled=True,
        query_expansion_enabled=False,
        chunking_enabled=True,
        chunk_size=2000,
        chunk_overlap=400,
        show_chunk_context=True,
        max_results_per_file=3,  # Show top 3 chunks per file
        default_exclude_types=["daily", "gleaning"]  # Focus on long content
    ),

    "keywords": SearchProfile(
        name="keywords",
        display_name="Keyword Search",
        description="Exact keyword matching for technical terms, names, phrases",
        hybrid_weight=0.2,  # 20% semantic, 80% BM25
        bm25_boost=1.5,
        cross_encoder_enabled=False,  # Speed
        query_expansion_enabled=False,
        chunking_enabled=True
    ),

    "default": SearchProfile(
        name="default",
        display_name="Balanced",
        description="General-purpose search (current behavior)",
        hybrid_weight=0.5,  # 50/50 hybrid
        cross_encoder_enabled=True,
        time_decay_config={
            "half_life_days": 90,
            "max_boost": 0.2
        },
        default_exclude_types=["daily"],
        chunking_enabled=True
    )
}
```

#### Profile Application

```python
# src/temoa/server.py

@app.get("/search")
async def search(
    q: str,
    profile: str = "default",  # NEW: profile parameter
    vault: Optional[str] = None,
    limit: int = 10,
    # Individual overrides still allowed
    hybrid: Optional[bool] = None,
    rerank: Optional[bool] = None,
    # ... other parameters
):
    """
    Search with profile support.

    Profile parameter takes precedence, but individual parameters
    can override specific profile settings.
    """
    # Load profile
    search_profile = SEARCH_PROFILES.get(profile, SEARCH_PROFILES["default"])

    # Apply profile settings (with parameter overrides)
    hybrid_mode = hybrid if hybrid is not None else (search_profile.hybrid_weight > 0)
    use_reranking = rerank if rerank is not None else search_profile.cross_encoder_enabled

    # Apply metadata boosting if profile specifies it
    if search_profile.metadata_boost:
        results = await search_with_metadata_boost(
            query=q,
            profile=search_profile,
            # ...
        )

    # Apply max age filter if specified
    if search_profile.max_age_days:
        results = filter_by_age(results, max_days=search_profile.max_age_days)

    # ... rest of search pipeline
```

### Chunking System

**Implementation**: Extend Synthesis vault reader to support chunking.

#### Chunking Logic

```python
# synthesis/src/embeddings/chunking.py (NEW FILE)

from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Chunk:
    """Represents a document chunk"""
    content: str
    chunk_index: int
    chunk_total: int
    start_offset: int
    end_offset: int
    file_path: str
    metadata: Dict[str, Any]

def should_chunk(content: str, threshold: int = 4000) -> bool:
    """
    Determine if content needs chunking.

    Args:
        content: Full document text
        threshold: Minimum chars before chunking (default: 4000)

    Returns:
        True if content exceeds threshold
    """
    return len(content) >= threshold

def chunk_document(
    content: str,
    file_path: str,
    metadata: Dict[str, Any],
    chunk_size: int = 2000,
    overlap: int = 400
) -> List[Chunk]:
    """
    Split document into overlapping chunks.

    Args:
        content: Full document text
        file_path: Path to source file
        metadata: Document metadata (title, tags, etc.)
        chunk_size: Target chunk size in chars (default: 2000)
        overlap: Overlap between chunks in chars (default: 400)

    Returns:
        List of Chunk objects
    """
    if not should_chunk(content):
        # Return single chunk for small documents
        return [Chunk(
            content=content,
            chunk_index=0,
            chunk_total=1,
            start_offset=0,
            end_offset=len(content),
            file_path=file_path,
            metadata=metadata
        )]

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(content):
        end = min(start + chunk_size, len(content))

        chunks.append(Chunk(
            content=content[start:end],
            chunk_index=len(chunks),
            chunk_total=0,  # Set after loop
            start_offset=start,
            end_offset=end,
            file_path=file_path,
            metadata=metadata.copy()
        ))

        if end >= len(content):
            break

        start += step

    # Update chunk totals
    total = len(chunks)
    for chunk in chunks:
        chunk.chunk_total = total

    return chunks
```

#### Index Format Update

```python
# synthesis/src/embeddings/vault_reader.py

def index_vault(vault_path: str, enable_chunking: bool = True) -> List[Dict]:
    """
    Index vault with optional chunking support.

    Returns:
        List of indexed entries (one per chunk or one per file)
    """
    entries = []

    for file_path in find_markdown_files(vault_path):
        content, metadata = read_file_with_frontmatter(file_path)

        if enable_chunking and should_chunk(content):
            # Chunk large files
            chunks = chunk_document(
                content=content,
                file_path=file_path,
                metadata=metadata
            )

            for chunk in chunks:
                embedding = generate_embedding(chunk.content)

                entries.append({
                    "file_path": chunk.file_path,
                    "embedding": embedding,
                    "content": chunk.content,  # Store chunk content
                    "chunk_index": chunk.chunk_index,
                    "chunk_total": chunk.chunk_total,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "metadata": chunk.metadata
                })
        else:
            # Small file - index as single entry
            embedding = generate_embedding(content)

            entries.append({
                "file_path": file_path,
                "embedding": embedding,
                "content": content,
                "chunk_index": 0,
                "chunk_total": 1,
                "start_offset": 0,
                "end_offset": len(content),
                "metadata": metadata
            })

    return entries
```

#### Search Result Handling

```python
# src/temoa/synthesis.py

def deduplicate_chunks(results: List[Dict], max_per_file: int = 1) -> List[Dict]:
    """
    Merge multiple chunk matches from same file.

    Args:
        results: Raw search results (may include multiple chunks per file)
        max_per_file: Maximum chunks to return per file

    Returns:
        Deduplicated results with chunk context
    """
    by_file = {}

    for result in results:
        file_path = result["file_path"]

        if file_path not in by_file:
            by_file[file_path] = []

        by_file[file_path].append(result)

    merged = []

    for file_path, chunks in by_file.items():
        # Sort chunks by score (descending)
        chunks.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        # Take top N chunks
        top_chunks = chunks[:max_per_file]

        if len(top_chunks) == 1:
            # Single chunk - return as-is
            merged.append(top_chunks[0])
        else:
            # Multiple chunks - merge with context
            merged.append({
                **top_chunks[0],  # Use best chunk as base
                "matched_chunks": [
                    {
                        "chunk_index": c["chunk_index"],
                        "score": c.get("similarity_score", 0),
                        "excerpt": c.get("content", "")[:200] + "..."
                    }
                    for c in top_chunks
                ],
                "total_chunks_matched": len(chunks)
            })

    return merged
```

### Metadata Boosting

**Implementation**: Boost scores based on GitHub metadata.

```python
# src/temoa/metadata_boosting.py (NEW FILE)

import math
from typing import Dict, List, Any

def apply_metadata_boosts(
    results: List[Dict],
    query: str,
    boost_config: Dict[str, Any]
) -> List[Dict]:
    """
    Apply metadata-based score boosts.

    Args:
        results: Search results with metadata
        query: Original search query
        boost_config: Boost configuration from search profile

    Returns:
        Results with boosted scores
    """
    boosted = []
    query_lower = query.lower()
    query_tokens = set(query_lower.split())

    for result in results:
        metadata = result.get("metadata", {})
        score = result.get("rrf_score", result.get("similarity_score", 0))
        boost_factors = []

        # GitHub stars boost (logarithmic scale)
        if boost_config.get("github_stars", {}).get("enabled"):
            stars = metadata.get("github_stars", 0)
            if stars > 0:
                stars_config = boost_config["github_stars"]
                max_boost = stars_config.get("max_boost", 0.5)

                # Logarithmic: log10(stars) / log10(100000) * max_boost
                # 100 stars → ~0.1x, 10k stars → ~0.4x, 100k stars → 0.5x
                normalized = min(math.log10(stars) / math.log10(100000), 1.0)
                stars_boost = normalized * max_boost
                boost_factors.append(("github_stars", stars_boost))

        # GitHub topics boost (exact match)
        if boost_config.get("github_topics", {}).get("enabled"):
            topics = metadata.get("github_topics", [])
            topics_lower = [t.lower() for t in topics]

            # Check if any query token matches any topic
            if any(token in topics_lower for token in query_tokens):
                topic_boost = boost_config["github_topics"].get("match_boost", 3.0)
                boost_factors.append(("github_topics", topic_boost - 1.0))  # -1 because we multiply

        # GitHub language boost (exact match)
        if boost_config.get("github_language", {}).get("enabled"):
            language = metadata.get("github_language", "").lower()
            if language and language in query_lower:
                lang_boost = boost_config["github_language"].get("match_boost", 1.5)
                boost_factors.append(("github_language", lang_boost - 1.0))

        # Apply boosts (multiplicative)
        total_boost = 1.0
        for name, factor in boost_factors:
            total_boost *= (1.0 + factor)

        boosted_score = score * total_boost

        boosted.append({
            **result,
            "base_score": score,
            "boosted_score": boosted_score,
            "boost_factors": dict(boost_factors) if boost_factors else {}
        })

    # Re-sort by boosted score
    boosted.sort(key=lambda x: x["boosted_score"], reverse=True)

    return boosted
```

### Profile Recommendation

**Goal**: Auto-suggest which profile to use based on query and context.

```python
# src/temoa/profile_recommender.py (NEW FILE)

from typing import Optional, List, Tuple
import re

def recommend_profile(
    query: str,
    include_types: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None
) -> Tuple[str, str]:
    """
    Recommend search profile based on query and filters.

    Args:
        query: Search query
        include_types: Type filter (if any)
        exclude_types: Excluded types (if any)

    Returns:
        (profile_name, reason)
    """
    query_lower = query.lower()

    # Check for type-based recommendations
    if include_types:
        if "gleaning" in include_types:
            return ("repos", "Searching gleanings - optimized for repos/links")
        if "daily" in include_types:
            return ("recent", "Searching daily notes - optimized for recent content")

    # Check for time-related keywords
    time_keywords = ["recent", "today", "yesterday", "this week", "last week"]
    if any(kw in query_lower for kw in time_keywords):
        return ("recent", "Time-related query detected - try Recent Work mode")

    # Check for GitHub/repo keywords
    repo_keywords = ["repo", "repository", "github", "library", "package", "tool"]
    if any(kw in query_lower for kw in repo_keywords):
        return ("repos", "Repository-related query - try Repos & Tech mode")

    # Check for conceptual/reading keywords
    concept_keywords = ["about", "concept", "idea", "theory", "article", "essay"]
    if any(kw in query_lower for kw in concept_keywords):
        return ("deep", "Conceptual query - try Deep Reading mode")

    # Check for exact matching indicators (quotes, specific terms)
    if '"' in query or "exact" in query_lower:
        return ("keywords", "Exact match needed - try Keyword Search mode")

    # Check for programming language/framework names
    tech_patterns = [
        r'\b(python|javascript|react|vue|rust|go|java)\b',
        r'\b(api|library|framework|package)\b'
    ]
    if any(re.search(pattern, query_lower) for pattern in tech_patterns):
        return ("repos", "Technical query - try Repos & Tech mode")

    # Default: balanced search
    return ("default", "")
```

---

## Implementation Plan

### Phase 3.5.1: Core Profile System (3-4 days)

**Goal**: Implement search profile infrastructure.

- [ ] Create `src/temoa/search_profiles.py`
  - [ ] `SearchProfile` dataclass
  - [ ] Built-in profile definitions (repos, recent, deep, keywords, default)
  - [ ] Profile registry and lookup functions
- [ ] Update `src/temoa/server.py`
  - [ ] Add `profile` parameter to `/search` endpoint
  - [ ] Apply profile settings to search pipeline
  - [ ] Support parameter overrides
- [ ] Update `src/temoa/cli.py`
  - [ ] Add `--profile` flag to search command
  - [ ] List available profiles with `temoa profiles` command
- [ ] Add configuration support
  - [ ] Allow custom profiles in `config.json`
  - [ ] Profile-specific overrides per vault
- [ ] Tests
  - [ ] Unit tests for profile loading
  - [ ] Integration tests for each profile
  - [ ] Parameter override tests

**Deliverable**: `/search?profile=repos` works with correct weightings

### Phase 3.5.2: Adaptive Chunking (4-5 days)

**Goal**: Implement chunking for large documents.

- [ ] Create `synthesis/src/embeddings/chunking.py`
  - [ ] `should_chunk(content, threshold)` function
  - [ ] `chunk_document(content, chunk_size, overlap)` function
  - [ ] `Chunk` dataclass with metadata
- [ ] Update `synthesis/src/embeddings/vault_reader.py`
  - [ ] Integrate chunking into indexing pipeline
  - [ ] Store chunk metadata in index
  - [ ] Backward compatibility for small files
- [ ] Update `src/temoa/synthesis.py`
  - [ ] Handle chunked search results
  - [ ] `deduplicate_chunks()` function
  - [ ] Merge multiple chunk matches per file
- [ ] Update index format
  - [ ] Add chunk fields to index schema
  - [ ] Migration for existing indexes (detect and warn)
- [ ] Tests
  - [ ] Unit tests for chunking logic
  - [ ] Test with 1002 vault (large books)
  - [ ] Verify 100% coverage for large files
  - [ ] Performance benchmarks

**Deliverable**: 9MB book file fully searchable, chunked results displayed

### Phase 3.5.3: Metadata Boosting (2 days)

**Goal**: Boost results based on GitHub metadata.

- [ ] Create `src/temoa/metadata_boosting.py`
  - [ ] `apply_metadata_boosts()` function
  - [ ] GitHub stars boost (logarithmic)
  - [ ] GitHub topics boost (exact match)
  - [ ] GitHub language boost
- [ ] Integrate with search pipeline
  - [ ] Apply boosts when profile specifies it
  - [ ] Include boost factors in results
- [ ] Tests
  - [ ] Unit tests for boost calculations
  - [ ] Verify popular repos rank higher
  - [ ] Topic/language matching tests

**Deliverable**: "python library" ranks high-star Python repos first

### Phase 3.5.4: Profile Recommendation (1-2 days)

**Goal**: Auto-suggest optimal profile.

- [ ] Create `src/temoa/profile_recommender.py`
  - [ ] `recommend_profile()` function
  - [ ] Heuristics for query patterns
  - [ ] Type-based recommendations
- [ ] Add to API response
  - [ ] Include `recommended_profile` in search results
  - [ ] Include reason for recommendation
- [ ] Tests
  - [ ] Unit tests for recommendation logic
  - [ ] Verify recommendations for known patterns

**Deliverable**: API suggests "Try Recent Work mode" for time-related queries

### Phase 3.5.5: UI Updates (2 days)

**Goal**: Profile selector in web UI.

- [ ] Update `src/temoa/ui/search.html`
  - [ ] Add profile dropdown (repos, recent, deep, keywords, default)
  - [ ] Show recommended profile as hint
  - [ ] Persist selected profile in localStorage
  - [ ] Show active profile in UI
- [ ] Update result display
  - [ ] Show chunk context for chunked results
  - [ ] Display boost factors (GitHub stars, topics)
  - [ ] Show "matched chunks" count for multi-chunk files
- [ ] Mobile optimization
  - [ ] Profile selector works on mobile
  - [ ] Chunk excerpts don't break layout

**Deliverable**: User-friendly profile selector, chunked results display

### Phase 3.5.6: Documentation & Testing (1-2 days)

**Goal**: Comprehensive docs and validation.

- [ ] Update documentation
  - [ ] `docs/SEARCH-MECHANISMS.md` - Add chunking and profiles sections
  - [ ] `README.md` - Document profile API parameters
  - [ ] `CLAUDE.md` - Update for Phase 3.5 completion
  - [ ] Create `docs/SEARCH-PROFILES.md` - Profile guide
- [ ] Integration testing
  - [ ] Test all 5 profiles with real queries
  - [ ] Verify chunking with 1002 vault
  - [ ] Performance benchmarks
- [ ] User testing
  - [ ] Test on mobile devices
  - [ ] Validate profile recommendations
  - [ ] Gather feedback on chunk display

**Deliverable**: Complete documentation, validated system

---

## Configuration

### Config File Format

```json
{
  "vaults": [
    {
      "name": "amoxtli",
      "path": "~/Obsidian/amoxtli",
      "is_default": true,
      "default_profile": "default",
      "chunking": {
        "enabled": true,
        "threshold": 4000,
        "chunk_size": 2000,
        "overlap": 400
      }
    },
    {
      "name": "1002",
      "path": "~/Obsidian/1002",
      "default_profile": "deep",
      "chunking": {
        "enabled": true,
        "threshold": 2000,
        "chunk_size": 2000,
        "overlap": 500
      }
    }
  ],

  "search_profiles": {
    "custom_profile": {
      "display_name": "My Custom Profile",
      "description": "Custom search configuration",
      "hybrid_weight": 0.6,
      "bm25_boost": 1.2,
      "cross_encoder_enabled": true
    }
  }
}
```

### API Parameters

```
GET /search?
  q=<query>
  &profile=<repos|recent|deep|keywords|default>  # NEW: Search profile
  &vault=<name>
  &limit=<int>
  # Individual overrides (take precedence over profile)
  &hybrid=<bool>
  &rerank=<bool>
  &expand_query=<bool>
  &time_boost=<bool>
  &include_types=<csv>
  &exclude_types=<csv>
```

---

## UI/UX Changes

### Search Interface

**Before**:
```
Search: [_________________________] [Search]
        ☑ Hybrid  ☐ Expand  ☑ Rerank  ☑ Time Boost
```

**After**:
```
Search: [_________________________] Mode: [Balanced ▼] [Search]

💡 Tip: Try "Repos & Tech" mode for repository searches

Results (3 chunks from "Complete Works"):
┌─────────────────────────────────────────────────────┐
│ 📖 Complete Project Gutenberg Works of Galsworthy  │
│ Chunk 342 of 5,721 • Matched 3 chunks             │
│                                                     │
│ ...Forsyte Saga Chapter 45 begins here...         │
│                                                     │
│ ⭐ Also matched: Chunks #129, #458                 │
└─────────────────────────────────────────────────────┘
```

### Profile Dropdown

```
Mode: [ Balanced ▼ ]
      ─────────────────────────────────────────────
      ✓ Balanced         General-purpose search
      ─────────────────────────────────────────────
        Repos & Tech     GitHub repos, libraries
        Recent Work      Last 90 days only
        Deep Reading     Long articles, books
        Keyword Search   Exact matching
```

### Chunk Display

```
📖 The Complete Project Gutenberg Works of Galsworthy
   Chunk 342 of 5,721 • Similarity: 0.87 • Cross-Encoder: 4.52

   ...Forsyte Saga Chapter 45 begins here. Young Jolyon
   had been sitting in his study...

   ⭐ Also matched 2 other chunks:
      • Chunk 129 (0.82) - "...earlier reference to Forsyte..."
      • Chunk 458 (0.79) - "...later chapter continues..."
```

---

## Testing Strategy

### Unit Tests

- [ ] Profile loading and validation
- [ ] Chunking logic (boundaries, overlap)
- [ ] Metadata boost calculations
- [ ] Profile recommendation heuristics
- [ ] Chunk deduplication

### Integration Tests

- [ ] Each profile with real queries
- [ ] Chunking with 1002 vault
- [ ] Metadata boosting with GitHub gleanings
- [ ] Profile switching between searches
- [ ] Parameter overrides

### Performance Tests

**Indexing Performance** (1002 vault):
```
Without chunking: 159s (1,002 docs)
With chunking:    400-500s (5,000-6,000 chunks)
Acceptable: Yes (one-time operation)
```

**Search Performance**:
```
Target: < 2s on mobile
Expected: 400-900ms (no change from Phase 3)
Chunk dedup: < 10ms overhead
```

**Memory Usage**:
```
Current: ~800MB (single vault, no chunking)
With chunking: ~1GB (5,000 chunks)
Acceptable: Yes (still under 2GB target)
```

### Validation Queries

**Repos Profile**:
- "python machine learning library" → High-star ML repos
- "react component library" → Popular React libs
- "rust web framework" → Actix, Rocket, Axum

**Recent Profile**:
- "what did I write yesterday" → Yesterday's daily note
- "last week meeting notes" → Recent notes only

**Deep Profile**:
- "forsyte saga chapter 45" → Correct chunk in 9MB book
- "long article about zettelkasten" → Full article, not truncated

**Keywords Profile**:
- "React.useState hook" → Exact mentions
- "ObsidianURI.open" → API references

---

## Migration Path

### Index Migration

**Backward Compatibility**:
- Old indexes (document-level) still work
- New indexes include chunk metadata
- Detection: Check for `chunk_index` field
- Migration: Re-index vault with `--force`

**Migration Commands**:
```bash
# Check if vault needs re-indexing
temoa check-index --vault amoxtli

# Re-index with chunking enabled
temoa index --vault amoxtli --force --chunking

# Verify chunking coverage
temoa stats --vault amoxtli --show-chunking
```

### Config Migration

**No breaking changes**:
- Default profile is "default" (current behavior)
- All current search parameters still work
- Profile parameter is optional

---

## Success Criteria

### Functionality

- [ ] All 5 built-in profiles work correctly
- [ ] Repos mode boosts popular GitHub repos
- [ ] Recent mode finds last week's content
- [ ] Deep mode makes 9MB book fully searchable
- [ ] Keywords mode prioritizes exact matches
- [ ] Profile recommendations make sense

### Performance

- [ ] Search latency < 2s on mobile (all profiles)
- [ ] Indexing completes in acceptable time (<10 min for 1002 vault)
- [ ] Memory usage < 2GB (3-vault cache with chunking)

### UX

- [ ] Profile selector intuitive on mobile
- [ ] Chunk excerpts useful and readable
- [ ] Recommendations helpful, not annoying
- [ ] Results clearly show which profile was used

### Coverage

- [ ] 100% search coverage for large documents (verified with 1002 vault)
- [ ] Chunking works with all file sizes
- [ ] No silent truncation warnings

---

## Trade-offs

### Benefits

✅ **Specialized search experiences** - Optimized for different use cases
✅ **100% large document coverage** - No more silent truncation
✅ **Metadata-aware ranking** - Use GitHub stars/topics/language
✅ **Smart recommendations** - Guide users to best profile
✅ **Backward compatible** - Current searches still work
✅ **User control** - Profiles are suggestions, not requirements

### Costs

❌ **Larger indexes** - 3-4x size for chunked content (75-100MB for 1002 vault)
❌ **Slower indexing** - 2.5-3x time for chunked content (acceptable - infrequent operation)
❌ **More complexity** - 5 profiles to understand/maintain
❌ **UI clutter** - Additional dropdown in interface
❌ **Migration required** - Existing indexes need re-indexing for chunking

### Verdict

**Worth it** - Chunking solves critical coverage gap, profiles enable use-case optimization without forcing one-size-fits-all. Costs are acceptable (disk is cheap, indexing is infrequent, UI is manageable).

---

## Related Issues & Decisions

- **Issue #43**: Chunking implementation (DEC-085)
- **Entry 40**: Token limits and chunking discovery
- **DEC-002**: Original "no chunking" decision (still valid for small files)
- **DEC-085**: Adaptive chunking approved

---

**Created**: 2025-12-30
**Author**: Claude (Sonnet 4.5) with pborenstein
**Status**: Planning - ready for implementation
**Next**: Begin Phase 3.5.1 - Core Profile System
