---
phase: "Experimentation"
phase_name: "Search Harness"
updated: 2026-01-25
last_commit: d89c34b
branch: knobs-and-dials
---

# Current Context

## Current Focus

Researched graph exploration for note relationships. Identified `obsidiantools` as best library for parsing wikilinks and building note graphs.

## Active Tasks

- [x] Score explainers and UX improvements (complete)
- [ ] Add note graph exploration (using obsidiantools + NetworkX)
- [ ] Prototype "show neighborhood" feature for search results

## Blockers

None.

## Context

- **Key Insight**: Temoa ignores explicit vault structure (wikilinks). Notes are islands; embeddings rediscover connections humans already made explicit.
- **obsidiantools** (v0.11.0, 502 stars): Production-ready library for Obsidian vault graph analysis
  - NetworkX integration for graph traversal (shortest path, clustering, centrality)
  - Parses wikilinks, backlinks, tags, frontmatter
  - Python 3.9+ compatible
- **Two layers of relatedness**: Explicit links (wikilinks) + Implicit similarity (embeddings)
- **Plain text fallback**: Non-Obsidian folders use pure semantic similarity
- **Use case**: "Show me notes 1-2 hops from this result" for exploration

## Next Session

Add `obsidiantools` dependency and prototype graph exploration. Start with: parse vault graph on startup, add "show neighbors" for selected result in Explorer.
