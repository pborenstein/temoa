---
created: 2025-09-06
tags: [tool, semantic-search, python]
status: production
---

# Synthesis

Local semantic search engine for Obsidian vault using sentence-transformers.

## What It Does

- Indexes markdown files with semantic embeddings
- Searches by meaning, not just keywords
- Temporal analysis ("archaeology" - when was I interested in X?)
- Runs locally, no external APIs

## Models Available

- `all-MiniLM-L6-v2` (384d) - Fast, good enough (default)
- `all-mpnet-base-v2` (768d) - Slower, better quality
- `multi-qa-mpnet-base-cos-v1` (768d) - Optimized for Q&A

## Performance

From real usage (1,899 files):
- Index time: ~2 minutes (cold)
- Search time: ~200-500ms
- Index size: ~3MB embeddings + 1MB metadata

## Usage

```bash
# Index vault
uv run main.py process

# Search
uv run main.py search "semantic search" --json

# Archaeology (temporal analysis)
uv run main.py archaeology "productivity" --json

# Stats
uv run main.py stats
```

## Architecture

- Python with sentence-transformers
- NumPy for vector storage
- JSON for metadata
- CLI with subprocess-friendly JSON output

## Why This Matters

Synthesis proves that local semantic search is fast enough for interactive use. This validates the [[Temoa]] architecture.

## Integration with Temoa

Temoa wraps Synthesis as subprocess:
- Clean separation of concerns
- Synthesis changes don't break Temoa
- Well-defined JSON interface
- ~50-100ms subprocess overhead (acceptable)

## Related

- [[Temoa]] - HTTP API wrapper for Synthesis
- [[Sentence Transformers]]
- [[Vector Databases]]
