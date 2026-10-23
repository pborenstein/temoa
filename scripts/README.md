# scripts

One-off tools that are not part of the `temoa` CLI. Run them from the repo root.

## Search-quality harvest (Phase 0)

Phase 0 of `docs/SEARCH-QUALITY-PLAN.md`: mine Claude Code transcripts for `temoa search` calls and what the agent did next, as candidate judgments for review.

| Script | What it does |
|:-------|:-------------|
| `harvest_transcripts.py` | Walks `~/.claude/projects/**/*.jsonl` (read-only), writes one JSONL row per search |
| `show_candidates.py` | Prints the rows, one block per search |

### Regenerate candidates

Transcripts no longer expire (`cleanupPeriodDays: 36500`), so the file can be rebuilt any time:

```bash
uv run python scripts/harvest_transcripts.py -o ~/Obsidian/amoxtli/.temoa/candidates.jsonl
```

Options: `--window N` (tool calls inspected after each search, default 5), `--vault PATH`, `--projects-dir PATH`. Without `-o` it writes to stdout. A summary line goes to stderr.

The output lives in `.temoa/` beside `search_log.db`: it lists vault paths, so it stays out of git and Obsidian Sync.

### Look at them

```bash
uv run python scripts/show_candidates.py              # every search
uv run python scripts/show_candidates.py Josiah 1095  # queries starting with these
uv run python scripts/show_candidates.py --all        # include grep_only
uv run python scripts/show_candidates.py -f other.jsonl
```

Each line: `suggested  rank  o= c= g=  path`, where `o` = opened by a later tool call, `c` = cited in the agent's reply, `g` = surfaced by grep/find.

| Suggested | Meaning |
|:----------|:--------|
| `used` | Returned by Temoa, then opened or cited |
| `missed` | Not returned, but cited, or surfaced by grep and then opened |
| `unopened` | Returned, never opened or cited (the description may have sufficed) |
| `context` | Not returned, opened without grep finding it (likely task background) |
| `grep_only` | Not returned, surfaced by grep, never opened (hidden by default) |

Header tags: `full` means Temoa's output was parsed as printed. `loose` means the agent piped it through grep or python first, so paths are whatever survived the filter and ranks may not be Temoa's.

### Limits

- Paths are matched against the vault as it is now; notes renamed since a search are not found.
- Searches in a shell loop (`temoa search "$q"`) can't be paired with their queries and come out as error rows.
- Every row has `reviewed: false`. These are candidates, not judgments.
