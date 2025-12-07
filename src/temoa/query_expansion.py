"""Query expansion using pseudo-relevance feedback for better short query handling.

TODO (Phase 4+): Smart query-aware suggestions
    Based on real-world usage, query expansion is often not useful for person names.
    Future enhancement: Analyze query content and suggest search modes intelligently:
    - If query looks like a person name → suggest hybrid search, disable expansion
    - If query is short but not a name → suggest expansion
    - If query contains technical terms → suggest semantic search
    Examples:
        "Philip Borenstein" → hybrid on, expansion off
        "AI" → expansion on (gets "AI machine learning neural")
        "React hooks" → semantic (concept-based)
"""

from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging

logger = logging.getLogger(__name__)


class QueryExpander:
    """Expands short/ambiguous queries using pseudo-relevance feedback."""

    def __init__(self, max_expansion_terms: int = 3):
        """Initialize query expander.

        Args:
            max_expansion_terms: Maximum number of terms to add to query
        """
        self.max_expansion_terms = max_expansion_terms
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2),  # unigrams and bigrams
            min_df=1  # Allow terms that appear in at least 1 document
        )
        logger.info(f"QueryExpander initialized: max_expansion_terms={max_expansion_terms}")

    def should_expand(self, query: str) -> bool:
        """Determine if query should be expanded.

        Short queries (< 3 words) are ambiguous and benefit from expansion.

        Args:
            query: Original search query

        Returns:
            True if query is short and would benefit from expansion
        """
        # Only expand short queries (< 3 words)
        word_count = len(query.split())
        return word_count < 3

    def expand(
        self,
        query: str,
        initial_results: List[Dict[str, Any]],
        top_k: int = 5
    ) -> str:
        """Expand query using pseudo-relevance feedback from top-k initial results.

        Algorithm:
        1. Extract text from top-k results
        2. Use TF-IDF to find important terms
        3. Append highest-scoring terms to query
        4. Filter out terms already in original query

        Args:
            query: Original search query
            initial_results: Initial search results to extract expansion terms from
            top_k: Number of top results to use for expansion (default: 5)

        Returns:
            Expanded query string (or original if expansion not needed/possible)
        """
        if not self.should_expand(query):
            logger.debug(f"Query '{query}' doesn't need expansion (>= 3 words)")
            return query

        if not initial_results or len(initial_results) < top_k:
            logger.debug(
                f"Not enough results for expansion "
                f"(need {top_k}, got {len(initial_results)})"
            )
            return query

        # Extract text from top-k results
        docs = []
        for result in initial_results[:top_k]:
            # Use content if available, otherwise title + path
            text = result.get('content') or \
                   f"{result.get('title', '')} {result.get('description', '')} " \
                   f"{result.get('relative_path', '')}"
            if text.strip():
                docs.append(text)

        if not docs:
            logger.debug("No text content available for expansion")
            return query

        # TF-IDF to find important terms
        try:
            tfidf_matrix = self.vectorizer.fit_transform(docs)
            feature_names = self.vectorizer.get_feature_names_out()

            # Get top terms by average TF-IDF score across documents
            avg_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
            top_indices = avg_tfidf.argsort()[-self.max_expansion_terms:][::-1]
            expansion_terms = [feature_names[i] for i in top_indices]

            # Filter out terms already in query (case-insensitive)
            query_lower = query.lower()
            expansion_terms = [
                term for term in expansion_terms
                if term.lower() not in query_lower
            ]

            if expansion_terms:
                expanded = f"{query} {' '.join(expansion_terms)}"
                logger.info(f"Expanded query: '{query}' → '{expanded}'")
                return expanded
            else:
                logger.debug(f"No new expansion terms found (all already in query)")
                return query

        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return query
