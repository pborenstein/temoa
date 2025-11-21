# CHRONICLES.md - Project Lore & Design Discussions

> **Purpose**: This document captures key discussions, design decisions, and historical context for the Temoa project. Unlike IMPLEMENTATION.md (which tracks *what* to build) or CLAUDE.md (which explains *how* to build), Chronicles explains *why* we're building it this way.

**Created**: 2025-11-18
**Format**: Chronological entries with discussion summaries
**Audience**: Future developers, decision-makers, and your future self

---

## Entry 7: Phase 2 Complete - Gleanings Integration (2025-11-19)

### Context

After Phase 1 delivered a working FastAPI server with semantic search, Phase 2 focused on extracting, migrating, and automating gleanings—the curated links saved in daily notes that represent the core value proposition of Temoa.

**Goal**: Make 505+ historical gleanings searchable, automate extraction of new ones, and establish a sustainable workflow.

---

### What Was Built

**Timeline**: Single day implementation (2025-11-19)
**Result**: Complete gleanings workflow from extraction to automation

#### 1. Extraction System (`scripts/extract_gleanings.py` - 319 lines)

**Challenge**: Parse gleanings from daily notes in a format like:
```markdown
## Gleanings
- [Title](URL) - Description
```

**Solution**:
- Regex-based parsing of gleanings sections
- MD5-based gleaning IDs from URLs (deduplication)
- State tracking in `.temoa/extraction_state.json`
- Incremental mode (only process new files)
- Dry-run support for testing

**Result**: Successfully extracted 6 gleanings from test-vault daily notes

#### 2. Historical Migration (`scripts/migrate_old_gleanings.py` - 259 lines)

**Challenge**: Migrate 505 gleanings from old-gleanings JSON format without losing metadata

**Solution**:
- Convert old JSON format to new markdown format
- Preserve all metadata (category, tags, timestamp, date)
- Mark with `migrated_from: old-gleanings` frontmatter
- Use same MD5 ID system for consistency

**Result**: All 505 gleanings migrated successfully, **total 516 gleanings** in test-vault

#### 3. Re-indexing Integration

**Challenge**: After extracting gleanings, Synthesis needs to re-index the vault

**Solution**:
- Added `SynthesisClient.reindex()` method (calls `pipeline.process_vault(force_rebuild=True)`)
- Added `POST /reindex` endpoint to FastAPI server
- Returns status with files indexed count

**Result**: Can trigger re-indexing via: `curl -X POST http://localhost:8080/reindex`

#### 4. Automation Scripts

**Challenge**: Daily gleanings need to be extracted automatically

**Solution**:
- `scripts/extract_and_reindex.sh`: Combined workflow (extract + reindex)
- Cron example: Daily at 11 PM
- Systemd service + timer units for modern Linux systems
- Logging support, dry-run mode

**Result**: Multiple automation options documented and tested

#### 5. Documentation (`docs/GLEANINGS.md` - 371 lines)

Comprehensive workflow guide covering:
- Gleaning format specification
- Manual and automated extraction
- Migration instructions
- Automation setup (cron and systemd)
- Troubleshooting and best practices

---

### Key Decisions Made

**DEC-016: Individual Files vs. In-Place Extraction**

**Date**: 2025-11-19
**Context**: Should gleanings stay in daily notes or be extracted to individual files?
**Decision**: Extract to individual files in `L/Gleanings/`
**Rationale**:
- Cleaner separation of concerns (daily notes = ephemeral, gleanings = permanent)
- Better for semantic search (each gleaning is a discrete unit)
- Easier to maintain and update individual gleanings
- Matches atomic note principle in Zettelkasten/Obsidian workflows
**Trade-offs**: Slightly more complex extraction, but worth the organizational benefits

---

**DEC-017: MD5-based Gleaning IDs**

**Date**: 2025-11-19
**Context**: How to uniquely identify gleanings for deduplication?
**Decision**: MD5 hash of URL (first 12 chars)
**Rationale**:
- URLs are naturally unique identifiers
- Same URL = same gleaning (prevents duplicates)
- Deterministic (same URL always produces same ID)
- Short enough for filenames (`9c72d1c06194.md`)
**Trade-offs**: Hash collisions possible but extremely unlikely in personal vault scale

---

**DEC-018: State Tracking for Incremental Extraction**

**Date**: 2025-11-19
**Context**: Should extraction re-process all files or only new ones?
**Decision**: Track processed files in `.temoa/extraction_state.json`
**Rationale**:
- Faster extraction (only process new files)
- Prevents duplicate processing
- Auditability (know what was extracted when)
- Can force full re-extraction with `--full` flag
**Trade-offs**: State file must be maintained, but low complexity cost

---

### What This Proves

**Gleanings are the killer feature**:
- 505+ curated links now searchable via semantic search
- Temporal context preserved (when you were interested)
- Automatic extraction ensures new gleanings are captured
- Vault-first research becomes practical

**Rapid iteration continues**:
- Phase 2 completed in 1 day (estimated 3-4 days)
- Clear planning + simple architecture = fast implementation
- No blockers, everything worked as designed

**Automation is essential**:
- Manual extraction is tedious (defeated old-gleanings project)
- Cron/systemd automation makes it sustainable
- Combined workflow script reduces friction

---

### Unexpected Wins

1. **Migration preserved everything**: Old gleanings kept all metadata (categories, tags, timestamps)
2. **State tracking works perfectly**: Incremental extraction prevents duplicates automatically
3. **Combined workflow script**: Single command handles extraction + re-indexing
4. **Documentation thoroughness**: Troubleshooting section anticipates common issues

---

### Commits

Phase 2 implementation:
- `ebeb7e5`: feat: complete Phase 2 - Gleanings Integration

---

### Lessons Learned

**1. Simplicity wins again**

Old-gleanings failed because it was complex (2,771 lines, 15+ categories, state management). Phase 2 succeeded because:
- Simple extraction regex
- Simple storage (individual markdown files)
- Simple state tracking (JSON file)
- Simple automation (bash script)

**2. Metadata preservation matters**

Migrating historical gleanings could have lost valuable context (categories, timestamps). Preserving metadata means:
- Temporal archaeology still works on old gleanings
- Categories available for future filtering
- Original dates maintained

**3. Automation makes or breaks adoption**

Manual extraction is fine for testing, but daily usage requires automation. Providing multiple options (cron, systemd) accommodates different user preferences.

**4. Documentation accelerates future work**

Comprehensive `GLEANINGS.md` means:
- Future users can set up automation without asking
- Troubleshooting section reduces support burden
- Best practices guide workflow decisions

**5. Testing validates assumptions**

Extracting from test-vault (6 gleanings) and migrating old-gleanings (505) proved:
- Regex parsing works correctly
- ID system prevents duplicates
- State tracking functions as designed
- End-to-end workflow is solid

---

### Phase 2 Status: COMPLETE ✅

**All deliverables met**:
- ✅ Extraction script (`extract_gleanings.py`)
- ✅ Migration script (`migrate_old_gleanings.py`)
- ✅ Combined workflow (`extract_and_reindex.sh`)
- ✅ Re-indexing endpoint (`POST /reindex`)
- ✅ Automation configs (cron, systemd)
- ✅ Documentation (`GLEANINGS.md`)

**All success criteria met**:
- ✅ 516 gleanings extractable and migrated
- ✅ Incremental extraction working
- ✅ Automation configured
- ✅ Re-indexing integrated

**Ready for Phase 3**: Enhanced Features
- Archaeology endpoint (temporal analysis)
- Enhanced UI with filters
- PWA support (installable on mobile)

---

### Key Insight

**Gleanings are not just links—they're temporal knowledge artifacts.**

Each gleaning captures:
1. **What** you found interesting (URL + description)
2. **When** you were interested (date from daily note)
3. **Why** it mattered (description context)

This temporal dimension enables archaeology: "When was I researching Tailscale?" → Find gleanings from that period → Reconstruct past research context.

**The value compounds over time.** With 505+ gleanings now searchable, semantic search can surface forgotten connections. The automation ensures this library continues to grow.

This is what "vault-first research" means: Your past research becomes the foundation for future research.

---

**Next**: Phase 3 will make this indispensable through archaeology, enhanced UI, and mobile PWA support.

---

## Entry 8: CLI Implementation and First Real-World Testing (2025-11-19)

### Context

After completing Phase 2 (gleanings integration), we needed a better command-line interface for daily use. The existing `uv run python -m temoa` was too verbose for regular CLI/tmux workflows.

### What Was Built

**Click-based CLI** (similar to obsidian-tag-tools):
- `temoa config` - Show current configuration
- `temoa index` - Build embedding index from scratch (first-time setup)
- `temoa reindex` - Incremental updates (daily use)
- `temoa search "query"` - Quick searches from terminal
- `temoa archaeology "topic"` - Temporal analysis
- `temoa stats` - Vault statistics
- `temoa extract` - Extract gleanings from daily notes
- `temoa migrate` - Migrate old gleanings
- `temoa server` - Start FastAPI server

**Installation**: `uv tool install --editable .` enables global `temoa` command.

### Key Decisions

**DEC-019: Click CLI Over Custom Argument Parsing**

**Date**: 2025-11-19
**Decision**: Use Click framework for CLI (like obsidian-tag-tools)
**Rationale**:
- Familiar pattern from existing tools
- Subcommands cleanly organized
- Built-in help, version, options handling
- `--json` flags for scripting
- Easy to extend with new commands

**Trade-offs**: Click dependency, but worth it for better UX

---

**DEC-020: Separate `index` vs `reindex` Commands**

**Date**: 2025-11-19
**Decision**: Split into two commands instead of `--force` flag only
**Rationale**:
- Clear intent: `index` = first-time setup, `reindex` = daily updates
- Prevents accidental full rebuilds (slow for large vaults)
- Better discoverability in help text
- `reindex --force` still available for explicit full rebuild

**Trade-offs**: Two commands instead of one, but clearer semantics

### Bugs Fixed

**The Stats Display Bug**:

During real-world testing on production vault (2,281 files), `temoa stats` showed:
```
Files indexed: 2281
Embeddings: 0        ← Wrong!
```

But search worked perfectly, finding results with good similarity scores.

**Root cause**: CLI was looking for `statistics.get('total_embeddings')` but Synthesis returns `num_embeddings`.

**Fix**: Changed to `statistics.get('num_embeddings', 0)` + improved model name extraction from nested `model_info` dict.

**Discovery method**: Created `debug_stats.py` script which revealed the actual JSON structure Synthesis returns.

### Real-World Validation

**First production test** (2,281 files, 2,006 tags, 31 directories):
- ✅ Index built successfully in ~17 seconds
- ✅ Search works: `temoa search "obsidian"` returned relevant results
- ✅ Stats displays correctly after fix
- ✅ CLI installed globally and works from any directory
- ✅ Performance meets targets (~400ms search time)

**Key insight**: The system works! Ready for mobile testing to validate the core behavioral hypothesis: "If vault search is fast enough (<2s from phone), it becomes the first place to check before Googling."

### Commits

CLI implementation and fixes:
- `396c49e`: feat: add Click-based CLI for easy command-line access
- `2706f6d`: fix: correct reindex parameter and add clearer index command
- `61af389`: chore: add [tool.uv] package=true for uv tool install support
- `272dc5e`: feat: improve stats command to detect missing/incomplete index
- `3ab7936`: debug: add logging to get_stats to diagnose index location issue
- `6739f53`: debug: add stats debugging script to diagnose embeddings detection issue
- `4c25a32`: fix: use correct key 'num_embeddings' from Synthesis stats

---

## Entry 9: Gleanings Extraction Fixes and First Real Extraction (2025-11-19)

### Context

With Phase 2 implementation complete, attempted first real extraction of gleanings from production vault (742 daily notes). Discovered multiple bugs preventing extraction from working correctly.

### Problems Discovered

**1. CLI Argument Mismatch**

`temoa extract` command was passing arguments incorrectly:
- **Bug**: Passed `vault_path` as positional argument
- **Expected**: `--vault-path` named argument
- **Impact**: Script failed immediately with "required: --vault-path" error

Same issue affected `temoa migrate` command.

**2. Extraction Pattern Mismatch**

The extraction regex expected format:
```markdown
- [Title](URL) - Description
```

But production vault used format:
```markdown
- [Title](URL)  [HH:MM]
>  Description
```

**Result**: Only 4 gleanings found from 742 daily notes (should have been hundreds).

**3. --full Flag Didn't Reset State**

`--full` flag processed all files but still skipped "duplicates" based on existing state:
- **Expected behavior**: `--full` = start completely fresh
- **Actual behavior**: `--full` = process all files, but skip gleanings already in state
- **Impact**: Running `temoa extract --full` after fixing bugs still found only 2 unique gleanings

**4. Search Results Lacked Context**

Search results showed similarity scores but no indication of *why* documents matched:
```
1. Some Document
   Similarity: 0.560
   Tags: foo, bar
```

No snippet or content preview to help judge relevance before opening.

**5. Tags Display Error**

Search crashed when displaying results:
```
Error: sequence item 0: expected str instance, int found
```

**Cause**: Synthesis returns some tags as integers (like years), but `', '.join(tags)` expects all strings.

**6. Gleanings Not Indexed After Extraction**

After successfully extracting 661 gleanings:
- `temoa stats` still showed 2281 files (unchanged)
- `temoa reindex` ran but didn't pick up new files
- **Cause**: Incremental reindex without `--force` flag

### Solutions Implemented

**CLI Argument Fixes** (`82afc0d`):
- Changed `vault_path` to named `--vault-path` argument
- Changed migrate `json_file` to named `--old-gleanings` argument
- Removed unsupported `--output` option (scripts hardcode `L/Gleanings/`)
- Updated docstrings to clarify output location

**Full Mode Reset** (`8f5dba2`):
- Made `--full` clear extraction state before processing
- Now truly starts from scratch, not just reprocessing files

**Gleaning Pattern Fix** (`af9004e`):
- Updated regex to match actual format: `- [Title](URL)` with optional timestamp
- Parse description from next line if it starts with `>`
- Handles both inline and multi-line gleaning formats

**Vault-Local Config** (`3158b0f`):
- Added `.temoa/config.json` as first search location
- Keeps all temoa state together in one hidden directory
- Search order: `.temoa/config.json` → `~/.config/temoa/config.json` → `~/.temoa.json` → `./config.json`

**Tags Display Fix** (`46f0f3c`):
- Convert all tags to strings before joining: `', '.join(str(tag) for tag in tags)`
- Handles mixed string/integer tags gracefully

**Content Snippets** (`af34ee7`, `71cbf83`):
- Display `description` field from results (if available)
- Added `extract_relevant_snippet()` function to find query terms in content
- Centers snippet around first query term match (~200 chars)
- Falls back to beginning if no terms found

### Real-World Results

**First successful extraction from production vault**:

```
Total gleanings found: 1,368
New gleanings created: 661
Duplicates skipped: 707
Files processed: 742
```

**After `temoa reindex --force`**:
- Files indexed: 2,942 (2,281 vault files + 661 gleanings)
- All gleanings now searchable via semantic search

**Search quality validation** (`temoa search "tmux github"`):
```
1. e29b189b9758 (How to configure tmux, from scratch)
   Similarity: 0.633

2. Claude Code SSH/tmux Authentication Issues
   Similarity: 0.560

3. a92960ea6bd1 (Customizing tmux and making it less dreadful)
   Similarity: 0.522
```

**Gleanings now surface in search results**, proving the end-to-end workflow works!

### Key Insights

**1. Real Production Data Reveals Hidden Assumptions**

The regex pattern worked in test vault but not production because:
- Test data was crafted to match expected format
- Production data evolved organically with timestamps, multi-line descriptions
- **Lesson**: Always test against real user data, not idealized examples

**2. "Full" Has Different Meanings in Different Contexts**

- **File processing**: Process all files (not just changed)
- **State reset**: Clear state and extract everything fresh
- **Index rebuild**: `--force` required for full reindex

Users expected `--full` to mean "start over completely" but implementation only did partial reset.

**3. Incremental Reindex Doesn't Discover New Files**

`temoa reindex` without `--force`:
- Updates embeddings for existing tracked files
- Doesn't scan for new files in vault
- **Result**: New gleanings invisible to search

**Solution**: Always use `temoa reindex --force` after extraction or migration.

**4. Search Results Without Context Are Useless**

Seeing "Similarity: 0.560" means nothing without knowing *why* it matched. Users need:
- Content snippets showing query terms
- Description/summary of document
- Visual hierarchy (dimmed text for snippets)

**Still needs work**: Current snippets sometimes show random beginning text, not relevant query context. The `extract_relevant_snippet()` function needs access to full document content (currently limited by what Synthesis returns).

### Architecture Decisions

**DEC-009: Config Location Priority**

**Decision**: Prioritize `.temoa/config.json` over global config locations.

**Rationale**:
- Keeps all temoa state co-located (config, extraction state, embeddings)
- Makes vault-local setup simpler (`vault_path: "."`)
- Easier to exclude from sync (one `.temoa/` directory)
- Still supports global config for multi-vault workflows

**Trade-off**: Need to set up config in each vault, but most users have one vault.

**DEC-010: Gleanings Output Location**

**Decision**: Hardcode gleaning output to `L/Gleanings/`, don't make configurable.

**Rationale**:
- Follows "avoid over-engineering" principle
- User has consistent location across vault
- Reduces configuration complexity
- Can make configurable later if needed

**Trade-off**: Less flexible, but simpler to implement and explain.

**DEC-011: Reindex Force Default**

**Decision**: Keep `temoa reindex` incremental by default, require `--force` for full rebuild.

**Rationale**:
- Incremental updates faster for daily use (eventual feature)
- Explicit `--force` prevents accidental expensive operations
- Matches user mental model ("reindex" = update, not rebuild)

**Trade-off**: Users must remember `--force` after extraction/migration. Could add reminder message to extraction output.

### Remaining Issues

**1. Snippet Quality Needs Improvement**

Current implementation sometimes shows:
- Random beginning text instead of query-relevant content
- Duplicated text from title
- Full sentences cut mid-word

**Root cause**: Synthesis may not return full `content` field, limiting snippet extraction options.

**Next**: Investigate what fields Synthesis actually returns and improve snippet extraction accordingly.

**2. Duplicate Daily Note Directories**

User has both `Daily/` and `daily/` directories (case-sensitive filesystem):
```
Daily/2025/08-August/2025-08-05-Tu.md
daily/2025/08-August/2025-08-05-Tu.md (duplicate)
```

Same gleanings appear in both, correctly marked as duplicates after URL hashing. Not a bug, but worth noting for data cleanup.

**3. Gleaning File Names Are MD5 Hashes**

Gleanings named `e29b189b9758.md` instead of human-readable titles:
- **Pro**: Prevents filename conflicts, stable identifiers
- **Con**: Harder to browse gleanings directly in file system

**Acceptable trade-off**: Gleanings accessed via search (not browsing), and MD5 prevents title change issues.

### Testing Lessons

**What worked**:
- Extracting ~1,400 gleanings from production vault proved end-to-end workflow
- Search returns relevant gleanings with good similarity scores (0.5-0.6 range)
- Gleanings co-located with notes make sense organizationally

**What needs work**:
- Result display UX (snippets, relevance indicators, better formatting)
- Better error messages when config missing or paths wrong
- More intuitive `--force` behavior

**What surprised us**:
- Pattern matching failures only discovered in production
- Incremental reindex subtlety (doesn't find new files)
- Tags can be integers (from Synthesis parsing years as ints)

### Commits

Gleanings extraction and CLI fixes:
- `82afc0d`: fix: correct argument passing in extract and migrate CLI commands
- `8f5dba2`: fix: make --full flag truly start from scratch
- `af9004e`: fix: update gleaning extraction pattern to match actual format
- `3158b0f`: feat: add support for vault-local config in .temoa/config.json
- `46f0f3c`: fix: convert tags to strings before joining in search output
- `af34ee7`: feat: show content snippets in search results
- `71cbf83`: feat: extract relevant snippets showing query context

### Status

✅ **Gleanings extraction working**: 661 gleanings successfully extracted from 742 daily notes
✅ **Gleanings searchable**: Semantic search finds relevant gleanings with good scores
✅ **End-to-end validated**: Extract → reindex → search workflow proven
⚠️ **UX needs polish**: Search result snippets need improvement for usefulness

**Next session**: Focus on making search results more useful with better snippets, highlighting, and result formatting.

---

### Next Steps

**Ready for Phase 3**: The core functionality works. Before adding enhancements (archaeology UI, PWA, filters), we should:

1. **Test the behavioral hypothesis**: Start `temoa server` and access from mobile via Tailscale
2. **Measure habit formation**: Is <500ms search fast enough to check vault-first?
3. **Identify real friction**: What actually prevents usage vs. what we think might help?

**Phase 3 can wait** until we validate that the core workflow (mobile search → vault-first habit) actually works in practice.

---

## Entry 10: Extraction Shakedown - Format Flexibility & Filesystem Edge Cases (2025-11-21)

### Context

After initial gleanings extraction worked (661 gleanings from 742 daily notes), user requested a thorough shakedown of the extraction process to identify and fix any remaining bugs before deployment. The goal: "be liberal in your input, conservative in your output" (Postel's Law).

### Problems Discovered

Real-world testing with production vault revealed **5 critical issues**:

#### 1. Case-Insensitive Filesystem Duplicates (macOS APFS)

**Symptom**:
```
Processing: Daily/2025/11-November/2025-11-21-Fr.md
Processing: daily/2025/11-November/2025-11-21-Fr.md
```

**Root cause**: On macOS with case-insensitive filesystem (APFS default), glob patterns `Daily/**/*.md` and `daily/**/*.md` both match the same files. Linux VM testing didn't catch this.

**User feedback**: "Is that why I'm getting all the duplicates?"

**Impact**: Confusing output, potential for duplicate gleaning extraction.

**Solution**: Added `seen_paths` set using `Path.resolve()` to deduplicate based on absolute paths. Each file processed exactly once regardless of how glob patterns match it.

**Test coverage**: Added `test_find_daily_notes_no_duplicates_on_case_insensitive_fs()` (though test runs on Linux, documents expected behavior).

#### 2. Missing 'hidden' Status in CLI

**Root cause**: System internals supported three statuses (active, inactive, hidden), but CLI `temoa gleaning mark` command only exposed active/inactive in Click choices.

**Impact**: Users couldn't mark gleanings as permanently hidden (different from inactive/dead links).

**Solution**: Added 'hidden' to CLI status choices:
```python
@click.option('--status', type=click.Choice(['active', 'inactive', 'hidden']))
```

Updated help text to explain all three statuses:
- **active**: Normal gleaning, included in search results
- **inactive**: Dead link, excluded from search, auto-restores if link comes back
- **hidden**: Manually hidden, never checked by maintenance tool

#### 3. Multiple Gleaning Formats Not Supported (10% Data Loss)

**Symptom**: User reported extraction was missing gleanings.

**Evidence**:
- Total URLs in vault: 766
- Extracted gleanings: 689
- Missing: 77 gleanings (10% loss!)

**Root cause**: Extraction only handled single format:
```python
GLEANING_LINK_PATTERN = re.compile(r'^-\s+\[([^\]]+)\]\(([^)]+)\)\s+-\s+(.+)$')
```

This missed:
- Naked URLs (with or without bullets)
- Multi-line descriptions
- Timestamps
- Descriptions on next line instead of same line

**User feedback**: "Basically, any URL in the Gleanings section is a gleaning."

**Real examples from vault**:
```markdown
## Gleanings

- [soimort/translate-shell](https://github.com/soimort/translate-shell)  [06:39]
> Command-line translator using Google Translate, Bing Translator, Yandex.Translate

- https://vrigger.com/info_forces.php?RC=RC0129  [07:42]
> You can use the vRigger software to calculate forces on rope systems

- [The White Noise Playlist](https://thewhitenoiseplaylist.com/)  [13:40]
> The White Noise Playlist
> - Variety of white noise experiences without ads
> - Extended and uninterrupted noise tracks for focus/sleep
> - Founded by Dr. Ir. Stéphane Pigeon

https://example.com/bare-url-no-bullet
```

**Solution**: Implemented **5 pattern types**:

1. **Markdown link**: `- [Title](URL)` (original)
2. **Markdown link with timestamp**: `- [Title](URL)  [HH:MM]`
3. **Naked URL with bullet**: `- https://...` (fetches title from web)
4. **Naked URL bare**: `https://...` (no bullet, fetches title)
5. **Multi-line descriptions**: ALL consecutive `>` lines captured, paragraph breaks preserved

**New extraction logic**:
```python
# Try patterns in order
if markdown_match:
    title = markdown_match.group(1)
    url = markdown_match.group(2)
elif naked_bullet_match:
    url = naked_bullet_match.group(1)
    title = fetch_title_from_url(url)  # <-- New!
elif naked_bare_match:
    url = naked_bare_match.group(1)
    title = fetch_title_from_url(url)  # <-- New!

# Collect ALL description lines
while lines[j].startswith('>'):
    description_lines.append(lines[j][1:].strip())
    j += 1
```

**Title fetching**:
```python
def fetch_title_from_url(url: str, timeout: int = 5) -> Optional[str]:
    """Fetch page title from <title> tag."""
    parser = TitleParser()  # HTMLParser subclass
    parser.feed(response.read(8192).decode())
    return parser.title or urlparse(url).netloc
```

**Performance impact**: Each naked URL adds ~1.5 seconds (HTTP request + parse). User had ~77 naked URLs = ~2 minutes extra extraction time. Acceptable for completeness.

**Result**: 766/766 gleanings extracted (100% coverage, 0% loss).

#### 4. Dry Run Fetching Titles Wastefully

**User feedback**: "Dry run should probably not actually fetch the titles, since you don't store them during dry run."

**Root cause**: `extract_from_note()` didn't know if it was in dry-run mode, so it fetched titles via HTTP even when they'd be discarded.

**Impact**: Wasted time and bandwidth during preview.

**Solution**: Added `dry_run` parameter to `extract_from_note()`:
```python
def extract_from_note(self, note_path: Path, dry_run: bool = False) -> List[Gleaning]:
    ...
    if dry_run:
        title = f"[{parsed.netloc or 'Title will be fetched'}]"
    else:
        print(f"  Fetching title for naked URL: {url[:60]}...")
        title = fetch_title_from_url(url)
```

**Result**: Instant dry-run preview, no HTTP requests made.

#### 5. Lowercase Patterns Causing User Confusion

**Symptom**: Even though deduplication worked correctly, output showed:
```
Processing: daily/2025/.../file.md
Processing: Daily/2025/.../file.md
```

**User feedback**: "Search ONLY for 'Daily'. ONLY 'Daily' is good. 'daily' is BAD BAD BAD."

**Root cause**: Patterns list included both cases:
```python
patterns = ["Daily/**/*.md", "daily/**/*.md", "Journal/**/*.md", "journal/**/*.md"]
```

On macOS (case-insensitive), both patterns matched the same files. Even though deduplication prevented double-processing, the *output* was confusing.

**User context**: User only has `Daily/` directory, not `daily/`. The lowercase pattern exists for cross-platform compatibility but shouldn't be shown.

**Solution**: Removed lowercase patterns entirely:
```python
patterns = ["Daily/**/*.md", "Journal/**/*.md"]  # Capital-case only
```

**Result**: Clean output showing only actual directory names. If future user has lowercase directories, they can add patterns back.

### Enhancement: Diagnostic Tool

Created `scripts/analyze_gleaning_formats.py` to preview what extraction will find:

**Features**:
- Scans vault for all gleaning formats
- Shows examples of each format (markdown links, naked URLs, multi-line descriptions)
- Reports format breakdown (how many of each type)
- Estimates extraction time based on naked URL count

**Example output**:
```
SUMMARY
======================================================================
Files with gleanings sections: 742
Total URLs found: 766

FORMAT BREAKDOWN:
  ✓ Markdown links ([Title](URL)):        689 (SUPPORTED)
  ✓ Naked URLs with bullet (- https://):   50 (SUPPORTED - fetches title)
  ✓ Naked URLs bare (https://):            27 (SUPPORTED - fetches title)

FEATURE USAGE:
  ✓ Timestamps [HH:MM]:                    234 (SUPPORTED)
  ✓ Multi-line descriptions (>2 lines):    45 (FULLY SUPPORTED)

📌 NOTE: 77 naked URLs will have titles fetched from web
   Extraction will take ~115 seconds longer (fetching titles)
```

**Value**: Users can run diagnostics *before* extraction to understand what will be captured and how long it will take.

### Design Decisions

**DEC-021: Postel's Law for Gleanings**

**Decision**: "Be liberal in your input, conservative in your output."

**Rationale**:
- Users format gleanings inconsistently (markdown links, naked URLs, multi-line descriptions, timestamps)
- Requiring a single rigid format would force manual cleanup or lose data
- Better to accept all reasonable formats and normalize to standard output format
- Mirrors successful protocols (HTTP, DNS, email) that succeed by being flexible

**Implementation**:
- Input: Accept 5 different gleaning formats
- Output: Normalize to consistent markdown files with frontmatter
- Preserve all information (titles, URLs, descriptions, timestamps)

**Trade-off**: More complex extraction logic, but 0% data loss and better user experience.

**DEC-022: Title Fetching for Naked URLs**

**Decision**: Fetch page titles from web for naked URLs instead of using URL as title.

**Rationale**:
- Naked URL like `https://vrigger.com/info_forces.php?RC=RC0129` is uninformative
- Real title "Rope Forces Calculator" much more useful for search and browsing
- ~1.5s per URL is acceptable for completeness (happens during extraction, not search)
- Fallback to domain name if fetch fails (graceful degradation)

**Implementation**:
```python
def fetch_title_from_url(url: str, timeout: int = 5) -> Optional[str]:
    """Only read first 8KB to find <title> tag (fast)."""
    response.read(8192)  # Don't fetch full page
    parser.feed(content)  # HTMLParser extracts <title>
    return parser.title or urlparse(url).netloc  # Fallback
```

**Trade-off**: Extraction slower for naked URLs, but search results much more useful.

**DEC-023: Case-Sensitive Pattern Matching**

**Decision**: Only search for `Daily/` and `Journal/` (capital-case), not lowercase variants.

**Rationale**:
- macOS case-insensitive filesystem makes both patterns match same files
- Showing both `daily/` and `Daily/` in output confuses users
- Most Obsidian vaults use capital-case by convention
- If user has lowercase directories, they can easily customize patterns

**Implementation**:
```python
patterns = ["Daily/**/*.md", "Journal/**/*.md"]  # Capital-case only
seen_paths = set()  # Still deduplicate via absolute paths (defense in depth)
```

**Trade-off**: Less "future-proof" for edge cases, but clearer UX for 99% case.

### Production Results

**Before fixes**:
```
Total gleanings found: 689
Missing gleanings: 77 (10% loss)
Confusing duplicate output
```

**After fixes**:
```
Total gleanings found: 766
New gleanings created: 739
Duplicates skipped: 27
Files processed: 374
Coverage: 100% (0% loss)
Clean output, no duplicate processing messages
```

### Testing

**Test coverage added**:
- `test_find_daily_notes_no_duplicates_on_case_insensitive_fs()` - Verifies deduplication works
- `test_extract_gleanings_no_duplicate_processing()` - Verifies no double-extraction

**All 19 gleaning tests passing**:
- Status management (active/inactive/hidden)
- Frontmatter parsing
- Status persistence
- File deduplication
- Extraction without duplicates

### Commits

- `c356fdb`: fix: resolve case-insensitive filesystem duplicate extraction bug + feat: add 'hidden' status support to CLI
- `6db212d`: feat: support multiple gleaning formats and naked URLs
- `aa903e5`: docs: update GLEANINGS.md with multiple format support
- `493143c`: fix: update diagnostic script to reflect current format support
- `ead20e3`: fix: skip title fetching during dry run
- `ef105f4`: fix: remove lowercase daily/journal patterns (user preference)

### Lessons

**Real-world testing is irreplaceable**:
- VM testing (Linux) didn't catch macOS filesystem issues
- Test data had single format; production vault had 5 formats
- User mental models differ from developer assumptions ("daily is BAD")

**Flexibility beats perfection**:
- Supporting 5 formats instead of 1 = 10% more data captured
- Title fetching overhead (~2 min) acceptable for completeness
- "Be liberal in your input" = better UX than forcing format changes

**Diagnostic tools accelerate debugging**:
- `analyze_gleaning_formats.py` made format gaps immediately visible
- Users can self-diagnose before filing bug reports
- Transparency builds trust ("show me what you'll do")

**User feedback is gold**:
- "daily is BAD BAD BAD" → Remove confusing patterns
- "Dry run shouldn't fetch" → Optimize preview performance
- "Any URL is a gleaning" → Expand pattern matching

### Status

✅ **Extraction robustness**: Handles 5 different gleaning formats
✅ **Data completeness**: 100% coverage (766/766 gleanings extracted)
✅ **Filesystem safety**: Case-insensitive filesystem handling
✅ **Performance**: Dry run instant, title fetching only when needed
✅ **Test coverage**: Deduplication and extraction tests passing
✅ **Documentation**: GLEANINGS.md updated with all formats

**Ready for deployment**: Extraction proven robust on production vault.

---

**Next**: Deploy to always-on machine and validate behavioral hypothesis (vault-first habit formation).

---

