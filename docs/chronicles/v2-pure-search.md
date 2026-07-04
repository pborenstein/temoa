# Pure Search Engine Era

Chronicle entries from the research and planning that led to the v2.0 rebuild (Entry 91+) through the current pure-search experimentation phase.

Earlier entries (search harness UI, Entries 50-90) are archived in `docs/archive/chronicles-v1/experimentation-harness.md`.

---

## Entry 91: Research — LLM Wiki Pattern & qmd Competitor Analysis (2026-04-04)

**What**: Research session reviewing Karpathy's "LLM Wiki" pattern and tobi/qmd (a TypeScript hybrid search tool). Wrote `docs/RESEARCH-NOTES.md` to capture findings with provenance.

**Why**: Orient the Experimentation phase around what peers are doing and identify gaps.

**Key findings**:
- Karpathy's LLM Wiki pattern: vault = persistent compounding wiki; Temoa is its search layer. Gleaning descriptions are the wiki page quality — 181 empty = 181 degraded results.
- qmd does the same BM25+semantic+reranker pipeline as Temoa in TypeScript/Node. 17k stars, created Dec 2025.
- qmd's notable technique: **position-aware score blending** — RRF/reranker ratio varies by rank (75/25 for top-3, 60/40 for 4-10, 40/60 for 11+). Temoa uses fixed ratio.

**Actionable ideas** (details in RESEARCH-NOTES.md Entry 001):
1. Position-aware score blending — testable with existing harness
2. Fill 181 gleaning descriptions (LLM-generated)
3. LLM-based query expansion (qmd uses fine-tuned 1.7B model)
4. MCP server for Claude Code integration
5. File synthesized answers back to vault (longer-term)

**Files**:
- `docs/RESEARCH-NOTES.md` (new)
- `docs/IMPLEMENTATION.md` (table updated)
- `CLAUDE.md` (doc index updated)

---

## Entry 92: Planning — Miyo Investigation, Two Improvement Plans, Synthesis Constraint Removed (2026-04-13)

**What**: Research and planning session. Investigated Obsidian Copilot's Miyo sidecar, scoped two phased improvement tracks, corrected a stale architectural constraint.

**Why**: User wanted to understand where to focus effort — semantic search tooling, vault skill elicitation on mobile, and what Temoa could learn from qmd.

**Key findings**:
- Miyo (Copilot Plus sidecar, port 8742) does hybrid search but requires a Copilot Plus license; on mobile needs a configured remote URL — exactly what Temoa already is. Temoa could speak the Miyo API dialect as a compatibility shim.
- Claude Code Remote Control (`claude remote-control` in tmux) is the immediate path to iOS vault access. User is on Pro/Max, CC v2.1.105. No coding required.
- `synthesis/` "do NOT modify" constraint (DEC-012) was scoped to Phase 1-2 only. Phase 3 complete. Constraint was stale; removed from CLAUDE.md.
- Zeitgeist snapshots contain synthesized connections not present in any individual note — Connections/Clusters sections are high-density signal that should be chunked separately from Inventory noise.

**Plans written**:
- `docs/plans/qmd-pipeline-improvements.md` — position-aware score blending (reranker.py), heading-aware chunking (synthesis/), zeitgeist-specific chunking
- `docs/plans/dashboard-zeitgeist-surface.md` — two new server endpoints + landing state with period links and cluster pills

**Files**:
- `CLAUDE.md` (synthesis constraint removed)
- `docs/plans/qmd-pipeline-improvements.md` (new)
- `docs/plans/dashboard-zeitgeist-surface.md` (new)
- `docs/CONTEXT.md` (updated)

---

## Entry 93: Cron-Friendly Log Format — `--log-format` Flag (2026-04-18)

**What**: Added `--log-format` flag to `temoa extract` and `temoa reindex` producing single-line markdown entries for cron log files.

**Why**: Cron output was verbose multi-block noise; needed scannable Obsidian markdown log at `~/Obsidian/amoxtli/log/temoa-log.md`.

**How**:
- Output format: `## YYYY-MM-DD HH:MM | command | +N new, N dupes, N found, N files | mode`
- Suppressed all tqdm progress bars and print() via `show_progress` param threaded through synthesis.py → vault_reader.py
- Graph rebuild skipped when no files changed (saves ~80s); rebuild triggered only when files actually differ
- `show_progress=False` passed from CLI → `client.reindex()` → `_find_changed_files()` → `read_vault()` → each `tqdm()` call

**Files**: `src/temoa/cli.py`, `src/temoa/synthesis.py`, `src/temoa/scripts/extract_gleanings.py`, `synthesis/src/embeddings/vault_reader.py`

---

## Entry 94: Decouple Graph Rebuild — `temoa build-graph` Command (2026-04-18)

**What**: Extracted vault graph rebuild into a standalone `temoa build-graph` command; `reindex --log-format` never rebuilds the graph.

**Why**: obsidiantools graph rebuild costs ~80s for 7897 nodes. `reindex` was triggering it on every cron run because "deleted" files (real clippings removals) counted as changes. Graph is only needed for similar-notes UI, not search — wrong tool for a fast cron job.

**How**:
- Deletions alone no longer trigger graph rebuild in `reindex` (only new/modified files do)
- `reindex --log-format` skips graph entirely, logs `graph skipped`
- `build-graph` command: standalone, supports `--log-format`, runs obsidiantools and caches to `vault_graph.pkl`
- Suggested cron: `0 8,20 * * *` (twice daily, independent of reindex schedule)

**Files**: `src/temoa/cli.py`

---

## Entry 95: Log Format — Split Stats to Second Line (2026-04-18)

**What**: Changed `--log-format` output from single long line to heading + detail line.

**Why**: User hand-edited existing log entries to split `## datetime | command` onto its own line with stats on the next line — makes the log more scannable as a Markdown document with real section headings.

**How**: Each `## {ts} | {command} | {stats}` becomes `## {ts} | {command}\n{stats}` in `cli.py` (reindex, build-graph) and `extract_gleanings.py` (extract).

**Files**: `src/temoa/cli.py`, `src/temoa/scripts/extract_gleanings.py`

---

## Entry 96: Temoa Rebuilt as Pure Search Engine (2026-05-30)

**What**: Stripped gleaning extraction, vault graph, and web UI from Temoa. Server rebuilt from 2671 → 430 lines as a pure JSON API. CLI reduced from 1242 → ~450 lines with 8 commands. Introduced composable pipeline abstraction.

**Why**: Temoa was doing too much — search engine + gleaning extractor + link maintainer + graph explorer + web UI. Gleanings are being offloaded to a separate tool. The rebuild clears the decks for swappable search behaviors.

**How**:
- `server.py` rewritten: kept `/search`, `/reindex`, `/health`, `/vaults`, `/config`, `/stats`, `/models`; dropped all gleaning/graph/UI routes
- New `pipeline.py`: `SearchContext` dataclass, `Stage` protocol, `Pipeline` runner, six concrete stages (ScoreFilter, StatusFilter, QueryFilter, Rerank, TimeBoost, Limit), `default_pipeline()` factory
- New `server_filters.py`: `filter_by_properties/tags/paths/files` and `build_file_filter` extracted from old server.py
- Deleted: `gleanings.py`, `normalizers.py`, `github_client.py`, `text_cleaner.py`, `vault_graph.py`, `scripts/` directory
- CLI: removed `extract`, `migrate`, `gleaning` group, `build-graph`; `search` now uses `default_pipeline()`
- Tests: 147 passing (69 gleaning/normalizer tests deleted with the code)

**Decisions**: Gleaning management → separate tool. UI → separate project. Temoa = search API only.

**Commits**: `d6dbe3a` through `1ef34ca` on branch `claude/docs-codebase-review-5YeTG`

---

## Entry 97: Restore Type Filtering (2026-05-30)

**What**: Restored `--type` / `--exclude-type` to the CLI and `include_types`/`exclude_types`
to the `/search` API after discovering they were load-bearing for the tlatecpana `temoa-search`
skill (`--type gleaning`, `--exclude-type daily`).

**Why**: The gleaning-related CLI commands were removed during the temoa rebuild, and type
filtering was accidentally dropped along with them. Type is a general frontmatter field,
not gleaning-specific.

**How**:
- `filter_by_type()` added to `server_filters.py` using `normalize_type()` from `nahuatl_frontmatter`
- `QueryFilterStage` wired to call it when `include_types`/`exclude_types` present
- `/search` endpoint gains `include_types`/`exclude_types` query params
- CLI `search` command gains `--type/-t` and `--exclude-type/-x` flags

**Files**: `server_filters.py`, `pipeline.py`, `server.py`, `cli.py` — commit `a826237`

---

## Entry 98: Versioned Releases — v1.1.0 and v2.0.0 (2026-06-07)

**What**: Tagged and released two versions on GitHub. `v1.1.0` marks the last
version with UI/gleanings/graph. `v2.0.0` marks the pure search engine rebuild.

**Why**: `origin/main` was stuck at `40e5bb6` (pre-rebuild). Needed releases to
make the history navigable and give users a way to run back to the UI version.

**How**:
- Annotated tag `v1.1.0` created at `40e5bb6` and pushed with GitHub release note
- `CHANGELOG.md` updated with v2.0.0 entry (Added, Removed/Breaking sections)
- `pyproject.toml` bumped to `2.0.0`
- Committed, tagged `v2.0.0`, pushed `origin/main` (now at `80e436e`)
- GitHub release created for both tags

**Files**: `CHANGELOG.md`, `pyproject.toml` — commits `e6d0967`, `80e436e`

---

## Entry 99: Documentation Overhaul for v2.0.0 (2026-06-07)

**What**: Scrapped and rewrote all documentation to match what temoa actually is after the v2.0 rebuild. Deleted 8 stale files, archived 2, rewrote 7.

**Why**: Docs still described v1.x — UI, gleanings, graph, harness, inspector, search profiles. None of it exists. A future session reading ARCHITECTURE.md would have been completely misled.

**How**:
- `ARCHITECTURE.md`: full rewrite, 2170 → ~300 lines
- `README.md`: full rewrite, accurate CLI/API surface
- `IMPLEMENTATION.md`: version bump, v2.0 rebuild phase added
- `DECISIONS.md`: DEC-092/093/094 marked superseded; DEC-098 added (v2.0 rationale)
- `DEPLOYMENT.md`: removed profiles, graph endpoints, `temoa extract`
- `SEARCH-MECHANISMS.md`: StatusFilterStage degleanified; pipeline viewer UI ref removed
- `CLAUDE.md`: commands updated, version corrected
- Deleted: GLEANINGS.md, TRACKING-SYSTEM.md, PRODUCTION-HARDENING-ROADMAP.md, OPUS-OPINES.md, SYNTHESIS_PREFILTER_PLAN.md, plans/dashboard-*.md, plans/qmd-pipeline-*.md
- Archived: MULTI-MODEL-PLAN.md, qmd-pipeline-improvements.md (pipeline improvements still applicable)

**Files**: commits `4ba0466`, `8516252`

---

## Entry 100: Zeitgeist Integration Design Notes (2026-06-07)

**What**: Moved `NOTE-FROM-ZEITGEIST.md` (root) → `docs/ZEITGEIST-INTEGRATION.md`. Added to docs index.

**Why**: The note (written during a vault zeitgeist session) articulates why zeitgeist snapshots are high-density signal for temoa search — cluster characterizations, cross-note connections, and gleaning annotations that only make sense in context of a period. Worth keeping where temoa development sessions will find it.

**Key ideas in the note**:
- Snapshots contain synthesized prose connections not expressed anywhere as wikilinks — "constructed meaning after defeat" type searches
- Zeitgeist chunking problem: sliding window destroys the connective structure (Connections section gets mixed with Inventory list items)
- `/archaeology` endpoint could return cluster characterizations from snapshots, not just individual note matches
- Ties directly to qmd pipeline improvements plan (zeitgeist-aware chunking is Improvement 3)

**Files**: `docs/ZEITGEIST-INTEGRATION.md`, `docs/README.md`

---

## Entry 101: Search Query Logging — Persistent Measurement Infrastructure (2026-06-08)

**What**: Every search (HTTP + CLI) now logs to `.temoa/search_log.db`: query, mode, timing, result count, top/median scores, per-result `{path, score}`, and pipeline stage breakdown. New `temoa log` CLI command shows recent searches and aggregate stats.

**Why**: Experimenting with algorithm changes (reranker blending, chunking, multi-model) without measurement is guesswork. The log enables before/after comparison of real queries. Modeled on apantli's SQLite cost tracking pattern.

**How**:
- `src/temoa/search_log.py`: `SearchLog` class, aiosqlite, schema with indexes on timestamp and vault
- Server lifespan initializes log at `{index_path}/search_log.db`; search handler awaits `log_search()` after response assembly
- CLI search command calls `asyncio.run()` to log synchronously after results returned
- Pipeline stage timing now always captured into `ctx.stages_debug` (previously gated on `pipeline_debug` param); HTTP response behavior unchanged
- Test suite overrides `app.state.search_log` with tmp_path instance to avoid polluting live vault
- Display converts UTC timestamps to local time

**Decisions**: Store UTC in DB, convert to local at display time (same as apantli). Store results as `{path, score}` only — no content or descriptions.

**Files**: `src/temoa/search_log.py` (new), `src/temoa/server.py`, `src/temoa/cli.py`, `src/temoa/pipeline.py`, `tests/test_search_log.py` (new) — commit `d2dbaba`

---

## Entry 102: Repo Cleanup — Archive v1 Era, Reframe Tracking (2026-07-04)

**What**: Archived 13 v1-era chronicle files to `docs/archive/chronicles-v1/`, split `experimentation-harness.md` at Entry 91 (this file carries Entries 91+), rewrote IMPLEMENTATION.md around the pure search engine, and deleted dead v1 code.

**Why**: Docs still described the UI-centric v1 tool — phase ladder in IMPLEMENTATION.md, gleaning/UI chronicles presented as live, `src/temoa/ui/` still tracked despite the server being a pure JSON API.

**How**:
- `git mv` v1 chronicles + `gleanings-history.md` to archive; new `chronicles/v2-pure-search.md`
- IMPLEMENTATION.md: v1 phases → one history table; active section now "Search Quality Experimentation"
- Deleted `src/temoa/ui/` (7 tracked files, ~250KB) and unused `GleaningError`
- Fixed stale cross-references (TEMOA-ORIGINS, SEARCH-MECHANISMS, READMEs); CLAUDE.md corrected (155 tests, 9 CLI commands, `search_log.py`)
- Removed empty `docs/plans/`, `docs/assets/`; kept `view-logs.sh` (still valid) and gleaning type-filter references in cli/server (legitimate — `gleaning` is still a note type in the vault)

**Decisions**: DEC-103

**Files**: docs/ reorganization, `src/temoa/exceptions.py`, `src/temoa/ui/` (deleted). 155 tests passing.

---
