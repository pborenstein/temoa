# Temoa

> [Temoa](https://nahuatl.wired-humanities.org/content/temoa) (Nahuatl): To search for, to seek

A local semantic search server for your Obsidian vault. Search by meaning, not keywords. Access from mobile via HTTP.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-orange.svg)](https://github.com/astral-sh/uv)

## What it does

- **Semantic search**: Find notes by meaning, not exact keywords
- **Mobile access**: Search from your phone via HTTP
- **Local processing**: All embeddings and search happen on your machine
- **Obsidian integration**: Results open directly in Obsidian app
- **Gleaning extraction**: Automatically extract saved links from daily notes

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
    "timeout": 10
  }
}
EOF
```

**Config search order:**
1. `~/.config/temoa/config.json` (recommended)
2. `~/.temoa.json` (alternative)
3. `./config.json` (development)

**Config fields:**
- `vault_path`: Path to your Obsidian vault
- `synthesis_path`: Path to Synthesis engine (bundled in `synthesis/`)
- `storage_dir`: Where to store embeddings index (default: `vault/.temoa/`)
- `default_model`: Embedding model (see Available Models below)
- `server`: HTTP server settings
- `search`: Search defaults and limits

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

**First startup**: Model download takes 30-60s (one-time). Subsequent starts: ~15s.

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

**`temoa index`** - Full rebuild
- Processes all files in the vault (3,000+ files)
- Takes ~2-3 minutes
- Use when: First time setup, or index corruption

**`temoa reindex`** - Incremental update (recommended)
- Only processes new, modified, or deleted files
- Takes ~5 seconds when no changes
- Takes ~6-8 seconds with 5-10 new files
- **30x faster** than full rebuild for typical daily use

**Performance example** (3,059 file vault):

| Operation | Time | Files Processed |
|-----------|------|-----------------|
| Full index | 159s | 3,059 files |
| Incremental (no changes) | 4.8s | 0 files |
| Incremental (5 new files) | 6-8s | 5 files |

**Incremental reindexing** detects:
- New files (not in previous index)
- Modified files (changed modification timestamp)
- Deleted files (in index but not in vault)

## HTTP API

### Search
```bash
GET /search?q=<query>&limit=10&min_score=0.3&exclude_types=daily
```

**Parameters:**
- `q`: Search query (required)
- `limit`: Max results (default: 10, max: 100)
- `min_score`: Minimum similarity score 0-1 (default: 0.3)
- `exclude_types`: Comma-separated types to exclude (default: "daily")
- `include_types`: Comma-separated types to include (optional)
- `hybrid`: Use hybrid search (BM25 + semantic) (default: false)

**Example:**
```bash
curl "http://localhost:8080/search?q=semantic+search&limit=5"
```

**Response:**
```json
{
  "query": "semantic search",
  "results": [
    {
      "title": "Semantic Search Tools",
      "relative_path": "L/Gleanings/abc123.md",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://open?vault=...",
      "description": "Overview of semantic search implementations",
      "tags": ["search", "ai"]
    }
  ],
  "total": 15,
  "model": "all-mpnet-base-v2"
}
```

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

**Parameters:**
- `force`: `false` (incremental - default) or `true` (full rebuild)

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
|-------|-----------|-------|---------|----------|
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

**Multiple formats supported:**
- Markdown links: `- [Title](URL) - Description`
- Naked URLs with bullet: `- https://...`
- Naked URLs bare: `https://...`
- Multi-line descriptions (lines starting with `>`)
- Timestamps: `[HH:MM]` preserved in date field

### Gleaning Management

```bash
# List inactive gleanings (dead links)
temoa gleaning list --status inactive

# Mark gleaning as hidden
temoa gleaning mark abc123 --status hidden --reason "duplicate"

# Check all gleaning links, mark dead ones inactive
temoa gleaning maintain --check-links --mark-dead-inactive
```

**Three status types:**
- `active`: Normal, included in search
- `inactive`: Dead link, excluded from search, auto-restores if link comes back
- `hidden`: Manually hidden, never auto-restored

## Mobile Access via Tailscale

Temoa runs on your local network. Access from mobile using Tailscale:

1. **Install Tailscale** on server and mobile device
2. **Start server**: `temoa server`
3. **Get server IP**: `tailscale ip -4` (e.g., `100.x.x.x`)
4. **Access from mobile**: `http://100.x.x.x:8080`

**Security**: Tailscale encrypts all traffic. No HTTPS needed. No public exposure.

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

**Key components:**
- **FastAPI server**: HTTP API, web UI, request handling
- **Synthesis engine**: Semantic search, embeddings, similarity calculation
- **sentence-transformers**: Pre-trained embedding models
- **Storage**: `.temoa/` directory in vault (embeddings index, state)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Performance

**Search**: ~400ms average (2,000+ files)
**Memory**: ~600 MB (model loaded in RAM)
**Startup**: ~15s (model loading)
**Scales**: Linear to 10,000+ files

## Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: System architecture with diagrams
- **[docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)**: Implementation progress and plans
- **[docs/CHRONICLES.md](docs/CHRONICLES.md)**: Design decisions and history
- **[docs/GLEANINGS.md](docs/GLEANINGS.md)**: Gleaning extraction guide
- **[CLAUDE.md](CLAUDE.md)**: Development guide for AI sessions

## Project Status

See [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for current phase and progress.

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
**Last Updated**: 2025-11-22
