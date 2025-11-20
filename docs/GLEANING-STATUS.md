# Gleaning Status Management

**Feature**: Mark gleanings as active or inactive without modifying the source of truth (daily notes)

**Status**: Implemented in Phase 2.5
**Date**: 2025-11-20

---

## Overview

Gleanings can become outdated, broken, or irrelevant over time. This feature allows you to mark gleanings as "inactive" so they're excluded from search results, without altering the daily notes where they originally appeared.

### Core Principles

1. **Daily notes are the source of truth** - Never modified
2. **Status stored separately** - In `.temoa/gleaning_status.json`
3. **Extraction preserves status** - Re-running extraction respects marked statuses
4. **Search respects status** - Inactive gleanings are automatically filtered out

---

## Architecture

### Status Storage

**File**: `.temoa/gleaning_status.json`

**Structure**:
```json
{
  "abc123def456": {
    "status": "inactive",
    "marked_at": "2025-11-20T15:30:00Z",
    "reason": "broken link",
    "history": [
      {
        "status": "inactive",
        "marked_at": "2025-11-20T15:30:00Z",
        "reason": "broken link"
      }
    ]
  }
}
```

### Gleaning Frontmatter

When extraction runs, status is added to each gleaning's frontmatter:

```yaml
---
title: "Example Gleaning"
url: https://example.com
domain: example.com
date: 2025-11-20
source: Daily/2025-11-20.md
gleaning_id: abc123def456
status: inactive
tags: [gleaning]
---
```

### Search Filtering

The `/search` endpoint:
1. Performs semantic search via Synthesis
2. Reads frontmatter from each result
3. Filters out any gleanings with `status: inactive`
4. Returns only active gleanings

---

## Usage

### CLI Commands

#### Mark a gleaning as inactive

```bash
temoa gleaning mark abc123def456 --status inactive --reason "broken link"
```

Output:
```
✓ Gleaning abc123def456 marked as inactive
  Reason: broken link
  Marked at: 2025-11-20T15:30:00Z
```

#### Mark a gleaning as active (restore)

```bash
temoa gleaning mark abc123def456 --status active
```

#### List all gleanings with status

```bash
# List all gleanings (with any status)
temoa gleaning list

# List only inactive gleanings
temoa gleaning list --status inactive

# List only active gleanings
temoa gleaning list --status active

# Output as JSON
temoa gleaning list --status inactive --json-output
```

Output:
```
Gleanings (inactive):

abc123def456
  Status: inactive
  Marked: 2025-11-20T15:30:00Z
  Reason: broken link

def789ghi012
  Status: inactive
  Marked: 2025-11-19T10:15:00Z
  Reason: duplicate

Total: 2
```

#### Show details for a specific gleaning

```bash
temoa gleaning show abc123def456

# Output as JSON
temoa gleaning show abc123def456 --json-output
```

Output:
```
Gleaning: abc123def456

Status: inactive
Marked: 2025-11-20T15:30:00Z
Reason: broken link

History:
  1. inactive at 2025-11-20T15:30:00Z
     Reason: broken link
```

---

### API Endpoints

#### POST /gleanings/{gleaning_id}/status

Mark a gleaning's status.

**Request**:
```bash
curl -X POST "http://localhost:8080/gleanings/abc123def456/status?status=inactive&reason=broken%20link"
```

**Response**:
```json
{
  "gleaning_id": "abc123def456",
  "status": "inactive",
  "marked_at": "2025-11-20T15:30:00Z",
  "reason": "broken link",
  "history": [...]
}
```

#### GET /gleanings

List gleanings by status.

**Request**:
```bash
# All gleanings
curl "http://localhost:8080/gleanings"

# Only inactive
curl "http://localhost:8080/gleanings?status=inactive"

# Only active
curl "http://localhost:8080/gleanings?status=active"
```

**Response**:
```json
{
  "gleanings": {
    "abc123def456": {
      "status": "inactive",
      "marked_at": "2025-11-20T15:30:00Z",
      "reason": "broken link"
    }
  },
  "total": 1,
  "filter": "inactive"
}
```

#### GET /gleanings/{gleaning_id}

Get details for a specific gleaning.

**Request**:
```bash
curl "http://localhost:8080/gleanings/abc123def456"
```

**Response**:
```json
{
  "gleaning_id": "abc123def456",
  "status": "inactive",
  "marked_at": "2025-11-20T15:30:00Z",
  "reason": "broken link",
  "history": [
    {
      "status": "inactive",
      "marked_at": "2025-11-20T15:30:00Z",
      "reason": "broken link"
    }
  ]
}
```

---

## Workflow

### Finding the Gleaning ID

Gleaning IDs are MD5 hashes of the URL (first 12 characters). To find a gleaning's ID:

1. **From the filename**: Gleaning files are named `{id}.md` in `L/Gleanings/`
   ```bash
   ls L/Gleanings/
   # abc123def456.md
   ```

2. **From the frontmatter**: Open the gleaning file and check `gleaning_id` field
   ```yaml
   ---
   gleaning_id: abc123def456
   ---
   ```

3. **Generate from URL**: Calculate MD5 hash yourself
   ```bash
   echo -n "https://example.com" | md5sum | cut -c1-12
   ```

### Marking Inactive Gleanings

**Scenario**: You find a gleaning with a broken link during search.

1. Note the gleaning ID from the file path or frontmatter
2. Mark it as inactive:
   ```bash
   temoa gleaning mark abc123def456 --status inactive --reason "404 error"
   ```
3. The gleaning file remains in `L/Gleanings/` but won't appear in future searches
4. The daily note where it came from is unchanged

### Re-extraction Preserves Status

When you run `temoa extract`, the extraction script:

1. Checks `.temoa/gleaning_status.json` for each gleaning
2. Applies the stored status to the frontmatter
3. Inactive gleanings stay inactive across re-extractions

**Example**:
```bash
# Mark a gleaning inactive
temoa gleaning mark abc123def456 --status inactive

# Re-extract gleanings (daily notes → L/Gleanings/)
temoa extract --full

# The gleaning abc123def456 will still have status: inactive
# in its frontmatter after re-extraction
```

### Restoring Inactive Gleanings

If you marked a gleaning as inactive by mistake:

```bash
# Restore it
temoa gleaning mark abc123def456 --status active

# Re-extract to update frontmatter
temoa extract
temoa reindex

# It will now appear in searches again
```

---

## Implementation Details

### GleaningStatusManager

**Module**: `src/temoa/gleanings.py`

**Key Methods**:
- `get_status(gleaning_id)` - Returns "active" or "inactive" (defaults to "active")
- `mark_status(gleaning_id, status, reason)` - Update status and save
- `get_gleaning_record(gleaning_id)` - Get full status record with history
- `list_gleanings(status_filter)` - List gleanings by status
- `parse_frontmatter_status(content)` - Extract status from markdown frontmatter

### Extraction Integration

**File**: `scripts/extract_gleanings.py`

**Changes**:
1. `GleaningsExtractor` initializes a `GleaningStatusManager`
2. When extracting gleanings, checks status for each gleaning ID
3. Passes status to `Gleaning` object
4. `Gleaning.to_markdown()` includes `status` and `gleaning_id` in frontmatter

### Search Filtering

**File**: `src/temoa/server.py`

**Function**: `filter_inactive_gleanings(results)`

**Logic**:
1. For each search result, read the file at `result["file_path"]`
2. Parse frontmatter to extract status
3. If status is "inactive", exclude from results
4. If status is "active" or missing, include in results
5. If file can't be read, include (fail open)

---

## Testing

### Unit Tests

**File**: `tests/test_gleanings.py`

**Coverage**:
- Status manager initialization
- Getting/setting status
- Status persistence across manager instances
- History tracking
- Frontmatter parsing
- List filtering

**Run tests**:
```bash
uv run pytest tests/test_gleanings.py -v
```

### Integration Testing

1. **Mark a gleaning inactive**:
   ```bash
   temoa gleaning mark abc123def456 --status inactive
   ```

2. **Verify it's in status file**:
   ```bash
   cat .temoa/gleaning_status.json
   ```

3. **Search for the gleaning** - Should not appear in results

4. **Mark it active again**:
   ```bash
   temoa gleaning mark abc123def456 --status active
   ```

5. **Search again** - Should now appear in results

---

## Future Enhancements

### Possible additions (if needed):

1. **More statuses**: `deprecated`, `duplicate`, `archived`
2. **Bulk operations**: Mark multiple gleanings at once
3. **UI integration**: Mark inactive directly from search results
4. **Auto-detection**: Automatically mark broken links as inactive
5. **Export**: Generate report of inactive gleanings

### Not implemented (intentionally):

- **Deletion**: Gleanings are never deleted (daily notes are source of truth)
- **Editing**: Gleanings can't be edited (daily notes are source of truth)
- **Complex workflows**: Keep it simple (just active/inactive)

---

## Troubleshooting

### Gleaning still appears in search after marking inactive

1. Check if status was saved:
   ```bash
   temoa gleaning show abc123def456
   ```

2. Re-extract to update frontmatter:
   ```bash
   temoa extract
   ```

3. Re-index to update Synthesis:
   ```bash
   temoa reindex
   ```

### Status file corrupted

If `.temoa/gleaning_status.json` is corrupted:

1. Backup the file:
   ```bash
   cp .temoa/gleaning_status.json .temoa/gleaning_status.json.bak
   ```

2. Fix JSON manually or delete:
   ```bash
   rm .temoa/gleaning_status.json
   ```

3. Re-mark gleanings as needed

### Can't find gleaning ID

If you know the URL, calculate the ID:

```bash
echo -n "https://example.com/article" | md5sum | cut -c1-12
```

Or search for the URL in `L/Gleanings/`:

```bash
grep -r "https://example.com/article" L/Gleanings/
```

---

## Design Decisions

### Why MD5 hash for IDs?

- Deterministic (same URL → same ID)
- Collision-resistant for our use case
- URL-independent of title/description changes
- 12 characters is enough uniqueness for typical vault sizes

### Why not delete inactive gleanings?

- Daily notes are source of truth
- Re-extraction would recreate deleted gleanings
- Status approach is reversible (can reactivate)
- Preserves history

### Why store status separately?

- Don't modify daily notes (principle #1)
- Frontmatter reflects status during extraction
- Extraction script can apply status consistently
- Easy to backup/restore status file

### Why filter at API level instead of Synthesis?

- Synthesis indexes all files (simpler)
- Filtering is fast (just reading frontmatter)
- Can easily toggle filtering behavior
- Synthesis remains agnostic to status concept

---

**Documentation created**: 2025-11-20
**Feature status**: Implemented and tested
**Phase**: 2.5 (Mobile Validation)
