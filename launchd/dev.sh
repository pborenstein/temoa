#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
USERNAME=$(whoami)
SERVICE_LABEL="dev.$USERNAME.temoa"
PLIST_FILE="$HOME/Library/LaunchAgents/$SERVICE_LABEL.plist"

echo -e "${GREEN}Temoa Development Mode${NC}"
echo "======================"
echo ""

# Check if launchd service is running
if launchctl list | grep -q "$SERVICE_LABEL"; then
    echo -e "${YELLOW}Stopping launchd service...${NC}"
    launchctl unload "$PLIST_FILE"

    # Wait for port to be free (max 5 seconds)
    for i in {1..10}; do
        if ! lsof -i :4001 >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done

    echo "Service stopped"
else
    echo "Launchd service not running"
fi

# Final check: if port is still in use, show error
if lsof -i :4001 >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 4001 still in use${NC}"
    echo "Process using port 4001:"
    lsof -i :4001
    echo ""
    read -p "Kill the process and continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti :4001)
        kill -9 $PID
        sleep 1
    else
        echo "Exiting..."
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Starting development server with --reload${NC}"
echo "Press Ctrl+C to stop"
echo ""

# Trap Ctrl+C
function cleanup {
    echo ""
    echo ""
    read -p "Restart launchd service? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Restarting launchd service...${NC}"
        launchctl load "$PLIST_FILE"
        echo "Service restarted"
    else
        echo "Launchd service remains stopped"
        echo "To restart manually: launchctl load $PLIST_FILE"
    fi
}
trap cleanup EXIT

# Run server with reload
cd "$PROJECT_DIR"
caffeinate -i uv run temoa server --host 0.0.0.0 --port 4001 --reload --log-level debug
