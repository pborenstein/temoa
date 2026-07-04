"""
Embedding engine for temoa — semantic embeddings, model registry, and
temporal archaeology. Extracted from the standalone Synthesis project.

Importing this package loads sentence_transformers (slow); import it
lazily from code paths that may not need the model (e.g. CLI startup).
"""
from .engine import EmbeddingEngine
from .vault_reader import VaultReader, VaultContent
from .store import EmbeddingStore
from .pipeline import EmbeddingPipeline
from .models import ModelRegistry
from .temporal_archaeology import TemporalArchaeologist

__all__ = [
    "EmbeddingEngine",
    "VaultReader",
    "VaultContent",
    "EmbeddingStore",
    "EmbeddingPipeline",
    "ModelRegistry",
    "TemporalArchaeologist",
]
