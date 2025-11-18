#!/bin/bash
# Setup script for Synthesis with Python 3.11

set -e  # Exit on error

echo "🔧 Setting up Synthesis with Python 3.11..."
echo

# Navigate to synthesis directory (relative to script location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/old-ideas/synthesis"

# Remove old venv if it exists
if [ -d ".venv" ]; then
    echo "📦 Removing old virtual environment..."
    rm -rf .venv
fi

# Create new venv with Python 3.11
echo "🐍 Creating virtual environment with Python 3.11..."
uv venv --python 3.11

# Install dependencies
echo "📥 Installing dependencies (this may take a few minutes)..."
uv sync

echo
echo "✅ Setup complete!"
echo
echo "To use Synthesis:"
echo "  cd old-ideas/synthesis"
echo "  uv run main.py --help"
echo
echo "To run Phase 0 tests:"
echo "  uv run main.py process          # Index test-vault"
echo "  uv run main.py search 'query'   # Search"
echo "  uv run main.py stats            # Vault stats"
