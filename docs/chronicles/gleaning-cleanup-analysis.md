# Gleaning Cleanup Analysis - February 2026

**Date**: 2026-02-06
**Vault**: ~/Obsidian/amoxtli

---

## The Numbers

**Total gleanings**: 1,054
**GitHub gleanings**: 347 (33%)

### Problems Found

| Issue | Count | % of Total |
|-------|-------|------------|
| Emojis | 25 | 2.4% |
| Emojis (GitHub only) | 11 | 3.2% of GitHub |
| JSON-formatted topics | 123 | 11.7% |
| Zero-width characters | 2 | 0.2% |
| RTL/LTR marks | 2 | 0.2% |
| Non-breaking spaces | 21 | 2.0% |
| Smart quotes | 65 | 6.2% |
| En/em dashes | 70 | 6.6% |

### Priority Issues

1. **JSON arrays in YAML** (123 files)
   - `github_topics: ["topic1", "topic2"]`
   - Should be proper YAML list format
   - Breaks YAML parsers, hard to search

2. **Emojis** (25 files, 11 GitHub)
   - In title/heading: "user/repo: 🚀 Description"
   - In link text
   - Can break indexing

3. **Smart quotes/dashes** (135 files combined)
   - Not critical but inconsistent
   - Should normalize to simple ASCII quotes/dashes

4. **Zero-width/RTL marks** (4 files)
   - Invisible characters that break searching
   - High priority to remove

---

## Example Problem File

**File**: `32d41bca1d59.md` (soxoj/maigret)

```yaml
---
github_topics: ["blueteam", "cli", "cybersecurity", ...]  # ❌ JSON array
---

# soxoj/maigret: 🕵️‍♂️ Collect a dossier...  # ❌ Emoji in heading

[soxoj/maigret: 🕵️‍♂️ Collect a dossier...]  # ❌ Emoji in link
```

**Should be**:

```yaml
---
github_topics:
  - blueteam
  - cli
  - cybersecurity
  ...
---

# soxoj/maigret: Collect a dossier...  # ✓ No emoji

[soxoj/maigret: Collect a dossier...]  # ✓ No emoji
```

---

## Cleanup Strategy

### Phase 1: Text Cleaning Function (Immediate)

Create `clean_text()` utility that removes:
- Emojis (all unicode emoji ranges)
- Zero-width characters (\u200B-\u200D, \uFEFF)
- RTL/LTR marks (\u200E-\u200F, \u202A-\u202E)
- Normalize smart quotes to ASCII quotes
- Normalize en/em dashes to hyphens
- Replace non-breaking spaces with regular spaces
- Clean up extra whitespace

Apply to:
- Frontmatter `title` field
- Frontmatter `description` field
- Frontmatter `github_description` field (if exists)
- Frontmatter `github_readme_excerpt` field (if exists)
- Body headings
- Link text

### Phase 2: YAML Topics Fix (Immediate)

Convert JSON arrays to proper YAML lists:

**Before**:
```yaml
github_topics: ["topic1", "topic2", "topic3"]
```

**After**:
```yaml
github_topics:
  - topic1
  - topic2
  - topic3
```

**Implementation**: Use YAML library to parse/dump properly, don't do string manipulation.

### Phase 3: GitHub Gleaning Reorganization (Next)

After text cleanup works, reorganize GitHub gleanings:
- Title: Just "user/repo" (no description)
- Description: README excerpt (emoji-free) or API description (emoji-free)
- Keep GitHub metadata in separate fields

---

## Implementation Plan

### Step 1: Create text cleaning utility

**File**: `src/temoa/text_cleaner.py`

Functions:
- `clean_text(text: str) -> str` - main cleaning function
- `remove_emojis(text: str) -> str`
- `remove_zero_width(text: str) -> str`
- `normalize_quotes(text: str) -> str`
- `normalize_dashes(text: str) -> str`

### Step 2: Create gleaning cleanup script

**File**: `src/temoa/scripts/cleanup_gleanings.py`

Functions:
- Parse frontmatter (use nahuatl-frontmatter)
- Apply text cleaning to all text fields
- Convert JSON topics to YAML lists
- Rewrite file with cleaned content
- Support `--dry-run` flag
- Progress bar for 1000+ files

### Step 3: Test on sample files

- Test on the 25 emoji files
- Test on the 123 JSON topics files
- Verify YAML still valid
- Verify no data loss

### Step 4: Run on full vault

- Dry run first
- Review changes
- Run for real
- Reindex vault

---

## Testing Checklist

- [ ] Emoji removal works in all fields
- [ ] Zero-width characters removed
- [ ] RTL marks removed
- [ ] Smart quotes → ASCII quotes
- [ ] En/em dashes → hyphens
- [ ] JSON topics → YAML lists
- [ ] YAML frontmatter still valid
- [ ] No data loss
- [ ] Files still searchable
- [ ] Indexing works without errors

---

## Next Actions

1. Create `text_cleaner.py` utility
2. Create `cleanup_gleanings.py` script
3. Test on 5-10 problem files
4. Dry run on full vault
5. Review output
6. Run cleanup on 1,054 gleanings
7. Reindex vault
8. Verify search works

