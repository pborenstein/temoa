"""LRU cache for SynthesisClient instances

This module provides an LRU (Least Recently Used) cache for SynthesisClient
objects, enabling efficient multi-vault support with bounded memory usage.
"""
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .synthesis import SynthesisClient

logger = logging.getLogger(__name__)


class ClientCache:
    """
    LRU cache for SynthesisClient instances.

    Keeps up to max_size clients in memory. When cache is full,
    evicts least-recently-used client to make room for new ones.

    Memory usage: ~200-500 MB per client (model dependent)
    Default max_size=3 → ~600-1500 MB total

    Example:
        cache = ClientCache(max_size=3)
        client = cache.get(
            vault_path=Path("~/vault1"),
            synthesis_path=Path("~/synthesis"),
            model="all-mpnet-base-v2",
            storage_dir=Path("~/vault1/.temoa")
        )
    """

    def __init__(self, max_size: int = 3):
        """
        Initialize client cache.

        Args:
            max_size: Maximum number of clients to cache (default: 3)
        """
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")

        self.max_size = max_size
        self.cache: OrderedDict[str, SynthesisClient] = OrderedDict()

    def get(
        self,
        vault_path: Path,
        synthesis_path: Path,
        model: str,
        storage_dir: Path
    ) -> SynthesisClient:
        """
        Get or create client for vault.

        Cache key is (vault_path, model) tuple to support different
        models for the same vault.

        When accessing cached client, moves it to end (marks as recently used).

        Args:
            vault_path: Path to vault
            synthesis_path: Path to Synthesis directory
            model: Model name (e.g., "all-mpnet-base-v2")
            storage_dir: Storage directory for index

        Returns:
            SynthesisClient instance (cached or newly created)
        """
        # Generate cache key
        key = self._make_key(vault_path, model)

        if key in self.cache:
            # Cache HIT - move to end (mark as recently used)
            self.cache.move_to_end(key)
            logger.debug(f"Cache HIT: {vault_path.name} ({model})")
            return self.cache[key]

        # Cache MISS - create new client
        logger.info(f"Cache MISS: Creating client for {vault_path.name} ({model})")
        client = SynthesisClient(
            synthesis_path=synthesis_path,
            vault_path=vault_path,
            model=model,
            storage_dir=storage_dir
        )

        # Add to cache
        self.cache[key] = client

        # Evict oldest if over limit
        if len(self.cache) > self.max_size:
            evicted_key, evicted_client = self.cache.popitem(last=False)
            logger.info(f"Cache EVICT: {evicted_key}")
            # Client cleanup happens automatically via garbage collection

        return client

    def invalidate(self, vault_path: Path, model: str) -> None:
        """
        Remove client from cache.

        Use this after operations that change the index (e.g., reindex),
        to ensure next access gets fresh client with updated index.

        Args:
            vault_path: Path to vault
            model: Model name
        """
        key = self._make_key(vault_path, model)

        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache INVALIDATE: {key}")

    def clear(self) -> None:
        """Clear entire cache, removing all clients."""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache CLEARED: Removed {count} client(s)")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for debugging and monitoring.

        Returns:
            Dict with cache metrics:
            {
                "size": 2,
                "max_size": 3,
                "utilization": 0.67,
                "cached_vaults": [
                    {"vault": "/path/to/vault1", "model": "all-mpnet-base-v2"},
                    ...
                ]
            }
        """
        cached_vaults = []

        for key in self.cache.keys():
            vault_path, model = self._parse_key(key)
            cached_vaults.append({
                "vault": vault_path,
                "model": model
            })

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size if self.max_size > 0 else 0.0,
            "cached_vaults": cached_vaults
        }

    def _make_key(self, vault_path: Path, model: str) -> str:
        """
        Generate cache key from vault path and model.

        Args:
            vault_path: Path to vault
            model: Model name

        Returns:
            Cache key string: "{resolved_vault_path}:{model}"
        """
        return f"{vault_path.resolve()}:{model}"

    def _parse_key(self, key: str) -> tuple[str, str]:
        """
        Parse cache key back into vault path and model.

        Args:
            key: Cache key string

        Returns:
            (vault_path, model) tuple
        """
        parts = key.rsplit(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Fallback for malformed key
            return key, "unknown"

    def __repr__(self) -> str:
        return f"ClientCache(size={len(self.cache)}/{self.max_size})"
