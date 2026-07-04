# Gleanings System: A Chronology

This document traces the history of the gleanings system — what it is, what we built, what broke, and what we discovered needed rethinking. It is a record, not a design document.

---

## What Is a Gleaning

A gleaning is a link saved from a daily note — something that was interesting enough to capture but either not worth writing a full note about, or inherently a snapshot rather than text (like a GitHub repository that changes over time). The essential information is: what it is (URL and title), why it was interesting (a description in your own words, in the moment), and when you found it (the date of the daily note). The temporal dimension is not incidental — knowing *when* you were interested in something is part of the value.

---

## The 505 Pre-Existing Links

Before Temoa existed, there was a project called `old-gleanings` — a JSON-based system that had accumulated 505 links with metadata including categories, tags, and timestamps. It had collapsed under its own complexity (2,771 lines of code, 15+ category types, extensive state management). The links were there, the organization had failed, and the useful piece — the URLs and their metadata — needed to be rescued.

This gave Temoa's gleanings system a useful concrete target: migrate these 505 links into a searchable format. It also established the design principle: make it simpler than what failed.

---

## Phase 2: The First Extraction System (November 2025)

Phase 2 of Temoa was built in a single day (2025-11-19) and delivered:

- An extraction script that parsed daily notes looking for `## Gleanings` sections and pulled out markdown links in the format `- [Title](URL) - Description`
- A migration script that converted the 505 old-gleanings JSON entries into individual markdown files
- Deduplication via MD5 hash of the URL (same URL = same ID = same file, `9c72d1c06194.md` style)
- Incremental extraction with state tracking in `.temoa/extraction_state.json` so daily notes weren't reprocessed
- A re-indexing endpoint so the search index could be updated after extraction
- The `temoa extract` CLI command

The extracted gleanings lived in `L/Gleanings/` as individual markdown files with frontmatter (`title`, `url`, `domain`, `created`, `source`, `gleaning_id`, `status`, `type`, `description`) and a simple body with the title as a heading, the description as a paragraph, and a link back to the source daily note.

The test extraction against 742 production daily notes found 1,368 total gleanings and created 661 new files (the rest were duplicates by URL hash). After a forced reindex, semantic search worked: searching "tmux github" surfaced relevant gleanings with similarity scores in the 0.5–0.6 range. The end-to-end workflow was proven.

What failed immediately on production: the regex pattern only matched one format, the `--full` flag didn't actually reset state, and CLI argument names were wrong. These were fixed in the same session.

---

## Phase 2.5: Format Flexibility (November 2025)

A shakedown pass a few days later (2025-11-21) revealed a 10% data loss problem: the extraction was only finding 689 of 766 URLs in the vault. The cause was that real daily notes used multiple formats that the original regex didn't handle.

A count of the vault showed five distinct patterns in the wild:

- `- [Title](URL) - Description` — the canonical form the extractor expected
- `- [Title](URL)  [HH:MM]` — link with a timestamp appended, description on the next line as a blockquote
- `- https://example.com/bare-url` — naked URL with a bullet, no title
- `https://example.com/bare-url` — naked URL with no bullet at all
- Multi-line blockquote descriptions (`> line 1\n> line 2\n>\n> paragraph 2`)

The extractor was rewritten to handle all five. For naked URLs, a title-fetching function was added that reads the first 8KB of the page and extracts the `<title>` tag, falling back to the domain name. This added about 1.5 seconds per naked URL (the vault had ~77 of them, so roughly two extra minutes for a full extraction). A dry-run mode was added to skip the title fetching when just previewing.

A macOS-specific bug was also fixed: the glob patterns included both `Daily/**/*.md` and `daily/**/*.md` for cross-platform compatibility, but on APFS (case-insensitive by default) both patterns matched the same files. The output was confusing even though deduplication via `Path.resolve()` prevented double-processing. The lowercase patterns were removed entirely — the user's vault used `Daily/` and that was all that mattered.

After these fixes: 766/766 URLs extracted, 0% loss.

---

## GitHub Enrichment (Late 2025)

A GitHub-specific enrichment system was added via `maintain_gleanings.py` with an `--enrich-github` flag. For any gleaning pointing to a GitHub repository URL, it would call the GitHub API and add frontmatter fields: `github_language`, `github_stars`, `github_topics`, `github_archived`, `github_last_push`, and `github_readme_excerpt` (first paragraph of the README, up to 500 characters).

The enrichment also updated the `title` field to the `user/repo: Description` format using the API's description field, and `normalizers.py` cleaned up obvious redundancies (removing "GitHub - " prefixes, stripping "Contribute to user/repo" suffixes, removing emojis from the description field).

The maintenance tool was rate-limited (2.5 seconds between API calls), idempotent (skipping already-enriched gleanings by checking for `github_stars`), and showed progress with an ETA for large vaults. By February 2026 the vault had grown to 1,054 gleanings, 347 of which (33%) were GitHub repositories.

---

## The February 2026 Rethink

By February 2026, two things happened in parallel: a data quality analysis of the existing gleanings, and a more fundamental question about what GitHub gleanings were actually supposed to contain.

### The Data Quality Problem

An audit of all 1,054 gleanings turned up a cluster of formatting problems:

- 25 gleanings had emojis in text fields (11 of them GitHub gleanings where the API description contained emoji characters like `🕵️‍♂️` or `🚀`)
- 123 gleanings had `github_topics` stored as JSON arrays in YAML frontmatter (`["topic1", "topic2"]`) rather than proper YAML lists — the enrichment script had been writing the Python list repr directly into the file
- 2 files had zero-width characters (`\u200B`–`\u200D`)
- 2 files had RTL/LTR direction marks (`\u200E`–`\u200F`, `\u202A`–`\u202E`)
- 21 files had non-breaking spaces
- 65 files had smart quotes
- 70 files had en/em dashes

The emojis and invisible unicode were the high-priority items — they could break indexing. The JSON-in-YAML problem was also a real issue since YAML parsers would either choke or produce a string instead of a list.

The normalizer had been removing emojis from the `description` field, but the `title` field was getting the API description *before* normalization, so emoji characters ended up in YAML frontmatter. Inconsistent handling.

### The Structural Problem

The deeper issue: GitHub gleanings were supposed to capture "why this was interesting" but they didn't. The API description field is what the repository author wrote about their project. It's not what the gleaner thought was worth saving. The `github_readme_excerpt` contained better information but wasn't being surfaced as the primary description.

The ideal GitHub gleaning structure became clear:

- `title`: just `user/repo` — clean, no description appended
- `description`: priority order — user-written context from the daily note (if present), then README excerpt (usually better written than the API description), then API description as fallback; all emoji-free
- `github_description`: the original API description, kept separately for reference
- `github_topics`: proper YAML list format
- All other GitHub metadata fields preserved

The key insight was that enrichment should *add* GitHub data without *overwriting* user-written descriptions. If someone wrote "good tool for calculating rope forces in rigging systems" in their daily note, that context is more valuable than what the repo author wrote, and it should survive the enrichment pass.

### What Was Broken

Summarizing what the February rethink identified:

1. Emojis and other problematic unicode appearing in frontmatter fields (including title)
2. `github_topics` stored as JSON arrays instead of YAML lists (breaks parsers)
3. GitHub title format including the API description, making it long and often emoji-contaminated
4. GitHub enrichment overwriting user-written descriptions with API descriptions
5. README excerpt added as a separate field but not used as the primary description source
6. No `clean_text()` utility shared across the codebase — each component handled (or didn't handle) text cleaning independently

---

## Where Things Stand

As of early March 2026, the February issues are documented but the fixes are not fully implemented. The extraction system works and handles all five input formats. The maintenance tool works and can enrich GitHub gleanings. But the data quality problems — emoji in frontmatter, JSON arrays in YAML, API descriptions overwriting user context — remain in the existing 1,054 gleaning files.

The planned fix has three parts: a shared `clean_text()` function that strips emojis, zero-width characters, RTL marks, smart quotes, and normalizes whitespace; an update to the GitHub normalizer to produce `user/repo` titles and prioritize README excerpts; and a migration script to clean up and reorganize the existing GitHub gleanings without losing user-written descriptions.

None of that has been built yet.
