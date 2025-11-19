#!/bin/bash
#
# extract_and_reindex.sh - Extract gleanings and trigger re-indexing
#
# This script automates the daily workflow:
# 1. Extract new gleanings from daily notes
# 2. Trigger vault re-indexing via Temoa API
#
# Usage:
#   ./scripts/extract_and_reindex.sh [--dry-run]
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration (adjust these for your setup)
VAULT_PATH="${VAULT_PATH:-$PROJECT_ROOT/test-vault}"
TEMOA_URL="${TEMOA_URL:-http://localhost:8080}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/extraction.log}"

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Starting gleaning extraction and reindex"
log "Vault: $VAULT_PATH"
log "Temoa URL: $TEMOA_URL"
log "=========================================="

# Step 1: Extract gleanings
log "Step 1: Extracting gleanings from daily notes..."
cd "$PROJECT_ROOT"

if [ "$1" = "--dry-run" ]; then
    log "DRY RUN MODE - no changes will be made"
    python scripts/extract_gleanings.py --vault-path "$VAULT_PATH" --dry-run | tee -a "$LOG_FILE"
    exit 0
fi

python scripts/extract_gleanings.py --vault-path "$VAULT_PATH" | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✓ Gleaning extraction complete"
else
    log "✗ Gleaning extraction failed!"
    exit 1
fi

# Step 2: Trigger re-indexing via API
log ""
log "Step 2: Triggering vault re-indexing..."

response=$(curl -s -X POST "$TEMOA_URL/reindex?force=true" -w "\nHTTP_STATUS:%{http_code}" 2>&1)

# Extract status code
http_status=$(echo "$response" | grep "HTTP_STATUS:" | cut -d: -f2)
body=$(echo "$response" | grep -v "HTTP_STATUS:")

log "Response status: $http_status"

if [ "$http_status" = "200" ]; then
    log "✓ Re-indexing triggered successfully"
    echo "$body" | python -m json.tool 2>/dev/null | tee -a "$LOG_FILE" || echo "$body" | tee -a "$LOG_FILE"
else
    log "✗ Re-indexing failed!"
    echo "$body" | tee -a "$LOG_FILE"
    exit 1
fi

log ""
log "=========================================="
log "Extraction and re-indexing complete!"
log "=========================================="
