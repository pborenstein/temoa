"""
Configuration management for the Synthesis Project.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages user configuration for the synthesis project."""
    
    DEFAULT_CONFIG = {
        "default_model": "all-MiniLM-L6-v2",
        "vault_path": None,
        "created_at": None,
        "last_updated": None
    }
    
    def __init__(self, config_dir: Path = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Directory to store config file. Defaults to project root.
        """
        if config_dir is None:
            # Store config in project root directory
            config_dir = Path(__file__).parent.parent
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "synthesis_config.json"
        self._config = None
        
        logger.debug(f"ConfigManager initialized: {self.config_file}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from disk."""
        if not self.config_file.exists():
            logger.info("No config file found, using defaults")
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to handle new config keys
            merged_config = self.DEFAULT_CONFIG.copy()
            merged_config.update(config)
            
            logger.debug(f"Loaded config from {self.config_file}")
            return merged_config
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_file}: {e}")
            logger.info("Using default configuration")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self) -> bool:
        """Save configuration to disk."""
        try:
            from datetime import datetime
            
            self._config["last_updated"] = datetime.now().isoformat()
            if self._config.get("created_at") is None:
                self._config["created_at"] = self._config["last_updated"]
            
            # Ensure directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            
            logger.debug(f"Saved config to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config to {self.config_file}: {e}")
            return False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration (lazy loaded)."""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save to disk.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if successfully saved
        """
        # Ensure config is loaded
        _ = self.config
        
        self._config[key] = value
        return self._save_config()
    
    def get_default_model(self) -> str:
        """Get the configured default model."""
        return self.get("default_model", "all-MiniLM-L6-v2")
    
    def set_default_model(self, model_name: str) -> bool:
        """Set the default model.

        Args:
            model_name: Name of the model to set as default

        Returns:
            True if successfully saved
        """
        return self.set("default_model", model_name)

    def get_vault_path(self) -> Optional[Path]:
        """Get the configured vault path.

        Returns:
            Path object if configured, None otherwise
        """
        vault_path = self.get("vault_path")
        if vault_path:
            return Path(vault_path).expanduser()
        return None

    def set_vault_path(self, vault_path: Path) -> bool:
        """Set the vault path.

        Args:
            vault_path: Path to the Obsidian vault

        Returns:
            True if successfully saved
        """
        # Convert to string and expand user home directory
        path_str = str(Path(vault_path).expanduser())
        return self.set("vault_path", path_str)
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        return self._save_config()
    
    def get_config_summary(self) -> str:
        """Get a formatted summary of current configuration."""
        config = self.config

        summary = ["Current Configuration:"]
        summary.append(f"  Default Model: {config.get('default_model', 'unknown')}")

        vault_path = config.get('vault_path')
        if vault_path:
            summary.append(f"  Vault Path: {vault_path}")
        else:
            summary.append("  Vault Path: (not configured)")

        if config.get('created_at'):
            summary.append(f"  Created: {config['created_at']}")
        if config.get('last_updated'):
            summary.append(f"  Last Updated: {config['last_updated']}")

        summary.append(f"  Config File: {self.config_file}")

        return "\n".join(summary)