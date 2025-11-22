"""
Main embedding generation pipeline for the Synthesis Project.
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np

from .engine import EmbeddingEngine
from .vault_reader import VaultReader, VaultContent
from .store import EmbeddingStore
from .models import ModelRegistry

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Main pipeline for processing vault content and generating embeddings."""
    
    def __init__(
        self,
        vault_root: Path,
        storage_dir: Path,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """Initialize the embedding pipeline.
        
        Args:
            vault_root: Path to Obsidian vault root
            storage_dir: Directory to store embeddings
            model_name: Sentence transformer model name
        """
        self.vault_root = Path(vault_root)
        self.base_storage_dir = Path(storage_dir)
        self.model_name = model_name
        
        # Validate model
        if not ModelRegistry.validate_model(model_name):
            available_models = list(ModelRegistry.list_models().keys())
            raise ValueError(f"Unknown model '{model_name}'. Available models: {available_models}")
        
        # Use model-specific storage for non-default models
        if model_name == ModelRegistry.FALLBACK_DEFAULT_MODEL:
            # Default model uses base storage directory for backward compatibility
            actual_storage_dir = self.base_storage_dir
        else:
            # Other models get their own subdirectory
            actual_storage_dir = self.base_storage_dir / model_name
        
        self.engine = EmbeddingEngine(model_name)
        self.reader = VaultReader(vault_root)
        self.store = EmbeddingStore(actual_storage_dir)
        
        logger.info(f"Pipeline initialized: {vault_root} -> {actual_storage_dir} (model: {model_name})")
    
    def process_vault(self, force_rebuild: bool = False, limit: Optional[int] = None, use_strategic_subset: bool = False) -> bool:
        """Process vault and generate embeddings.
        
        Args:
            force_rebuild: If True, regenerate even if embeddings exist
            limit: Optional limit on number of files (for testing)
            use_strategic_subset: If True, use strategic ~200 file subset
            
        Returns:
            True if processing completed successfully
        """
        if self.store.exists() and not force_rebuild:
            logger.info("Embeddings already exist. Use force_rebuild=True to regenerate.")
            return True
        
        if force_rebuild:
            logger.info("Force rebuild requested - clearing existing embeddings")
            self.store.clear()
        
        logger.info("Starting vault processing...")
        
        if use_strategic_subset:
            logger.info("Using strategic subset selection")
            strategic_files = self.reader.get_strategic_subset()
            vault_content = []
            for file_path in strategic_files:
                content = self.reader.read_file(file_path)
                if content and content.content.strip():
                    vault_content.append(content)
        else:
            vault_content = self.reader.read_vault(limit=limit)
        if not vault_content:
            logger.error("No content found in vault")
            return False
        
        logger.info(f"Processing {len(vault_content)} files")
        
        texts = [content.content for content in vault_content]
        embeddings = self.engine.embed_texts(texts, show_progress=True)
        
        metadata = []
        for content in vault_content:
            metadata.append({
                "relative_path": content.relative_path,
                "title": content.title,
                "tags": content.tags,
                "created_date": content.created_date,
                "modified_date": content.modified_date,
                "content_length": len(content.content),
                "frontmatter": content.frontmatter
            })
        
        model_info = {
            "model_name": self.engine.model_name,
            "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0
        }
        
        self.store.save_embeddings(embeddings, metadata, model_info)
        
        logger.info("Vault processing completed successfully")
        return True
    
    def find_similar(
        self, 
        query_text: str, 
        top_k: int = 10
    ) -> List[Dict]:
        """Find content similar to query text.
        
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            
        Returns:
            List of result dicts with similarity scores and metadata
        """
        embeddings, metadata, index_info = self.store.load_embeddings()
        if embeddings is None:
            logger.error("No embeddings found. Run process_vault() first.")
            return []
        
        query_embedding = self.engine.embed_text(query_text)
        
        similar_indices = self.engine.find_most_similar(
            query_embedding, embeddings, top_k
        )
        
        results = []
        for idx, similarity in similar_indices:
            result = metadata[idx].copy()
            result["similarity_score"] = float(similarity)
            
            # Add description by reading the file content
            description = self._get_content_description(result["relative_path"])
            result["description"] = description
            
            results.append(result)
        
        return results
    
    def _get_content_description(self, relative_path: str, max_length: int = 150) -> str:
        """
        Get a description snippet from file content.
        
        Args:
            relative_path: Path to the file relative to vault root
            max_length: Maximum length of description
            
        Returns:
            Content description or empty string if unavailable
        """
        try:
            from .vault_reader import VaultReader
            reader = VaultReader(self.vault_root)
            
            full_path = Path(self.vault_root) / relative_path
            content_obj = reader.read_file(full_path)
            
            if content_obj and content_obj.content:
                content = content_obj.content.strip()
                if len(content) <= max_length:
                    return content
                else:
                    # Find a good breaking point (end of sentence or word)
                    truncated = content[:max_length]
                    if '.' in truncated:
                        # Break at last sentence
                        last_sentence = truncated.rfind('.')
                        if last_sentence > max_length * 0.5:  # Only if we don't lose too much
                            return truncated[:last_sentence + 1]
                    elif ' ' in truncated:
                        # Break at last word
                        last_space = truncated.rfind(' ')
                        return truncated[:last_space] + "..."
                    else:
                        return truncated + "..."
            return ""
        except Exception as e:
            logger.debug(f"Failed to get description for {relative_path}: {e}")
            return ""
    
    def get_stats(self) -> Dict:
        """Get statistics about the embedding store."""
        stats = self.store.get_stats() or {}
        
        if self.store.exists():
            embeddings, metadata, _ = self.store.load_embeddings()
            if embeddings is not None and metadata is not None:
                stats.update({
                    "total_files": len(metadata),
                    "avg_content_length": np.mean([m.get("content_length", 0) for m in metadata]),
                    "total_tags": len(set(tag for m in metadata for tag in m.get("tags", []))),
                    "directories": len(set(Path(m["relative_path"]).parent.as_posix() for m in metadata))
                })
        
        return stats