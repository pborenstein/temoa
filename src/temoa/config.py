"""Configuration management for Temoa"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigError(Exception):
    """Configuration error"""
    pass


class Config:
    """
    Application configuration loaded from config.json.

    Design Note: Property Methods
    ------------------------------
    This class provides property methods (e.g., vault_path, default_model) that
    forward to the internal _config dict. While these might seem redundant, they
    serve important purposes:

    1. **IDE Support**: Properties provide autocomplete and type hints, making the
       API more discoverable and less error-prone than dict access.

    2. **Type Safety**: Properties return typed values (Path, str, int, bool)
       instead of Any, enabling better static analysis.

    3. **API Stability**: Properties provide a stable interface that can evolve
       independently of the internal dict structure.

    4. **Backward Compatibility**: Changing internal dict keys doesn't break
       external code using properties.

    5. **Documentation**: Each property has its own docstring explaining purpose,
       whereas dict keys are just strings.

    Alternative approaches considered:
    - Direct dict access (config['key']): Loses type hints and IDE support
    - __getitem__ method: Still returns Any type, no autocomplete
    - Dataclass: Requires migration, breaks existing code

    The small overhead of property forwarding is worth the developer experience
    and maintainability benefits.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Load configuration from JSON file.

        Searches for config in this order:
        1. Provided config_path
        2. ~/.config/temoa/config.json (XDG standard)
        3. ~/.temoa.json (simple alternative)
        4. ./config.json (current directory, for development)

        Args:
            config_path: Optional path to configuration file

        Raises:
            ConfigError: If config file not found or invalid
        """
        self.config_path = self._find_config(config_path)
        self._config = self._load_config()

    def _find_config(self, config_path: Optional[Path]) -> Path:
        """
        Find configuration file in standard locations.

        Args:
            config_path: Optional explicit path

        Returns:
            Path to config file

        Raises:
            ConfigError: If no config file found
        """
        import os

        # If explicit path provided, use it
        if config_path:
            if config_path.exists():
                return config_path
            raise ConfigError(f"Specified config file not found: {config_path}")

        # Check environment variable
        env_path = os.getenv("TEMOA_CONFIG_PATH")
        if env_path:
            env_config = Path(env_path)
            if env_config.exists():
                return env_config
            raise ConfigError(f"TEMOA_CONFIG_PATH file not found: {env_config}")

        # Search standard locations (global config only - not vault-local)
        search_paths = [
            Path.home() / ".config" / "temoa" / "config.json",  # XDG standard
            Path.home() / ".temoa.json",                         # Simple alternative
            Path("config.json"),                                 # Current directory (dev)
        ]

        for path in search_paths:
            if path.exists():
                return path

        # No config found - provide helpful error
        raise ConfigError(
            "No config file found. Create one in any of these locations:\n\n"
            "  1. ~/.config/temoa/config.json (recommended - XDG standard)\n"
            "  2. ~/.temoa.json (simple alternative)\n"
            "  3. ./config.json (current directory - for development)\n\n"
            "Quick setup:\n"
            "  mkdir -p ~/.config/temoa\n"
            "  cat > ~/.config/temoa/config.json << 'EOF'\n"
            "{\n"
            '  "vault_path": "~/Obsidian/your-vault",\n'
            '  "synthesis_path": "~/projects/temoa/synthesis",\n'
            '  "index_path": null,\n'
            '  "default_model": "all-mpnet-base-v2",\n'
            '  "server": {"host": "0.0.0.0", "port": 8080},\n'
            '  "search": {"default_limit": 10, "max_limit": 100, "timeout": 10}\n'
            "}\n"
            "EOF\n"
        )

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from JSON file.

        Returns:
            Dict with configuration values

        Raises:
            ConfigError: If config file not found or invalid JSON
        """
        # config_path should already exist (found by _find_config)
        if not self.config_path.exists():
            raise ConfigError(f"Config file disappeared: {self.config_path}")

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
            # Default to .temoa/ inside vault
            config["index_path"] = config["vault_path"] / ".temoa"

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
            # Build helpful error message
            error_msg = [
                f"Configuration error: {name} path does not exist",
                f"",
                f"  Configured: {path}",
                f"  Expands to: {expanded}",
                f"",
                f"This path was not found on your system.",
                f"",
                f"Possible causes:",
                f"  • The project was moved to a different location",
                f"  • The path in your config is outdated",
                f"  • A typo in the path",
                f"",
                f"To fix this:",
                f"  1. Find the correct path to your {name.replace('_', ' ')}",
                f"  2. Edit {self.config_path}",
                f"  3. Update the '{name}' field with the correct path",
            ]

            # Check for similar paths that might exist
            parent = expanded.parent
            if parent.exists():
                # Look for directories with similar names
                similar = []
                target_name = expanded.name.lower()
                for item in parent.iterdir():
                    if item.is_dir() and target_name in item.name.lower():
                        similar.append(str(item))

                if similar:
                    error_msg.extend([
                        f"",
                        f"Found similar paths in {parent}:",
                    ])
                    for s in similar[:5]:  # Limit to 5 suggestions
                        error_msg.append(f"  • {s}")

            raise ConfigError("\n".join(error_msg))

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
        """Path to store index (default: vault/.temoa)"""
        return self._config["index_path"]

    @property
    def storage_dir(self) -> Optional[Path]:
        """Alias for index_path (for compatibility with Synthesis)"""
        return self.index_path

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

    @property
    def hybrid_search_enabled(self) -> bool:
        """Whether hybrid search (BM25 + semantic) is enabled by default"""
        # Default to False if not specified for backwards compatibility
        return self._config.get("search", {}).get("hybrid_enabled", False)

    def get_all_vaults(self) -> List[Dict[str, Any]]:
        """
        Get list of all configured vaults.

        Returns:
            List of vault configs with format:
            [
                {"name": "Main Vault", "path": "~/Obsidian/vault", "is_default": True},
                ...
            ]

        If no 'vaults' array in config, auto-generates single-vault list
        from vault_path (backward compatibility).
        """
        vaults = self._config.get("vaults", [])

        if not vaults:
            # Backward compatibility: generate from vault_path
            return [{
                "name": self.vault_path.name,
                "path": str(self.vault_path),
                "is_default": True
            }]

        return vaults

    def get_default_vault(self) -> Dict[str, Any]:
        """
        Get default vault config.

        Returns:
            Vault config dict marked as default, or first vault if none marked.

        Raises:
            ConfigError: If no vaults configured
        """
        vaults = self.get_all_vaults()

        if not vaults:
            raise ConfigError("No vaults configured")

        # Find vault marked as default
        for vault in vaults:
            if vault.get("is_default"):
                return vault

        # Fallback to first vault
        return vaults[0]

    def find_vault(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Find vault by name or path.

        Args:
            identifier: Vault name (case-insensitive) or path string

        Returns:
            Vault config dict or None if not found

        Examples:
            config.find_vault("Main Vault")  # By name
            config.find_vault("~/Obsidian/amoxtli")  # By path
        """
        vaults = self.get_all_vaults()

        # Try matching by name (case-insensitive)
        for vault in vaults:
            if vault["name"].lower() == identifier.lower():
                return vault

        # Try matching by path
        try:
            search_path = Path(identifier).expanduser().resolve()
            for vault in vaults:
                vault_path = Path(vault["path"]).expanduser().resolve()
                if vault_path == search_path:
                    return vault
        except (OSError, RuntimeError):
            # Invalid path string - not a match
            pass

        return None

    def __repr__(self) -> str:
        return (
            f"Config(vault={self.vault_path}, "
            f"synthesis={self.synthesis_path}, "
            f"model={self.default_model})"
        )
