# GitHub Gleaning Fix Plan

**Date**: 2026-02-06
**Context**: Fixing GitHub gleanings to be more useful and avoid odd characters

---

## Current State Analysis

### What Works
1. **GitHub API enrichment exists** (`src/temoa/github_client.py`)
   - Fetches: description, language, stars, topics, archived status, last_push
   - Extracts README excerpt (first paragraph, max 500 chars)
   - Has emoji removal in `normalizers.py` (description only)

2. **Normalizers handle GitHub URLs** (`src/temoa/normalizers.py`)
   - Removes "GitHub - " prefix
   - Removes redundant " - user/repo" suffixes
   - Removes emojis from descriptions
   - Cleans up "Contribute to..." text

3. **Maintenance tool can enrich** (`maintain_gleanings.py`)
   - `--enrich-github` flag
   - Adds frontmatter: `github_language`, `github_stars`, `github_topics`, `github_archived`, `github_last_push`, `github_readme_excerpt`
   - Updates title to "user/repo: Description" format

### What's Broken

1. **Title still has problems**
   - Format: "user/repo: Description from API"
   - The API description often has emojis and odd characters
   - These end up in YAML frontmatter `title:` field
   - **Problem**: Emojis/unicode in frontmatter breaks indexing

2. **Description field redundancy**
   - Normalizer removes emojis from description
   - But title field gets description WITH emojis
   - Inconsistent handling

3. **"Why I saved this" is missing**
   - GitHub API description is what the repo author wrote
   - Not what the gleaner (user) thought was interesting
   - No context from daily note captured

4. **README excerpt not used effectively**
   - `github_readme_excerpt` added to frontmatter
   - But not used in main description or body
   - Extra API call, but value not surfaced

---

## The Fix

### Phase 1: Clean up existing emoji/unicode problems

**Immediate issue**: Frontmatter `title` field contains emojis/unicode that break indexing.

**Solution**: Apply emoji removal to title field, not just description.

**Changes needed**:
1. Update `GitHubNormalizer.normalize_title()` to remove emojis
2. Update `maintain_gleanings.py` enrichment to clean title before writing

**Implementation**:
- Extract emoji removal pattern to shared function
- Apply to both title and description in normalizer
- Apply when building title in enrichment

### Phase 2: Better title format

**Current**: "user/repo: API description with emojis 🚀"
**Problem**: API description is often long, emoji-filled, not the "why"

**Option A: Simple title only**
```yaml
title: "user/repo"
description: "[README excerpt or API description, emoji-free]"
```

**Option B: Title with one-liner**
```yaml
title: "user/repo"
description: "[Short cleaned description]"
github_readme_excerpt: "[Longer context]"
```

**Option C: Use README as primary description**
```yaml
title: "user/repo"
description: "[README first paragraph, emoji-free, max 500 chars]"
github_description: "[Original API description]"
```

**Recommendation**: Option C
- README is usually better written than API description
- README first paragraph often explains "what this does"
- Keep API description in separate field for reference
- Fall back to API description if no README

### Phase 3: Extract context from daily note

**Goal**: Capture "why I saved this" from daily note

**Current extraction format**:
```markdown
## Gleanings

- [user/repo](https://github.com/user/repo)  [14:30]
> Some context I wrote about why this is interesting

- [Another](URL) - Inline description here
```

**What we can extract**:
1. Quoted block after link (already supported for multi-line)
2. Inline description after " - " (already supported)
3. Surrounding context? (harder, would need to parse nearby text)

**Changes needed**:
1. ✅ Already supported: Quoted blocks captured as description
2. ✅ Already supported: Inline " - description" captured
3. **Preserve user description** when enriching with GitHub API
   - If gleaning already has description, keep it
   - Add GitHub data as separate fields
   - Don't overwrite user context with API description

### Phase 4: Frontmatter field reorganization

**Current frontmatter** (after enrichment):
```yaml
---
title: "user/repo: Long API description with emojis 🚀"
description: "Long API description with emojis 🚀"
github_language: Python
github_stars: 12345
github_topics: [python, api, web]
github_archived: false
github_last_push: 2025-01-15T12:34:56Z
github_readme_excerpt: "First paragraph of README..."
---
```

**Proposed frontmatter**:
```yaml
---
title: "user/repo"
description: "[User context if provided, else README excerpt, else API description - all emoji-free]"
type: gleaning
status: active
url: https://github.com/user/repo
domain: github.com
created: 2025-11-15
source: Daily/2025/2025-11-15-Fr.md
gleaning_id: 9c72d1c06194
github_language: Python
github_stars: 12345
github_topics:
  - python
  - api
  - web
github_archived: false
github_last_push: 2025-01-15
github_description: "Original API description (cleaned, no emojis)"
---
```

**Key changes**:
- Title: Just "user/repo" (no description)
- Description: Priority order: user context > README excerpt > API description
- All text fields: emoji-free
- GitHub data: separate fields, preserved for filtering/searching
- `github_description`: original API description (for reference)

---

## Implementation Steps

### Step 1: Extract and share emoji removal
- Create `clean_text()` function in normalizers.py
- Remove emojis and other problematic unicode
- Apply to all text fields (title, description, readme_excerpt)

### Step 2: Update GitHubNormalizer
- Change `normalize_title()` to return just "user/repo"
- Move description logic to prioritize README > API description
- Apply emoji cleaning to all outputs

### Step 3: Update GitHub enrichment
- Change title format to "user/repo" only
- Use README excerpt as primary description source
- Store original API description in `github_description`
- Preserve existing user-written descriptions (don't overwrite)

### Step 4: Update extraction script
- Already captures user context from daily notes ✓
- Ensure it's preserved during enrichment

### Step 5: Migration script for existing gleanings
- Re-process existing GitHub gleanings
- Clean up emoji from all frontmatter fields
- Reorganize title/description per new format
- Preserve any manually-written descriptions

---

## Testing Plan

1. **Extract new GitHub gleaning from daily note**
   - With user description
   - Without user description (naked URL)
   - Verify emoji-free frontmatter
   - Verify title = "user/repo"
   - Verify description = user context or README excerpt

2. **Enrich existing gleaning**
   - Verify preserves user description if present
   - Verify adds README excerpt if available
   - Verify all frontmatter emoji-free

3. **Search indexed gleanings**
   - Verify no indexing errors
   - Verify searchability

4. **Migration of existing 500+ gleanings**
   - Dry run first
   - Verify no data loss
   - Verify emoji cleanup

---

## Questions to Resolve

1. **Date format for `github_last_push`**
   - Current: ISO 8601 with time (2025-01-15T12:34:56Z)
   - Proposed: Date only (2025-01-15)
   - Rationale: Time precision not useful, date is enough

2. **Topics as YAML list vs JSON array**
   - Current: JSON string in frontmatter
   - Should be: YAML list format
   - Needs proper YAML serialization

3. **What other unicode causes problems?**
   - Just emojis?
   - Zero-width characters?
   - Right-to-left marks?
   - Non-breaking spaces?

4. **Should we backfill all existing gleanings?**
   - How many GitHub gleanings exist?
   - How many have emoji problems?
   - Do all need re-enrichment or just cleaning?

---

## Next Actions

1. Check existing gleanings for emoji problems
2. Count GitHub gleanings needing cleanup
3. Implement Step 1 (emoji cleaning function)
4. Update normalizer (Step 2)
5. Test on sample gleanings
6. Implement enrichment changes (Step 3)
7. Build migration script (Step 5)
8. Run migration on real vault

