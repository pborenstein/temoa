---
phase: "Experimentation"
phase_name: "Gleanings Cleanup"
updated: 2026-03-16
last_commit: bbbb927
branch: main
---

# Current Context

## Current Focus

Gleaning enrichment complete. YouTube titles and HTML meta descriptions now fetched at extraction time. Reached the floor of what's automatable without LLM.

## Active Tasks

- [x] Run full re-extraction to apply GitHub API fix
- [x] Fix YouTube URL-as-title (oEmbed API): 19 → 1 remaining (channel URL, not fixable)
- [x] Fetch meta description from HTML for naked URLs at extraction time
- [x] Re-extraction: empty descriptions 202 → 181 (floor without LLM)
- [ ] Handle channel URL gleaning (`youtube.com/@mcpdevsummit`) — manual title or accept
- [ ] 181 remaining empty descriptions — needs LLM enrichment or manual, not automatable

## Blockers

None

## Context

- `_fetch_html_title_and_description()` now captures both title + meta description in one read
- `fetch_youtube_title()` uses oEmbed — works for videos, not channels/playlists
- 181 empty descriptions are HN threads, paywalled sites, JS-rendered pages — no meta tags
- Test baseline: 196 passed, 0 failed, 0 skipped

## Next Session

Gleaning cleanup is essentially done. Move to Experimentation phase: document baseline search performance and start parameter tuning with the Search Harness.
