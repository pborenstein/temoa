# Search Harness Implementation Plan

## Goal

Build a "Score Mixer" / "Harness" that lets you:
1. See all raw component scores for search results
2. Adjust weights and watch results re-sort instantly (client-side)
3. Identify which changes need server re-fetch
4. Save good combinations as profiles
5. Work across CLI, API, and Web UI (parity)

## Key Insight: Two-Tier Parameters

**Client-side re-mixable** (instant, no fetch):
- `semantic_weight` - how much semantic score matters
- `bm25_weight` - how much BM25 score matters
- `tag_multiplier` - boost for tag matches (currently fixed 5x)
- `time_weight` - how much recency matters

**Server-side** (requires re-fetch):
- `hybrid_weight` - changes which docs are retrieved
- `rerank` - whether cross-encoder runs at all
- `expand_query` - modifies query before search
- `limit`, `min_score` - filtering

## Bugs to Fix First

1. **cross_encoder_score display bug**: `search.html:2407` looks for `rerank_score` but backend sets `cross_encoder_score`

2. **Pipeline diagram wrong**: docs/SEARCH-MECHANISMS.md shows 7 stages, should be 8 (chunk deduplication)

## Implementation

### Phase 1: API Enhancement

Add `?harness=true` parameter to existing `/search` endpoint (simpler than new endpoint).

**Enhanced response when harness=true:**
```json
{
  "results": [{
    "scores": {
      "semantic": 0.72,
      "bm25": 12.4,
      "bm25_base": 2.48,
      "tag_boosted": true,
      "tags_matched": ["obsidian"],
      "cross_encoder": 0.891,
      "time_boost": 0.15
    },
    "final_score": 0.0394,
    ...
  }],
  "harness": {
    "mix": {
      "semantic_weight": 1.0,
      "bm25_weight": 1.0,
      "tag_multiplier": 5.0,
      "time_weight": 1.0
    },
    "server": {
      "hybrid_weight": 0.5,
      "rerank": true,
      "expand_query": false
    }
  }
}
```

**Files:**
- `src/temoa/server.py` - add harness parameter, restructure score output
- `src/temoa/synthesis.py` - ensure all raw scores preserved

### Phase 2: Web UI Harness Page

Create a **separate `harness.html` page** for score mixing experiments. This keeps the production search UI (`search.html`) stable while we iterate on the harness.

**Why separate?**
- Can use existing search while developing harness
- Keeps `search.html` simple for normal use
- Dedicated space for experimentation
- Can merge into search.html later if desired

**Layout:**
```
┌─────────────────────────────────────────────┐
│ Score Mixer                    [← Search]   │
├─────────────────────────────────────────────┤
│ Query: [____________________] [Search]      │
│ Vault: [dropdown]  Profile: [dropdown]      │
├─────────────────────────────────────────────┤
│ Mix Weights (instant re-sort)               │
│ Semantic: [1.0] BM25: [1.0]                 │
│ Tags: [5.0]     Time: [1.0]                 │
├─────────────────────────────────────────────┤
│ Server (re-fetch needed)                    │
│ Hybrid: [0.5]  [x]Rerank [ ]Expand          │
│                       [Re-Search]           │
├─────────────────────────────────────────────┤
│ [Save Profile...] [Export JSON]             │
├─────────────────────────────────────────────┤
│ Results (showing scores)                    │
│ ┌─────────────────────────────────────────┐ │
│ │ 1. Title                                │ │
│ │    sem: 72% | bm25: 12.4 | tags: +5x    │ │
│ │    time: +15% | cross: 89% | final: 3.9%│ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Behavior:**
- Mix weight changes → instant client-side re-sort
- Server param changes → enable "Re-Search" button
- Number inputs (not sliders)
- Results always show all score components
- Link back to main search UI

**Files:**
- `src/temoa/ui/harness.html` - new standalone harness page
- `src/temoa/server.py` - add route for `/harness`

**Client-side remix function:**
```javascript
function remixResults(results, mix) {
  const normalize = (bm25) => bm25 / (bm25 + 10)  // 0-1 range
  return results.map(r => ({
    ...r,
    mixed: (r.scores.semantic * mix.semantic_weight +
            normalize(r.scores.bm25) * mix.bm25_weight) *
           (r.scores.tag_boosted ? mix.tag_multiplier : 1) *
           (1 + r.scores.time_boost * mix.time_weight)
  })).sort((a, b) => b.mixed - a.mixed)
}
```

### Phase 3: CLI Harness Command

```bash
# Show all scores in table format
temoa harness "obsidian sync" --vault amoxtli

# With custom mix weights
temoa harness "query" --semantic 1.5 --bm25 0.5 --tags 10

# Save as profile
temoa harness "query" --save-profile my-custom

# Export profile JSON
temoa harness "query" --export my-custom.json
```

**Output format:**
```
Harness: "obsidian sync"
Mix: sem=1.0 bm25=1.0 tags=5.0 time=1.0
Server: hybrid=0.5 rerank=true expand=false

 # │ Final  │ Sem   │ BM25  │ Tags │ Time │ Title
───┼────────┼───────┼───────┼──────┼──────┼──────────────────
 1 │ 0.0394 │ 72.0% │ 12.4  │ +5x  │ +15% │ Obsidian Sync...
 2 │ 0.0312 │ 68.5% │  8.2  │  -   │ +8%  │ Sync Alterna...
```

**Files:**
- `src/temoa/cli.py` - add `temoa harness` command

### Phase 4: Profile Saving

**Web UI:** localStorage only + export JSON (user decision: keep it simple, no server writes)
**CLI:** `--save-profile name` writes to config.json
**API:** Skip POST /profiles for now (not needed if Web UI uses localStorage)

**Extended SearchProfile:**
```python
@dataclass
class SearchProfile:
    ...existing fields...

    # New: client-side mix formula
    mix_formula: Optional[Dict[str, float]] = None
    # {"semantic_weight": 1.0, "bm25_weight": 1.0,
    #  "tag_multiplier": 5.0, "time_weight": 1.0}
```

**Files:**
- `src/temoa/search_profiles.py` - add mix_formula field, save function
- `src/temoa/config.py` - profile persistence (CLI only)

## Files Summary

| File | Changes |
|------|---------|
| `src/temoa/server.py` | `?harness=true` param, `/harness` route |
| `src/temoa/synthesis.py` | Ensure raw scores preserved |
| `src/temoa/ui/harness.html` | New standalone harness page with remix function |
| `src/temoa/cli.py` | `temoa harness` command |
| `src/temoa/search_profiles.py` | mix_formula field, profile saving |
| `docs/SEARCH-MECHANISMS.md` | Fix pipeline diagram (8 stages) |

## Implementation Order

1. Fix bugs (cross_encoder display, pipeline diagram) ✅
2. API: add harness=true response format ✅
3. Web UI: new harness.html page + client-side remix
4. CLI: harness command
5. Profile saving (all interfaces)

## Verification

1. Search with harness=true, verify all scores in response
2. Adjust mix weights in UI, verify instant re-sort without network
3. Change server param, verify "Re-Search" required
4. Save profile, verify it appears in profile list
5. CLI harness output matches UI scores
6. Saved profile produces same results when selected
