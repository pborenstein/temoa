"""Temoa version information - auto-synced from pyproject.toml"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("temoa")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development/uninstalled package
    __version__ = "1.0.0"
