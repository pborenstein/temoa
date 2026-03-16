---
phase: "Experimentation"
phase_name: "Gleanings Cleanup"
updated: 2026-03-15
last_commit: d389c66
branch: main
---

# Current Context

## Current Focus

Fixing the gleanings extraction pipeline. A clean re-extraction revealed title-fetch failures for GitHub URLs (domain name written as title). Fixed extractor to use GitHub API for `github.com` URLs and read 64KB instead of 8KB for other sites.

## Active Tasks

- [x] Write `docs/gleanings-history.md` — chronology of the gleanings system
- [x] Fix `extract_gleanings.py`: GitHub URLs use API, not HTML scrape
- [ ] Run full re-extraction on `~/Obsidian/amoxtli` with fixed extractor
- [ ] Fix remaining domain-fallback titles (YouTube x19, paywalled sites — likely manual)
- [ ] Address 210 gleanings with empty descriptions

## Blockers

None

## Context

- 1,146 gleanings total; 49 have domain name as title (fetch failed at extraction time)
- Root cause for GitHub: `<title>` tag appears beyond 8KB in GitHub HTML
- Fix: `fetch_github_title_and_description()` calls `/api.github.com/repos/user/repo`
- Naked URL GitHub gleanings now also get description from API (not just title)
- YouTube/WaPo/WSJ/NYer domain-fallbacks are expected — those sites block scrapers
- 0 gleanings have GitHub enrichment data (the old enriched files were wiped by re-extraction)

## Next Session

Run `temoa extract --full --vault ~/Obsidian/amoxtli` with the fixed extractor and verify the 9 previously bad GitHub gleanings now have correct titles. Then decide how to handle the 19 youtube.com fallbacks.
