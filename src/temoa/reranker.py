"""Cross-encoder re-ranking for improved search precision.

This module provides two-stage retrieval:
1. Fast bi-encoder semantic search (retrieves top-N candidates)
2. Precise cross-encoder re-ranking (re-ranks candidates for better precision)

Cross-encoders process query and document together, allowing for better
relevance scoring at the cost of additional latency (~2ms per pair).

Typical usage:
    reranker = CrossEncoderReranker()
    results = reranker.rerank(
        query="how to set up obsidian sync",
        results=search_results,
        top_k=10,
        rerank_top_n=100
    )
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Re-ranks search results using cross-encoder for better precision.

    Uses a pre-trained cross-encoder model to score (query, document) pairs
    and re-rank search results. This improves ranking precision by 20-30%
    compared to bi-encoder similarity alone.

    The cross-encoder model processes query and document together, learning
    relevance patterns that bi-encoders miss. This is slower than bi-encoder
    search but much more accurate for ranking.

    Attributes:
        model: CrossEncoder model instance
        model_name: HuggingFace model identifier
    """

    def __init__(self, model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2'):
        """Initialize cross-encoder model.

        Args:
            model_name: HuggingFace model identifier. Default is MiniLM-L-6-v2
                       which is trained on MS MARCO dataset and optimized for
                       speed (~2ms per pair) while maintaining good quality.

        Note:
            Model is ~90MB and will be downloaded on first use.
            Loading takes ~2-3 seconds.
        """
        logger.info(f"Loading cross-encoder model: {model_name}")
        self.model_name = model_name
        self.model = CrossEncoder(model_name)
        logger.info("Cross-encoder loaded successfully")

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10,
        rerank_top_n: int = 100
    ) -> List[Dict[str, Any]]:
        """Re-rank search results using cross-encoder.

        Takes search results from bi-encoder semantic search and re-ranks them
        using cross-encoder for better precision. Only re-ranks top N candidates
        for performance (default: 100).

        Args:
            query: Search query string
            results: List of search results from bi-encoder. Each result should
                    be a dict with at least 'title' and 'relative_path' keys.
                    'content' key is preferred if available.
            top_k: Number of results to return after re-ranking (default: 10)
            rerank_top_n: Number of top results to re-rank (default: 100).
                         Higher values = better recall but slower.

        Returns:
            Re-ranked results (top_k items) with added 'cross_encoder_score' field.
            Original similarity scores preserved in results.

        Example:
            >>> reranker = CrossEncoderReranker()
            >>> results = [
            ...     {"title": "Doc A", "content": "...", "similarity_score": 0.8},
            ...     {"title": "Doc B", "content": "...", "similarity_score": 0.75},
            ... ]
            >>> reranked = reranker.rerank("search query", results, top_k=5)
            >>> print(reranked[0]['cross_encoder_score'])
            0.92
        """
        if not results:
            return results

        # Only re-rank top N candidates (performance optimization)
        candidates = results[:rerank_top_n]

        # Build (query, document) pairs
        # Use content if available, otherwise title + path
        pairs = []
        for result in candidates:
            doc_text = result.get('content') or f"{result.get('title', '')} {result.get('relative_path', '')}"
            pairs.append([query, doc_text])

        # Score with cross-encoder
        logger.debug(f"Re-ranking {len(pairs)} candidates with cross-encoder")
        scores = self.model.predict(pairs)

        # Attach cross-encoder scores to results
        for result, score in zip(candidates, scores):
            result['cross_encoder_score'] = float(score)

        # Sort by cross-encoder score (descending)
        reranked = sorted(
            candidates,
            key=lambda x: x.get('cross_encoder_score', 0),
            reverse=True
        )

        logger.debug(f"Re-ranking complete, returning top {top_k} results")
        return reranked[:top_k]
