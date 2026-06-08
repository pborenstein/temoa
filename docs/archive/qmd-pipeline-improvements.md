# Plan: Pipeline Improvements from qmd

**Status**: Not started
**Created**: 2026-04-13
**Phase**: Experimentation

Three targeted improvements borrowed from qmd's design, in order of expected impact.

---

## Improvement 1: Position-Aware Score Blending

### What's wrong now

`reranker.py` sorts results purely by cross-encoder score. This discards the RRF signal entirely after reranking. qmd's research shows this destroys high-confidence exact matches: when the reranker disagrees with RRF at the top positions, the exact match loses.

### What to change

After reranking, blend cross-encoder score and RRF score using a ratio that varies by rank position:

| Rank | RRF weight | Reranker weight | Rationale |
|------|-----------|-----------------|-----------|
| 1–3  | 75% | 25% | Preserve exact matches; reranker can demote false positives |
| 4–10 | 60% | 40% | Balance retrieval and reranking signals |
| 11+  | 40% | 60% | Trust reranker more in the long tail |

Both scores need to be normalized to [0,1] before blending (RRF scores are not bounded).

### Where to change it

`src/temoa/reranker.py` — `CrossEncoderReranker.rerank()` currently returns `reranked[:top_k]` sorted by `cross_encoder_score`. Add a blending step after scoring:

```python
max_rrf = max(r.get('rrf_score', 0) for r in candidates) or 1.0
for i, result in enumerate(reranked):
    norm_reranker = (result['cross_encoder_score'] + 1) / 2  # [-1,1] → [0,1]
    norm_rrf = result.get('rrf_score', 0) / max_rrf
    rank = i + 1
    if rank <= 3:
        rrf_w, rer_w = 0.75, 0.25
    elif rank <= 10:
        rrf_w, rer_w = 0.60, 0.40
    else:
        rrf_w, rer_w = 0.40, 0.60
    result['final_score'] = rrf_w * norm_rrf + rer_w * norm_reranker
reranked.sort(key=lambda r: r['final_score'], reverse=True)
```

Note: tag-boosted results (marked `tag_boosted: True` in synthesis.py) should have their position preserved — don't let blending demote them back below non-tag results. Check for the flag before computing position.

### How to test

Use the search harness (`src/temoa/ui/harness.html`) with a query for a proper noun that also has conceptually related notes. Compare rank ordering before and after. The proper noun should stay at rank 1-2; conceptually similar but less exact matches should be 3+.

---

## Improvement 2: Heading-Aware Chunking

### What's wrong now

Chunking uses a sliding character window (`chunk_size=2000, chunk_overlap=400`). This splits mid-sentence, mid-paragraph, and through section boundaries indiscriminately. A chunk that starts mid-paragraph loses the heading context that explains what the section is about.

### What to change

Score potential break points before committing to a cut. When the current chunk approaches `chunk_size`, look ahead up to 200 tokens for the highest-scoring break:

| Break type | Score |
|-----------|-------|
| H1 (`# `) | 100 |
| H2 (`## `) | 90 |
| H3+ (`### `) | 70 |
| Code fence (` ``` `) | 80 |
| Blank line after paragraph | 20 |
| List item (`- `, `* `, `1. `) | 5 |

Cut at the highest-scoring break found. If no break is found in the lookahead window, fall back to word boundary (current behavior). Never split inside a code fence.

Additionally: prepend the last seen heading to each chunk as context, so a chunk starting mid-section knows what section it's in. Format: `[Section: <heading text>]\n\n<chunk content>`.

### Where to change it

`src/temoa/synthesis.py` — the chunking logic is called around line 1120. Read how `synthesis/` implements chunking and modify it directly. The break-point scoring logic belongs in the chunking method itself, not as a pre-processing step.

### How to test

Index a long structured note (a zeitgeist snapshot is ideal — has H2 sections, inventory lists, prose paragraphs). Search for a term that appears in a synthesis section. Check whether the returned chunk includes the section heading as context.

---

## Improvement 3: Zeitgeist Snapshot Chunking Strategy

### What's wrong now

Zeitgeist snapshots (`clauding/zeitgeist/*.md`) have a specific structure:

1. Frontmatter (epoch, generated date)
2. **Inventory** — a list of note paths (low signal, just filenames)
3. **Clusters** — thematic groupings with prose characterizations (high signal)
4. **Connections** — explicit cross-note connections in prose (highest signal)
5. **Gleanings annotated** — list of annotated items (medium signal)

A sliding window chunker will mix Inventory list items with Clusters prose, producing noisy chunks. A search for "constructed meaning after defeat" needs to land in the Connections section, not in the Inventory.

### What to change

Add a document-type-aware chunking path for zeitgeist snapshots:

1. Detect snapshots by path (`clauding/zeitgeist/` prefix) or by frontmatter (`epoch:` field present)
2. Skip or de-weight the Inventory section (everything between `## Inventory` and `## Clusters`)
3. Chunk Clusters and Connections sections independently, preserving section headings as chunk prefixes
4. Tag these chunks with `doc_type: zeitgeist` in their metadata

This does not require modifying Synthesis. The pre-split approach from Improvement 2 applies: pre-process snapshot files into section-level chunks before they reach the indexer.

### How to test

Search for a theme that only appears in the Connections section of a snapshot (not in any individual note). Verify the snapshot surfaces in results and the returned chunk is from the Connections section, not the Inventory.

---

## Implementation Order

1. **Position-aware blending** — self-contained change to `reranker.py`, testable in an afternoon
2. **Heading-aware chunking** — requires investigating Synthesis internals first; pre-split approach is the safe path
3. **Zeitgeist chunking** — builds on heading-aware chunking; can be done as a special case in the pre-split logic

---

## Open Questions

- Does Synthesis expose chunk boundaries or does it chunk internally? (Read `synthesis/` before starting #2)
- What's the cross-encoder score range in practice? (Confirm it's [-1, 1] before normalizing)
- Should `final_score` be returned in API results for harness visibility?
