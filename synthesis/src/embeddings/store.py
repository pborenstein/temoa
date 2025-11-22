"""
Embedding storage and persistence for the Synthesis Project.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Handles storage and retrieval of embeddings with metadata."""
    
    def __init__(self, storage_dir: Path):
        """Initialize embedding store.
        
        Args:
            storage_dir: Directory to store embeddings and metadata
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.embeddings_file = self.storage_dir / "embeddings.npy"
        self.metadata_file = self.storage_dir / "metadata.json"
        self.index_file = self.storage_dir / "index.json"
        
        logger.info(f"EmbeddingStore initialized at: {self.storage_dir}")
    
    def save_embeddings(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict[str, Any]],
        model_info: Dict[str, str]
    ) -> None:
        """Save embeddings and metadata to disk.
        
        Args:
            embeddings: Array of embeddings
            metadata: List of metadata dicts (one per embedding)
            model_info: Information about the model used
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")
        
        np.save(self.embeddings_file, embeddings)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        index_data = {
            "model_info": model_info,
            "created_at": datetime.now().isoformat(),
            "num_embeddings": len(embeddings),
            "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
            "files": {
                "embeddings": str(self.embeddings_file.name),
                "metadata": str(self.metadata_file.name)
            }
        }
        
        with open(self.index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Saved {len(embeddings)} embeddings to {self.storage_dir}")
    
    def load_embeddings(self) -> Tuple[Optional[np.ndarray], Optional[List[Dict]], Optional[Dict]]:
        """Load embeddings and metadata from disk.
        
        Returns:
            Tuple of (embeddings_array, metadata_list, index_info)
            Returns (None, None, None) if no saved data exists
        """
        if not self.embeddings_file.exists() or not self.metadata_file.exists():
            logger.info("No saved embeddings found")
            return None, None, None
        
        try:
            embeddings = np.load(self.embeddings_file)
            
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            index_info = None
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    index_info = json.load(f)
            
            logger.info(f"Loaded {len(embeddings)} embeddings from {self.storage_dir}")
            return embeddings, metadata, index_info
            
        except Exception as e:
            logger.error(f"Failed to load embeddings: {e}")
            return None, None, None
    
    def exists(self) -> bool:
        """Check if embeddings exist on disk."""
        return self.embeddings_file.exists() and self.metadata_file.exists()
    
    def get_stats(self) -> Optional[Dict]:
        """Get statistics about stored embeddings."""
        if not self.exists():
            return None
        
        try:
            with open(self.index_file, 'r') as f:
                index_info = json.load(f)
            return index_info
        except:
            return {"error": "Could not load index information"}
    
    def clear(self) -> None:
        """Remove all stored embeddings."""
        for file_path in [self.embeddings_file, self.metadata_file, self.index_file]:
            if file_path.exists():
                file_path.unlink()
        logger.info("Cleared all stored embeddings")
    
    def backup(self, backup_name: str = None) -> Path:
        """Create a backup of current embeddings.
        
        Args:
            backup_name: Optional name for backup. If None, uses timestamp.
            
        Returns:
            Path to backup directory
        """
        if backup_name is None:
            backup_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_dir = self.storage_dir.parent / f"backups/embeddings_{backup_name}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if self.embeddings_file.exists():
            np.save(backup_dir / "embeddings.npy", np.load(self.embeddings_file))
        
        for file_path in [self.metadata_file, self.index_file]:
            if file_path.exists():
                with open(file_path, 'r') as src, open(backup_dir / file_path.name, 'w') as dst:
                    dst.write(src.read())
        
        logger.info(f"Created backup at: {backup_dir}")
        return backup_dir