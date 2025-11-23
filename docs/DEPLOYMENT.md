# Temoa Deployment Guide

> Get Temoa running and accessible from your phone in ~10 minutes

**Last Updated**: 2025-11-22
**For**: Phase 2.5 Mobile Validation

---

## Prerequisites

**On server machine** (Mac/Linux desktop/laptop):
- Python 3.11+
- uv package manager
- Git
- Your Obsidian vault accessible
- Tailscale installed and running

**On mobile device**:
- iOS or Android
- Tailscale app installed
- Obsidian app installed
- Connected to same Tailscale network

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

**Adjust**:
- `vault_path`: Path to your Obsidian vault
- `storage_dir`: Leave `null` to use `vault/.temoa/`
- `server.port`: Change if 8080 already in use

**Path tips**: Use `~` for home directory (auto-expanded)

---

## Build Index

First time only (~15-20 seconds for ~2000 files):

```bash
temoa index
```

**What happens**:
- Scans vault for markdown files
- Downloads sentence-transformer model (first time, cached after)
- Generates embeddings for all files
- Stores in `vault/.temoa/embeddings.pkl`

**Expected output**:
```
Building index for: /Users/you/Obsidian/vault
Indexing vault...
✓ Index built successfully
Files indexed: 2,281
Model: all-mpnet-base-v2
```

**Troubleshooting**:
- "No config file found" → Create config (see above)
- "Vault path does not exist" → Fix `vault_path` in config
- Takes >2 minutes → Normal for large vaults (>1000 files)

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

Now you have a home screen icon! 📱

---

## Daily Operations

### Update Index

After adding new notes or gleanings:

```bash
# Extract new gleanings
temoa extract

# Update index (incremental)
temoa reindex
```

Or force full rebuild:
```bash
temoa reindex --force
```

Or via API:
```bash
curl -X POST http://localhost:8080/reindex?force=false
```

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

**Expected timings**:
- Server startup: 13-15s (loads model)
- Search from mobile: <2s (usually ~400-500ms)
- Index rebuild: 15-20s for ~2000 files

**Resource usage**:
- Memory: ~600 MB (model in RAM)
- Disk: ~10 MB per 2000 files (embeddings index)
- CPU: Spike during search, idle otherwise

---

## Security Notes

**Current setup (Phase 2.5)**:
- No authentication (anyone on Tailscale network can access)
- No HTTPS (encrypted by Tailscale/WireGuard)
- Single-user assumption

**This is fine for**: Personal use, trusted Tailscale network

**This is NOT suitable for**: Public internet, multi-user environments

**Future enhancements** (if needed):
- API keys (Phase 3+)
- Rate limiting (Phase 3+)
- HTTPS (if exposing beyond Tailscale)

---

## Next Steps

After deployment, start **Phase 2.5: Mobile Validation**:

1. ✅ Server deployed and accessible
2. ✅ Mobile bookmark created
3. ✅ Test search works
4. ⏭️ **Use daily for 1-2 weeks**
5. ⏭️ Track usage patterns
6. ⏭️ Document friction points
7. ⏭️ Review findings

See [IMPLEMENTATION.md - Phase 2.5](IMPLEMENTATION.md#phase-25-mobile-validation-) for validation criteria.

---

## References

- **[README.md](../README.md)**: Quick start guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture
- **[IMPLEMENTATION.md](IMPLEMENTATION.md)**: Phase 2.5 details
- **[CHRONICLES.md](CHRONICLES.md)**: Design decisions

---

**Created**: 2025-11-19
**Last Updated**: 2025-11-22
**Purpose**: Production deployment guide
