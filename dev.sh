#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVICE_PLIST="$HOME/Library/LaunchAgents/dev.pborenstein.temoa.plist"

echo -e "${BLUE}🔧 temoa Development Mode${NC}"
echo

# Check if launchd service exists
if [ ! -f "$SERVICE_PLIST" ]; then
    echo -e "${YELLOW}No launchd service found. Running directly...${NC}"
    echo
else
    # Check if service is running
    if launchctl list | grep -q "dev.pborenstein.temoa"; then
        echo -e "${YELLOW}Stopping launchd service...${NC}"
        launchctl unload "$SERVICE_PLIST" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} Service stopped"
        echo
        STOPPED_SERVICE=true
    else
        STOPPED_SERVICE=false
    fi
fi

# Check for any running temoa server process
if pgrep -f "temoa server" > /dev/null; then
    echo -e "${YELLOW}Found running temoa server process. Stopping it...${NC}"
    pkill -f "temoa server"
    sleep 1
    echo -e "${GREEN}✓${NC} Process stopped"
    echo
fi

# Function to restore service on exit
cleanup() {
    echo
    echo
    if [ "$STOPPED_SERVICE" = true ]; then
        echo -e "${YELLOW}Restore launchd service? (y/n)${NC}"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Restarting launchd service...${NC}"
            launchctl load "$SERVICE_PLIST"
            echo -e "${GREEN}✓${NC} Service restored"
        else
            echo -e "${YELLOW}Service not restored. To start it manually:${NC}"
            echo "  launchctl load $SERVICE_PLIST"
        fi
    fi
}

trap cleanup EXIT

# Run temoa in development mode with auto-reload
echo -e "${GREEN}Starting temoa in development mode with auto-reload...${NC}"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo

caffeinate -dimsu -- uv run temoa server --reload
