"""Tests for storage utilities (multi-vault support)"""
import json
import pytest
from pathlib import Path
from temoa.storage import (
    derive_storage_dir,
    validate_storage_safe,
    get_vault_metadata
)
from temoa.config import ConfigError


class TestDeriveStorageDir:
    """Test storage directory derivation logic"""

    def test_config_vault_uses_config_storage(self, tmp_path):
        """When vault matches config vault, use config's storage_dir"""
        vault = tmp_path / "my-vault"
        vault.mkdir()

        config_storage = tmp_path / "custom-storage"

        result = derive_storage_dir(
            vault_path=vault,
            config_vault_path=vault,
            config_storage_dir=config_storage
        )

        assert result == config_storage

    def test_other_vault_derives_storage(self, tmp_path):
        """When vault differs from config, derive as vault/.temoa/"""
        config_vault = tmp_path / "vault1"
        other_vault = tmp_path / "vault2"
        config_vault.mkdir()
        other_vault.mkdir()

        config_storage = config_vault / ".temoa"

        result = derive_storage_dir(
            vault_path=other_vault,
            config_vault_path=config_vault,
            config_storage_dir=config_storage
        )

        assert result == other_vault / ".temoa"

    def test_handles_relative_vs_absolute_paths(self, tmp_path):
        """Path comparison works even with relative vs absolute paths"""
        vault = tmp_path / "vault"
        vault.mkdir()

        config_storage = tmp_path / "storage"

        # Use relative path for one, absolute for other
        relative_vault = Path("../temoa") / vault.name

        # Should still match when resolved
        result = derive_storage_dir(
            vault_path=vault,
            config_vault_path=vault,  # Same vault, different representation
            config_storage_dir=config_storage
        )

        assert result == config_storage


class TestValidateStorageSafe:
    """Test storage validation (prevents vault mismatch)"""

    def test_no_index_is_safe(self, tmp_path):
        """No index.json means safe to proceed"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()

        # Should not raise
        validate_storage_safe(storage, vault, "index", force=False)

    def test_matching_vault_is_safe(self, tmp_path):
        """Index for same vault is safe"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create index with matching vault
        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text(json.dumps({
            "vault_path": str(vault.resolve()),
            "vault_name": vault.name
        }))

        # Should not raise
        validate_storage_safe(storage, vault, "index", force=False, model="all-mpnet-base-v2")

    def test_mismatched_vault_raises_error(self, tmp_path):
        """Index for different vault raises ConfigError"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault1 = tmp_path / "vault1"
        vault2 = tmp_path / "vault2"
        vault1.mkdir()
        vault2.mkdir()

        # Create index for vault1
        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text(json.dumps({
            "vault_path": str(vault1.resolve()),
            "vault_name": vault1.name
        }))

        # Try to validate for vault2 - should raise
        with pytest.raises(ConfigError) as exc_info:
            validate_storage_safe(storage, vault2, "index", force=False, model="all-mpnet-base-v2")

        assert "Storage directory mismatch" in str(exc_info.value)
        assert "vault1" in str(exc_info.value)
        assert "vault2" in str(exc_info.value)

    def test_force_skips_validation(self, tmp_path):
        """force=True skips validation"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault1 = tmp_path / "vault1"
        vault2 = tmp_path / "vault2"
        vault1.mkdir()
        vault2.mkdir()

        # Create index for vault1
        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text(json.dumps({
            "vault_path": str(vault1.resolve()),
            "vault_name": vault1.name
        }))

        # With force=True, should not raise
        validate_storage_safe(storage, vault2, "index", force=True, model="all-mpnet-base-v2")

    def test_old_index_without_metadata_migrates(self, tmp_path):
        """Index without vault_path gets auto-migrated"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create old index without vault metadata
        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text(json.dumps({
            "model_name": "all-mpnet-base-v2",
            "embedding_dim": 768
        }))

        # Should not raise, and should add metadata
        validate_storage_safe(storage, vault, "index", force=False, model="all-mpnet-base-v2")

        # Check metadata was added
        updated_data = json.loads(index_file.read_text())
        assert "vault_path" in updated_data
        assert updated_data["vault_path"] == str(vault.resolve())
        assert "vault_name" in updated_data
        assert updated_data["vault_name"] == vault.name
        assert "migrated_at" in updated_data

    def test_corrupted_index_does_not_crash(self, tmp_path):
        """Corrupted index.json doesn't crash validation"""
        storage = tmp_path / "storage"
        storage.mkdir()
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create corrupted index
        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text("{ invalid json }")

        # Should not raise (can't validate, so let it proceed)
        validate_storage_safe(storage, vault, "index", force=False, model="all-mpnet-base-v2")


class TestGetVaultMetadata:
    """Test vault metadata retrieval"""

    def test_returns_metadata_when_present(self, tmp_path):
        """Returns vault metadata from index"""
        storage = tmp_path / "storage"
        storage.mkdir()

        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        # Synthesis uses 'created_at', not 'indexed_at'
        index_file.write_text(json.dumps({
            "vault_path": "/Users/test/vault",
            "vault_name": "vault",
            "created_at": "2025-11-26T12:00:00"
        }))

        metadata = get_vault_metadata(storage, "all-mpnet-base-v2")

        assert metadata is not None
        assert metadata["vault_path"] == Path("/Users/test/vault")
        assert metadata["vault_name"] == "vault"
        assert metadata["indexed_at"] == "2025-11-26T12:00:00"

    def test_returns_none_when_no_index(self, tmp_path):
        """Returns None when index.json doesn't exist"""
        storage = tmp_path / "storage"
        storage.mkdir()

        metadata = get_vault_metadata(storage, "all-mpnet-base-v2")

        assert metadata is None

    def test_returns_none_when_no_metadata(self, tmp_path):
        """Returns None for old index without vault metadata"""
        storage = tmp_path / "storage"
        storage.mkdir()

        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text(json.dumps({
            "model_name": "all-mpnet-base-v2"
        }))

        metadata = get_vault_metadata(storage, "all-mpnet-base-v2")

        assert metadata is None

    def test_handles_corrupted_index(self, tmp_path):
        """Returns None for corrupted index.json"""
        storage = tmp_path / "storage"
        storage.mkdir()

        model_dir = storage / "all-mpnet-base-v2"
        model_dir.mkdir(parents=True)
        index_file = model_dir / "index.json"
        index_file.write_text("{ invalid json }")

        metadata = get_vault_metadata(storage, "all-mpnet-base-v2")

        assert metadata is None
