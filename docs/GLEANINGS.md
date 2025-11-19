# Gleanings Workflow

This document describes how gleanings are extracted, stored, and indexed for semantic search in Temoa.

## What are Gleanings?

**Gleanings** are curated links saved from your daily notes. Each gleaning represents:
- A webpage you found interesting
- A brief description of why it matters
- Temporal context (when you were interested)

## Format

### In Daily Notes

Gleanings are extracted from daily notes using this format:

```markdown
## Gleanings

- [Title](URL) - Description of why this link matters
- [Another Link](URL) - More context about this resource
```

**Example:**
```markdown
## Gleanings

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices) - Async patterns, project structure, testing
- [Building a Local RAG System](https://news.ycombinator.com/item?id=38309611) - HN discussion on local vs cloud RAG, privacy considerations
```

### As Individual Notes

After extraction, each gleaning becomes an individual markdown file in `L/Gleanings/`:

**File name**: `{gleaning_id}.md` (e.g., `9c72d1c06194.md`)

**Content**:
```markdown
---
url: https://example.com/article
domain: example.com
date: 2025-11-15
source: Daily/2025/2025-11-15-Fr.md
tags: [gleaning]
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

Extract gleanings from daily notes:

```bash
# Preview what would be extracted
python scripts/extract_gleanings.py --vault-path ~/Obsidian/vault --dry-run

# Extract gleanings
python scripts/extract_gleanings.py --vault-path ~/Obsidian/vault

# Force re-process all files (not just new ones)
python scripts/extract_gleanings.py --vault-path ~/Obsidian/vault --full
```

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

### Via API (Recommended)

If Temoa server is running:
```bash
curl -X POST http://localhost:8080/reindex?force=true
```

### Via Extraction Script

The `extract_and_reindex.sh` script does both automatically:
```bash
./scripts/extract_and_reindex.sh
```

### Manual Re-indexing

If running Synthesis directly (not via Temoa server):
```bash
cd old-ideas/synthesis
uv run main.py reindex
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

## Migration from Old Gleanings

If you have historical gleanings from the old `old-gleanings` project:

```bash
# Preview migration
python scripts/migrate_old_gleanings.py \
  --vault-path ~/Obsidian/vault \
  --old-gleanings old-ideas/old-gleanings/gleanings_state.json \
  --dry-run

# Migrate all historical gleanings
python scripts/migrate_old_gleanings.py \
  --vault-path ~/Obsidian/vault \
  --old-gleanings old-ideas/old-gleanings/gleanings_state.json
```

Migrated gleanings will have:
- Original metadata preserved (category, tags, timestamp)
- `migrated_from: old-gleanings` in frontmatter
- Original gleaning ID maintained

## Searching Gleanings

Once indexed, gleanings are searchable like any other note:

```bash
# Via Temoa API
curl "http://localhost:8080/search?q=FastAPI&limit=10"

# Via Temoa web UI
open http://localhost:8080/

# Via Synthesis directly
cd old-ideas/synthesis
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

1. **Consistent format**: Stick to the `- [Title](URL) - Description` pattern
2. **Descriptive titles**: Use meaningful titles (not just domain names)
3. **Useful descriptions**: Explain WHY you saved this link
4. **Daily extraction**: Automate via cron/systemd for regular updates
5. **Re-index after extraction**: Ensure new gleanings are searchable
6. **Review periodically**: Check extraction logs for issues

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
