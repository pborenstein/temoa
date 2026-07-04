"""
Core embedding engine for the Synthesis Project.
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Core engine for generating semantic embeddings of vault content."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a sentence transformer model.
        
        Args:
            model_name: HuggingFace model name. Default is lightweight and fast.
        """
        self.model_name = model_name
        self._model = None
        logger.info(f"EmbeddingEngine initialized with model: {model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model to avoid startup overhead."""
        if self._model is None:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            try:
                # Try loading from cache first (fast)
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
            except (OSError, ValueError):
                # Cache miss - download the model
                print(f"\nDownloading model '{self.model_name}' from HuggingFace Hub...")
                print("This is a one-time download, subsequent uses will be fast.\n")
                logger.info(f"Model not in cache, downloading: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                print(f"\n✓ Model '{self.model_name}' downloaded and cached\n")
        return self._model
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        return self.model.encode([text])[0]
    
    def embed_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of text strings to embed
            show_progress: Show tqdm progress bar
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        if show_progress:
            return self.model.encode(texts, show_progress_bar=True)
        else:
            return self.model.encode(texts)
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        return np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
    
    def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        embeddings: np.ndarray, 
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """Find most similar embeddings to a query.
        
        Args:
            query_embedding: Query vector
            embeddings: Array of embeddings to search
            top_k: Number of results to return
            
        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        similarities = []
        for i, embedding in enumerate(embeddings):
            sim = self.similarity(query_embedding, embedding)
            similarities.append((i, sim))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]