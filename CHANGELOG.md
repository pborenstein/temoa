# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-03-28

First stable release. Local semantic search server for Obsidian vaults with
multi-stage search pipeline (semantic + BM25 + frontmatter), web UI, and
macOS launchd service management.

### Added

- Semantic search via Synthesis engine with configurable embedding models (all-MiniLM-L6-v2, all-mpnet-base-v2, all-MiniLM-L12-v2)
- BM25 keyword search with hybrid score blending (live slider)
- Cross-encoder reranking for result quality
- TF-IDF query expansion
- Time-aware scoring for recency weighting
- Frontmatter-aware search with tag boosting and description indexing
- Adaptive chunking for large documents ([ebbc70b](https://github.com/pborenstein/temoa/commit/ebbc70b))
- Obsidian-compatible filter syntax for search results ([4ba9053](https://github.com/pborenstein/temoa/commit/4ba9053))
- Query Filter pre-filtering with 15-20x speedup ([876ff8d](https://github.com/pborenstein/temoa/commit/876ff8d))
- Multi-vault support with per-vault model configuration ([94978f7](https://github.com/pborenstein/temoa/commit/94978f7))
- Incremental reindexing ([3b2c54e](https://github.com/pborenstein/temoa/commit/3b2c54e))
- Gleaning extraction from daily notes with URL normalization ([a5585da](https://github.com/pborenstein/temoa/commit/a5585da))
- GitHub API enrichment for gleaning metadata ([1a7dbd2](https://github.com/pborenstein/temoa/commit/1a7dbd2))
- YouTube oEmbed API for video title extraction ([a665aad](https://github.com/pborenstein/temoa/commit/a665aad))
- Mobile-first web UI with search, management, and harness views
- Search harness and Inspector for parameter tuning ([73289ac](https://github.com/pborenstein/temoa/commit/73289ac))
- PWA support ([ebf18fa](https://github.com/pborenstein/temoa/commit/ebf18fa))
- CLI with search, index, extract, config, and vaults commands
- macOS launchd service with modern bootstrap/bootout API ([309e608](https://github.com/pborenstein/temoa/commit/309e608))
- Configuration via config.json with environment variable support

### Fixed

- Unicode surrogate sanitization in JSON responses ([03d3468](https://github.com/pborenstein/temoa/commit/03d3468))
- Vault model selection honoring per-vault config ([219313c](https://github.com/pborenstein/temoa/commit/219313c))
- Reindex metadata loss and YAML surrogate escapes ([90c5e2e](https://github.com/pborenstein/temoa/commit/90c5e2e))
- Filter results displaying correctly ([48e8bdf](https://github.com/pborenstein/temoa/commit/48e8bdf))
- Port conflict detection in dev mode ([9e9bfe6](https://github.com/pborenstein/temoa/commit/9e9bfe6))

### Changed

- Eliminated double vault scan in incremental reindex ([584bd7f](https://github.com/pborenstein/temoa/commit/584bd7f))
- Per-vault filter state management ([2b6a36a](https://github.com/pborenstein/temoa/commit/2b6a36a))
- Query expansion disabled by default based on production usage ([79aa611](https://github.com/pborenstein/temoa/commit/79aa611))

[Unreleased]: https://github.com/pborenstein/temoa/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/pborenstein/temoa/releases/tag/v1.0.0
