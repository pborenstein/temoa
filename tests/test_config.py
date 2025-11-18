"""Tests for configuration management"""
import json
import pytest
from pathlib import Path
from temoa.config import Config, ConfigError


def test_config_loads_successfully(tmp_path):
    """Test that config loads from valid JSON file"""
    config_file = tmp_path / "config.json"
    config_data = {
        "vault_path": str(tmp_path / "vault"),
        "synthesis_path": str(tmp_path / "synthesis"),
        "index_path": None,
        "default_model": "all-MiniLM-L6-v2",
        "server": {"host": "0.0.0.0", "port": 8080},
        "search": {"default_limit": 10, "max_limit": 50, "timeout": 10}
    }

    # Create required directories
    (tmp_path / "vault").mkdir()
    (tmp_path / "synthesis").mkdir()

    # Write config file
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    # Load config
    config = Config(config_file)

    # Verify properties
    assert config.vault_path == (tmp_path / "vault").resolve()
    assert config.synthesis_path == (tmp_path / "synthesis").resolve()
    assert config.default_model == "all-MiniLM-L6-v2"
    assert config.server_host == "0.0.0.0"
    assert config.server_port == 8080
    assert config.search_default_limit == 10
    assert config.search_max_limit == 50
    assert config.search_timeout == 10


def test_config_missing_file_raises_error(tmp_path):
    """Test that missing config file raises helpful error"""
    config_file = tmp_path / "nonexistent.json"

    with pytest.raises(ConfigError) as exc_info:
        Config(config_file)

    assert "not found" in str(exc_info.value).lower()
    assert "config.example.json" in str(exc_info.value)


def test_config_invalid_json_raises_error(tmp_path):
    """Test that invalid JSON raises error"""
    config_file = tmp_path / "config.json"
    config_file.write_text("{ invalid json }")

    with pytest.raises(ConfigError) as exc_info:
        Config(config_file)

    assert "invalid json" in str(exc_info.value).lower()


def test_config_expands_tilde_paths(tmp_path):
    """Test that ~ in paths is expanded"""
    config_file = tmp_path / "config.json"

    # Use actual home directory for this test
    home = Path.home()
    vault_path = home / "test-vault"
    synthesis_path = home / "test-synthesis"

    # Create test directories
    vault_path.mkdir(exist_ok=True)
    synthesis_path.mkdir(exist_ok=True)

    try:
        config_data = {
            "vault_path": "~/test-vault",
            "synthesis_path": "~/test-synthesis",
            "index_path": None,
            "default_model": "all-MiniLM-L6-v2",
            "server": {"host": "0.0.0.0", "port": 8080},
            "search": {"default_limit": 10, "max_limit": 50, "timeout": 10}
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(config_file)

        # Verify paths are expanded
        assert config.vault_path == vault_path.resolve()
        assert config.synthesis_path == synthesis_path.resolve()
        assert "~" not in str(config.vault_path)

    finally:
        # Cleanup
        vault_path.rmdir()
        synthesis_path.rmdir()


def test_config_default_index_path(tmp_path):
    """Test that index_path defaults to vault/.temoa"""
    config_file = tmp_path / "config.json"
    config_data = {
        "vault_path": str(tmp_path / "vault"),
        "synthesis_path": str(tmp_path / "synthesis"),
        "index_path": None,  # Should default
        "default_model": "all-MiniLM-L6-v2",
        "server": {"host": "0.0.0.0", "port": 8080},
        "search": {"default_limit": 10, "max_limit": 50, "timeout": 10}
    }

    (tmp_path / "vault").mkdir()
    (tmp_path / "synthesis").mkdir()

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    config = Config(config_file)

    # Should default to .temoa inside vault
    expected = (tmp_path / "vault" / ".temoa").resolve()
    assert config.index_path == expected


def test_config_nonexistent_vault_raises_error(tmp_path):
    """Test that nonexistent vault path raises error"""
    config_file = tmp_path / "config.json"
    config_data = {
        "vault_path": str(tmp_path / "nonexistent-vault"),
        "synthesis_path": str(tmp_path / "synthesis"),
        "index_path": None,
        "default_model": "all-MiniLM-L6-v2",
        "server": {"host": "0.0.0.0", "port": 8080},
        "search": {"default_limit": 10, "max_limit": 50, "timeout": 10}
    }

    # Only create synthesis, not vault
    (tmp_path / "synthesis").mkdir()

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    with pytest.raises(ConfigError) as exc_info:
        Config(config_file)

    assert "vault_path" in str(exc_info.value).lower()
    assert "does not exist" in str(exc_info.value).lower()


def test_config_repr(tmp_path):
    """Test that config has useful string representation"""
    config_file = tmp_path / "config.json"
    config_data = {
        "vault_path": str(tmp_path / "vault"),
        "synthesis_path": str(tmp_path / "synthesis"),
        "index_path": None,
        "default_model": "all-MiniLM-L6-v2",
        "server": {"host": "0.0.0.0", "port": 8080},
        "search": {"default_limit": 10, "max_limit": 50, "timeout": 10}
    }

    (tmp_path / "vault").mkdir()
    (tmp_path / "synthesis").mkdir()

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    config = Config(config_file)
    repr_str = repr(config)

    assert "Config" in repr_str
    assert "vault" in repr_str.lower()
    assert "synthesis" in repr_str.lower()
    assert "all-MiniLM-L6-v2" in repr_str
