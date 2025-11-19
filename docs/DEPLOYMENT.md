# Temoa Deployment Guide

> **Quick Start**: Get Temoa running and accessible from your phone in ~10 minutes

**Last Updated**: 2025-11-19
**For**: Phase 2.5 Mobile Validation

---

## Prerequisites

**On server machine** (desktop/laptop that will run Temoa):
- Python 3.11+
- uv package manager
- Git (to clone/pull Temoa)
- Your Obsidian vault accessible
- Tailscale installed and running

**On mobile device**:
- iOS or Android
- Tailscale app installed
- Obsidian app installed
- Connected to same Tailscale network

---

## Step 1: Server Setup (5 minutes)

### Clone/Update Temoa

```bash
# If first time
cd ~/projects
git clone https://github.com/your-username/temoa.git
cd temoa

# If updating
cd ~/projects/temoa
git pull origin main
```

### Install Dependencies

```bash
uv sync
```

This will:
- Create virtual environment in `.venv/`
- Install FastAPI, uvicorn, sentence-transformers, etc.
- Take ~30 seconds (or longer if downloading large dependencies)

### Create Configuration

```bash
# Create config.json in project root
cat > config.json << 'EOF'
{
  "vault_path": "~/Obsidian/amoxtli",
  "synthesis_path": "old-ideas/synthesis",
  "index_path": null,
  "default_model": "all-MiniLM-L6-v2",
  "server": {
    "host": "0.0.0.0",
    "port": 8080
  },
  "search": {
    "default_limit": 10,
    "max_limit": 50,
    "timeout": 10
  }
}
EOF
```

**Adjust**:
- `vault_path`: Path to your Obsidian vault
- `index_path`: Leave as `null` to use `.temoa/` inside vault
- `server.port`: Change if 8080 is already in use

**Path tips**:
- Use `~` for home directory (will be expanded)
- Use relative paths if possible
- Absolute paths work but less portable

---

## Step 2: Build Index (First Time, ~15-20 seconds)

```bash
uv run temoa index
```

**What this does**:
- Scans your vault for markdown files
- Downloads sentence-transformer model (if not cached)
- Generates embeddings for all files
- Stores in `<vault>/.temoa/` (or configured `index_path`)

**Expected output**:
```
Building index for: /Users/you/Obsidian/amoxtli
This may take a few minutes for large vaults...

Indexing [████████████████████] 100%

✓ Index built successfully
Files indexed: 2,281
Model: all-MiniLM-L6-v2
```

**Troubleshooting**:
- **"No config file found"**: Create `config.json` (see Step 1)
- **"Vault path does not exist"**: Fix `vault_path` in config
- **Takes >2 minutes**: Normal for large vaults (>1000 files)
- **Model download fails**: Check internet connection

---

## Step 3: Start Server (2 minutes)

### Option A: Foreground (for testing)

```bash
uv run temoa server
```

Press `Ctrl-C` to stop.

### Option B: Background (for daily use)

```bash
nohup uv run temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid
```

**To stop**:
```bash
kill $(cat ~/temoa.pid)
```

**To view logs**:
```bash
tail -f ~/temoa.log
```

### Option C: Systemd Service (Linux, persistent)

Create `/etc/systemd/system/temoa.service`:
```ini
[Unit]
Description=Temoa Semantic Search Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/projects/temoa
Environment="PATH=/home/youruser/.local/bin:/usr/bin"
ExecStart=/home/youruser/projects/temoa/.venv/bin/uvicorn temoa.server:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable temoa
sudo systemctl start temoa
sudo systemctl status temoa
```

**Logs**:
```bash
sudo journalctl -u temoa -f
```

---

## Step 4: Verify Server (1 minute)

```bash
# Test health endpoint
curl http://localhost:8080/health | jq .

# Expected:
# {
#   "status": "healthy",
#   "synthesis": "connected",
#   "model": "all-MiniLM-L6-v2",
#   "vault": "/Users/you/Obsidian/amoxtli",
#   "files_indexed": 2281
# }
```

```bash
# Test search
curl "http://localhost:8080/search?q=obsidian&limit=3" | jq '.results[] | {title, score: .similarity_score}'

# Expected:
# [
#   {
#     "title": "Obsidian Plugin Development",
#     "score": 0.782
#   },
#   ...
# ]
```

**If this works**: Server is ready for mobile! ✅

**If not**:
- Check `~/temoa.log` or `journalctl -u temoa`
- Verify config.json paths are correct
- Ensure port 8080 is not in use: `lsof -i :8080`

---

## Step 5: Tailscale Setup (2 minutes)

### On Server Machine

```bash
# Get your Tailscale IP
tailscale ip -4
# Example output: 100.85.23.42
```

**Note this IP** - you'll use it from mobile.

### On Mobile Device

1. Install Tailscale app (iOS App Store / Google Play)
2. Sign in with same account as server
3. Verify connection: Should see server machine in Tailscale app

---

## Step 6: Mobile Testing (3 minutes)

### Test in Mobile Browser

**Open**: `http://100.85.23.42:8080` (use your Tailscale IP)

**Expected**: Temoa search UI appears

**Try searching**:
1. Type a query (e.g., "obsidian")
2. Tap Search
3. Results should appear in <2 seconds
4. Tap a result link

**If obsidian:// URIs work**: Obsidian app should open to that note ✅

**If not**:
- Obsidian app not installed? Install it
- Link just opens in browser? obsidian:// handler not registered
- Nothing happens? Check browser console for errors

### Bookmark for Easy Access

**iOS Safari**:
1. Tap Share button
2. Tap "Add to Home Screen"
3. Name it "Vault Search" or "Temoa"
4. Tap "Add"

**Android Chrome**:
1. Tap ⋮ (three dots)
2. Tap "Add to Home screen"
3. Name it "Vault Search"
4. Tap "Add"

Now you have an icon on your home screen! 📱

---

## Step 7: Quick Smoke Test

Use the provided test script:

```bash
cd ~/projects/temoa
chmod +x scripts/test_api.sh
./scripts/test_api.sh http://100.85.23.42:8080
```

**Expected output**:
```
🏥 Health Check
{
  "status": "healthy",
  ...
}

📊 Stats
{
  "file_count": 2281,
  ...
}

🔍 Search Test
[
  {
    "title": "...",
    "score": 0.xx
  },
  ...
]

📖 API Docs: http://100.85.23.42:8080/docs
```

If all three pass ✅ you're ready to use Temoa!

---

## Usage Tips

### Daily Workflow

1. **Server runs in background** (systemd or nohup)
2. **Open bookmark on phone** when you want to search
3. **Type query, get results** in <2 seconds
4. **Tap result** → Opens in Obsidian app

### Updating Gleanings

After adding new notes or gleanings:

```bash
# Extract new gleanings from daily notes
uv run temoa extract

# Re-index vault (picks up new gleanings)
uv run temoa reindex --force
```

Or trigger via API:
```bash
curl -X POST http://localhost:8080/reindex?force=true
```

### Checking Server Status

```bash
# If using systemd
sudo systemctl status temoa

# If using nohup
ps aux | grep "temoa server"
tail -f ~/temoa.log
```

### Restarting Server

```bash
# Systemd
sudo systemctl restart temoa

# nohup
kill $(cat ~/temoa.pid)
nohup uv run temoa server > ~/temoa.log 2>&1 &
echo $! > ~/temoa.pid
```

---

## Troubleshooting

### Server Won't Start

**Error: "No config file found"**
- Create `config.json` in project root (see Step 1)
- Or: Create `.temoa/config.json` in your vault

**Error: "Vault path does not exist"**
- Fix `vault_path` in config.json
- Make sure path uses `~` or correct absolute path

**Error: "Port 8080 already in use"**
- Change `server.port` in config.json
- Or: Find and kill process using port: `lsof -i :8080`

### Mobile Can't Connect

**"Can't reach server"**
- Verify Tailscale running on both devices
- Check Tailscale IP: `tailscale ip -4`
- Ping server from phone: Tailscale app → Machines → Ping
- Verify server is running: `curl http://localhost:8080/health`

**Works on server, not from mobile**
- Check `server.host` in config.json is `0.0.0.0` (not `127.0.0.1`)
- Firewall blocking port 8080? (Tailscale usually bypasses this)

### Search Returns No Results

**"files_indexed": 0**
- Run `uv run temoa index` to build index
- Check `~/temoa.log` for errors during indexing

**Index exists but no results**
- Model might be different: Check `/stats` endpoint
- Try reindexing: `uv run temoa reindex --force`
- Check vault has markdown files: `find ~/Obsidian/amoxtli -name "*.md" | wc -l`

### obsidian:// Links Don't Work

**iOS**:
- Obsidian app installed?
- Try opening `obsidian://vault/` manually in Safari
- If that doesn't work, Obsidian URL scheme may not be registered

**Android**:
- Same as iOS troubleshooting
- Check "Open supported links" permission for Obsidian app

**Workaround**:
- If obsidian:// doesn't work, you can still copy the path and open manually
- Future enhancement: Fallback to file:// or custom scheme

### Search Is Slow (>3s)

**Check network latency**:
- From mobile: `ping <tailscale-ip>`
- Should be <50ms typically

**Check server performance**:
- Model loaded? Check startup logs for "✓ Model loaded"
- Index loaded? Check `/stats` → should show file count immediately

**If consistently slow**:
- Might need caching (Phase 3 enhancement)
- Or: Network issue (try from WiFi vs. cellular)

---

## Security Notes

### Current Setup (Phase 2.5)

- **No authentication**: Anyone on your Tailscale network can access
- **No HTTPS**: Traffic encrypted by Tailscale (Wireguard)
- **Single-user assumption**: Trusted network

**This is fine for**: Personal use, Tailscale network

**This is NOT suitable for**: Public internet, multiple users

### Future Enhancements (If Needed)

- API keys (Phase 3+)
- Rate limiting (Phase 3+)
- HTTPS certificates (if exposing beyond Tailscale)
- Multi-user support (Phase 4+)

---

## Performance Notes

**Expected Timings**:
- Server startup: 13-15s (one-time, loads model)
- Search from mobile: <2s (usually ~500ms)
- Index rebuild: 15-20s for ~2000 files

**If slower**:
- Check network latency (Tailscale ping)
- Check server CPU usage during search
- Vault size might affect performance (test with smaller vault first)

---

## Next Steps

After deployment, start **Phase 2.5: Mobile Validation**:

1. ✅ Server deployed and accessible
2. ✅ Mobile bookmark created
3. ✅ Test search works
4. ⏭️ **Use daily for 1-2 weeks**
5. ⏭️ Track usage in daily notes
6. ⏭️ Document friction points
7. ⏭️ Return and review findings

See [IMPLEMENTATION.md - Phase 2.5](IMPLEMENTATION.md#phase-25-mobile-validation-) for usage tracking template.

---

## References

- **IMPLEMENTATION.md**: Phase 2.5 details and success criteria
- **MIDCOURSE-2025-11-19.md**: Rationale for this phase
- **CHRONICLES.md Entry 10**: Mid-course assessment
- **CLAUDE.md**: Development guidelines

---

**Created**: 2025-11-19
**Purpose**: Phase 2.5 deployment guide
**Audience**: User (pborenstein) deploying to production environment
