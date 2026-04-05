# RESEARCH-NOTES.md - External Research & Learnings

> **Purpose**: Notes from external reading, tools, and ideas that inform Temoa's direction.
> Each entry records provenance (source), what was learned, and what (if anything) is actionable.

**Last Updated**: 2026-04-04

---

## Entry 001 — Karpathy LLM Wiki Pattern + qmd

**Date**: 2026-04-04
**Sources**:
- Karpathy, "LLM Wiki" — https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw/ac46de1ad27f92b28ac95459c782c07f6b8c964a/llm-wiki.md
- tobi/qmd — https://github.com/tobi/qmd (MIT, TypeScript, 17k stars as of 2026-04-04)

---

### The LLM Wiki Pattern (Karpathy)

The core idea: instead of re-deriving answers from raw documents at every query (RAG), an LLM incrementally builds and maintains a persistent wiki — a directory of structured markdown files that sits between you and raw sources. New sources are integrated into the wiki (updating entity pages, flagging contradictions, building cross-references), not just indexed. The wiki compounds over time.

**Three layers:**

- **Raw sources** — immutable source documents (articles, papers, clips). Never modified.
- **The wiki** — LLM-maintained markdown pages. Summaries, entity pages, synthesis.
- **The schema** — a CLAUDE.md-style config telling the LLM how the wiki is structured and what workflows to follow.

**Operations:** Ingest (process new source → touch 10-15 wiki pages), Query (answer from wiki, optionally file good answers back as new pages), Lint (health-check: orphans, contradictions, stale claims, missing cross-references).

**Why it works:** Humans abandon wikis because maintenance cost grows faster than value. LLMs don't get bored and can touch 15 files per ingest pass.

**Temoa relevance:**

1. This is exactly what Temoa supports — the vault is the wiki, gleanings are the raw sources layer.
2. The 181 empty gleaning descriptions are structurally equivalent to wiki pages that were never populated. Filling them (manually or with LLM) is the highest-leverage quality improvement.
3. The Karpathy workflow assumes a local search tool. He explicitly recommends qmd (see below) for this role. Temoa does the same job.
4. "Good answers can be filed back into the wiki as new pages" — a direction for Phase 4 or later: search results that synthesize well could be saved back as vault notes.

---

### qmd (tobi/qmd)

**What it is:** A local hybrid search CLI + MCP server for markdown files. Created 2025-12-08, 17k stars, MIT, actively maintained.

**Stack:** TypeScript/Node.js, SQLite + sqlite-vec, GGUF models via node-llama-cpp.

**Pipeline:**

```
query
  └─► LLM query expansion (fine-tuned 1.7B model → 2 variants)
        └─► BM25 (FTS5) + vector search on each variant in parallel
              └─► RRF fusion (k=60), original query weighted ×2
                    └─► top-30 candidates
                          └─► LLM re-ranking (Qwen3-Reranker-0.6B, yes/no + logprobs)
                                └─► position-aware score blending
                                      └─► final results
```

**Models (auto-downloaded GGUF):**
- `embeddinggemma-300M-Q8_0` — embeddings (~300MB)
- `qwen3-reranker-0.6b-q8_0` — reranker (~640MB)
- `qmd-query-expansion-1.7B-q4_k_m` — query expansion, fine-tuned (~1.1GB)

**Notable technical decisions:**

**Position-aware score blending** — RRF and reranker scores are blended at different ratios depending on rank position:
- Ranks 1-3: 75% RRF / 25% reranker (preserve exact matches)
- Ranks 4-10: 60% RRF / 40% reranker
- Ranks 11+: 40% RRF / 60% reranker (trust reranker more)
- Rationale: pure RRF dilutes exact matches when expanded queries don't match; reranker alone destroys high-confidence retrieval results at the top.

**Context annotations** — collections and sub-paths can have descriptive text attached (`qmd context add qmd://notes "Personal notes"`). This context travels with search results and improves relevance. Structurally similar to gleaning description fields.

**Smart markdown chunking** — break-point scoring by heading level (H1=100, H2=90, code fence=80, blank line=20, list item=5). Cuts at the highest-scoring break in a 200-token lookahead window before the chunk limit. Code blocks are never split.

**Similarities to Temoa:**

| Feature | Temoa | qmd |
|---------|-------|-----|
| BM25 | rank-bm25, custom | SQLite FTS5 |
| Semantic search | sentence-transformers | GGUF embedding model |
| Hybrid fusion | RRF (k=60) | RRF (k=60) |
| Re-ranking | cross-encoder (sentence-transformers) | Qwen3-Reranker (GGUF) |
| Query expansion | TF-IDF based | fine-tuned 1.7B LLM |
| Chunking | sliding window | scoring-based smart chunking |
| Score blending | fixed ratio | position-aware ratio |
| Index storage | per-vault `.temoa/` | global `~/.cache/qmd/index.sqlite` |
| Interface | FastAPI HTTP server | CLI + MCP server |
| Language | Python | TypeScript |

**Differences that matter:**

- qmd uses GGUF models (portable, auto-download, ~2GB total); Temoa uses sentence-transformers (Python ecosystem, no separate download needed for embeddings).
- qmd's query expansion is LLM-based and presumably more semantically rich than Temoa's TF-IDF approach.
- qmd's MCP server enables direct tool use from Claude Code; Temoa's HTTP server requires a wrapper.

---

### Actionable ideas for Temoa

**Near-term (Experimentation phase):**

1. **Position-aware score blending** — Test varying RRF/reranker blend ratio by rank. Current code in `server.py` uses a fixed blend. qmd's rationale (exact matches should dominate top slots) is sound and testable with the existing harness.

2. **Gleaning descriptions = wiki quality** — The 181 empty descriptions are the clearest path to better search quality. Karpathy's framing makes this explicit: incomplete wiki pages degrade the whole system. LLM-generated descriptions via the extract pipeline would be straightforward.

**Medium-term:**

3. **LLM-based query expansion** — TF-IDF expansion helps for short queries but misses semantic variation. A small local model (or even a prompted call to the reranker model) for query expansion would be a meaningful quality step. qmd uses a fine-tuned 1.7B model; a general-purpose small model would be a reasonable starting point.

4. **MCP server** — qmd's Claude Code integration via MCP makes vault search a native tool call rather than an HTTP request. Given the LLM wiki workflow (Karpathy), an MCP server for Temoa would complete the loop: Claude Code could search the vault directly while working.

**Longer-term:**

5. **Filing answers back** — Karpathy's observation that good query answers should be filed as new wiki pages is a Phase 4 direction: a `/synthesize` endpoint that runs a search, generates a summary, and optionally writes it back to the vault.

---
