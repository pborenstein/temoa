"""Vault graph analysis using obsidiantools.

Provides link graph analysis for Obsidian vaults, enabling exploration
of note relationships beyond semantic similarity.
"""

import logging
from pathlib import Path
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


class VaultGraph:
    """
    Wrapper around obsidiantools for vault graph analysis.

    Provides methods for exploring note relationships via wikilinks.
    """

    def __init__(self, vault_path: Path):
        """
        Initialize vault graph.

        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = vault_path
        self._vault = None
        self._graph = None
        self._undirected = None
        self._loaded = False

    def load(self) -> bool:
        """
        Load and connect vault graph.

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._loaded:
            return True

        try:
            from obsidiantools.api import Vault

            logger.info(f"Loading vault graph from {self.vault_path}...")
            self._vault = Vault(self.vault_path)
            self._vault.connect()
            self._graph = self._vault.graph
            self._undirected = self._graph.to_undirected()
            self._loaded = True

            logger.info(
                f"Vault graph loaded: {self._graph.number_of_nodes()} nodes, "
                f"{self._graph.number_of_edges()} edges"
            )
            return True

        except ImportError:
            logger.warning("obsidiantools not installed, graph features disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to load vault graph: {e}")
            return False

    @property
    def is_loaded(self) -> bool:
        """Check if graph is loaded."""
        return self._loaded

    def _normalize_note_name(self, name: str) -> Optional[str]:
        """
        Normalize a note name for graph lookup.

        Handles paths like 'L/Gleanings/foo.md' -> 'foo'

        Args:
            name: Note name or path

        Returns:
            Normalized name if found in graph, None otherwise
        """
        if not self._loaded:
            return None

        # Strip .md extension if present
        if name.endswith('.md'):
            name = name[:-3]

        # Try direct match first
        if name in self._graph:
            return name

        # Try just the filename (no path)
        if '/' in name:
            filename = name.rsplit('/', 1)[-1]
            if filename in self._graph:
                return filename

        # Try case-insensitive exact match
        name_lower = name.lower()
        for node in self._graph.nodes():
            if node.lower() == name_lower:
                return node

        # Try matching just the filename part case-insensitively
        if '/' in name:
            filename_lower = name.rsplit('/', 1)[-1].lower()
            for node in self._graph.nodes():
                node_filename = node.rsplit('/', 1)[-1].lower() if '/' in node else node.lower()
                if node_filename == filename_lower:
                    return node

        return None

    def get_neighbors(self, note_name: str, max_hops: int = 2) -> dict:
        """
        Get notes within N hops of target note.

        Args:
            note_name: Note name or path
            max_hops: Maximum distance (default 2)

        Returns:
            Dict with neighborhood info:
            {
                "note": normalized note name,
                "found": bool,
                "incoming": list of notes linking TO this note,
                "outgoing": list of notes this note links TO,
                "by_distance": {1: [...], 2: [...], ...}
            }
        """
        if not self._loaded:
            return {"note": note_name, "found": False, "error": "Graph not loaded"}

        normalized = self._normalize_note_name(note_name)
        if not normalized:
            return {"note": note_name, "found": False, "error": "Note not found in graph"}

        # Direct connections
        incoming = list(self._graph.predecessors(normalized))
        outgoing = list(self._graph.successors(normalized))

        # N-hop neighborhood (undirected for exploration)
        paths = nx.single_source_shortest_path_length(
            self._undirected, normalized, cutoff=max_hops
        )

        by_distance = {}
        for node, dist in paths.items():
            if node != normalized:
                by_distance.setdefault(dist, []).append(node)

        return {
            "note": normalized,
            "found": True,
            "incoming": incoming,
            "outgoing": outgoing,
            "by_distance": by_distance
        }

    def get_hub_notes(self, min_in: int = 2, min_out: int = 2, limit: int = 50) -> list:
        """
        Find well-connected notes (hub notes).

        Args:
            min_in: Minimum incoming links
            min_out: Minimum outgoing links
            limit: Maximum results

        Returns:
            List of (note_name, in_degree, out_degree) tuples, sorted by total degree
        """
        if not self._loaded:
            return []

        hubs = []
        for node in self._graph.nodes():
            in_deg = self._graph.in_degree(node)
            out_deg = self._graph.out_degree(node)
            if in_deg >= min_in and out_deg >= min_out:
                hubs.append((node, in_deg, out_deg))

        # Sort by total connections
        hubs.sort(key=lambda x: x[1] + x[2], reverse=True)
        return hubs[:limit]

    def get_path(self, source: str, target: str) -> Optional[list]:
        """
        Find shortest path between two notes.

        Args:
            source: Source note name
            target: Target note name

        Returns:
            List of note names in path, or None if no path exists
        """
        if not self._loaded:
            return None

        source_norm = self._normalize_note_name(source)
        target_norm = self._normalize_note_name(target)

        if not source_norm or not target_norm:
            return None

        try:
            return nx.shortest_path(self._undirected, source_norm, target_norm)
        except nx.NetworkXNoPath:
            return None

    def get_stats(self) -> dict:
        """
        Get graph statistics.

        Returns:
            Dict with node_count, edge_count, connected components, etc.
        """
        if not self._loaded:
            return {"loaded": False}

        components = list(nx.connected_components(self._undirected))

        return {
            "loaded": True,
            "node_count": self._graph.number_of_nodes(),
            "edge_count": self._graph.number_of_edges(),
            "connected_components": len(components),
            "largest_component_size": max(len(c) for c in components) if components else 0,
            "isolated_notes": sum(1 for c in components if len(c) == 1)
        }
