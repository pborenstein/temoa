"""
Synthesis direct import wrapper - loads model once, keeps in memory.

This module imports Synthesis code directly (not subprocess) to achieve
~400ms search times by keeping the sentence-transformer model in memory.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class SynthesisError(Exception):
    """Synthesis operation failed"""
    pass


class SynthesisClient:
    """
    Client for calling Synthesis via direct imports (NOT subprocess).

    This loads the sentence-transformer model into memory ONCE at startup.
    Subsequent searches reuse the loaded model (~400ms vs ~3s per search).
    """

    def __init__(
        self,
        synthesis_path: Path,
        vault_path: Path,
        model: str = "all-MiniLM-L6-v2",
        storage_dir: Optional[Path] = None
    ):
        """
        Initialize Synthesis client with direct imports.

        Args:
            synthesis_path: Path to Synthesis directory (old-ideas/synthesis)
            vault_path: Path to Obsidian vault
            model: Model name to load (default: all-MiniLM-L6-v2)
            storage_dir: Where embeddings are stored (default: synthesis_path/embeddings)

        Raises:
            SynthesisError: If Synthesis cannot be imported or initialized
        """
        self.synthesis_path = synthesis_path.resolve()
        self.vault_path = vault_path.resolve()
        self.vault_name = vault_path.name
        self.model_name = model

        # Default storage to synthesis/embeddings/
        if storage_dir is None:
            storage_dir = synthesis_path / "embeddings"
        self.storage_dir = storage_dir

        logger.info(
            f"Initializing Synthesis: vault={vault_path}, "
            f"synthesis={synthesis_path}, model={model}"
        )

        # Add Synthesis to Python path
        synthesis_str = str(self.synthesis_path)
        if synthesis_str not in sys.path:
            sys.path.insert(0, synthesis_str)
            logger.debug(f"Added {synthesis_str} to sys.path")

        # Import Synthesis modules (after adding to path)
        try:
            from src.embeddings import EmbeddingPipeline
            from src.embeddings.models import ModelRegistry
            from src.temporal_archaeology import TemporalArchaeologist

            self.EmbeddingPipeline = EmbeddingPipeline
            self.ModelRegistry = ModelRegistry
            self.TemporalArchaeologist = TemporalArchaeologist

            logger.debug("Successfully imported Synthesis modules")
        except ImportError as e:
            raise SynthesisError(
                f"Could not import Synthesis from {synthesis_path}: {e}\n"
                f"Make sure Synthesis is installed at that location."
            )

        # Validate model
        if not self.ModelRegistry.validate_model(model):
            available = list(self.ModelRegistry.list_models().keys())
            raise SynthesisError(
                f"Unknown model '{model}'. Available models: {available}"
            )

        # Initialize Synthesis pipeline
        # This loads the model into memory (takes ~10-15s, but only once!)
        try:
            logger.info(f"Loading sentence-transformer model '{model}' (this may take 10-15s)...")
            self.pipeline = self.EmbeddingPipeline(
                vault_root=self.vault_path,
                storage_dir=self.storage_dir,
                model_name=model
            )
            logger.info(f"✓ Model '{model}' loaded into memory")
        except Exception as e:
            raise SynthesisError(f"Failed to initialize Synthesis pipeline: {e}")

        # Initialize temporal archaeologist (for archaeology queries)
        try:
            self.archaeologist = self.TemporalArchaeologist(
                vault_root=self.vault_path,
                embeddings_dir=self.storage_dir,
                model_name=model
            )
            logger.debug("Temporal archaeologist initialized")
        except Exception as e:
            logger.warning(f"Could not initialize temporal archaeologist: {e}")
            self.archaeologist = None

    def search(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search using loaded model.

        This is FAST (~400ms) because model is already in memory.

        Args:
            query: Search query string
            limit: Optional result limit (default: return all)

        Returns:
            Dict with 'results' key containing search matches:
            {
                "query": str,
                "results": [
                    {
                        "title": str,
                        "relative_path": str,
                        "similarity_score": float,
                        "description": str,
                        "tags": List[str],
                        "obsidian_uri": str,
                        "wiki_link": str,
                        "file_path": str,
                        ...
                    },
                    ...
                ],
                "total": int,
                "model": str
            }

        Raises:
            SynthesisError: If search fails
        """
        try:
            logger.debug(f"Searching: query='{query}', limit={limit}")

            # Default to 10 if no limit specified
            top_k = limit if limit else 10

            # Perform search
            results = self.pipeline.find_similar(query, top_k=top_k)

            if not results:
                logger.warning(f"No results found for query: {query}")
                return {
                    "query": query,
                    "results": [],
                    "total": 0,
                    "model": self.model_name
                }

            # Enhance results with Obsidian URIs and links
            enhanced_results = []
            for result in results:
                rel_path = result['relative_path']

                # Remove .md extension for URI and wiki link
                path_no_ext = rel_path.rsplit('.md', 1)[0] if rel_path.endswith('.md') else rel_path
                title = result.get('title', path_no_ext.split('/')[-1])

                enhanced_result = dict(result)  # Copy original result
                enhanced_result.update({
                    "obsidian_uri": f"obsidian://vault/{self.vault_name}/{quote(path_no_ext)}",
                    "wiki_link": f"[[{title}]]",
                    "file_path": str(self.vault_path / rel_path)
                })
                enhanced_results.append(enhanced_result)

            logger.debug(f"Found {len(enhanced_results)} results")

            return {
                "query": query,
                "results": enhanced_results,
                "total": len(enhanced_results),
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise SynthesisError(f"Search failed: {e}")

    def archaeology(
        self,
        query: str,
        threshold: float = 0.2,
        top_k: int = 100
    ) -> Dict[str, Any]:
        """
        Perform temporal archaeology analysis.

        Analyzes when interest in a topic peaked across time by examining
        document similarity scores and temporal patterns.

        Args:
            query: Topic to analyze
            threshold: Similarity threshold (0.0-1.0, default: 0.2)
            top_k: Number of documents to analyze (default: 100)

        Returns:
            Dict with temporal analysis data:
            {
                "query": str,
                "threshold": float,
                "timeline": [...],
                "model": str
            }

        Raises:
            SynthesisError: If archaeology fails or not available
        """
        if self.archaeologist is None:
            raise SynthesisError(
                "Temporal archaeology not available. "
                "Check that Synthesis temporal_archaeology module is present."
            )

        try:
            logger.debug(f"Archaeology: query='{query}', threshold={threshold}")

            timeline = self.archaeologist.analyze_topic(
                query=query,
                threshold=threshold,
                top_k=top_k
            )

            return {
                "query": query,
                "threshold": threshold,
                "timeline": timeline,
                "model": self.model_name
            }

        except Exception as e:
            logger.error(f"Archaeology failed: {e}", exc_info=True)
            raise SynthesisError(f"Archaeology failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about indexed vault.

        Returns:
            Dict with vault statistics:
            {
                "file_count": int,
                "model_info": {...},
                "embedding_dim": int,
                ...
            }

        Raises:
            SynthesisError: If stats retrieval fails
        """
        try:
            stats = self.pipeline.get_stats()

            if not stats:
                return {
                    "file_count": 0,
                    "model_info": {"model_name": self.model_name},
                    "error": "No embeddings found"
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            raise SynthesisError(f"Failed to get stats: {e}")

    def reindex(self, force: bool = True) -> Dict[str, Any]:
        """
        Trigger re-indexing of the vault.

        This rebuilds embeddings for all files in the vault. Useful after:
        - Adding new gleanings
        - Modifying existing notes
        - Changing vault structure

        Args:
            force: Force rebuild even if embeddings exist (default: True)

        Returns:
            Dict with reindexing results:
            {
                "status": "success",
                "files_processed": int,
                "files_indexed": int,
                "model": str
            }

        Raises:
            SynthesisError: If reindexing fails
        """
        try:
            logger.info(f"Starting vault reindex (force={force})...")

            # Trigger reindexing
            success = self.pipeline.process_vault(force_rebuild=force)

            if not success:
                raise SynthesisError("Reindexing failed (process_vault returned False)")

            # Get updated stats
            stats = self.pipeline.get_stats()
            files_indexed = stats.get("total_files") or stats.get("file_count", 0)

            logger.info(f"✓ Reindexing complete: {files_indexed} files indexed")

            return {
                "status": "success",
                "files_indexed": files_indexed,
                "model": self.model_name,
                "message": f"Successfully reindexed {files_indexed} files"
            }

        except Exception as e:
            logger.error(f"Reindexing failed: {e}", exc_info=True)
            raise SynthesisError(f"Reindexing failed: {e}")

    def __repr__(self) -> str:
        return (
            f"SynthesisClient(vault={self.vault_name}, "
            f"model={self.model_name})"
        )
