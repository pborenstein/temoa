"""Integration tests for multi-vault support

These tests verify that multiple vaults can be indexed independently
without data corruption or cross-contamination.

NOTE: Most of these tests require full Synthesis integration and are better
tested manually. The unit tests in test_storage.py provide coverage for
the core logic.
"""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from temoa.cli import main
from temoa.config import ConfigError

# Mark all integration tests as requiring Synthesis
pytestmark = pytest.mark.skip(reason="Requires full Synthesis integration - test manually")


@pytest.fixture
def test_vaults(tmp_path):
    """Create two test vaults with sample markdown files"""
    # Vault 1
    vault1 = tmp_path / "vault1"
    vault1.mkdir()
    (vault1 / "note1.md").write_text("This is vault 1 content about embeddings")
    (vault1 / "note2.md").write_text("Another note in vault 1 about search")

    # Vault 2
    vault2 = tmp_path / "vault2"
    vault2.mkdir()
    (vault2 / "note1.md").write_text("This is vault 2 content about databases")
    (vault2 / "note2.md").write_text("Another note in vault 2 about indexing")

    return {"vault1": vault1, "vault2": vault2}


@pytest.fixture
def config_file(tmp_path, test_vaults):
    """Create a config file pointing to vault1"""
    synthesis_path = Path(__file__).parent.parent / "synthesis"

    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "vault_path": str(test_vaults["vault1"]),
        "synthesis_path": str(synthesis_path),
        "index_path": None,  # Will use default vault/.temoa
        "default_model": "all-MiniLM-L6-v2",
        "server": {"host": "0.0.0.0", "port": 8080},
        "search": {"default_limit": 10, "max_limit": 100, "timeout": 10}
    }))

    return config


class TestMultiVaultIndexing:
    """Test that multiple vaults can be indexed independently"""

    def test_each_vault_gets_own_storage_dir(self, test_vaults, config_file, monkeypatch):
        """Each vault should have its own .temoa/ directory"""
        # Set config path env var
        monkeypatch.setenv("HOME", str(config_file.parent))

        vault1 = test_vaults["vault1"]
        vault2 = test_vaults["vault2"]

        runner = CliRunner()

        # Index vault1 (via config)
        result = runner.invoke(main, ["index", "--config", str(config_file)])
        assert result.exit_code == 0, f"vault1 index failed: {result.output}"

        # Index vault2 (via --vault flag)
        result = runner.invoke(main, ["index", "--vault", str(vault2), "--config", str(config_file)])
        assert result.exit_code == 0, f"vault2 index failed: {result.output}"

        # Verify both vaults have their own .temoa/
        assert (vault1 / ".temoa" / "index.json").exists(), "vault1 should have index"
        assert (vault2 / ".temoa" / "index.json").exists(), "vault2 should have index"

        # Verify they have different vault_path metadata
        vault1_index = json.loads((vault1 / ".temoa" / "index.json").read_text())
        vault2_index = json.loads((vault2 / ".temoa" / "index.json").read_text())

        assert vault1_index["vault_path"] != vault2_index["vault_path"]
        assert vault1_index["vault_name"] == "vault1"
        assert vault2_index["vault_name"] == "vault2"

    def test_vault_mismatch_blocked(self, test_vaults, config_file, monkeypatch):
        """Attempting to index wrong vault should be blocked"""
        monkeypatch.setenv("HOME", str(config_file.parent))

        vault1 = test_vaults["vault1"]
        vault2 = test_vaults["vault2"]

        runner = CliRunner()

        # Index vault1 first
        result = runner.invoke(main, ["index", "--config", str(config_file)])
        assert result.exit_code == 0

        # Try to index vault2 into vault1's storage (simulate the bug)
        # This would require manually manipulating storage_dir, which our fix prevents
        # Instead, verify that the metadata check works

        # Create a scenario where vault2's index is in wrong location
        wrong_storage = vault1 / ".temoa"
        vault2_index_file = wrong_storage / "index.json"

        # Read current index (for vault1)
        current_index = json.loads(vault2_index_file.read_text())

        # Try to use validate_storage_safe
        from temoa.storage import validate_storage_safe

        with pytest.raises(ConfigError) as exc_info:
            validate_storage_safe(wrong_storage, vault2, "index", force=False)

        assert "Storage directory mismatch" in str(exc_info.value)

    def test_force_override_works(self, test_vaults, config_file, monkeypatch):
        """--force flag should allow override of validation"""
        monkeypatch.setenv("HOME", str(config_file.parent))

        vault1 = test_vaults["vault1"]
        vault2 = test_vaults["vault2"]

        runner = CliRunner()

        # Index vault1 first
        result = runner.invoke(main, ["index", "--config", str(config_file)])
        assert result.exit_code == 0

        # Validate that force works programmatically
        from temoa.storage import validate_storage_safe
        wrong_storage = vault1 / ".temoa"

        # Should not raise with force=True
        validate_storage_safe(wrong_storage, vault2, "index", force=True)


class TestMultiVaultStats:
    """Test that stats work correctly for different vaults"""

    @pytest.mark.skip(reason="Requires full Synthesis integration - test manually")
    def test_stats_shows_correct_vault(self, test_vaults, config_file, monkeypatch):
        """Stats should show correct vault when using --vault flag"""
        monkeypatch.setenv("HOME", str(config_file.parent))

        vault1 = test_vaults["vault1"]
        vault2 = test_vaults["vault2"]

        runner = CliRunner()

        # Index both vaults
        runner.invoke(main, ["index", "--config", str(config_file)])
        runner.invoke(main, ["index", "--vault", str(vault2), "--config", str(config_file)])

        # Check stats for vault1 (config default)
        result = runner.invoke(main, ["stats", "--config", str(config_file)])
        assert str(vault1) in result.output

        # Check stats for vault2 (via --vault)
        result = runner.invoke(main, ["stats", "--vault", str(vault2), "--config", str(config_file)])
        assert str(vault2) in result.output


class TestBackwardCompatibility:
    """Test that existing single-vault setups still work"""

    def test_single_vault_unchanged(self, test_vaults, config_file, monkeypatch):
        """Existing single-vault users should see no changes"""
        monkeypatch.setenv("HOME", str(config_file.parent))

        vault1 = test_vaults["vault1"]

        runner = CliRunner()

        # Index without --vault (traditional usage)
        result = runner.invoke(main, ["index", "--config", str(config_file)])
        assert result.exit_code == 0

        # Verify index is in default location (vault/.temoa)
        assert (vault1 / ".temoa" / "index.json").exists()

        # Verify metadata is added
        index_data = json.loads((vault1 / ".temoa" / "index.json").read_text())
        assert "vault_path" in index_data
        assert index_data["vault_path"] == str(vault1.resolve())
