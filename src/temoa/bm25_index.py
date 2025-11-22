"""
BM25 keyword search index for hybrid search.

BM25 is a statistical ranking algorithm that scores documents based on:
- Term frequency (how often query terms appear)
- Inverse document frequency (rarity of terms)
- Document length normalization

This complements semantic search by catching exact mentions that might be
diluted in document-level embeddings.
"""
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25Index:
    """BM25 keyword search index for vault documents."""

    def __init__(self, storage_dir: Path):
        """
        Initialize BM25 index.

        Args:
            storage_dir: Directory to store BM25 index files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.index_file = self.storage_dir / "bm25_index.pkl"
        self.metadata_file = self.storage_dir / "bm25_metadata.pkl"

        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []

        logger.info(f"BM25Index initialized at: {self.storage_dir}")

    def tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25.

        Splits on whitespace and converts to lowercase.
        Could be enhanced with stemming, stopword removal, etc.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        if not text:
            return []

        # Simple whitespace tokenization + lowercase
        # Preserve some punctuation for exact matches (e.g., "Joan Doe")
        tokens = text.lower().split()

        return tokens

    def build(self, documents: List[Dict[str, Any]]) -> None:
        """
        Build BM25 index from documents.

        Args:
            documents: List of document dicts with 'content' and metadata
                Expected keys: 'content', 'relative_path', 'title', etc.
        """
        if not documents:
            logger.warning("No documents provided for BM25 indexing")
            return

        logger.info(f"Building BM25 index for {len(documents)} documents...")

        # Store document metadata
        self.documents = documents

        # Tokenize all documents
        corpus = []
        for doc in documents:
            # Combine title and content for better matching
            text = doc.get('title', '') + ' ' + doc.get('content', '')
            tokens = self.tokenize(text)
            corpus.append(tokens)

        # Build BM25 index
        self.bm25 = BM25Okapi(corpus)

        # Save to disk
        self.save()

        logger.info(f"✓ BM25 index built: {len(documents)} documents")

    def search(self, query: str, limit: int = 10, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search using BM25 ranking.

        Args:
            query: Search query
            limit: Maximum number of results
            min_score: Minimum BM25 score threshold

        Returns:
            List of results with BM25 scores
        """
        if self.bm25 is None:
            if not self.load():
                logger.warning("No BM25 index available")
                return []

        # Tokenize query
        query_tokens = self.tokenize(query)

        if not query_tokens:
            logger.warning("Empty query after tokenization")
            return []

        # Get BM25 scores for all documents
        scores = self.bm25.get_scores(query_tokens)

        # Create results with scores
        results = []
        for idx, score in enumerate(scores):
            if score > min_score:
                result = self.documents[idx].copy()
                result['bm25_score'] = float(score)
                results.append(result)

        # Sort by score (descending) and limit
        results.sort(key=lambda x: x['bm25_score'], reverse=True)
        results = results[:limit]

        logger.debug(f"BM25 search: query='{query}', results={len(results)}")

        return results

    def save(self) -> None:
        """Save BM25 index and metadata to disk."""
        try:
            # Save BM25 object
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.bm25, f)

            # Save document metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.documents, f)

            logger.debug(f"BM25 index saved to {self.storage_dir}")
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")
            raise

    def load(self) -> bool:
        """
        Load BM25 index from disk.

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.index_file.exists() or not self.metadata_file.exists():
            logger.debug("BM25 index files not found")
            return False

        try:
            # Load BM25 object
            with open(self.index_file, 'rb') as f:
                self.bm25 = pickle.load(f)

            # Load document metadata
            with open(self.metadata_file, 'rb') as f:
                self.documents = pickle.load(f)

            logger.info(f"BM25 index loaded: {len(self.documents)} documents")
            return True
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            return False

    def exists(self) -> bool:
        """Check if BM25 index exists on disk."""
        return self.index_file.exists() and self.metadata_file.exists()

    def clear(self) -> None:
        """Remove BM25 index files."""
        for file_path in [self.index_file, self.metadata_file]:
            if file_path.exists():
                file_path.unlink()

        self.bm25 = None
        self.documents = []

        logger.info("BM25 index cleared")


def reciprocal_rank_fusion(
    results_lists: List[List[Dict[str, Any]]],
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Merge multiple result lists using Reciprocal Rank Fusion (RRF).

    RRF is a simple but effective way to combine rankings from different
    search systems. It gives each result a score based on its rank position
    in each list, then combines scores.

    Formula: RRF(doc) = sum(1 / (k + rank)) for each list where doc appears

    Args:
        results_lists: List of result lists (e.g., [semantic_results, bm25_results])
        k: Constant for RRF formula (default: 60, standard value)

    Returns:
        Merged and re-ranked results
    """
    # Collect all unique documents by path
    doc_scores: Dict[str, float] = {}
    doc_data: Dict[str, Dict[str, Any]] = {}

    for results in results_lists:
        for rank, result in enumerate(results, start=1):
            path = result.get('relative_path', result.get('file_path', ''))

            if not path:
                continue

            # Calculate RRF score contribution from this ranking
            rrf_score = 1.0 / (k + rank)

            # Accumulate scores
            doc_scores[path] = doc_scores.get(path, 0.0) + rrf_score

            # Store document data (prefer first occurrence for metadata)
            if path not in doc_data:
                doc_data[path] = result

    # Create merged results
    merged = []
    for path, rrf_score in doc_scores.items():
        result = doc_data[path].copy()
        result['rrf_score'] = rrf_score
        merged.append(result)

    # Sort by RRF score (descending)
    merged.sort(key=lambda x: x['rrf_score'], reverse=True)

    return merged
