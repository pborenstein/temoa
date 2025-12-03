# 👣 Temoa

> [Temoa](https://nahuatl.wired-humanities.org/content/temoa) (Nahuatl): To search for, to seek

A local semantic search server for your Obsidian vault. Search by meaning, not keywords. Access from mobile via HTTP.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

## What it does

### Core Search Features

| Feature | Description |
|:--------|:------------|
| Semantic search | Find notes by meaning, not exact keywords |
| Hybrid search | Combine BM25 keyword search with semantic embeddings |
| Cross-encoder re-ranking | Two-stage retrieval for 20-30% better precision |
| Query expansion | Automatically expand short queries using TF-IDF |
| Time-aware scoring | Boost recent documents with configurable decay |
| Type filtering | Filter by document type (gleaning, writering, daily, etc.) |

### Mobile Experience

| Feature | Description |
|:--------|:------------|
| Mobile-first UI | Optimized for phone use with compact collapsible results |
| PWA support | Install on home screen for one-tap access |
| Search history | Last 10 searches saved locally |
| Keyboard shortcuts | `/` to focus search, `Esc` to clear, `t` to toggle expanded query |

### Infrastructure

| Feature | Description |
|:--------|:------------|
| Multi-vault support | Search across multiple vaults with fast switching |
| Local processing | All embeddings and search happen on your machine |
| Obsidian integration | Results open directly in Obsidian app |
| Gleaning extraction | Automatically extract saved links from daily notes |
| Incremental reindexing | 30x faster updates (5s vs 159s) |

## Installation

```bash
# Clone repository
git clone https://github.com/pborenstein/temoa
cd temoa

# Install with uv
uv sync

# Install CLI globally (optional)
uv tool install --editable .
```

## Configuration

Create a config file at `~/.config/temoa/config.json`:

```bash
mkdir -p ~/.config/temoa
cat > ~/.config/temoa/config.json << 'EOF'
{
  "vault_path": "~/Obsidian/your-vault",
  "synthesis_path": "~/projects/temoa/synthesis",
  "storage_dir": null,
  "default_model": "all-mpnet-base-v2",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 10,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  }
}
EOF
```

### Multi-Vault Configuration

To search across multiple vaults, use the `vaults` array:

```json
{
  "vaults": [
    {"name": "main", "path": "~/Obsidian/main-vault", "is_default": true},
    {"name": "work", "path": "~/Obsidian/work-vault", "is_default": false},
    {"name": "archive", "path": "~/Obsidian/archive", "is_default": false}
  ],
  "vault_path": "~/Obsidian/main-vault",
  "synthesis_path": "~/projects/temoa/synthesis",
  "storage_dir": null,
  "default_model": "all-mpnet-base-v2",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 10,
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  }
}
```

Multi-vault support includes LRU cache (max 3 vaults in memory, ~1.5GB RAM), fast vault switching (~400ms when cached), independent indexes per vault (stored in `vault/.temoa/`), vault selector in web UI, and `--vault` CLI flag for all commands.

Configuration files are searched in priority order:

1. `~/.config/temoa/config.json` (recommended)
2. `~/.temoa.json` (alternative)
3. `./config.json` (development)

### Configuration Fields

| Field | Description |
|:------|:------------|
| `vaults` | Array of vault configurations (optional, for multi-vault) |
| `vault_path` | Path to your Obsidian vault (or default vault) |
| `synthesis_path` | Path to Synthesis engine (bundled in `synthesis/`) |
| `storage_dir` | Where to store embeddings index (default: `vault/.temoa/`) |
| `default_model` | Embedding model (see Available Models below) |
| `server` | HTTP server settings |
| `search.time_decay.enabled` | Enable recency boost (default: true) |
| `search.time_decay.half_life_days` | Days for 50% decay (default: 90) |
| `search.time_decay.max_boost` | Maximum boost for today's docs (default: 0.2 = 20%) |

## Quick Start

```bash
# Build embedding index (first time only)
temoa index

# Start server
temoa server

# Access web UI
open http://localhost:8080

# Or search from CLI
temoa search "semantic search"

# Access from mobile (via Tailscale)
# http://<tailscale-ip>:8080
```

First startup requires model download (30-60s one-time). Subsequent starts take ~15s.

## CLI Commands

```bash
# Configuration
temoa config              # Show current config

# Indexing
temoa index               # Build index from scratch (first time)
temoa reindex             # Update index incrementally (daily use)

# Searching
temoa search "query"      # Quick search from terminal
temoa archaeology "topic" # Temporal analysis (when was I interested in X?)
temoa stats               # Vault statistics

# Gleanings
temoa extract             # Extract gleanings from daily notes

# Gleaning management
temoa gleaning list                           # List all gleanings
temoa gleaning show <id>                      # Show gleaning details
temoa gleaning mark <id> --status inactive    # Mark gleaning status
temoa gleaning maintain                       # Check links, add descriptions

# Server
temoa server              # Start HTTP server (port 8080)
temoa server --reload     # Start with auto-reload (dev)
```

### Index vs Reindex

| Command | Description | Files Processed | Time | Use Case |
|:--------|:------------|:----------------|:-----|:---------|
| `temoa index` | Full rebuild | All files (3,000+) | ~2-3 minutes | First time setup, index corruption |
| `temoa reindex` | Incremental update | New, modified, deleted | ~5 seconds | Daily use (30x faster) |

#### Performance Example (3,059 file vault)

| Operation | Time | Files Processed |
|:----------|:-----|:----------------|
| Full index | 159s | 3,059 files |
| Incremental (no changes) | 4.8s | 0 files |
| Incremental (5 new files) | 6-8s | 5 files |

Incremental reindexing detects new files (not in previous index), modified files (changed modification timestamp), and deleted files (in index but not in vault).

## HTTP API

### Search
```bash
GET /search?q=<query>&limit=10&min_score=0.3&exclude_types=daily&vault=main
```

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `q` | string | required | Search query |
| `limit` | integer | 10 | Maximum results (max: 100) |
| `min_score` | float | 0.3 | Minimum similarity score (0-1) |
| `exclude_types` | string | "daily" | Comma-separated types to exclude |
| `include_types` | string | none | Comma-separated types to include |
| `hybrid` | boolean | false | Use hybrid search (BM25 + semantic) |
| `rerank` | boolean | true | Enable cross-encoder re-ranking |
| `expand_query` | boolean | true | Auto-expand short queries (<3 words) |
| `time_boost` | boolean | true | Apply time-decay boost to recent docs |
| `vault` | string | config | Vault name to search |

**Example:**
```bash
curl "http://localhost:8080/search?q=semantic+search&limit=5"
```

**Response:**
```json
{
  "query": "semantic search",
  "expanded_query": null,
  "results": [
    {
      "title": "Semantic Search Tools",
      "relative_path": "L/Gleanings/abc123.md",
      "similarity_score": 0.847,
      "cross_encoder_score": 4.523,
      "obsidian_uri": "obsidian://open?vault=...",
      "description": "Overview of semantic search implementations",
      "tags": ["search", "ai"],
      "frontmatter": {
        "type": "gleaning",
        "date": "2025-01-15"
      }
    }
  ],
  "total": 15,
  "filtered_count": 10,
  "model": "all-mpnet-base-v2",
  "vault": "main"
}
```

**Note**: When query expansion is triggered (short queries), `expanded_query` shows the enhanced query used for search.

### Archaeology (Temporal Analysis)
```bash
GET /archaeology?q=<topic>&threshold=0.2
```

Shows when you were interested in a topic over time.

### Statistics
```bash
GET /stats
```

Vault statistics (file count, embeddings, tags).

### Health Check
```bash
GET /health
```

Server health and model status.

### Extract Gleanings
```bash
POST /extract?incremental=true&auto_reindex=true
```

Extract gleanings from daily notes and optionally reindex.

### Reindex
```bash
POST /reindex?force=false
```

Update embedding index with new/modified files.

| Parameter | Type | Default | Description |
|:----------|:-----|:--------|:------------|
| `force` | boolean | false | `false` for incremental update, `true` for full rebuild |

**Examples:**
```bash
# Incremental reindex (only changed files)
curl -X POST "http://localhost:8080/reindex?force=false"

# Full rebuild (all files)
curl -X POST "http://localhost:8080/reindex?force=true"
```

**Response:**
```json
{
  "status": "success",
  "files_indexed": 3059,
  "new_files": 5,
  "modified_files": 2,
  "deleted_files": 1
}
```

## Available Models

| Model | Dimensions | Speed | Quality | Use Case |
|:------|:-----------|:------|:--------|:---------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | Quick searches |
| `all-MiniLM-L12-v2` | 384 | Medium | Better | Balanced |
| `all-mpnet-base-v2` | 768 | Slower | Best | Default (quality) |
| `multi-qa-mpnet-base-cos-v1` | 768 | Slower | Best | Q&A optimized |
| `paraphrase-albert-small-v2` | 768 | Slower | Good | Paraphrasing |

Default: `all-mpnet-base-v2`

Change model in config or via `--model` flag.

## Gleanings

**Gleanings** are saved links extracted from your daily notes.

### Format in Daily Notes

```markdown
## Gleanings

- [Article Title](https://example.com) - Description here
- https://example.com (naked URLs work too)
```

### Extraction

```bash
# Extract new gleanings from daily notes
temoa extract

# Full re-extraction (process all files)
temoa extract --full

# Dry run (preview what would be extracted)
temoa extract --dry-run
```

Supports multiple formats including markdown links (`- [Title](URL) - Description`), naked URLs with bullets (`- https://...`), bare naked URLs (`https://...`), multi-line descriptions (lines starting with `>`), and timestamps (`[HH:MM]` preserved in date field).

### Gleaning Management

```bash
# List inactive gleanings (dead links)
temoa gleaning list --status inactive

# Mark gleaning as hidden
temoa gleaning mark abc123 --status hidden --reason "duplicate"

# Check all gleaning links, mark dead ones inactive
temoa gleaning maintain --check-links --mark-dead-inactive
```

Gleanings have three status types: `active` (normal, included in search), `inactive` (dead link, excluded from search, auto-restores if link comes back), and `hidden` (manually hidden, never auto-restored).

## Mobile Access via Tailscale

Temoa runs on your local network. Access from mobile using Tailscale:

1. **Install Tailscale** on server and mobile device
2. **Start server**: `temoa server`
3. **Get server IP**: `tailscale ip -4` (e.g., `100.x.x.x`)
4. **Access from mobile**: `http://100.x.x.x:8080`

Tailscale encrypts all traffic, eliminating the need for HTTPS and preventing public exposure.

### PWA Installation (Progressive Web App)

Temoa can be installed as a PWA on mobile devices for quick access:

**iOS (Safari)**:
1. Open Temoa in Safari: `http://100.x.x.x:8080`
2. Tap the Share button (box with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Name it "Temoa" and tap "Add"
5. Tap the Temoa icon on your home screen to launch

**Android (Chrome)**:
1. Open Temoa in Chrome: `http://100.x.x.x:8080`
2. Tap the three-dot menu (⋮)
3. Tap "Add to Home screen" or "Install app"
4. Confirm by tapping "Add" or "Install"
5. Tap the Temoa icon on your home screen to launch

Installing as a PWA provides one-tap access from your home screen, launches like a native app without browser UI, provides offline UI (search requires network), and maintains persistent state and settings.

## Deployment

### Background Process (Mac/Linux)

```bash
# Start server in background
nohup temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid

# View logs
tail -f ~/temoa.log

# Stop server
kill $(cat ~/temoa.pid)
```

### System Service (Linux)

```bash
# Create systemd service
sudo tee /etc/systemd/system/temoa.service << 'EOF'
[Unit]
Description=Temoa Semantic Search Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/projects/temoa
ExecStart=/home/youruser/.local/bin/temoa server
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable temoa
sudo systemctl start temoa
```

### Automation

```bash
# Daily gleaning extraction (add to crontab)
0 23 * * * cd ~/projects/temoa && temoa extract
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete deployment guide.

## Architecture

```
Mobile Browser
    ↓ HTTP over Tailscale VPN
FastAPI Server (temoa)
    ↓ Direct Python imports
Synthesis Engine (sentence-transformers)
    ↓ Embeddings
Obsidian Vault + .temoa/index
```

The architecture includes a FastAPI server for HTTP API and web UI, Synthesis engine for semantic search and embeddings, sentence-transformers for pre-trained models, and local storage in the `.temoa/` directory within the vault for embeddings index and state.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Performance

### Search Latency (3,000 file vault)

| Operation | Time |
|:----------|:-----|
| Semantic search | ~400ms |
| Hybrid search (BM25 + semantic) | ~450ms |
| With cross-encoder re-ranking | ~600ms |
| Short query with expansion + re-ranking | ~800-1000ms |

### Memory Usage

| Configuration | Memory |
|:--------------|:-------|
| Single vault | ~600 MB (bi-encoder model) |
| With re-ranking | ~800 MB (bi-encoder + cross-encoder) |
| Multi-vault (3 vaults cached) | ~1.5 GB |

### Other Metrics

| Metric | Value |
|:-------|:------|
| Startup time | ~15-20s (model loading) |
| Full reindex (3,059 files) | ~159s |
| Incremental reindex (no changes) | ~5s (30x faster) |
| Incremental reindex (5-10 new files) | ~6-8s |
| Scalability | Linear to 10,000+ files |

## Search Quality Pipeline

Temoa uses a multi-stage search pipeline for high precision:

1. Query Enhancement (optional, for short queries) - Auto-expand queries <3 words using TF-IDF. Example: `"AI"` → `"AI machine learning neural networks"`

2. Initial Retrieval - Fast bi-encoder similarity (all-mpnet-base-v2) for semantic search, or BM25 keyword + semantic with RRF fusion for hybrid search. Returns top 100 candidates.

3. Filtering - Apply score threshold (min_score), status filter (exclude inactive gleanings), and type filter (exclude/include by document type).

4. Time-Aware Boost (optional) - Recent documents get exponential decay boost with configurable half-life (default: 90 days) and max boost of 20% for today's documents.

5. Cross-Encoder Re-Ranking (optional, enabled by default) - Precise two-stage retrieval using ms-marco-MiniLM-L-6-v2. Re-ranks top 100 candidates for 20-30% precision improvement with ~200ms latency.

6. Top-K Selection - Return final results (default: 10).

Expected quality improvements include Precision@5 of 80-90% (up from 60-70% without re-ranking), much better results for short queries with expansion, and improved ranking for recent topics with time boost.

See [docs/SEARCH-MECHANISMS.md](docs/SEARCH-MECHANISMS.md) for detailed technical reference.

## Documentation

- **[docs/README.md](docs/README.md)**: Documentation index and navigation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture with diagrams
- **[docs/SEARCH-MECHANISMS.md](docs/SEARCH-MECHANISMS.md)**: Search algorithms and quality pipeline
- **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)**: Implementation progress and plans
- **[docs/CHRONICLES.md](docs/CHRONICLES.md)**: Design decisions and history (split into chapters)
- **[docs/GLEANINGS.md](docs/GLEANINGS.md)**: Gleaning extraction guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)**: Production deployment guide
- **[CLAUDE.md](CLAUDE.md)**: Development guide for AI sessions

## Project Status

**Version**: 0.6.0

**Phase**: Phase 3 Complete ✅

All major phases completed: Phase 0 (Discovery & Validation), Phase 1 (Minimal Viable Search), Phase 2 (Gleanings Integration), Phase 2.5 (Mobile Validation & UI Optimization), and Phase 3 (Enhanced Features including multi-vault, search quality, and UX polish).

**Next**: Phase 4 (Vault-First LLM) or Production Hardening

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for complete history and next steps.

## Philosophy

> You don't have an organization problem. You have a surfacing problem.

- **Simple over complex**: Individual files, not state management
- **Semantic search**: Let embeddings find connections
- **Mobile-first**: Optimize for phone use
- **Local processing**: Privacy, no external APIs
- **Vault-first habit**: Check your vault before searching the internet

## Tech Stack

- Python 3.11+ with [uv](https://github.com/astral-sh/uv)
- FastAPI (async HTTP server)
- sentence-transformers (embeddings)
- Click (CLI)
- Vanilla HTML/CSS/JS (web UI)

---

**Created**: 2025-11-17
**Last Updated**: 2025-12-03
**Version**: 0.6.0
