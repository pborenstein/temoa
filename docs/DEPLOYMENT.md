# Temoa Deployment Guide

**Last Updated**: 2026-01-04
**Version**: 0.6.0
**For**: Phase 3.5 Complete - Production Deployment

---

## Prerequisites

| Component | Requirements |
|:----------|:-------------|
| Server machine (Mac/Linux) | Python 3.11+, uv package manager, Git, Obsidian vault accessible, Tailscale installed and running |
| Mobile device | iOS or Android, Tailscale app installed, Obsidian app installed, connected to same Tailscale network |

---

## Installation

### Clone Repository

```bash
# First time
cd ~/projects
git clone https://github.com/pborenstein/temoa.git
cd temoa

# Updates
cd ~/projects/temoa
git pull origin main
```

### Install Dependencies

```bash
uv sync
```

This creates `.venv/` and installs FastAPI, uvicorn, sentence-transformers, etc. (~30-60 seconds)

### Install CLI (Optional)

```bash
# Install globally
uv tool install --editable .

# Now 'temoa' command available everywhere
temoa --help
```

---

## Configuration

Create `~/.config/temoa/config.json`:

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
    "port": 8080,
    "cors_origins": [
      "http://localhost:8080",
      "http://127.0.0.1:8080"
    ]
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 10,
    "default_profile": "default",
    "time_decay": {
      "enabled": true,
      "half_life_days": 90,
      "max_boost": 0.2
    }
  },
  "chunking": {
    "enabled": true,
    "chunk_size": 2000,
    "chunk_overlap": 400,
    "chunk_threshold": 4000
  },
  "rate_limits": {
    "search_per_hour": 1000,
    "archaeology_per_hour": 20,
    "reindex_per_hour": 5,
    "extract_per_hour": 10
  }
}
EOF
```

**New in Phase 3.5:**
- `search.default_profile`: Default search profile to use ("default", "repos", "recent", "deep", "keywords")
- `chunking`: Adaptive chunking configuration (Phase 3.5.2 - enables 100% content searchability)

**New in Phase 4:**
- `server.cors_origins`: CORS allowed origins (restrictive by default)
- `rate_limits`: DoS protection for expensive endpoints

### Multi-Vault Configuration

For multiple vaults, use the `vaults` dictionary with per-vault settings:

```bash
cat > ~/.config/temoa/config.json << 'EOF'
{
  "vaults": {
    "amoxtli": {
      "path": "~/Obsidian/amoxtli",
      "model": "all-mpnet-base-v2",
      "default_profile": "default"
    },
    "1002": {
      "path": "~/Obsidian/1002",
      "model": "all-MiniLM-L6-v2",
      "default_profile": "deep"
    },
    "work": {
      "path": "~/Obsidian/work-vault",
      "model": "all-mpnet-base-v2",
      "default_profile": "repos"
    }
  },
  "default_vault": "amoxtli",
  "synthesis_path": "~/projects/temoa/synthesis",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 100,
    "timeout": 10
  },
  "chunking": {
    "enabled": true,
    "chunk_size": 2000,
    "chunk_overlap": 400,
    "chunk_threshold": 4000
  }
}
EOF
```

**Multi-vault features:**
- **LRU cache**: Max 3 vaults in memory (~1.5GB total)
- **Independent indexes**: Each vault has `.temoa/model-name/` directory
- **Per-vault configuration**: Model, default profile customizable per vault
- **Vault selector**: Dropdown in web UI
- **CLI vault flag**: `--vault` flag for all commands
- **Fast switching**: ~400ms when cached, ~15-20s on first load

### Configuration Fields

| Field | Description |
|:------|:------------|
| `vaults` | Dictionary of vault configurations with per-vault settings (optional) |
| `default_vault` | Which vault to use by default (multi-vault only) |
| `vault_path` | Path to your Obsidian vault (single-vault setup) |
| `storage_dir` | Leave `null` to use `vault/.temoa/model-name/` |
| `server.port` | Change if 8080 already in use |
| `search.default_profile` | Default search profile ("default", "repos", "recent", "deep", "keywords") |
| `search.time_decay` | Time-aware scoring configuration (boosts recent documents) |
| `chunking.enabled` | Enable adaptive chunking for large files (recommended: true) |
| `chunking.chunk_size` | Chunk size in characters (default: 2000) |
| `chunking.chunk_overlap` | Overlap between chunks to prevent boundary misses (default: 400) |
| `chunking.chunk_threshold` | Minimum file size to trigger chunking (default: 4000) |

Use `~` for home directory in paths (auto-expanded).

---

## Build Index

**First time only** - full rebuild (~2-3 minutes for ~3000 files):

```bash
temoa index
```

The indexing process scans the vault for all markdown files, downloads the sentence-transformer model (first time only, then cached), generates embeddings for all files (splitting large files into chunks if chunking enabled), and stores them in the `vault/.temoa/model-name/` directory with file tracking.

Expected output:
```
Building index for: /Users/you/Obsidian/vault
Indexing vault...
✓ Index built successfully
Files indexed: 3,059
Chunks created: 8,755 (from 2,006 files with chunking enabled)
Model: all-mpnet-base-v2
```

First index takes 2-3 minutes. After that, use `temoa reindex` which is 30x faster (only processes changed files).

**Adaptive Chunking (Phase 3.5.2)**:

```bash
# Enable chunking during indexing (recommended)
temoa index --enable-chunking

# Or configure in config.json (chunking.enabled = true)
```

**IMPORTANT**: `--enable-chunking` is an **indexing-time setting only**. Once indexed with chunking:
- Searches work normally (no special flag needed)
- Chunk deduplication happens automatically (keeps best chunk per file)
- You don't need to "remember" the index was chunked

**What chunking does**:
- Files >= 4,000 chars: Split into 2,000-char chunks with 400-char overlap
- Files < 4,000 chars: Indexed as-is (no chunking)
- Result: 100% content searchability (vs ~35% for large files without chunking)

**Multi-vault indexing**:
```bash
# Index specific vault
temoa index --vault work --enable-chunking

# Each vault gets independent index at vault/.temoa/model-name/
```

**Troubleshooting**:
- "No config file found" → Create config (see above)
- "Vault path does not exist" → Fix `vault_path` in config
- Takes >2 minutes → Normal for large vaults (>1000 files)
- Chunking adds 2.5-3x indexing time (acceptable for 100% coverage)

---

## Deploy Server

### Background Process (Mac/Linux)

**Primary deployment method:**

```bash
# Start server in background
nohup temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid
```

**View logs**:
```bash
tail -f ~/temoa.log
```

**Stop server**:
```bash
kill $(cat ~/temoa.pid)
rm ~/temoa.pid
```

**Check status**:
```bash
ps aux | grep "temoa server"
# Or check logs
tail ~/temoa.log
```

**Restart**:
```bash
kill $(cat ~/temoa.pid)
nohup temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid
```

### Foreground (Testing)

For testing or development:

```bash
temoa server
# Press Ctrl-C to stop
```

Use `--reload` flag for auto-reload during development:
```bash
temoa server --reload
```

### System Service (macOS)

For production deployment on macOS with auto-start and auto-restart:

```bash
# Install launchd service
./launchd/install.sh

# Access at http://localhost:4001
```

**Features**:

- **Auto-start**: Service starts on login
- **Auto-restart**: Automatic recovery from crashes
- **Log management**: Centralized logs in `~/Library/Logs/`
- **Development mode**: Helper scripts for dev workflow

**Service management**:

```bash
# Status
launchctl list | grep temoa

# Stop/start
launchctl stop dev.$(whoami).temoa
launchctl start dev.$(whoami).temoa

# Uninstall
launchctl unload ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
rm ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

**Development workflow**:

```bash
# Run with auto-reload
./launchd/dev.sh

# View logs
./launchd/view-logs.sh
```

See [launchd/README.md](../launchd/README.md) for complete documentation.

### System Service (Linux)

For always-on Linux servers:

```bash
sudo tee /etc/systemd/system/temoa.service << 'EOF'
[Unit]
Description=Temoa Semantic Search Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/projects/temoa
Environment="PATH=/home/youruser/.local/bin:/usr/bin"
ExecStart=/home/youruser/.local/bin/temoa server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable temoa
sudo systemctl start temoa
```

**Control service**:
```bash
sudo systemctl status temoa
sudo systemctl restart temoa
sudo systemctl stop temoa
```

**View logs**:
```bash
sudo journalctl -u temoa -f
```

---

## Verify Deployment

### Health Check

```bash
curl http://localhost:8080/health | jq .
```

**Expected**:
```json
{
  "status": "healthy",
  "synthesis": "connected",
  "model": "all-mpnet-base-v2",
  "vault": "/Users/you/Obsidian/vault",
  "files_indexed": 2281
}
```

### Search Test

**Basic search**:
```bash
curl "http://localhost:8080/search?q=obsidian&limit=3" | jq '.results[] | {title, score: .similarity_score}'
```

**Expected**:
```json
[
  {
    "title": "Obsidian Plugin Development",
    "score": 0.782
  },
  ...
]
```

**Search with profile** (Phase 3.5.1):
```bash
# Repos profile (optimized for GitHub repos/tech docs)
curl "http://localhost:8080/search?q=obsidian&profile=repos&limit=3" | jq '.results[] | {title, score: .similarity_score}'

# Deep profile (optimized for long-form content)
curl "http://localhost:8080/search?q=narrative&profile=deep&limit=3" | jq '.results[] | {title, score: .similarity_score}'
```

**List available profiles**:
```bash
curl http://localhost:8080/profiles | jq .
```

**Expected**:
```json
{
  "default": "Balanced search (50/50 hybrid, all features)",
  "repos": "GitHub repos and tech docs (70% BM25, metadata boost)",
  "recent": "Recent work (7-day half-life, 90-day cutoff)",
  "deep": "Long-form content (80% semantic, 3 chunks/file)",
  "keywords": "Exact keyword matching (80% BM25, fast)"
}
```

### Statistics

```bash
curl http://localhost:8080/stats | jq .
```

**Expected**:
```json
{
  "file_count": 2281,
  "num_embeddings": 2281,
  "model_name": "all-mpnet-base-v2",
  "num_tags": 1543,
  "num_directories": 42
}
```

### Web UI

Open in browser:
```bash
open http://localhost:8080
```

Try searching for something. Results should appear in <1 second.

### Automated Smoke Test

Use the provided test script:

```bash
chmod +x scripts/test_api.sh
./scripts/test_api.sh http://localhost:8080
```

**Expected output**:
```
🏥 Health Check
✓ Status: healthy

📊 Stats
✓ Files indexed: 2281

🔍 Search Test
✓ Found 15 results

All tests passed! ✓
```

**If any fail**:
- Check `~/temoa.log` (background) or `journalctl -u temoa` (systemd)
- Verify config.json paths are correct
- Ensure port 8080 not in use: `lsof -i :8080`

---

## Tailscale Setup

### Get Server IP

On server machine:

```bash
tailscale ip -4
# Example: 100.85.23.42
```

Note this IP - you'll use it from mobile.

### Connect Mobile

1. Install Tailscale app (iOS App Store / Google Play)
2. Sign in with same account as server
3. Verify connection: Should see server machine in Tailscale app

### Test from Mobile

Open mobile browser: `http://100.85.23.42:8080` (use your IP)

**Expected**: Temoa search UI appears

**If not**:
- Verify Tailscale running on both devices
- Check server `host` is `0.0.0.0` (not `127.0.0.1`) in config
- Ping server from Tailscale app
- Verify server running: `curl http://localhost:8080/health`

---

## Mobile Access

### Search from Phone

1. Open `http://100.x.x.x:8080` in mobile browser
2. Type query (e.g., "obsidian")
3. Tap Search
4. Results appear in <2 seconds
5. Tap result link

**If obsidian:// URIs work**: Note opens in Obsidian app ✓

**If not**:
- Obsidian app installed?
- Try manually opening `obsidian://vault/` in Safari/Chrome
- Check "Open supported links" permission (Android)

### Add to Home Screen

**iOS Safari**:
1. Tap Share button
2. "Add to Home Screen"
3. Name: "Vault Search"
4. Tap "Add"

**Android Chrome**:
1. Tap ⋮ (three dots)
2. "Add to Home screen"
3. Name: "Vault Search"
4. Tap "Add"

Now you have a home screen icon for quick access!

---

## Daily Operations

### Update Index

After adding new notes or gleanings:

```bash
# Extract new gleanings (if needed)
temoa extract

# Update index incrementally (recommended - only changed files)
temoa reindex
```

Incremental reindex (default) only processes new, modified, or deleted files, taking ~5 seconds when no changes occur and ~6-8 seconds with 5-10 new files (30x faster than full rebuild).

Full rebuild (rarely needed):
```bash
temoa index
```

Use full rebuild for first time setup, when index corruption is suspected, or when switching models.

**Via API**:
```bash
# Incremental (recommended)
curl -X POST http://localhost:8080/reindex?force=false

# Full rebuild
curl -X POST http://localhost:8080/reindex?force=true
```

**Via Web UI**:
1. Navigate to Management page: `http://localhost:8080/manage`
2. Click "Reindex Vault" button
3. For full rebuild: Check "Full rebuild (process all files)" first
4. Default (unchecked) is incremental

**Performance comparison** (3,059 file vault):

| Operation | Time | Files Processed |
|-----------|------|-----------------|
| Full index (`temoa index`) | 159s | 3,059 files |
| Incremental (no changes) | 4.8s | 0 files |
| Incremental (5 new) | 6-8s | 5 files |

### Automated Gleaning Extraction

Add to crontab (daily at 11 PM):

```bash
crontab -e
# Add this line:
0 23 * * * cd ~/projects/temoa && temoa extract
```

### Check Server Status

**Background process**:
```bash
ps aux | grep "temoa server"
tail -f ~/temoa.log
```

**Systemd**:
```bash
sudo systemctl status temoa
sudo journalctl -u temoa -f
```

### Restart Server

**Background process**:
```bash
kill $(cat ~/temoa.pid)
nohup temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid
```

**Systemd**:
```bash
sudo systemctl restart temoa
```

---

## Troubleshooting

### Server Won't Start

**"No config file found"**
- Create `~/.config/temoa/config.json` (see Configuration section)

**"Vault path does not exist"**
- Fix `vault_path` in config.json
- Ensure path uses `~` or correct absolute path

**"Port 8080 already in use"**
- Change `server.port` in config.json
- Or kill process: `lsof -i :8080` then `kill <PID>`

**Model loading fails**
- Check internet connection (first download)
- Check disk space (~1GB needed for models)
- Check `~/temoa.log` for errors

### Mobile Can't Connect

**"Can't reach server"**
- Verify Tailscale running on both devices
- Check Tailscale IP: `tailscale ip -4`
- Ping from phone: Tailscale app → Machines → tap server → Ping
- Verify server running: `curl http://localhost:8080/health`

**Works locally, not from mobile**
- Check `server.host` is `0.0.0.0` in config (not `127.0.0.1`)
- Firewall blocking port 8080? (Tailscale usually bypasses)

### Search Returns No Results

**"files_indexed": 0 in /health**
- Run `temoa index` to build index
- Check `~/temoa.log` for indexing errors

**Index exists but searches return nothing**
- Model mismatch? Check `/stats` → model_name
- Try rebuilding: `temoa reindex --force`
- Check vault has markdown files: `find ~/Obsidian/vault -name "*.md" | wc -l`

### obsidian:// Links Don't Work

**iOS**:
- Obsidian app installed?
- Try `obsidian://vault/` manually in Safari
- If fails, URL scheme not registered (reinstall Obsidian?)

**Android**:
- Check "Open supported links" permission for Obsidian
- Try `obsidian://vault/` in Chrome

**Workaround**: Copy path from result and open manually in Obsidian

### Search Is Slow (>3s)

**Check network latency**:
```bash
# From mobile, in Tailscale app
Machines → tap server → Ping
# Should be <50ms
```

**Check server performance**:
- Model loaded? Check startup logs: "✓ Model loaded"
- Index loaded? `/stats` should show file count immediately
- Server under load? Check CPU: `top` or `htop`

**Try from different network**:
- WiFi vs cellular may have different latency
- Cellular may route through different Tailscale relay

---

## Performance Notes

### Expected Timings

| Operation | Time |
|:----------|:-----|
| Server startup | 15-20s (loads bi-encoder + cross-encoder models) |
| Search from mobile (semantic) | ~400ms |
| Search from mobile (hybrid BM25 + semantic) | ~450ms |
| Search with re-ranking | ~600ms |
| Short query with expansion + re-ranking | ~800-1000ms |
| Full index rebuild (~3000 files) | 2-3 minutes |
| Incremental reindex (no changes) | ~5 seconds |
| Incremental reindex (5-10 new files) | ~6-8 seconds |

### Reindexing Comparison (3,059 file vault)

| Operation | Time | Speedup |
|:----------|:-----|:--------|
| Full | 159s (all files) | baseline |
| Incremental (no changes) | 4.8s | 30x faster |
| Incremental (5 new files) | 6-8s | 25x faster |

### Resource Usage

| Resource | Usage |
|:---------|:------|
| Memory (single vault) | ~800 MB (bi-encoder + cross-encoder) |
| Memory (multi-vault, 3 cached) | ~1.5 GB |
| Disk (~2000 files) | ~10 MB (embeddings index) |
| CPU | Spike during search/indexing, idle otherwise |

---

## Security Notes

**Current setup (Phase 4 - Security Hardening Complete)**:
- No authentication (anyone on Tailscale network can access)
- No HTTPS (encrypted by Tailscale/WireGuard)
- Single-user assumption
- ✅ **CORS protection** (restrictive by default)
- ✅ **Rate limiting** (DoS protection for expensive endpoints)
- ✅ **Path traversal validation** (prevents access outside vault)

**This is fine for**: Personal use, trusted Tailscale network

**This is NOT suitable for**: Public internet, multi-user environments

### CORS Configuration

**Default behavior** (Phase 4):
- Restricts origins to `localhost` and `127.0.0.1` with configured port
- Automatically includes Tailscale IP if `TAILSCALE_IP` environment variable is set
- Logs warning if wildcard (`*`) is used

**To configure CORS origins**:

Option 1: Environment variable (recommended for Tailscale):
```bash
export TAILSCALE_IP="100.x.x.x"
export TEMOA_CORS_ORIGINS="http://localhost:8080,http://100.x.x.x:8080"
```

Option 2: Configuration file (`~/.config/temoa/config.json`):
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "cors_origins": [
      "http://localhost:8080",
      "http://127.0.0.1:8080",
      "http://100.x.x.x:8080"
    ]
  }
}
```

### Rate Limiting

**Default limits** (Phase 4):
- `/search`: 1,000 requests per hour per IP
- `/archaeology`: 20 requests per hour per IP
- `/reindex`: 5 requests per hour per IP
- `/extract`: 10 requests per hour per IP

Returns HTTP 429 (Too Many Requests) when limits are exceeded.

**To configure rate limits** (`~/.config/temoa/config.json`):
```json
{
  "rate_limits": {
    "search_per_hour": 1000,
    "archaeology_per_hour": 20,
    "reindex_per_hour": 5,
    "extract_per_hour": 10
  }
}
```

### Path Traversal Protection

**Automatic validation** (Phase 4):
- All file operations validate paths are within the vault
- Logs warnings for detected traversal attempts
- Silently skips results outside vault boundaries

**Future enhancements** (if needed):
- API keys/authentication
- HTTPS (if exposing beyond Tailscale)
- User management (multi-user support)

---

## PWA Installation

Temoa can be installed as a Progressive Web App on mobile devices.

**iOS (Safari)**:
1. Open Temoa in Safari: `http://100.x.x.x:8080`
2. Tap the Share button
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add"

**Android (Chrome)**:
1. Open Temoa in Chrome: `http://100.x.x.x:8080`
2. Tap the three-dot menu
3. Tap "Add to Home screen" or "Install app"
4. Tap "Add" or "Install"

Installing as a PWA provides one-tap access from your home screen, launches without browser UI, provides offline UI (search requires network), and maintains persistent state and settings.

---

## References

- **[README.md](../README.md)**: Quick start guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture (updated for Phase 3.5)
- **[SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md)**: Search algorithms and profiles
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)**: Implementation plan and progress
- **[CONTEXT.md](CONTEXT.md)**: Current project status

---

**Created**: 2025-11-19
**Last Updated**: 2026-01-09 (Phase 4 - Security Hardening)
**Version**: 0.6.0
