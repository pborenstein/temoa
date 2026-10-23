# Search Quality Plan: Logging Outcomes

**Status**: Proposed (2026-10-22)
**Implements**: the "Known-miss list" and "Score baseline" items under Open in [IMPLEMENTATION.md](IMPLEMENTATION.md)

## Problem

`search_log.db` records what Temoa returned. It doesn't record whether that was what the searcher wanted. Without that, no change to the pipeline can be measured: there is nothing to compare before and after against.

Most searches come from Claude Code sessions running the `temoa-search` skill in the vault. The agent's next moves after a search show whether it worked: it reads a result, or it falls back to grep and finds the answer somewhere Temoa didn't point. That signal exists today and is thrown away.

## What exists

| Source | Holds | Missing |
|:-------|:------|:--------|
| `search_log.db` | 452 searches, 2026-06-08 to 2026-10-23 (357 hybrid, 94 semantic, 1 BM25); query, params, ranked paths and scores, timing | Who searched, what was used, what was missed |
| Claude Code transcripts (`~/.claude/projects/*/*.jsonl`) | Every `temoa search` call by an agent, and every tool call after it | Expire: the oldest left is 2026-09-22. Not linked to log rows |
| Web UI (server) | Searches from the phone | Click-through |

## First look at the transcripts

A rough pass over the 10 transcripts that contain `temoa search`: 24 searches. In the three tool calls that followed each one:

| Next move | Searches |
|:----------|---------:|
| grep or find | 18 |
| web search | 1 |
| nothing classifiable | 5 |
| Read of a result, with no grep | 0 |

This overstates failure. Grep after a search is sometimes a follow-up for an exact string, not a miss, and reads done with `cat` weren't counted. But 18 of 24 is enough to say that agents usually don't stop at Temoa.

## Worked example: 2026-10-22

Query, hybrid: `Josiah scroll reform 622 BCE Deuteronomy book of the law found in the Temple`. The agent wanted every vault note that dates Josiah's reform.

| Note | Temoa rank | Found by |
|:-----|:-----------|:---------|
| The Jewish diaspora at the time of the Great Revolt | 1 | Temoa (irrelevant; BM25 204.9, semantic 0.275) |
| TIMELINE event schema | 2 | Temoa (irrelevant) |
| The Parthians and the Jewish revolt | 3 | Temoa (irrelevant) |
| Has the Name of King Josiah's Trusted Official Been Found on an Ancient Sealing | 7 | Temoa (relevant; semantic 0.509, BM25 0) |
| The Bible Unearthed (Review) | 8 | Temoa (relevant; semantic 0.509, BM25 0) |
| when did Jews start sacrificing exclusively art the Temple | not returned | grep. The only source for the 621 BCE date |
| It's Tradition! How Deuteronomy's Reform Permits Non-Sacrificial Slaughter | not returned | grep |
| Becoming a Religion of the Book Konrad Schmid and Jens Schröter | not returned | grep |
| sacrifice judaism christianity | not returned | grep. Philip's own comment, with his ~650 date |

The two relevant results Temoa found were semantic-only and ranked below three BM25 floods. Four relevant notes weren't returned at all. This matches the observation in CONTEXT.md that hybrid hurts conceptual queries. It also shows the agent's query was keyword-stuffed, which feeds BM25.

Each grep-found note is a labeled pair: (query, path that should have been returned). That is the known-miss list, produced as a side effect of normal work.

## Plan

```
   agent searches (temoa search)
              │
              ▼
   search_log.db row  ──  id printed with results
              │
              ▼
   agent reads results, maybe greps
              │
              ▼
   temoa judge <id> --used ... --missed ...
              │
              ▼
   judgments table  ──►  temoa eval  ──►  recall@10, MRR by mode
```

### Phase 0: harvest the transcripts now

Transcripts expire. Before building anything, write a read-only script that walks the transcripts and, for each `temoa search`, records the query, the session, and the paths the agent read or grepped up in the next few calls. Output is a JSONL of candidate judgments, reviewed by hand before it counts.

`cleanupPeriodDays` in `~/.claude/settings.json` was set to 36500 on 2026-10-22, so the transcripts still on disk (back to 2026-09-22) and every later one are kept. Anything older was already deleted.

### Phase 1: identify searches

| Change | Where |
|:-------|:------|
| Add `caller` (`cli`, `server`, `agent`) and `session` columns | `search_log.py` schema, with a migration |
| Print the log row id with CLI results, and include it in `--json` output | `cli.py` |
| Take `--session` / `TEMOA_SESSION` so an agent can tag its searches | `cli.py` |
| Fix the vault inconsistency (CLI logs path, server logs name) | already an open item |

### Phase 2: record outcomes

A `judgments` table keyed on the search id: `path`, `verdict` (`used`, `irrelevant`, `missed`), `found_by` (`temoa`, `grep`, `web`, `memory`), `judge` (`agent`, `philip`), timestamp.

`temoa judge <id> --used PATH... --missed PATH... --irrelevant PATH...` writes rows.

The `temoa-search` skill (in tlatecpana) gets one step: after a search, if you read results or grep for the same thing, run `temoa judge` with what was used and what grep found that Temoa didn't. One call, at the point where the agent already knows the answer.

For the phone UI, log result clicks as `used` with `judge: philip`. Optional; depends on how much the phone gets used.

### Phase 3: eval

`temoa eval` replays every judged query against the current index and config and reports, per mode:

| Metric | Meaning |
|:-------|:--------|
| recall@10 | share of `used` + `missed` paths that appear in the top 10 |
| MRR | how high the first relevant path ranks |
| flood rate | share of queries where the top 3 are all `irrelevant` |

Run it before and after one change. This is the methodology already in IMPLEMENTATION.md, with a real test set in place of "standard queries".

### Phase 4: first measured change

Candidates already on the list, in the order the example suggests:

1. Position-aware reranker blending (qmd's ratio by rank), aimed at BM25 floods.
2. Default to semantic for long or conceptual queries, or change what the skill tells agents about `--hybrid`.
3. Zeitgeist snapshot chunking.

Wait for about 30 judged queries before trusting a difference.

## Caveats

- **Self-grading.** Agent judgments are the agent's view of relevance. Philip should spot-check them, at least early on.
- **Agent behavior confounds results.** A miss can be a bad query, not bad search: the example query was keyword-stuffed. Log the query as given, and keep query-writing advice in the skill separate from pipeline changes.
- **Grep isn't always a miss.** Grep for a literal string after a good search is normal. Only paths grep found that weren't in Temoa's results count as `missed`.
- **Overhead.** One extra command per search. If agents skip it, Phase 0's transcript script can run periodically instead, at lower accuracy.

## Open questions

- Is the phone UI used enough to be worth instrumenting?
- Should judgments live in `search_log.db` or in a separate file the vault can see?
