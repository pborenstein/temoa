#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 temoa launchd Service Installer${NC}"
echo

# Detect environment
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USERNAME="$(whoami)"
HOME_DIR="$HOME"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
VENV_BIN="$PROJECT_DIR/.venv/bin"

echo -e "${BLUE}Detected environment:${NC}"
echo "  Username:    $USERNAME"
echo "  Project dir: $PROJECT_DIR"
echo "  Python:      $VENV_PYTHON"
echo

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PYTHON${NC}"
    echo "Please run 'uv sync' or create a virtual environment first."
    exit 1
fi

# Check if project module is importable
if ! "$VENV_PYTHON" -c "import temoa" 2>/dev/null; then
    echo -e "${RED}Error: temoa module not found in virtual environment${NC}"
    echo "Please run 'uv sync' to install dependencies."
    exit 1
fi

# Generate service plist
echo -e "${BLUE}Generating temoa service...${NC}"
SERVICE_PLIST="$HOME_DIR/Library/LaunchAgents/dev.pborenstein.temoa.plist"

# Ensure LaunchAgents directory exists
mkdir -p "$HOME_DIR/Library/LaunchAgents"

cat "$PROJECT_DIR/launchd/temoa.plist.template" | \
    sed "s|{{USERNAME}}|$USERNAME|g" | \
    sed "s|{{VENV_PYTHON}}|$VENV_PYTHON|g" | \
    sed "s|{{PROJECT_DIR}}|$PROJECT_DIR|g" | \
    sed "s|{{HOME}}|$HOME_DIR|g" | \
    sed "s|{{VENV_BIN}}|$VENV_BIN|g" \
    > "$SERVICE_PLIST"

echo -e "${GREEN}✓${NC} Created $SERVICE_PLIST"

# Unload existing service if running
echo
echo -e "${BLUE}Unloading any existing service...${NC}"
launchctl unload "$SERVICE_PLIST" 2>/dev/null || true

# Load service
echo -e "${BLUE}Loading service...${NC}"
launchctl load "$SERVICE_PLIST"
echo -e "${GREEN}✓${NC} Loaded temoa service"

# Give it a moment to start
sleep 2

# Show status
echo
echo -e "${GREEN}✓ Installation complete!${NC}"
echo
echo -e "${BLUE}Service status:${NC}"
launchctl list | grep "dev.pborenstein.temoa" || echo "  No service found"

echo
echo -e "${BLUE}Access temoa at:${NC}"
echo "  Local:       http://localhost:8080"

# Try to get LAN IP
LAN_IP=$(ifconfig | grep "inet " | grep -v 127.0.1 | head -1 | awk '{print $2}')
if [ -n "$LAN_IP" ]; then
    echo "  LAN:         http://$LAN_IP:8080"
fi

echo
echo -e "${BLUE}View logs:${NC}"
echo "  $PROJECT_DIR/view-logs.sh"
echo
echo -e "${BLUE}Manage service:${NC}"
echo "  Stop:    launchctl unload ~/Library/LaunchAgents/dev.pborenstein.temoa.plist"
echo "  Start:   launchctl load ~/Library/LaunchAgents/dev.pborenstein.temoa.plist"
echo "  Restart: launchctl unload ~/Library/LaunchAgents/dev.pborenstein.temoa.plist && launchctl load ~/Library/LaunchAgents/dev.pborenstein.temoa.plist"
echo
