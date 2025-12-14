# Gleanings Workflow

This document describes how gleanings are extracted, stored, and indexed for semantic search in Temoa.

## What are Gleanings?

**Gleanings** are curated links saved from your daily notes. Each gleaning represents:
- A webpage you found interesting
- A brief description of why it matters
- Temporal context (when you were interested)

## Format

### In Daily Notes

Gleanings are extracted from daily notes in **multiple formats**. The extractor is flexible and handles:

#### Format 1: Markdown Link (Recommended)
```markdown
## Gleanings

- [Title](URL) - Brief description
- [Another Link](URL) - More context
```

#### Format 2: Markdown Link with Timestamp
```markdown
## Gleanings

- [Title](URL)  [14:30]
> Description can be on the next line
```

#### Format 3: Naked URL with Bullet
```markdown
## Gleanings

- https://example.com/article
```
**Note:** Title will be fetched from the page's `<title>` tag automatically.

#### Format 4: Naked URL Bare
```markdown
## Gleanings

https://example.com/article
```
**Note:** Title will be fetched from the page automatically.

#### Format 5: Multi-Line Descriptions
```markdown
## Gleanings

- [Article Title](URL)  [15:54]
> First paragraph of description
> - Bullet point 1
> - Bullet point 2
>
> Second paragraph with more details
```
**Note:** ALL consecutive lines starting with `>` are captured.

### URL Normalization

Gleanings are automatically normalized based on their domain to produce cleaner, more searchable titles and descriptions:

**GitHub Repositories:**
- Title is extracted as `user/repo` (without description suffix)
- Description is cleaned of redundant repo names and "Contribute to..." suffixes
- Emojis are removed from descriptions

**Example:**
```
Before normalization:
  title: "user/repo: A great tool for developers"
  description: "A great tool for developers. - user/repo"

After normalization:
  title: "user/repo"
  description: "A great tool for developers."
```

**Other Domains:**
- Passed through unchanged (backward compatible)

This normalization applies both during extraction (new gleanings) and can be run retroactively on existing gleanings using the backfill script.

**Real Example:**
```markdown
## Gleanings

> what did we surf into now?

- [soimort/translate-shell](https://github.com/soimort/translate-shell)  [06:39]
> Command-line translator using Google Translate, Bing Translator, Yandex.Translate

- https://vrigger.com/info_forces.php?RC=RC0129  [07:42]
> You can use the vRigger software to calculate forces on rope systems

- [The White Noise Playlist](https://thewhitenoiseplaylist.com/)  [13:40]
> The White Noise Playlist
> - Variety of white noise experiences without ads
> - Extended and uninterrupted noise tracks for focus/sleep
> - Founded by Dr. Ir. Stéphane Pigeon
```

### As Individual Notes

After extraction, each gleaning becomes an individual markdown file in `L/Gleanings/`:

**File name**: `{gleaning_id}.md` (e.g., `9c72d1c06194.md`)

**Content**:
```markdown
---
title: "Article Title"
url: https://example.com/article
domain: example.com
created: 2025-11-15
source: Daily/2025/2025-11-15-Fr.md
gleaning_id: 9c72d1c06194
status: active
type: gleaning
description: "Brief description of the article and why it's interesting"
---

# Article Title

Brief description of the article and why it's interesting.

## Link

[Article Title](https://example.com/article)

## Source

Gleaned from [[2025-11-15-Fr]] on 2025-11-15
```

## Extraction Workflow

### Manual Extraction

Extract gleanings from daily notes using the Temoa CLI:

```bash
# Preview what would be extracted (dry run)
temoa extract --dry-run

# Extract new gleanings (incremental, only processes new daily notes)
temoa extract

# Force re-process all files (full extraction)
temoa extract --full
```

**Note about Naked URLs:**
- Extraction will be slower for naked URLs (fetches page titles from web)
- Each naked URL adds ~1-2 seconds (5s timeout per URL)
- Progress is shown: `Fetching title for naked URL: https://...`
- Falls back to domain name if fetch fails

### Automated Extraction

#### Option 1: Cron (Simple)

Edit your crontab:
```bash
crontab -e
```

Add this line to extract daily at 11 PM:
```cron
0 23 * * * /path/to/temoa/scripts/extract_and_reindex.sh >> /path/to/temoa/logs/cron.log 2>&1
```

#### Option 2: Systemd Timer (Recommended)

1. Copy service files:
```bash
sudo cp scripts/automation/temoa-extract.service /etc/systemd/system/
sudo cp scripts/automation/temoa-extract.timer /etc/systemd/system/
```

2. Edit paths in service file:
```bash
sudo nano /etc/systemd/system/temoa-extract.service
# Update WorkingDirectory, ExecStart, User, VAULT_PATH, TEMOA_URL
```

3. Enable and start timer:
```bash
sudo systemctl daemon-reload
sudo systemctl enable temoa-extract.timer
sudo systemctl start temoa-extract.timer
```

4. Check timer status:
```bash
sudo systemctl status temoa-extract.timer
sudo systemctl list-timers --all | grep temoa
```

5. View logs:
```bash
sudo journalctl -u temoa-extract.service -f
```

## Re-indexing

After extracting gleanings, you need to trigger re-indexing so they become searchable.

### Via CLI (Recommended)

```bash
temoa reindex --vault ~/Obsidian/your-vault
```

### Via API

If Temoa server is running:
```bash
curl -X POST http://localhost:8080/reindex?force=false
```

### Via Extraction Script

The `extract_and_reindex.sh` script does both automatically:
```bash
./scripts/extract_and_reindex.sh
```

## Normalizing Existing Gleanings

If you have existing gleanings that were extracted before URL normalization was implemented, you can normalize them retroactively:

### Preview Changes (Dry Run)

```bash
uv run python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/your-vault --dry-run
```

This will show you what would be changed without modifying any files.

### Apply Normalization

```bash
uv run python scripts/normalize_existing_gleanings.py --vault-path ~/Obsidian/your-vault
```

### Reindex After Normalization

After normalizing, reindex so the search index picks up the changes:

```bash
temoa reindex --vault ~/Obsidian/your-vault
```

## State Management

Extraction state is tracked in `.temoa/extraction_state.json`:

```json
{
  "version": "1.0",
  "created_at": "2025-11-19T...",
  "last_run": "2025-11-19T...",
  "extracted_gleanings": {
    "9c72d1c06194": {
      "id": "9c72d1c06194",
      "title": "...",
      "url": "...",
      "date": "...",
      ...
    }
  },
  "processed_files": [
    "Daily/2025/2025-11-15-Fr.md",
    ...
  ]
}
```

This ensures:
- **No duplicates**: Same gleaning URL won't be extracted twice
- **Incremental extraction**: Only new files processed by default
- **Auditability**: Track what was extracted and when

## Maintaining Gleanings

The maintenance tool checks link health and enriches gleanings with metadata.

### What It Does

```bash
temoa gleaning maintain
```

The maintenance tool checks if URLs are alive using HEAD/GET requests, fetches meta descriptions from live URLs, automatically marks broken links as inactive, and updates frontmatter with descriptions and status information.

### Usage Examples

```bash
# Dry run (preview changes)
temoa gleaning maintain --dry-run

# Full maintenance (check all gleanings)
temoa gleaning maintain

# Only check links (skip descriptions)
temoa gleaning maintain --no-add-descriptions

# Only add descriptions (skip link checking)
temoa gleaning maintain --no-check-links

# Slow down requests (be nice to servers)
temoa gleaning maintain --rate-limit 2.0

# Custom timeout
temoa gleaning maintain --timeout 15
```

### What Gets Updated

The description field uses meta description from the `<meta name="description">` tag without truncation, falling back to `<meta property="og:description">` if missing. Only gleanings without existing descriptions are updated, preserving manually-written content.

The status field is set to `inactive` for dead links (404, timeout, or connection errors) with reasons recorded in `.temoa/gleaning_status.json`. Live links remain `active`.

### Rate Limiting

The tool adds a 1-second delay between requests by default to be respectful to web servers. Adjust with `--rate-limit 2.0` for slower checking, or use `--timeout 10` to control response wait time.

### Output Example

```
Maintaining 661 gleanings
Options:
  Check links: True
  Add descriptions: True
  Mark dead inactive: True
  Dry run: False
  Rate limit: 1.0s between requests

  Checking: FastAPI Best Practices
    ✓ Link alive (200)
    ✓ Added description (145 chars)
    ✓ Updated: description

  Checking: Old Tutorial Site
    ✗ Link dead: HTTP 404
    → Marked as inactive
    ✓ Updated: status

============================================================
Maintenance complete!
Total gleanings: 661
Checked: 661
  Alive: 650
  Dead: 11
  Errors: 0
Descriptions added: 423
Descriptions skipped: 238
Marked inactive: 11
============================================================
```

### When to Run

Run maintenance after initial extraction to enrich gleanings with descriptions, periodically (monthly) to check for link rot, before re-indexing to ensure metadata is up-to-date, and after bulk imports to add missing descriptions.

### Script Version

You can also run the maintenance tool as a standalone script:

```bash
python scripts/maintain_gleanings.py \
  --vault-path ~/Obsidian/vault \
  --dry-run

python scripts/maintain_gleanings.py \
  --vault-path ~/Obsidian/vault \
  --check-links \
  --add-descriptions \
  --mark-dead-inactive \
  --rate-limit 1.0
```

## Searching Gleanings

Once indexed, gleanings are searchable like any other note:

```bash
# Via Temoa API
curl "http://localhost:8080/search?q=FastAPI&limit=10"

# Via Temoa web UI
open http://localhost:8080/

# Via Synthesis directly
cd synthesis
uv run main.py search "FastAPI best practices" --json
```

Gleanings benefit from semantic search:
- Find related concepts even without exact keyword matches
- Discover forgotten links from similar topics
- Time-based analysis (archaeology) of your interests

## Troubleshooting

### Gleanings not found in search

1. Check extraction state:
```bash
cat .temoa/extraction_state.json | jq '.extracted_gleanings | length'
```

2. Verify files exist:
```bash
ls -1 L/Gleanings/ | wc -l
```

3. Trigger re-indexing:
```bash
curl -X POST http://localhost:8080/reindex?force=true
```

4. Check Synthesis stats:
```bash
curl http://localhost:8080/stats
```

### Extraction fails

1. Check daily note format:
   - Must have `## Gleanings` section (case-sensitive)
   - Format: `- [Title](URL) - Description`
   - URL must be valid

2. Check logs:
```bash
tail -f logs/extraction.log
```

3. Run with dry-run to debug:
```bash
python scripts/extract_gleanings.py --vault-path . --dry-run
```

### Duplicates detected

This is expected! The system tracks:
- URL-based IDs (same URL = same gleaning)
- Already-extracted gleanings are skipped
- Use `--full` flag to re-process if needed

## Best Practices

Use consistent formatting with the `- [Title](URL) - Description` pattern. Write descriptive titles (not just domain names) and useful descriptions that explain why you saved each link. Automate daily extraction via cron or systemd for regular updates, re-index after extraction to ensure new gleanings are searchable, and periodically review extraction logs for issues.

## Future Enhancements

Potential improvements to gleanings system:

- **Tag inference**: Automatically suggest tags from URL/description
- **Duplicate URL detection**: Warn if URL already gleaned
- **Archive integration**: Save full text/PDF for offline access
- **Related gleanings**: Show similar gleanings when viewing one
- **Gleaning stats**: Track most-gleaned domains, topics over time
- **Mobile app**: Add gleanings directly from phone browser

---

**See also**:
- [Phase 2 Implementation](phases/phase-2-gleanings.md)
- [Extraction Script](../scripts/extract_gleanings.py)
- [Migration Script](../scripts/migrate_old_gleanings.py)
- [Automation Scripts](../scripts/automation/)
