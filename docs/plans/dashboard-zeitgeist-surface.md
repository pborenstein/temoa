# Plan: Dashboard — Cluster Links and Snapshot Previews

**Status**: Not started
**Created**: 2026-04-13
**Phase**: Experimentation
**Depends on**: qmd-pipeline-improvements.md (Improvement 3, zeitgeist chunking) is useful but not required

The search UI (`search.html`) currently shows a search box and results. This plan adds a structured entry surface above the fold: recent zeitgeist snapshots as period links, and active clusters from the most recent snapshot as clickable queries.

---

## What we're building

A "landing state" for the search UI — what you see before you type anything. Two sections:

**Recent periods** — the last 3–4 zeitgeist snapshots as named links. Tap one to open the snapshot as a structured preview (epoch summary + clusters + connections), not as a raw note result.

**Active clusters** — the cluster names from the most recent snapshot, displayed as pill/tag buttons. Tap one to run a semantic search for that theme.

This turns the search UI from a blank box into a place that already knows what's been on your mind.

---

## Data source

Zeitgeist snapshots live at `~/Obsidian/amoxtli/clauding/zeitgeist/`. They have consistent structure:

```markdown
---
epoch: YYYY-MM-DD to YYYY-MM-DD
generated: YYYY-MM-DD
---

# Zeitgeist: [description]

## Inventory
...

## Clusters

### [Cluster name]
[characterization]
- [note](path)

## Connections
...
```

The server needs to read these files and parse out:
- Snapshot list (filename, epoch dates, description from `# Zeitgeist:` heading)
- Cluster names from the most recent snapshot (H3 headings under `## Clusters`)
- Full snapshot content for the preview pane

---

## Backend changes

### New endpoint: `GET /zeitgeist/snapshots`

Returns the list of available snapshots, newest first.

```json
{
  "snapshots": [
    {
      "filename": "2026-04-12.md",
      "epoch_start": "2026-03-13",
      "epoch_end": "2026-04-12",
      "generated": "2026-04-12",
      "title": "Last 30 days (mid-March through April 12)",
      "cluster_names": ["LLM/AI tooling", "Memory and cognition", "Jewish identity"]
    }
  ]
}
```

Implementation: scan `clauding/zeitgeist/` for `.md` files, parse frontmatter + H1 + H3 cluster headings. No heavy processing — just metadata extraction.

### New endpoint: `GET /zeitgeist/snapshot?filename=<name>`

Returns parsed snapshot content for display.

```json
{
  "filename": "2026-04-12.md",
  "epoch_start": "2026-03-13",
  "epoch_end": "2026-04-12",
  "title": "Last 30 days",
  "clusters": [
    {
      "name": "LLM/AI tooling",
      "characterization": "Sustained reading on Claude Code internals, cognitive architectures, and RAG systems.",
      "notes": ["Reference/Tech/Cog — Cognitive Architecture for Claude Code.md", "..."]
    }
  ],
  "connections": "Raw markdown of the Connections section"
}
```

Implementation: parse the snapshot file into sections. The Inventory section is not returned (noise). Clusters section is parsed into name + characterization + note list. Connections section is returned as raw markdown for rendering.

### Server location

Both endpoints go in `src/temoa/server.py`. The vault path is already known from config. The zeitgeist directory path is `{vault_path}/clauding/zeitgeist/`.

No new dependencies — this is just file reading and markdown parsing with stdlib `re`.

---

## Frontend changes

### Landing state (before search)

When the search input is empty and no results are shown, display:

```
RECENT PERIODS
[Apr 2026 — Last 30 days]  [Apr 1–9]  [Jan 2026]  [May 2025]

THIS PERIOD
[LLM/AI tooling]  [Memory and cognition]  [Jewish identity]  [Old films]
```

- Period links: tap → opens snapshot preview pane (see below)
- Cluster pills: tap → populates search box with cluster name and runs search

The landing state disappears as soon as the user types. It reappears when the input is cleared.

### Snapshot preview pane

When a period link is tapped, the results area shows the snapshot instead of search results:

```
← Back to search

Apr 2026 — Last 30 days (Mar 13 – Apr 12)

CLUSTERS
  LLM/AI tooling — Sustained reading on Claude Code internals...
  Memory and cognition — Repeated return to memory, decay, the cost...
  Jewish identity — Passover archaeology, La Belle Juive, the JBC controversy

CONNECTIONS
  [rendered markdown of the Connections section]
```

- "← Back to search" clears the preview and returns to landing state
- Cluster names in the preview are tappable → runs search (same as cluster pills)
- Note paths in cluster lists are tappable → opens the note (existing behavior)

### Implementation approach

The search UI is a single HTML file (`search.html`, ~5000 lines). The landing state is a new `<div id="landing">` shown/hidden based on input state. The snapshot preview is a new `<div id="snapshot-preview">` that replaces the results area.

Add to the existing `fetch`-based API call pattern already in `search.html`. Two new functions:
- `loadLanding()` — fetches `/zeitgeist/snapshots`, renders landing state
- `loadSnapshot(filename)` — fetches `/zeitgeist/snapshot?filename=...`, renders preview pane

Call `loadLanding()` on page load and on input clear.

---

## Mobile considerations

The landing state is the most important surface on mobile — it's what you see when you open Temoa without a query in mind. The cluster pills especially should be large tap targets (minimum 44px height). The snapshot preview should be scrollable within the results area (existing scroll behavior applies).

---

## Implementation order

1. **Backend: `/zeitgeist/snapshots`** — list endpoint, just file scanning and frontmatter parsing
2. **Backend: `/zeitgeist/snapshot`** — detail endpoint, section parsing
3. **Frontend: landing state** — period links + cluster pills, hide/show on input
4. **Frontend: snapshot preview pane** — replace results area with parsed snapshot view

Steps 1–2 are independently testable via curl before any frontend work.

---

## Open questions

- Should compare snapshots (`compare_*.md`) appear in the period list? They have a different structure. Probably yes, listed separately or with a "compare" badge.
- What vault config key points to the zeitgeist directory? Currently assumed to be `{vault_path}/clauding/zeitgeist/` — should be configurable or at least documented.
- Should cluster search pre-filter by date range matching the snapshot's epoch? Probably not for v1 — just run the query vault-wide.
