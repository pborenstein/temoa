# Multi-Model Embeddings Plan

> **Status**: Draft / Pre-implementation
> **Created**: 2026-03-16
> **Author**: pborenstein

---

## The Core Idea

Different embedding models are trained differently and may be better at different retrieval tasks. A model optimized for question-answer matching might outperform a general-purpose model when the user is looking for an answer to a specific question. A paraphrase model might surface more results for "how do I do X" that are phrased as "the way to do X is...".

The hypothesis worth testing: **no single model is optimal for all query types.** If that's true, we'd want to route queries to the model most likely to return good results for that query shape.

---

## What Already Exists

The infrastructure is largely in place:

- **5 models registered** in `synthesis/src/embeddings/models.py` with documented use cases
- **Per-model storage** — each model writes to its own subdirectory under `.temoa/` (e.g., `.temoa/all-mpnet-base-v2/index.json`)
- **LRU client cache** keyed on `(vault_path, model)` — already supports holding multiple loaded models simultaneously (max 3)
- **`SynthesisClient`** accepts `model` at construction time

What's missing is any way to actually use this from Temoa: the `/search` and `/reindex` endpoints ignore the `model` parameter and always use `config.default_model`.

---

## The Real Cost: Memory

This is the constraint that shapes everything.

Each loaded model occupies RAM:

| Model | Dimensions | RAM (approx) |
|-------|------------|-------------|
| all-MiniLM-L6-v2 | 384 | ~90MB |
| all-MiniLM-L12-v2 | 384 | ~130MB |
| all-mpnet-base-v2 | 768 | ~420MB |
| multi-qa-mpnet-base-cos-v1 | 768 | ~420MB |
| paraphrase-albert-small-v2 | 768 | ~45MB |

Loading a model takes 10-15s. The LRU cache (max 3) keeps models resident after first load. But on a Mac mini or similar machine running other things, holding 2-3 large models in memory simultaneously is a real cost.

**Indexing cost is one-time per model.** Once a vault is indexed under a model, searches against that index are fast with no re-indexing needed. Switching between pre-built indexes is cheap — the bottleneck is which models are already loaded in the LRU cache.

---

## Available Models and Their Strengths

From the Synthesis model registry:

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `all-MiniLM-L6-v2` | fast | good | General purpose, default |
| `all-MiniLM-L12-v2` | medium | better | Better quality, same storage as L6 |
| `all-mpnet-base-v2` | medium | better | Cross-domain connections, production |
| `multi-qa-mpnet-base-cos-v1` | medium | better | Question-answer matching |
| `paraphrase-albert-small-v2` | medium | good | Similarity, paraphrase detection |

For Temoa's use cases:
- **General recall** (find notes about X): `all-mpnet-base-v2` likely wins
- **Question queries** (how do I..., what is...): `multi-qa-mpnet-base-cos-v1` is purpose-built
- **"Something like this"** (paraphrase/similarity): `paraphrase-albert-small-v2`
- **Speed / low memory**: `all-MiniLM-L6-v2`

---

## Phased Plan

### Phase A: Harness Comparison (Experiment First)

Before building anything production-facing, validate whether the models actually behave differently on real queries from the vault.

**What to build:**
- Extend the Search Harness (`/harness`) with a model selector dropdown
- Wire the `model` param through `/search` so the harness can query the same term against two models side-by-side
- Display results in parallel columns with scores

**What to learn:**
- Do the models return meaningfully different result sets?
- Which query types diverge most between models?
- Is the quality difference worth the memory cost?

**Prerequisite**: Index the vault under at least one alternative model. This is a one-time CLI operation:
```bash
uv run temoa index --vault amoxtli --model all-mpnet-base-v2
```
(This requires wiring `--model` through the index command first.)

**Decision gate**: If results are not meaningfully different across models for typical queries, there's no reason to build model routing. Ship what we learn, stop here.

---

### Phase B: Per-Request Model Selection (If Warranted)

If Phase A shows real differences, add model selection to the search API and UI.

**Changes:**
- `/search` accepts `?model=` query param, defaults to `config.default_model`
- Search UI exposes model as an advanced option (hidden by default, not prominent)
- Harness gets full model selector

**Not in scope:**
- Automatic model routing (choosing model based on query shape) — this requires training data we don't have yet
- Changing the configured default model at runtime — still requires config.json edit + restart

**Memory management:**
- The LRU cache already handles multiple loaded models
- Cap the cache at 2 models simultaneously to avoid memory pressure
- Document that loading a new model incurs a one-time 10-15s delay

---

### Phase C: Query-Aware Routing (Future / Speculative)

If we accumulate enough data from Phase B (which model users prefer for which queries), we could build lightweight routing:

- Classify query intent (question vs. topic vs. paraphrase) using simple heuristics
- Route to the model registered for that intent
- Fall back to default if classification is uncertain

This is speculative. Don't build it until Phase B produces enough evidence that it would help.

---

## What Not to Do

- **Don't run all models on every query and merge results.** The memory and latency cost is too high. The models share the same pipeline (BM25, reranker) — parallelizing embeddings doesn't multiply the benefit proportionally.
- **Don't expose model switching in the main search UI.** The primary UI should be simple. Model selection belongs in the Harness/advanced tooling.
- **Don't auto-select models based on query length or keyword heuristics without evidence.** This is premature optimization.
- **Don't index under all 5 models by default.** Storage and index time multiply per model. Start with 2 (current default + one alternative) and only add more if the experiment justifies it.

---

## The Cross-Encoder Reranker

This is the third model in the pipeline, and it complicates the multi-model question significantly.

### What it is

There are two fundamentally different ways to score relevance:

**Bi-encoder** (what the embedding models do): Encode the query into a vector. Encode the document into a vector. Measure the angle between them. Fast because document vectors are pre-computed and stored in the index — a search is just a vector lookup.

**Cross-encoder** (what the reranker does): Take the query and the document *together* and run them through a model as a single input. The model was trained to output a relevance score for that pair. Much slower — can't be pre-computed — but more accurate because the model sees both at once and can reason about how they relate.

The tradeoff: you can't use a cross-encoder for retrieval (too slow to score every document), but you can use it to *re-rank* a short candidate list that a fast retrieval already found.

### What ours does specifically

The model is `cross-encoder/ms-marco-MiniLM-L-6-v2`, trained on the MS MARCO dataset — a large collection of real Bing search queries with human relevance judgments. It has a notion of "what a good search result looks like" baked into its weights, independently of which bi-encoder found the candidates.

The pipeline:

1. Bi-encoder (your embedding model) retrieves top 100 candidates by cosine similarity
2. Cross-encoder scores each `(query, document)` pair
3. Results are re-sorted by cross-encoder score
4. You get back the top K

The bi-encoder's original scores are preserved in results (`similarity_score`), and the cross-encoder score is added as `cross_encoder_score`. The Pipeline Viewer captures the top 20 results before and after reranking and shows rank changes.

### Turning it off

The rerank checkbox is already in the search UI — you can toggle it per-search today. Turning it off means results come back in pure bi-encoder order (cosine similarity). The interesting comparison isn't on/off in isolation: it's looking at a query where you know what the right answer is and seeing whether the cross-encoder moved the right thing up or down.

The "20-30% precision improvement" figure in the code comments is a benchmark number from MS MARCO, not measured on this vault. Whether it holds for notes, gleanings, and daily entries is an open question.

### Why this matters for multi-model

The cross-encoder is a *third* model, completely separate from the embedding models. It's always `ms-marco-MiniLM-L-6-v2` regardless of which bi-encoder you used. So if you switch from `all-MiniLM-L6-v2` to `all-mpnet-base-v2`, the reranker still runs afterward and may correct whatever ranking differences the switch introduced.

**The key implication**: the cross-encoder can only re-order what the bi-encoder already retrieved. If two embedding models return overlapping candidate sets (say, 80 of the same 100 documents), the reranker will produce nearly identical final results regardless of which model you used. The models would only produce meaningfully different outputs if they retrieve *different candidates* — i.e., one model finds a document in its top 100 that the other misses entirely.

This means the experiment in Phase A needs to compare candidate sets, not just final ranked results. If the top 100 from two models are mostly the same, switching models won't help no matter what.

---

## Open Questions

1. **Does `multi-qa-mpnet-base-cos-v1` actually outperform `all-mpnet-base-v2` for question queries against this vault?** The vault is not a Q&A dataset — it's notes, gleanings, and daily entries. The QA model's advantage may not transfer.

2. **Is `paraphrase-albert-small-v2` worth it?** Max sequence length of 100 tokens means it truncates most notes. Probably not useful for full-document retrieval.

3. **How much does the cross-encoder reranker offset model quality differences?** See the reranker section above. This is the central unknown — if candidate sets overlap heavily across models, switching models achieves nothing.

4. **Storage cost per model?** Need to measure index size for the vault under each model before committing to multi-model indexing.

---

## Success Criteria

- Phase A complete when: at least 20 representative queries compared across 2 models with qualitative notes on differences
- Phase B complete when: model param works end-to-end in API and harness
- Phase C triggered only if: clear evidence from Phase B that users reach for a specific model for a specific query type

---

## Related Docs

- `docs/ARCHITECTURE.md` — storage layout, LRU cache details
- `docs/SEARCH-MECHANISMS.md` — search pipeline
- `synthesis/src/embeddings/models.py` — ModelRegistry and ModelSpec definitions
- `synthesis/CLAUDE.md` — synthesis multi-model architecture notes
