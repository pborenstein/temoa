#!/usr/bin/env python3
"""
Debug script to investigate why stats doesn't find embeddings that clearly exist.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from temoa.config import Config
from temoa.synthesis import SynthesisClient

print("=" * 60)
print("TEMOA STATS DEBUG")
print("=" * 60)

# Load config
config = Config()
print(f"\n📝 Config loaded from: {config.config_path}")
print(f"   Vault: {config.vault_path}")
print(f"   Storage: {config.storage_dir}")
print(f"   Synthesis: {config.synthesis_path}")

# Check if storage directory exists
print(f"\n📁 Storage directory check:")
print(f"   Path: {config.storage_dir}")
print(f"   Exists: {config.storage_dir.exists()}")

if config.storage_dir.exists():
    import os
    files = os.listdir(config.storage_dir)
    print(f"   Files found: {files}")

    # Check file sizes
    for f in files:
        file_path = config.storage_dir / f
        size = file_path.stat().st_size
        print(f"     - {f}: {size:,} bytes")

# Initialize client
print(f"\n🔧 Initializing SynthesisClient...")
try:
    client = SynthesisClient(
        synthesis_path=config.synthesis_path,
        vault_path=config.vault_path,
        model=config.default_model,
        storage_dir=config.storage_dir
    )
    print(f"   ✓ Client initialized successfully")
    print(f"   Client storage_dir: {client.storage_dir}")
    print(f"   Client vault_path: {client.vault_path}")
except Exception as e:
    print(f"   ✗ Failed to initialize client: {e}")
    sys.exit(1)

# Get stats
print(f"\n📊 Calling get_stats()...")
try:
    stats = client.get_stats()
    print(f"   ✓ Stats retrieved")
    print(f"\n   Raw stats dict:")
    import json
    print(json.dumps(stats, indent=4))
except Exception as e:
    print(f"   ✗ Failed to get stats: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test search to verify embeddings work
print(f"\n🔍 Testing search (to verify embeddings work)...")
try:
    results = client.search("test", limit=1)
    if results.get('results'):
        print(f"   ✓ Search works! Found {len(results['results'])} result(s)")
        print(f"   First result: {results['results'][0].get('title', 'Unknown')}")
    else:
        print(f"   ⚠ Search returned no results")
except Exception as e:
    print(f"   ✗ Search failed: {e}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
