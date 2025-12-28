#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️  temoa launchd Service Uninstaller${NC}"
echo

# Detect environment
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME_DIR="$HOME"
SERVICE_PLIST="$HOME_DIR/Library/LaunchAgents/dev.pborenstein.temoa.plist"

# Check if service exists
if [ ! -f "$SERVICE_PLIST" ]; then
    echo -e "${YELLOW}No temoa service found at:${NC}"
    echo "  $SERVICE_PLIST"
    echo
    echo "Nothing to uninstall."
    exit 0
fi

# Show what will be removed
echo -e "${BLUE}The following will be removed:${NC}"
echo "  Service file: $SERVICE_PLIST"
echo

# Ask for confirmation
echo -e "${YELLOW}Are you sure you want to uninstall temoa service? (y/n)${NC}"
read -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Uninstall cancelled.${NC}"
    exit 0
fi

# Check if service is running
echo -e "${BLUE}Checking service status...${NC}"
if launchctl list | grep -q "dev.pborenstein.temoa"; then
    echo -e "${YELLOW}Service is running. Stopping...${NC}"
    launchctl unload "$SERVICE_PLIST" 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Service stopped"
else
    echo -e "${BLUE}Service is not running${NC}"
fi

# Remove plist file
echo
echo -e "${BLUE}Removing service file...${NC}"
rm "$SERVICE_PLIST"
echo -e "${GREEN}✓${NC} Removed $SERVICE_PLIST"

# Completion message
echo
echo -e "${GREEN}✓ Uninstall complete!${NC}"
echo
echo -e "${BLUE}temoa service has been removed.${NC}"
echo
echo "To reinstall, run: ./launchd/install.sh"
echo
