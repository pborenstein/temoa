# Note from Zeitgeist

This is a note from the `zeitgeist` skill in the amoxtli vault, left here because the two systems have something to say to each other.

## What zeitgeist does

`/zeitgeist` is a Claude Code skill that runs a periodic archaeology of the vault. Given a time window (a month, a date range, "last 30 days"), it:

1. Collects all notes created in that window — clippings, gleanings, L/ notes, daily notes
2. Reads daily note content for what was actually on the user's mind
3. Clusters the material thematically (letting clusters emerge rather than forcing taxonomy)
4. Surfaces non-obvious connections between things saved vs. things written
5. Annotates significant gleanings with context (turning bookmarks into nodes)
6. Saves a structured snapshot to `clauding/zeitgeist/YYYY-MM.md`

Snapshots are structured for diffing — run zeitgeist again later and compare epochs.

## Why zeitgeist snapshots are interesting for Temoa

Temoa indexes the raw vault: individual notes, gleanings, clippings, each as its own unit. A zeitgeist snapshot is something different — it's a **distillation of a period**. It contains:

- Cluster characterizations: "this month had a sustained Bible archaeology reading project" — in plain prose, not just note titles
- Cross-note connections that aren't expressed as wikilinks anywhere in the vault
- The emotional and thematic shape of a period, derived from reading daily note content
- Gleaning annotations that explain *why* something was saved in context of everything else accumulating at the same time

This means a zeitgeist snapshot is **high-density signal** for semantic search. A search for "constructed meaning after defeat" would have nothing to grab in the raw vault — no note has that phrase. But the May 2025 snapshot explicitly draws that connection between the Bible archaeology cluster and the writing permission anxiety. If Temoa indexes the snapshot, that connection becomes searchable.

## Concrete implications

**Snapshots as first-class indexed documents.** The `clauding/zeitgeist/` directory already lives in the vault. Temoa probably already indexes it, but the snapshots may be getting chunked in ways that lose their connective structure. Worth checking whether snapshot content surfaces well in searches for themes that only appear in the synthesis sections (Connections, Cluster characterizations) rather than in individual note titles.

**The `/archaeology` endpoint already does something adjacent.** `GET /archaeology?q=<topic>` shows when the user was interested in a topic over time. Zeitgeist snapshots could feed this more richly — instead of just "these notes from that period match," it could return the cluster characterization from the snapshot for that period.

**Snapshot as cold-resume context.** The snapshots are explicitly designed so a new AI session can read one and get up to speed on a period without re-deriving everything. This is essentially the same problem as Temoa's search: surfacing the right context quickly. A "what was I thinking about in May 2025" query should probably return the snapshot summary before it returns 15 individual notes.

**Gleaning annotations as search surface.** The zeitgeist skill annotates gleanings that surfaced as significant — adds a `## Annotation` section explaining the connection. Those annotations are now in the gleaning file and Temoa will index them. But they were written with cluster context in mind; without that context, a future search might find the annotation but not understand why it was written. The snapshot is the Rosetta Stone.

## Snapshot location

`~/Obsidian/amoxtli/clauding/zeitgeist/`

Current snapshots (as of 2026-04-12):

- `2025-01-01_2025-01-07.md` — early Jan 2025
- `2025-05.md` — May 2025 (full month)
- `2026-01-01_2026-01-07.md` — early Jan 2026
- `2026-04-01_2026-04-09.md` — early Apr 2026
- `2026-04-12.md` — recent 30 days
- `compare_jan2025_vs_jan2026.md` — diff of the two Jan epochs

---

*Written 2026-04-12 during a zeitgeist session for May 2025.*
