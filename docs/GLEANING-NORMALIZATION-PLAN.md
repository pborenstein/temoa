# Gleaning Normalization Plan

**Created**: 2025-12-14
**Status**: Planning
**Goal**: Normalize GitHub gleaning titles/descriptions and create extensible system for other URL types

---

## Problem Statement

Currently, GitHub gleanings have verbose titles and descriptions fetched from HTML:

**Current**:
```
title: "filiksyos/gittodoc: Turn any Git repository into a documentation link."
description: "Turn any Git repository into a documentation link. - filiksyos/gittodoc"
```

**Desired**:
```
title: "filiksyos/gittodoc"
description: "Turn any Git repository into a documentation link."
```

The system should be extensible for other URL types (YouTube, Reddit, etc.) that may need similar normalization.

---

## Current State

**Stats**:
- Total gleanings with github.com: 776 files
- Files examined show pattern: `{user}/{repo}: {description}` format

**Current extraction** (`extract_gleanings.py`):
- Fetches title from HTML `<title>` tag
- Stores as-is in frontmatter
- No domain-specific processing

**Example files**:
- `686177b0642d.md` - GitHub repo with full title/description
- `b45d086505bc.md` - Non-GitHub (hollywood.computer) - OK as-is
- `ada1203750f9.md` - YouTube with generic "youtube.com" title (also needs help!)
- `41fea37fd443.md` - Reddit with "Reddit - The heart of the internet" (also needs help!)

---

## Proposed Solution

### Architecture

Create a **URL normalizer system** that applies domain-specific rules:

```
URLNormalizer
  ├─ GitHubNormalizer
  ├─ YouTubeNormalizer  (future)
  ├─ RedditNormalizer   (future)
  └─ DefaultNormalizer  (pass-through)
```

### Design Principles

1. **Registry pattern**: Normalizers register for domain patterns
2. **Extensibility**: Easy to add new normalizers
3. **Backward compatible**: Non-matching URLs pass through unchanged
4. **Testable**: Each normalizer is isolated and unit-testable
5. **Two-phase**: Extract first, normalize after (for existing files)

---

## Implementation Plan

### Phase 1: Create Normalizer Infrastructure

**File**: `src/temoa/normalizers.py` (new)

```python
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

class URLNormalizer(ABC):
    """Base class for URL normalizers."""
    
    @abstractmethod
    def matches(self, url: str) -> bool:
        """Check if this normalizer handles the URL."""
        pass
    
    @abstractmethod
    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """Normalize the title."""
        pass
    
    @abstractmethod
    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """Normalize the description."""
        pass


class GitHubNormalizer(URLNormalizer):
    """Normalize GitHub repository URLs."""
    
    def matches(self, url: str) -> bool:
        """Match github.com URLs."""
        return "github.com" in urlparse(url).netloc
    
    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """
        Extract user/repo from title.
        
        Examples:
            "user/repo: Description" -> "user/repo"
            "user/repo" -> "user/repo"
            None -> Extract from URL path
        """
        if fetched_title:
            # Split on ": " or " - " and take first part
            for sep in [": ", " - "]:
                if sep in fetched_title:
                    return fetched_title.split(sep)[0].strip()
            return fetched_title.strip()
        
        # Fallback: extract from URL
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
        return url
    
    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """
        Extract description, remove redundant repo name.
        
        Examples:
            "Description text. - user/repo" -> "Description text."
            "Description text. Contribute to user/repo..." -> "Description text."
        """
        if not fetched_description:
            return ""
        
        desc = fetched_description.strip()
        
        # Remove " - user/repo" suffix
        if " - " in desc:
            parts = desc.split(" - ")
            # Check if last part looks like user/repo
            if "/" in parts[-1]:
                desc = " - ".join(parts[:-1]).strip()
        
        # Remove "Contribute to user/repo..." suffix
        if "Contribute to " in desc:
            desc = desc.split("Contribute to ")[0].strip()
        
        return desc


class DefaultNormalizer(URLNormalizer):
    """Pass-through normalizer for unknown domains."""
    
    def matches(self, url: str) -> bool:
        """Match everything (fallback)."""
        return True
    
    def normalize_title(self, url: str, fetched_title: Optional[str]) -> str:
        """Return title as-is."""
        return fetched_title or url
    
    def normalize_description(self, url: str, fetched_description: Optional[str]) -> str:
        """Return description as-is."""
        return fetched_description or ""


class NormalizerRegistry:
    """Registry of URL normalizers."""
    
    def __init__(self):
        self.normalizers = [
            GitHubNormalizer(),
            # YouTubeNormalizer(),  # Future
            # RedditNormalizer(),   # Future
            DefaultNormalizer(),  # Always last (fallback)
        ]
    
    def get_normalizer(self, url: str) -> URLNormalizer:
        """Get the appropriate normalizer for a URL."""
        for normalizer in self.normalizers:
            if normalizer.matches(url):
                return normalizer
        return self.normalizers[-1]  # DefaultNormalizer
    
    def normalize(self, url: str, title: Optional[str], description: Optional[str]) -> tuple[str, str]:
        """
        Normalize title and description for a URL.
        
        Returns:
            (normalized_title, normalized_description)
        """
        normalizer = self.get_normalizer(url)
        norm_title = normalizer.normalize_title(url, title)
        norm_desc = normalizer.normalize_description(url, description)
        return norm_title, norm_desc
```

**Tests**: `tests/test_normalizers.py`

Test cases:
- GitHub: `user/repo: Description` -> `user/repo`, `Description`
- GitHub: `user/repo` (no description) -> `user/repo`, ``
- GitHub: URL with no title -> extract from path
- Default: Pass-through for non-GitHub URLs
- Registry: Correct normalizer selection

---

### Phase 2: Integrate with Extraction Script

**File**: `src/temoa/scripts/extract_gleanings.py`

**Changes**:

1. Import normalizers:
```python
from temoa.normalizers import NormalizerRegistry
```

2. Initialize registry in `extract_gleanings()`:
```python
normalizer_registry = NormalizerRegistry()
```

3. Apply normalization after fetching title:
```python
# In parse_gleaning() or wherever title is fetched
fetched_title = fetch_title_from_url(url) if not title else title

# NEW: Normalize based on URL domain
title, description = normalizer_registry.normalize(
    url, 
    fetched_title, 
    description
)
```

**Impact**: New extractions automatically normalized.

---

### Phase 3: Backfill Existing Gleanings

**Script**: `scripts/normalize_existing_gleanings.py`

```python
#!/usr/bin/env python3
"""
Normalize existing gleaning files.

Updates title and description in frontmatter for GitHub URLs and other
domains that benefit from normalization.

Usage:
    python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/amoxtli [--dry-run]
"""

import argparse
import frontmatter
from pathlib import Path
from temoa.normalizers import NormalizerRegistry


def normalize_gleanings(vault_path: Path, dry_run: bool = False):
    """Normalize existing gleaning files."""
    
    gleanings_dir = vault_path / "L" / "Gleanings"
    if not gleanings_dir.exists():
        print(f"Error: {gleanings_dir} does not exist")
        return
    
    registry = NormalizerRegistry()
    
    stats = {
        "total": 0,
        "normalized": 0,
        "unchanged": 0,
        "errors": 0,
    }
    
    for gleaning_file in sorted(gleanings_dir.glob("*.md")):
        stats["total"] += 1
        
        try:
            # Read frontmatter
            post = frontmatter.load(gleaning_file)
            
            url = post.metadata.get("url")
            old_title = post.metadata.get("title")
            old_desc = post.metadata.get("description", "")
            
            if not url:
                print(f"⚠️  No URL: {gleaning_file.name}")
                stats["unchanged"] += 1
                continue
            
            # Normalize
            new_title, new_desc = registry.normalize(url, old_title, old_desc)
            
            # Check if changed
            if new_title == old_title and new_desc == old_desc:
                stats["unchanged"] += 1
                continue
            
            # Show changes
            if new_title != old_title:
                print(f"📝 {gleaning_file.name}")
                print(f"   Title: {old_title}")
                print(f"       -> {new_title}")
            
            if new_desc != old_desc:
                print(f"   Desc: {old_desc[:60]}...")
                print(f"      -> {new_desc[:60]}...")
            
            stats["normalized"] += 1
            
            if not dry_run:
                # Update frontmatter
                post.metadata["title"] = new_title
                post.metadata["description"] = new_desc
                
                # Write back
                with open(gleaning_file, "w", encoding="utf-8") as f:
                    f.write(frontmatter.dumps(post))
        
        except Exception as e:
            print(f"❌ Error processing {gleaning_file.name}: {e}")
            stats["errors"] += 1
    
    # Summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Total: {stats['total']}")
    print(f"  Normalized: {stats['normalized']}")
    print(f"  Unchanged: {stats['unchanged']}")
    print(f"  Errors: {stats['errors']}")
    
    if dry_run:
        print("\n🔍 DRY RUN - No files were modified")


def main():
    parser = argparse.ArgumentParser(description="Normalize existing gleaning files")
    parser.add_argument("--vault-path", type=Path, required=True, help="Path to vault")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    
    args = parser.parse_args()
    normalize_gleanings(args.vault_path, args.dry_run)


if __name__ == "__main__":
    main()
```

**Usage**:
```bash
# Preview changes
python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/amoxtli --dry-run

# Apply normalization
python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/amoxtli
```

---

### Phase 4: Reindex After Backfill

After normalizing existing files:

```bash
temoa reindex --vault ~/Obsidian/amoxtli
```

This updates the search index with normalized titles/descriptions.

---

## Testing Strategy

### Unit Tests (`tests/test_normalizers.py`)

**GitHubNormalizer**:
- ✅ `user/repo: Description` -> `user/repo`, `Description`
- ✅ `user/repo - Description` -> `user/repo`, `Description`
- ✅ `Description. - user/repo` -> Remove suffix
- ✅ `Description. Contribute to user/repo...` -> Remove suffix
- ✅ URL with no title -> Extract from path
- ✅ Matches `github.com` domain

**DefaultNormalizer**:
- ✅ Pass-through title unchanged
- ✅ Pass-through description unchanged
- ✅ Matches all URLs

**NormalizerRegistry**:
- ✅ Selects GitHubNormalizer for GitHub URLs
- ✅ Falls back to DefaultNormalizer for unknown domains

### Integration Test

Create test vault with sample gleanings:
- GitHub repo with full title
- Non-GitHub URL (should pass through)
- GitHub URL with missing title (extract from path)

Run backfill script in dry-run mode, verify output.

---

## Examples

### Before Normalization

**GitHub**:
```yaml
title: "filiksyos/gittodoc: Turn any Git repository into a documentation link."
description: "Turn any Git repository into a documentation link. - filiksyos/gittodoc"
```

**YouTube**:
```yaml
title: "youtube.com"
description: ""
```

**Reddit**:
```yaml
title: "Reddit - The heart of the internet"
description: ""
```

### After Normalization

**GitHub**:
```yaml
title: "filiksyos/gittodoc"
description: "Turn any Git repository into a documentation link."
```

**YouTube**: (no normalizer yet)
```yaml
title: "youtube.com"
description: ""
```

**Reddit**: (no normalizer yet)
```yaml
title: "Reddit - The heart of the internet"
description: ""
```

---

## Future Normalizers

### YouTubeNormalizer

Extract video title from YouTube URLs:
- Fetch video title from YouTube API or HTML
- Extract channel name
- Format: `{channel} - {video_title}`

### RedditNormalizer

Extract subreddit and post info:
- Parse URL for subreddit name
- Fetch post title
- Format: `r/{subreddit}: {post_title}`

---

## Files to Create

1. ✅ Plan: `docs/GLEANING-NORMALIZATION-PLAN.md` (this file)
2. ⬜ Code: `src/temoa/normalizers.py` (~200 lines)
3. ⬜ Tests: `tests/test_normalizers.py` (~150 lines)
4. ⬜ Script: `scripts/normalize_existing_gleanings.py` (~150 lines)
5. ⬜ Integration: Update `src/temoa/scripts/extract_gleanings.py` (~10 lines changed)

---

## Files to Modify

1. ⬜ `src/temoa/scripts/extract_gleanings.py` - Add normalization call
2. ⬜ `docs/GLEANINGS.md` - Document normalization behavior

---

## Rollout Plan

### Step 1: Review Plan
- User reviews this document
- Approve approach or request changes

### Step 2: Implement Core (30 min)
- Create `normalizers.py`
- Write unit tests
- Verify tests pass

### Step 3: Integration (15 min)
- Update extraction script
- Test extraction with new URL

### Step 4: Backfill Script (20 min)
- Create backfill script
- Dry-run on production vault
- Review sample outputs

### Step 5: Execute Backfill (5 min)
- Run backfill on production vault (~776 GitHub gleanings)
- Reindex vault
- Verify search results

**Total Estimated Time**: ~70 minutes

---

## Risks & Mitigation

### Risk: Normalization logic is wrong
**Mitigation**: Extensive unit tests, dry-run mode with manual review

### Risk: Break existing gleanings
**Mitigation**: Git commit before backfill, easy to revert

### Risk: Performance (776 files to update)
**Mitigation**: Simple file I/O, estimated <1 minute for backfill

### Risk: Edge cases in GitHub titles
**Mitigation**: Comprehensive test coverage, iterative refinement

---

## Success Criteria

1. ✅ All GitHub gleanings have clean `user/repo` titles
2. ✅ Descriptions no longer duplicate repo names
3. ✅ Non-GitHub URLs unchanged (backward compatible)
4. ✅ New extractions automatically normalized
5. ✅ System extensible for YouTube/Reddit normalizers
6. ✅ All tests passing
7. ✅ Documentation updated

---

## Questions for User

1. **Scope**: Start with GitHub only, or also implement YouTube/Reddit normalizers?
2. **Description handling**: Should we fetch better descriptions if current one is empty?
3. **Titles from URLs**: For failed fetches, extract title from URL path?
4. **Other domains**: Are there other domains besides GitHub/YouTube/Reddit to prioritize?

---

**Ready to proceed?** Let me know if you want to:
- Adjust the approach
- Add/remove normalizers
- Change implementation details
- Start implementation
