"""Configuration management for Ixpantilia"""
import json
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigError(Exception):
    """Configuration error"""
    pass


class Config:
    """Application configuration loaded from config.json"""

    def __init__(self, config_path: Path = Path("config.json")):
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to configuration file (default: config.json)

        Raises:
            ConfigError: If config file not found or invalid
        """
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from JSON file.

        Returns:
            Dict with configuration values

        Raises:
            ConfigError: If config file not found or invalid JSON
        """
        if not self.config_path.exists():
            raise ConfigError(
                f"Config file not found: {self.config_path}\n\n"
                f"Please copy config.example.json to config.json and update paths:\n"
                f"  cp config.example.json config.json\n"
                f"  # Edit config.json with your vault and synthesis paths"
            )

        try:
            with open(self.config_path) as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in {self.config_path}: {e}")

        # Expand and validate paths
        config["vault_path"] = self._expand_path(config["vault_path"], "vault_path")
        config["synthesis_path"] = self._expand_path(config["synthesis_path"], "synthesis_path")

        # Handle optional index_path
        if config.get("index_path"):
            config["index_path"] = self._expand_path(config["index_path"], "index_path")
        else:
            # Default to .ixpantilia/ inside vault
            config["index_path"] = config["vault_path"] / ".ixpantilia"

        return config

    def _expand_path(self, path: str, name: str) -> Path:
        """
        Expand path with ~ and convert to absolute Path.

        Args:
            path: Path string (may contain ~)
            name: Config key name (for error messages)

        Returns:
            Expanded absolute Path

        Raises:
            ConfigError: If path doesn't exist
        """
        expanded = Path(path).expanduser().resolve()

        # Only validate vault_path and synthesis_path exist
        # (index_path will be created if needed)
        if name in ["vault_path", "synthesis_path"] and not expanded.exists():
            raise ConfigError(
                f"{name} does not exist: {expanded}\n"
                f"Please update {self.config_path} with correct path"
            )

        return expanded

    @property
    def vault_path(self) -> Path:
        """Path to Obsidian vault"""
        return self._config["vault_path"]

    @property
    def synthesis_path(self) -> Path:
        """Path to Synthesis directory"""
        return self._config["synthesis_path"]

    @property
    def index_path(self) -> Optional[Path]:
        """Path to store index (default: vault/.ixpantilia)"""
        return self._config["index_path"]

    @property
    def default_model(self) -> str:
        """Default sentence-transformer model"""
        return self._config["default_model"]

    @property
    def server_host(self) -> str:
        """Server host address"""
        return self._config["server"]["host"]

    @property
    def server_port(self) -> int:
        """Server port"""
        return self._config["server"]["port"]

    @property
    def search_default_limit(self) -> int:
        """Default number of search results"""
        return self._config["search"]["default_limit"]

    @property
    def search_max_limit(self) -> int:
        """Maximum number of search results"""
        return self._config["search"]["max_limit"]

    @property
    def search_timeout(self) -> int:
        """Search timeout in seconds"""
        return self._config["search"]["timeout"]

    def __repr__(self) -> str:
        return (
            f"Config(vault={self.vault_path}, "
            f"synthesis={self.synthesis_path}, "
            f"model={self.default_model})"
        )
