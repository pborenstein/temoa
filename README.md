# Ixpantilia

> [Ixpantilia](https://nahuatl.wired-humanities.org/content/ixpantilia) (Nahuatl): To find out something about a friend; for something to present or manifest itself

**A local semantic search server that enables vault-first research workflows, making your personal knowledge base the first stop before searching the broader internet.**

[![Status](https://img.shields.io/badge/status-planning-yellow)](docs/IXPANTILIA.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

## The Problem

**Current Research Workflow (Broken)**:
```
Question → Perplexity/Claude/GPT → Save link to daily note → Never see it again
```

**Pain Points**:
- Saved links (gleanings) accumulate but are never surfaced when needed
- No way to check "what do I already know about X?" before searching externally
- Obsidian Copilot semantic search is slow and unusable on mobile
- Mobile is the primary research environment, but search is friction-full
- Native Obsidian search only works if you know exact keywords

## The Solution

**Vault-First Research Workflow**:
```
Question → Ixpantilia (semantic search) → [if relevant found: build on it]
                                        → [if not: external search → save → connect to vault]
```

Ixpantilia is a **local HTTP server** that provides:
- Fast semantic search across your entire Obsidian vault (~1,900 files)
- Mobile-first design (server does the heavy lifting)
- Private and local (runs on your network via Tailscale)
- Automatic surfacing of gleanings (saved links) when contextually relevant
- Sub-2-second response times from mobile devices

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Mobile (Browser / Obsidian / API client)            │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP Request: /search?q=semantic+search
                  ↓
┌─────────────────────────────────────────────────────┐
│ Ixpantilia Server (FastAPI)                         │
│ - Receives query                                    │
│ - Calls synthesis subprocess                        │
│ - Returns formatted results                         │
└─────────────────┬───────────────────────────────────┘
                  │ Subprocess call
                  ↓
┌─────────────────────────────────────────────────────┐
│ Synthesis (existing semantic search engine)         │
│ - Loads embeddings (sentence-transformers)          │
│ - Performs semantic search                          │
│ - Returns JSON with obsidian:// URIs                │
└─────────────────────────────────────────────────────┘
```

### Key Components

1. **Synthesis** (existing): Local semantic search engine using sentence-transformers
   - 5 embedding models to choose from
   - 1,899 vault files already indexed
   - Supports search, archaeology (temporal analysis), and statistics
   - Located at `.tools/synthesis/` in main Obsidian vault

2. **Ixpantilia Server** (to be built): FastAPI HTTP wrapper around Synthesis
   - Provides `/search`, `/archaeology`, `/stats` endpoints
   - Serves mobile-friendly web UI
   - Handles authentication via Tailscale network

3. **Mobile Interface**: Simple HTML/JS search interface
   - Clean, minimal design optimized for phone screens
   - Click results to open directly in Obsidian mobile app
   - Progressive Web App (PWA) support for installation

4. **Gleanings**: Individual notes for saved links
   - Extracted from daily notes `## Gleanings` sections
   - Each gleaning becomes a searchable note in `L/Gleanings/`
   - Automatically indexed by Synthesis for semantic search

## Project Status

**Current Phase**: Planning / Phase 0 Discovery

**Completed**:
- ✅ Problem definition and requirements
- ✅ Architecture design
- ✅ Technical stack selection (FastAPI + Synthesis)
- ✅ Planning documentation (847 lines in `docs/IXPANTILIA.md`)
- ✅ Analysis of similar tools (Obsidian Copilot learnings)
- ✅ Existing infrastructure (Synthesis search engine ready)

**Next Steps**:
- [ ] Phase 0: Discovery & validation (test Synthesis performance)
- [ ] Phase 1: Minimal viable search (basic HTTP API + web UI)
- [ ] Phase 2: Gleanings integration (extraction + indexing)
- [ ] Phase 3: Enhanced features (better UI, archaeology endpoint)
- [ ] Phase 4: Vault-first LLM (chat with vault context)

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for detailed implementation plan.

## Tech Stack

- **Language**: Python 3.11+ with [uv](https://github.com/astral-sh/uv) package manager
- **Web Framework**: FastAPI (async, OpenAPI docs, easy testing)
- **Search Engine**: Synthesis (sentence-transformers, local embeddings)
- **Embeddings**: 5 models available, default `all-MiniLM-L6-v2` (384d, fast)
- **Deployment**: Tailscale network, systemd service (or Docker)
- **Frontend**: Vanilla HTML/JS (no framework complexity)

## Quick Start (Future)

> Note: Implementation not yet started. These are planned commands.

```bash
# Clone the repository
git clone https://github.com/pborenstein/ixpantilia
cd ixpantilia

# Install dependencies with uv
uv sync

# Configure vault path
cp config.example.json config.json
# Edit config.json to point to your vault and synthesis installation

# Start the server
uv run server.py
# Server will run at http://localhost:8080

# Or use systemd service
sudo systemctl start ixpantilia

# Access from mobile
# http://<tailscale-ip>:8080
```

## Planned API Endpoints

### `GET /search?q=<query>&limit=<n>&model=<model>`
Semantic search across vault.

**Example**:
```bash
curl "http://localhost:8080/search?q=semantic+search&limit=5"
```

**Response**:
```json
{
  "query": "semantic search",
  "results": [
    {
      "relative_path": "L/Gleanings/2025-11-11-semantic-search.md",
      "title": "Semantic Search Tools",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://vault/amoxtli/L/Gleanings/2025-11-11-semantic-search",
      "wiki_link": "[[Semantic Search Tools]]",
      "file_path": "~/Obsidian/amoxtli/L/Gleanings/2025-11-11-semantic-search.md"
    }
  ],
  "total": 15,
  "model": "all-MiniLM-L6-v2"
}
```

### `GET /archaeology?q=<topic>&threshold=<n>`
Temporal analysis showing when you were interested in a topic.

**Example**:
```bash
curl "http://localhost:8080/archaeology?q=AI&threshold=0.2"
```

**Response**: JSON with timeline entries showing interest over time.

### `GET /stats`
Vault statistics and server health.

### `POST /chat` (Phase 4)
Vault-first LLM chat - searches vault before calling external LLM.

## Example Queries

**Gleanings-focused**:
- "GitHub LLM projects"
- "semantic search implementations"
- "obsidian copilot alternatives"

**General vault**:
- "writing about trust"
- "notes on retirement planning"
- "productivity systems"

**MOC discovery**:
- "knowledge management"
- "personal knowledge base patterns"

**Temporal**:
- "when was I interested in AI agents?"
- "timeline of my productivity experiments"

## Documentation

- **[docs/IXPANTILIA.md](docs/IXPANTILIA.md)**: Comprehensive project plan (847 lines)
- **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)**: Detailed waterfall implementation plan
- **[docs/CHRONICLES.md](docs/CHRONICLES.md)**: Design discussions and decision log
- **[docs/copilot-learnings.md](docs/copilot-learnings.md)**: Analysis of Obsidian Copilot architecture
- **[CLAUDE.md](CLAUDE.md)**: Development guide for Claude AI sessions

## Related Projects

- **[Synthesis](old-ideas/synthesis/)**: Semantic search engine (production-ready)
  - Powers the actual search functionality
  - 5 embedding models, multi-modal support
  - Currently indexes 1,899 vault files

- **[Apantli](https://github.com/pborenstein/apantli)**: LLM proxy server
  - May be integrated with Ixpantilia in Phase 4
  - Provider-agnostic, usage tracking

- **[Old Gleanings](old-ideas/old-gleanings/)**: Previous gleaning management system (abandoned)
  - Contains 505 historical gleanings to migrate
  - Reference for extraction patterns
  - Example of over-engineering to avoid

## Philosophy

> **You don't have an organization problem. You have a surfacing problem.**

This project rejects the complexity trap of categorization, tagging systems, and manual curation. Instead:

- **Gleanings as notes**: Simple individual files, not state management
- **Semantic search**: Let embeddings find connections, not manual categories
- **Mobile-first**: Research happens on the phone, so optimize for that
- **Integration**: Lives inside Obsidian workflow, not separate app
- **Vault-first habit**: Check what you know before external search

## Success Metrics

**Quantitative**:
- Response time: < 2 seconds from mobile search to results
- Relevance: Top 3 results useful for 80%+ of queries
- Coverage: All 505+ gleanings searchable
- Usage: 5+ searches per day

**Qualitative**:
- Lower friction than opening Obsidian + manual search
- More useful than Obsidian Copilot on mobile
- Check vault before googling (vault-first habit formed)
- Finding forgotten gleanings regularly

**Behavioral**:
- Reduced external searches for known topics
- More connections between new findings and existing notes
- Actually using saved links instead of hoarding
- Building on past knowledge instead of starting from scratch

## Contributing

This is a personal knowledge management project, but the architecture and learnings may be useful for others building similar systems.

Key principles:
- **uv shop**: We use uv for dependency management, not pip or poetry
- **Plan like waterfall, implement in agile**: Detailed upfront planning, iterative execution
- **Mobile-first**: If it doesn't work on the phone, it doesn't work
- **Privacy**: All processing local, no external APIs (except LLM in Phase 4)

## License

[To be determined]

## Acknowledgments

- **Synthesis project**: Provides the semantic search foundation
- **Obsidian Copilot**: Architecture patterns and learnings
- **Nahuatl language**: Beautiful word meanings for project names

---

**Created**: 2025-11-17
**Status**: Planning Phase
**Next Milestone**: Phase 0 Discovery
