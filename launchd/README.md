# Temoa launchd Service

Production macOS service management for Temoa using launchd.

## Quick Start

```bash
# Install and start service
./launchd/install.sh

# Access Temoa
open http://localhost:4001
```

## Installation

The `install.sh` script automates service setup:

1. Detects project location and virtual environment
2. Generates service file from template
3. Installs to `~/Library/LaunchAgents/dev.{username}.temoa.plist`
4. Loads and starts the service

**Requirements**:

- uv installed and synced (`uv sync`)
- Temoa dependencies installed
- macOS with launchd (10.10+)

**Port**: Service runs on port 4001 by default (pairs with apantli on 4000)

## Manual Management

### Status

```bash
launchctl list | grep temoa
```

### Stop Service

```bash
launchctl stop dev.$(whoami).temoa
```

### Start Service

```bash
launchctl start dev.$(whoami).temoa
```

### Restart Service

```bash
launchctl unload ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
launchctl load ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

### Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
rm ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

## Development Mode

Use `dev.sh` to run Temoa with auto-reload during development:

```bash
./dev.sh
```

This script:

1. Stops the launchd service
2. Runs `temoa server --reload` with debug logging
3. Prompts to restart launchd service on exit

## Viewing Logs

### Using Helper Script

```bash
./view-logs.sh          # Both stdout and stderr
./view-logs.sh stderr   # Errors only
./view-logs.sh stdout   # Output only
```

### Manual Log Access

```bash
# Standard output
tail -f ~/Library/Logs/temoa.log

# Error output
tail -f ~/Library/Logs/temoa.error.log

# Both
tail -f ~/Library/Logs/temoa.log ~/Library/Logs/temoa.error.log
```

## Configuration

The service uses CLI arguments for core settings:

- `--host 0.0.0.0` - Accessible on LAN/Tailscale
- `--port 4001` - Default port (pairs with apantli on 4000)
- `--log-level info` - Production logging

Application configuration (vaults, models, search parameters) is read from:

1. `~/.config/temoa/config.json` (default)
2. `~/.temoa.json` (fallback)
3. `./config.json` (local override)

To use a custom config location, modify the plist template:

```xml
<string>--config</string>
<string>/path/to/config.json</string>
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
tail -f ~/Library/Logs/temoa.error.log

# Verify venv is activated
.venv/bin/python -c "import temoa"

# Check service file
cat ~/Library/LaunchAgents/dev.$(whoami).temoa.plist

# Validate plist syntax
plutil -lint ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

### Port Already in Use

```bash
# Find process using port 4001
lsof -i :4001

# Kill process (if safe)
kill -9 <PID>
```

### Permission Errors

```bash
# Ensure LaunchAgents directory exists
mkdir -p ~/Library/LaunchAgents

# Check file permissions
ls -la ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

### Service Keeps Restarting

The service is configured with `KeepAlive: true`, so it will auto-restart on crashes. Check error logs to diagnose the issue.

### Changes Not Taking Effect

If you modify the plist file and changes don't appear:

```bash
# Reload the service
launchctl unload ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
launchctl load ~/Library/LaunchAgents/dev.$(whoami).temoa.plist
```

## Service Details

**Label**: `dev.{username}.temoa`
**Type**: LaunchAgent (runs as user, not root)
**Auto-start**: Yes (RunAtLoad: true)
**Auto-restart**: Yes (KeepAlive: true)
**Working Directory**: Project root
**Logs**: `~/Library/Logs/temoa.log` and `temoa.error.log`

## Network Access

The service binds to `0.0.0.0:4001`, making it accessible:

- **Localhost**: http://localhost:4001
- **LAN**: http://{hostname}.local:4001
- **Tailscale**: http://{tailscale-hostname}:4001

For production deployments, consider:

- Tailscale for secure remote access
- HTTPS via reverse proxy (nginx, Caddy)
- Firewall rules to restrict access

## See Also

- [Temoa Deployment Docs](../docs/DEPLOYMENT.md)
- [Apantli launchd Setup](../../apantli/launchd/)
