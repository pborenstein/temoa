#!/usr/bin/env python3
"""
Helper script to configure Synthesis to use a specific vault.

Usage:
    python prototypes/setup_vault.py ~/Obsidian/toy-vault
"""

import json
import sys
from pathlib import Path

SYNTHESIS_DIR = Path("synthesis")
CONFIG_FILE = SYNTHESIS_DIR / "synthesis_config.json"


def update_vault_path(vault_path: str):
    """Update Synthesis config to point at the specified vault."""

    vault_path = Path(vault_path).expanduser().resolve()

    if not vault_path.exists():
        print(f"❌ Error: Vault path does not exist: {vault_path}")
        return False

    if not vault_path.is_dir():
        print(f"❌ Error: Path is not a directory: {vault_path}")
        return False

    print(f"📁 Vault path: {vault_path}")

    # Read or create config
    if CONFIG_FILE.exists():
        print(f"📝 Reading existing config: {CONFIG_FILE}")
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        print(f"📝 Creating new config: {CONFIG_FILE}")
        config = {}

    # Update vault path
    old_path = config.get('vault_path', 'not set')
    config['vault_path'] = str(vault_path)

    # Write config
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Updated vault_path:")
    print(f"  Old: {old_path}")
    print(f"  New: {vault_path}")

    return True


def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_vault.py <vault-path>")
        print("\nExample:")
        print("  python setup_vault.py ~/Obsidian/toy-vault")
        sys.exit(1)

    vault_path = sys.argv[1]

    print("""
╔══════════════════════════════════════════════════════════════╗
║  Configure Synthesis for Vault                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    if update_vault_path(vault_path):
        print(f"""
✓ Configuration updated successfully!

Next steps:

1. Process the vault (create embeddings):
   cd synthesis
   uv run main.py process

2. Run performance tests:
   cd ../..  # back to temoa root
   python prototypes/test_synthesis_performance.py

3. Investigate performance:
   python prototypes/investigate_performance.py
""")
    else:
        print("\n❌ Configuration failed. Please check the vault path and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
