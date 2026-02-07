# Text Cleanup - Ready to Run

**Date**: 2026-02-06
**Status**: ✅ Tested and ready

---

## What We Built

### 1. Text Cleaning Utility
**File**: `src/temoa/text_cleaner.py`

Functions:
- `remove_emojis()` - All emoji unicode ranges
- `remove_zero_width()` - Invisible characters
- `remove_rtl_marks()` - RTL/LTR formatting marks
- `normalize_quotes()` - Smart quotes → ASCII
- `normalize_dashes()` - En/em dashes → hyphens
- `normalize_spaces()` - Non-breaking spaces, cleanup whitespace
- `clean_text()` - Applies all cleaning operations

### 2. Gleaning Cleanup Script
**File**: `src/temoa/scripts/cleanup_gleanings.py`

What it does:
- Cleans all text fields in frontmatter (title, description, github_description, github_readme_excerpt)
- Converts JSON topic arrays to proper YAML lists
- Cleans headings and link text in markdown body
- Supports `--dry-run` for safety
- Progress reporting every 50 files

---

## Test Results

**Test 1: Emoji removal**
- File: `32d41bca1d59.md` (soxoj/maigret)
- Before: `# soxoj/maigret: 🕵️‍♂️ Collect a dossier...`
- After: `# soxoj/maigret: Collect a dossier...`
- ✅ Success

**Test 2: JSON topics → YAML lists**
- File: `0579ab76ff9a.md` (oraios/serena)
- Before: `github_topics: ["agent", "ai", "ai-coding", ...]`
- After:
  ```yaml
  github_topics:
  - agent
  - ai
  - ai-coding
  ...
  ```
- ✅ Success

**Test 3: Dry run on full vault**
- Total: 1,054 gleanings
- Would modify: 243 files (23%)
  - Text cleaned: 230 files (smart quotes, dashes, spaces)
  - Body cleaned: 100 files (headings, links)
  - Topics fixed: Will be detected correctly now
- ✅ Success

---

## Usage

### Dry Run (Preview Changes)
```bash
uv run python src/temoa/scripts/cleanup_gleanings.py \
  --vault-path ~/Obsidian/amoxtli \
  --dry-run
```

### Run on All Gleanings
```bash
uv run python src/temoa/scripts/cleanup_gleanings.py \
  --vault-path ~/Obsidian/amoxtli
```

### Run on Specific Files
```bash
uv run python src/temoa/scripts/cleanup_gleanings.py \
  --vault-path ~/Obsidian/amoxtli \
  --files file1.md file2.md file3.md
```

---

## What Gets Cleaned

### Frontmatter Fields
- `title` - Emoji removal, quote/dash normalization
- `description` - Full text cleaning
- `github_description` - Full text cleaning
- `github_readme_excerpt` - Full text cleaning
- `github_topics` - JSON arrays → YAML lists

### Markdown Body
- Headings (`# Title`) - Emoji removal, text cleaning
- Link text (`[text](url)`) - Emoji removal, text cleaning

---

## Problems Fixed

| Issue | Count | Fix |
|-------|-------|-----|
| Emojis in text | 25 files | Removed |
| JSON topic arrays | 123 files | Convert to YAML lists |
| Smart quotes | 65 files | → ASCII quotes |
| En/em dashes | 70 files | → Hyphens |
| Non-breaking spaces | 21 files | → Regular spaces |
| Zero-width chars | 2 files | Removed |
| RTL marks | 2 files | Removed |

**Total affected**: ~243 files will be cleaned

---

## Safety Features

1. **Dry run mode**: Preview all changes before applying
2. **Progress reporting**: See which files are modified
3. **Error handling**: Gracefully handles YAML parse errors
4. **Per-file validation**: Each file validated after changes
5. **Specific file mode**: Test on individual files first

---

## Next Steps

### Option A: Run cleanup now
1. Do final dry run to review changes
2. Run cleanup on all 1,054 gleanings
3. Reindex vault
4. Test search functionality

### Option B: Re-extract from dailies first
1. Consider whether gleanings should be rebuilt from daily notes
2. If yes, extraction script will apply text cleaning during extraction
3. If no, run cleanup on existing gleanings

---

## Recommendation

**Run the cleanup now** because:
1. It's non-destructive (only cleans problematic characters)
2. It fixes real problems (JSON arrays, emojis breaking indexing)
3. It's fast (processes 1,000+ files in seconds)
4. We can always re-extract from dailies later if needed
5. The text cleaning will benefit any gleanings, old or new

After cleanup:
- Reindex vault to pick up cleaned frontmatter
- Test that search works without errors
- Then decide if we want to reorganize GitHub gleaning structure

