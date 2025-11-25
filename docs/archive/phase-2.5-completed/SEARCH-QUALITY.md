# Search Quality Improvements

**Date**: 2025-11-20
**Status**: Implemented in Phase 2.5

## Overview

During Phase 2.5 mobile validation, real-world usage revealed that semantic search was returning too many low-relevance results ("fluff"). This document describes the improvements implemented to address this issue.

---

## Changes Made

### 1. Minimum Similarity Score Filtering

**Problem**: Search returned results with low similarity scores that weren't relevant.

**Solution**: Added `min_score` parameter to filter out low-relevance results.

**Implementation**:
- Default threshold: `0.3` (30% similarity)
- Configurable per-query via API or CLI
- Filters results before applying limit

**API Usage**:
```bash
# Default (min_score=0.3)
curl "http://localhost:8080/search?q=obsidian"

# Higher threshold for more relevant results
curl "http://localhost:8080/search?q=obsidian&min_score=0.5"

# Lower threshold for broader results
curl "http://localhost:8080/search?q=obsidian&min_score=0.2"
```

**CLI Usage**:
```bash
# Default (min_score=0.3)
temoa search "obsidian"

# Higher threshold
temoa search "obsidian" --min-score 0.5

# Lower threshold
temoa search "obsidian" -s 0.2
```

**Response Format**:
```json
{
  "query": "obsidian",
  "results": [...],
  "total": 8,
  "min_score": 0.3,
  "filtered_count": {
    "by_score": 12,
    "by_status": 2,
    "total_removed": 14
  }
}
```

---

### 2. Better Embedding Model

**Problem**: `all-MiniLM-L6-v2` (384d) is fast but lower quality, leading to poor semantic matching.

**Solution**: Switch to `all-mpnet-base-v2` (768d) for better search quality.

**Model Comparison**:

| Model | Dimensions | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| **all-MiniLM-L6-v2** | 384 | Fast | Good | Quick searches, large vaults |
| **all-mpnet-base-v2** ✅ | 768 | Medium | Better | **Recommended default** |
| all-MiniLM-L12-v2 | 384 | Medium | Better | Balance speed/quality |
| multi-qa-mpnet-base-cos-v1 | 768 | Medium | Best (Q&A) | Question-answer searches |

**New Default**: `all-mpnet-base-v2` (updated in config template)

---

## How to Switch Models

### Option 1: Update Existing Config (Recommended)

Edit your config file (usually `~/.config/temoa/config.json`):

```json
{
  "vault_path": "~/Obsidian/your-vault",
  "synthesis_path": "~/projects/temoa/synthesis",
  "index_path": null,
  "default_model": "all-mpnet-base-v2",  ← Change this line
  "server": {...},
  "search": {...}
}
```

**Then reindex your vault**:
```bash
# This will download the new model and rebuild embeddings
temoa index --force

# Takes ~30-60 seconds depending on vault size
# Model download: ~420MB (one-time)
# Indexing time: ~20-30s for 2000 files
```

### Option 2: Test Different Models

You can test different models without changing your config:

```bash
# Try mpnet model
temoa search "obsidian" --model all-mpnet-base-v2

# Try MiniLM-L12 (middle ground)
temoa search "obsidian" --model all-MiniLM-L12-v2

# Try Q&A optimized model
temoa search "obsidian" --model multi-qa-mpnet-base-cos-v1
```

**Note**: Each model requires reindexing and keeps separate embeddings, so switching models repeatedly will use more disk space.

---

## Migration Guide

### For Existing Deployments

**Current setup**: Running with `all-MiniLM-L6-v2`

**Migration steps**:

1. **Stop the server**:
   ```bash
   # If running via systemd
   sudo systemctl stop temoa

   # If running manually
   pkill -f "temoa server"
   ```

2. **Update config**:
   ```bash
   vim ~/.config/temoa/config.json
   # Change "default_model" to "all-mpnet-base-v2"
   ```

3. **Reindex vault** (this will download the new model):
   ```bash
   temoa index --force
   ```

   Expected output:
   ```
   Loading model: all-mpnet-base-v2 (this may take 10-15s)...
   ✓ Model loaded
   Processing vault...
   ████████████████████ 2281/2281 files
   ✓ Index built successfully
   Files indexed: 2281
   ```

4. **Restart server**:
   ```bash
   # If using systemd
   sudo systemctl start temoa

   # If running manually
   temoa server
   ```

5. **Test search quality**:
   ```bash
   # Try some searches that were returning "fluff"
   temoa search "your problematic query" --min-score 0.3
   ```

**Disk space note**: The new model uses ~420MB. Old embeddings (~50-100MB) can be deleted after confirming the new model works well.

---

## Performance Impact

### Model Loading (One-Time at Startup)

| Model | Load Time | Memory |
|-------|-----------|--------|
| all-MiniLM-L6-v2 | ~10s | ~250MB |
| **all-mpnet-base-v2** | ~13-15s | ~420MB |

### Search Time (Per Query)

| Model | Cold Start | Warm |
|-------|-----------|------|
| all-MiniLM-L6-v2 | ~400ms | ~400ms |
| **all-mpnet-base-v2** | ~450ms | ~450ms |

**Impact**: ~50ms slower per search (still well under 2s target ✅)

### Disk Space

| Model | Model Size | Embeddings (2000 files) |
|-------|-----------|------------------------|
| all-MiniLM-L6-v2 | ~90MB | ~30MB |
| **all-mpnet-base-v2** | ~420MB | ~60MB |

**Total**: ~480MB for model + embeddings

---

## Tuning min_score for Your Use Case

The optimal `min_score` depends on your vault and query patterns:

### Finding the Right Threshold

**Too many results** (lots of irrelevant matches):
- Increase `min_score`: Try 0.4, 0.5, or higher
- Example: `temoa search "obsidian" -s 0.5`

**Too few results** (missing relevant matches):
- Decrease `min_score`: Try 0.2 or 0.1
- Example: `temoa search "obsidian" -s 0.2`

**Good balance** (current default):
- Use `min_score=0.3` (filters obvious non-matches while keeping relevant results)

### Recommended Thresholds by Query Type

| Query Type | min_score | Example |
|-----------|-----------|---------|
| **Broad topic** | 0.2-0.3 | "AI", "productivity" |
| **Specific concept** | 0.3-0.4 | "semantic search", "Tailscale" |
| **Exact match** | 0.5+ | "Obsidian vault sync", "FastAPI lifespan" |

---

## Testing Your Setup

After switching models and updating `min_score`, test with queries that were returning "fluff":

```bash
# Test with default threshold
temoa search "your problematic query"

# If still too much fluff, increase threshold
temoa search "your problematic query" -s 0.4

# Compare before/after
temoa search "obsidian" -s 0.0  # See all results (no filtering)
temoa search "obsidian" -s 0.3  # With filtering (default)
temoa search "obsidian" -s 0.5  # More aggressive filtering
```

---

## Rollback Instructions

If the new model doesn't work well for your use case:

1. **Edit config** back to `all-MiniLM-L6-v2`
2. **Reindex**: `temoa index --force`
3. **Restart server**

The old model embeddings are preserved (stored separately), so rollback is fast if done immediately. After several days, old embeddings may be cleaned up.

---

## Phase 2.5 Learnings

**What triggered these changes**: Real-world mobile usage in Phase 2.5

**User feedback**: "Search returning a lot of fluff" + "UI hard to read and use"

**Root causes identified**:
1. No relevance threshold → low-quality results included
2. Lower-quality model → poor semantic matching
3. UI issues → separate task (not addressed here)

**Solutions implemented**:
1. ✅ `min_score` parameter with sensible default (0.3)
2. ✅ Better model recommendation (all-mpnet-base-v2)
3. ⏸️ UI improvements → Phase 3

**Validation needed**: Test search quality improvements over 1-2 weeks of real usage.

---

## Next Steps

1. **Deploy changes** to your always-on machine
2. **Update config** to use `all-mpnet-base-v2`
3. **Reindex vault** with new model
4. **Test search quality** with real queries
5. **Tune `min_score`** based on results
6. **Document friction points** for Phase 3 UI improvements

---

**Created**: 2025-11-20
**Phase**: 2.5 (Mobile Validation)
**Status**: Ready for testing
