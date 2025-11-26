"""Storage utilities for multi-vault support"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .config import ConfigError

logger = logging.getLogger(__name__)


def derive_storage_dir(
    vault_path: Path,
    config_vault_path: Path,
    config_storage_dir: Path
) -> Path:
    """
    Derive storage directory for a vault.

    Strategy:
    - If vault matches config vault → use config's storage_dir (honors user config)
    - Otherwise → derive as vault/.temoa/ (auto-create per-vault index)

    Args:
        vault_path: Path to vault being operated on
        config_vault_path: Path to vault from config
        config_storage_dir: Storage dir from config

    Returns:
        Path where index should be stored for this vault
    """
    vault_abs = vault_path.resolve()
    config_vault_abs = config_vault_path.resolve()

    if vault_abs == config_vault_abs:
        # This is the config vault - honor user's configured storage_dir
        return config_storage_dir
    else:
        # Different vault - derive storage as vault/.temoa/
        return vault_abs / ".temoa"


def validate_storage_safe(
    storage_dir: Path,
    vault_path: Path,
    operation: str,
    force: bool = False
) -> None:
    """
    Validate that storage directory is safe for operation on vault.

    Checks if storage_dir already contains an index for a different vault.
    If mismatch detected and force=False, raises ConfigError with solutions.

    Args:
        storage_dir: Storage directory to validate
        vault_path: Vault being operated on
        operation: Operation name (for error messages)
        force: If True, skip validation (dangerous!)

    Raises:
        ConfigError: If vault mismatch detected and force=False
    """
    if force:
        logger.warning(f"⚠️  Force mode: Skipping vault validation for {operation}")
        return

    index_file = storage_dir / "index.json"

    if not index_file.exists():
        # No index yet - safe to proceed
        return

    # Read existing index metadata
    try:
        with open(index_file) as f:
            index_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read index metadata: {e}")
        # Can't validate - let it proceed (might be corrupted index)
        return

    # Check for vault_path in metadata
    if "vault_path" not in index_data:
        # Old index without metadata - auto-migrate
        logger.info("Migrating old index format (adding vault metadata)...")
        _add_vault_metadata(index_file, index_data, vault_path)
        return

    # Compare stored vault with current vault
    stored_vault = Path(index_data["vault_path"]).resolve()
    current_vault = vault_path.resolve()

    if stored_vault != current_vault:
        # MISMATCH DETECTED - block operation
        raise ConfigError(
            f"""
Storage directory mismatch detected!

Operation: {operation}
Target vault: {current_vault}
Existing index vault: {stored_vault}
Storage dir: {storage_dir}

This would overwrite the index for a different vault, causing data loss.

Solutions:
  1. Use correct vault path:
     temoa {operation} --vault {stored_vault}

  2. Delete existing index (if you're sure):
     rm -rf {storage_dir}

  3. Force overwrite (DANGER - will lose existing index):
     temoa {operation} --vault {current_vault} --force

Explanation:
  The storage directory contains an index for '{stored_vault}',
  but you're trying to index '{current_vault}'. This would
  overwrite the existing index with data from a different vault.
            """.strip()
        )


def _add_vault_metadata(
    index_file: Path,
    index_data: Dict[str, Any],
    vault_path: Path
) -> None:
    """
    Add vault metadata to an old index (migration).

    Updates index.json with vault_path, vault_name, and migrated_at.

    Args:
        index_file: Path to index.json
        index_data: Current index data (will be modified)
        vault_path: Vault this index belongs to
    """
    # Add metadata
    index_data["vault_path"] = str(vault_path.resolve())
    index_data["vault_name"] = vault_path.name
    index_data["migrated_at"] = datetime.now().isoformat()

    # Write back
    try:
        with open(index_file, "w") as f:
            json.dump(index_data, f, indent=2)
        logger.info(f"✓ Migrated index metadata for vault: {vault_path.name}")
    except IOError as e:
        logger.warning(f"Could not update index metadata: {e}")
        # Non-fatal - continue anyway


def get_vault_metadata(storage_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Get vault metadata from index.

    Args:
        storage_dir: Storage directory containing index.json

    Returns:
        Dict with vault metadata, or None if no index or no metadata
    """
    index_file = storage_dir / "index.json"

    if not index_file.exists():
        return None

    try:
        with open(index_file) as f:
            index_data = json.load(f)

        if "vault_path" in index_data:
            return {
                "vault_path": Path(index_data["vault_path"]),
                "vault_name": index_data.get("vault_name"),
                "indexed_at": index_data.get("indexed_at"),
                "migrated_at": index_data.get("migrated_at")
            }
        return None
    except (json.JSONDecodeError, IOError):
        return None
