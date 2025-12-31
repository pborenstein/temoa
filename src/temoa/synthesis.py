"""
Synthesis direct import wrapper - loads model once, keeps in memory.

This module imports Synthesis code directly (not subprocess) to achieve
~400ms search times by keeping the sentence-transformer model in memory.
"""
import sys
import logging
import re
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote

from .bm25_index import BM25Index, reciprocal_rank_fusion

logger = logging.getLogger(__name__)


def serialize_datetime_values(obj: Any) -> Any:
    """
    Recursively convert datetime/date objects to ISO format strings for JSON serialization.

    Args:
        obj: Object to serialize (dict, list, or primitive)

    Returns:
        Object with datetime/date values converted to ISO strings
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_values(item) for item in obj]
    else:
        return obj


def extract_relevant_snippet(content: str, query: str, snippet_length: int = 150) -> str:
    """
    Extract a snippet from content that contains query terms.

    Falls back to beginning of content if no query terms found.

    Args:
        content: Full document content
        query: Search query
        snippet_length: Target snippet length in characters

    Returns:
        Extracted snippet with query context
    """
    if not content or not query:
        return content[:snippet_length] if content else ""

    # Clean query and split into terms
    query_terms = query.lower().split()
    content_lower = content.lower()

    # Find first occurrence of any query term
    best_pos = -1
    best_term = None

    for term in query_terms:
        # Skip very short terms
        if len(term) < 3:
            continue

        pos = content_lower.find(term)
        if pos != -1 and (best_pos == -1 or pos < best_pos):
            best_pos = pos
            best_term = term

    # If no query terms found, return beginning
    if best_pos == -1:
        snippet = content[:snippet_length].strip()
        if len(content) > snippet_length:
            snippet += "..."
        return snippet

    # Extract snippet around the found term
    # Try to center the term in the snippet
    half_length = snippet_length // 2
    start = max(0, best_pos - half_length)
    end = min(len(content), start + snippet_length)

    # Adjust start if we're at the end
    if end == len(content) and end - start < snippet_length:
        start = max(0, end - snippet_length)

    # Try to break at word boundaries
    snippet = content[start:end]

    # Add ellipsis if we're not at the start/end
    if start > 0:
        # Find first space to start cleanly
        first_space = snippet.find(' ')
        if first_space > 0 and first_space < 30:
            snippet = "..." + snippet[first_space:]
        else:
            snippet = "..." + snippet

    if end < len(content):
        # Find last space to end cleanly
        last_space = snippet.rfind(' ')
        if last_space > len(snippet) - 30:
            snippet = snippet[:last_space] + "..."
        else:
            snippet = snippet + "..."

    return snippet.strip()


def deduplicate_chunks(
    results: List[Dict[str, Any]],
    max_chunks_per_file: int = 1,
    merge_mode: str = "best"
) -> List[Dict[str, Any]]:
    """
    Deduplicate search results when multiple chunks from the same file appear.

    Strategy:
    - Group results by file path (relative_path)
    - For each file with multiple chunks:
      - If merge_mode="best": Keep only the highest-scoring chunk
      - If merge_mode="all": Keep all chunks but add chunk_count metadata
    - Preserve original order based on best score

    Args:
        results: List of search results (may include chunks)
        max_chunks_per_file: Maximum chunks to keep per file (default: 1)
        merge_mode: How to handle multiple chunks:
                   "best" - keep only highest scoring chunk
                   "all" - keep all chunks with metadata

    Returns:
        Deduplicated list of results
    """
    if not results:
        return results

    # Group by file path
    files_to_chunks: Dict[str, List[Dict[str, Any]]] = {}

    for result in results:
        rel_path = result.get('relative_path', '')

        # For chunked files, the relative_path is the same across chunks
        # We need to identify the base file (without chunk info)
        base_path = rel_path

        if base_path not in files_to_chunks:
            files_to_chunks[base_path] = []

        files_to_chunks[base_path].append(result)

    # Determine which score key to use for sorting
    score_key = None
    if results:
        for key in ['rrf_score', 'similarity_score', 'bm25_score']:
            if key in results[0]:
                score_key = key
                break

    # Process each file's chunks
    deduplicated = []

    for base_path, chunks in files_to_chunks.items():
        if len(chunks) == 1:
            # Single result for this file, keep as is
            deduplicated.append(chunks[0])
            continue

        # Multiple chunks from same file
        # Sort by score (descending) using the score_key we found
        if score_key:
            chunks.sort(key=lambda x: x.get(score_key, 0), reverse=True)

        if merge_mode == "best":
            # Keep only the highest-scoring chunk
            best_chunk = chunks[0].copy()

            # Add metadata about multiple matches
            if len(chunks) > 1:
                best_chunk['matched_chunks'] = len(chunks)
                best_chunk['is_chunked_file'] = True

                # Add chunk position info if available
                if 'chunk_index' in best_chunk:
                    best_chunk['best_chunk_index'] = best_chunk['chunk_index']
                    best_chunk['total_file_chunks'] = best_chunk.get('chunk_total', len(chunks))

            deduplicated.append(best_chunk)

        elif merge_mode == "all":
            # Keep up to max_chunks_per_file chunks
            for chunk in chunks[:max_chunks_per_file]:
                chunk_copy = chunk.copy()
                chunk_copy['matched_chunks'] = len(chunks)
                chunk_copy['is_chunked_file'] = True
                deduplicated.append(chunk_copy)

    # Re-sort by original score to maintain ranking
    if deduplicated and score_key:
        deduplicated.sort(key=lambda x: x.get(score_key, 0), reverse=True)

    return deduplicated


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
            synthesis_path: Path to Synthesis directory (synthesis/)
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

        # Import Synthesis modules
        # Note: Synthesis is a bundled external dependency, we need it on the path
        self._ensure_synthesis_on_path()

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

        # Initialize BM25 index (for hybrid search)
        try:
            self.bm25_index = BM25Index(storage_dir=self.storage_dir)
            logger.debug("BM25 index initialized")
        except Exception as e:
            logger.warning(f"Could not initialize BM25 index: {e}")
            self.bm25_index = None

    def _ensure_synthesis_on_path(self):
        """
        Ensure Synthesis directory is on sys.path for imports.

        Note: Synthesis is a bundled external dependency that we import from.
        This is cleaner than manipulating sys.path inline in __init__.
        """
        synthesis_str = str(self.synthesis_path)
        if synthesis_str not in sys.path:
            sys.path.insert(0, synthesis_str)
            logger.debug(f"Added {synthesis_str} to sys.path")

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

            # Enhance results with Obsidian URIs, links, and better snippets
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

                # Use frontmatter description if available, otherwise extract snippet
                # This preserves curated descriptions from gleanings
                frontmatter = result.get('frontmatter', {})
                if frontmatter and frontmatter.get('description'):
                    # Use curated description from frontmatter (gleanings have this)
                    enhanced_result['description'] = frontmatter['description']
                elif 'content' in result and result['content']:
                    # No frontmatter description, extract query-aware snippet from content
                    try:
                        better_snippet = extract_relevant_snippet(
                            result['content'],
                            query,
                            snippet_length=200
                        )
                        enhanced_result['description'] = better_snippet
                    except Exception as e:
                        logger.debug(f"Could not extract snippet: {e}")
                        # Keep original description on error

                enhanced_results.append(enhanced_result)

            logger.debug(f"Found {len(enhanced_results)} results")

            # Deduplicate chunks from the same file (keep best-scoring chunk)
            deduplicated_results = deduplicate_chunks(enhanced_results, max_chunks_per_file=1, merge_mode="best")
            logger.debug(f"After deduplication: {len(deduplicated_results)} results")

            # Serialize datetime values to ISO strings for JSON compatibility
            response = {
                "query": query,
                "results": deduplicated_results,
                "total": len(deduplicated_results),
                "model": self.model_name
            }
            return serialize_datetime_values(response)

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            raise SynthesisError(f"Search failed: {e}")

    def bm25_search(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform BM25 keyword search only (for debugging).

        Args:
            query: Search query string
            limit: Optional result limit (default: 10)

        Returns:
            Dict with BM25 results

        Raises:
            SynthesisError: If BM25 not available
        """
        if self.bm25_index is None:
            raise SynthesisError("BM25 index not available. Run 'temoa index' to build it.")

        if limit is None:
            limit = 10

        try:
            # Load BM25 index if needed
            if self.bm25_index.bm25 is None:
                self.bm25_index.load()

            bm25_results = self.bm25_index.search(query, limit=limit)

            # Enhance with Obsidian URIs
            for result in bm25_results:
                rel_path = result['relative_path']
                path_no_ext = rel_path.rsplit('.md', 1)[0] if rel_path.endswith('.md') else rel_path
                title = result.get('title', path_no_ext.split('/')[-1])

                result.update({
                    "obsidian_uri": f"obsidian://vault/{self.vault_name}/{quote(path_no_ext)}",
                    "wiki_link": f"[[{title}]]",
                    "file_path": str(self.vault_path / rel_path)
                })

            response = {
                "query": query,
                "results": bm25_results,
                "total": len(bm25_results),
                "model": self.model_name,
                "search_mode": "bm25"
            }
            return serialize_datetime_values(response)

        except Exception as e:
            logger.error(f"BM25 search failed: {e}", exc_info=True)
            raise SynthesisError(f"BM25 search failed: {e}")

    def hybrid_search(
        self,
        query: str,
        limit: Optional[int] = None,
        semantic_weight: float = 0.5
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic and keyword (BM25) search.

        This combines the strengths of both approaches:
        - Semantic search: Finds conceptually similar content
        - Keyword (BM25): Finds exact mentions and term matches

        Results are merged using Reciprocal Rank Fusion (RRF).

        Args:
            query: Search query string
            limit: Optional result limit (default: 10)
            semantic_weight: Weight for semantic vs keyword (0.0-1.0, default: 0.5)
                            0.0 = keyword only, 1.0 = semantic only

        Returns:
            Dict with merged results:
            {
                "query": str,
                "results": [...],  # Merged results with rrf_score
                "total": int,
                "model": str,
                "search_mode": "hybrid"
            }

        Raises:
            SynthesisError: If hybrid search fails or BM25 not available
        """
        if self.bm25_index is None:
            raise SynthesisError(
                "BM25 index not available. Run 'temoa index' to build it."
            )

        try:
            logger.debug(f"Hybrid search: query='{query}', limit={limit}")

            # Default limit
            if limit is None:
                limit = 10

            # Get more results from each to ensure good coverage after merging
            fetch_limit = limit * 3

            # Perform both searches
            semantic_results = []
            bm25_results = []

            # Semantic search (if weight > 0)
            if semantic_weight > 0.0:
                semantic_data = self.search(query, limit=fetch_limit)
                semantic_results = semantic_data.get('results', [])
                logger.debug(f"Semantic search found {len(semantic_results)} results")

            # Keyword search (if weight < 1.0)
            if semantic_weight < 1.0 and self.bm25_index.exists():
                # Load BM25 index if needed
                if self.bm25_index.bm25 is None:
                    self.bm25_index.load()

                bm25_results = self.bm25_index.search(query, limit=fetch_limit)
                logger.debug(f"BM25 search found {len(bm25_results)} results")

                # Enhance BM25 results with same format as semantic results
                for result in bm25_results:
                    rel_path = result['relative_path']
                    path_no_ext = rel_path.rsplit('.md', 1)[0] if rel_path.endswith('.md') else rel_path
                    title = result.get('title', path_no_ext.split('/')[-1])

                    result.update({
                        "obsidian_uri": f"obsidian://vault/{self.vault_name}/{quote(path_no_ext)}",
                        "wiki_link": f"[[{title}]]",
                        "file_path": str(self.vault_path / rel_path)
                    })

            # Merge using Reciprocal Rank Fusion
            merged_results = reciprocal_rank_fusion([semantic_results, bm25_results])

            # IMPORTANT: Boost top BM25 results that don't appear in semantic results
            # RRF penalizes documents that only appear in one list, but high BM25 matches
            # (exact keyword mentions) should still rank well even without semantic match
            semantic_paths = {r.get('relative_path') for r in semantic_results}

            # Get max RRF score to understand the scale
            max_rrf = max((r.get('rrf_score', 0) for r in merged_results), default=0.1)

            # Get max BM25 score for relative scoring
            max_bm25 = bm25_results[0].get('bm25_score', 1.0) if bm25_results else 1.0

            # Boost top BM25 results with tag matches (regardless of semantic presence)
            # This is crucial: when a doc appears in both lists but ranks poorly in semantic,
            # RRF averages the ranks and can bury a perfect BM25 tag match.
            for idx, bm25_result in enumerate(bm25_results[:10]):  # Top 10 BM25
                path = bm25_result.get('relative_path')
                bm25_score = bm25_result.get('bm25_score', 0)
                tags_matched = bm25_result.get('tags_matched', [])

                # Only boost if tags were matched (the whole point of this feature)
                if tags_matched:
                    # Find this result in merged_results and boost it
                    for merged_result in merged_results:
                        if merged_result.get('relative_path') == path:
                            old_rrf = merged_result.get('rrf_score', 0)

                            # AGGRESSIVE TAG BOOST
                            # Tag-matched results get AGGRESSIVE boost (can exceed max_rrf)
                            # This ensures tag queries surface the right results
                            score_ratio = bm25_score / max_bm25

                            # AGGRESSIVE: Tag-matched results range from 1.5x to 2.0x max_rrf
                            # This allows tag queries to dominate
                            boost_multiplier = 1.5 + (score_ratio * 0.5)  # Range: 1.5 to 2.0

                            artificial_rrf = max_rrf * boost_multiplier
                            merged_result['rrf_score'] = artificial_rrf
                            merged_result['tag_boosted'] = True  # Mark for reranker to preserve

                            logger.debug(f"Boosting tag-matched result: {merged_result.get('title')} (BM25: {bm25_score:.3f}, ratio: {score_ratio:.2f}, old RRF: {old_rrf:.4f}, new RRF: {artificial_rrf:.4f})")
                            break
                else:
                    # Apply conservative boost for BM25-only results without tags
                    if path not in semantic_paths:
                        for merged_result in merged_results:
                            if merged_result.get('relative_path') == path:
                                old_rrf = merged_result.get('rrf_score', 0)
                                score_ratio = bm25_score / max_bm25
                                boost_multiplier = score_ratio * 0.95  # Conservative: 0 to 0.95
                                artificial_rrf = max_rrf * boost_multiplier
                                merged_result['rrf_score'] = artificial_rrf
                                break

            # Re-sort by RRF score
            merged_results.sort(key=lambda x: x.get('rrf_score', 0), reverse=True)

            # Enrich merged results with individual scores for debugging
            # First, calculate query embedding once for BM25-only results
            query_embedding = None
            embeddings_array = None
            metadata_list = None

            for result in merged_results:
                path = result.get('relative_path')

                # Find this result in semantic results
                semantic_match = next((r for r in semantic_results if r.get('relative_path') == path), None)
                if semantic_match:
                    result['similarity_score'] = semantic_match.get('similarity_score', 0.0)
                else:
                    # BM25-only result: calculate ACTUAL semantic similarity
                    # Load embeddings on-demand if needed
                    if query_embedding is None:
                        query_embedding = self.pipeline.engine.embed_text(query)
                        embeddings_array, metadata_list, _ = self.pipeline.store.load_embeddings()

                    # Find this document's embedding by path
                    if embeddings_array is not None and metadata_list is not None:
                        doc_idx = None
                        for idx, meta in enumerate(metadata_list):
                            if meta.get('relative_path') == path:
                                doc_idx = idx
                                break

                        if doc_idx is not None:
                            # Calculate actual cosine similarity
                            doc_embedding = embeddings_array[doc_idx]
                            similarity = self.pipeline.engine.similarity(query_embedding, doc_embedding)
                            result['similarity_score'] = float(similarity)
                        else:
                            # Document not in embeddings (shouldn't happen)
                            result['similarity_score'] = 0.0
                    else:
                        # No embeddings loaded (shouldn't happen in hybrid mode)
                        result['similarity_score'] = 0.0

                # Find this result in BM25 results
                bm25_match = next((r for r in bm25_results if r.get('relative_path') == path), None)
                if bm25_match:
                    result['bm25_score'] = bm25_match.get('bm25_score', 0.0)
                else:
                    # Semantic-only result: set bm25_score to 0.0
                    result['bm25_score'] = 0.0

            logger.debug(f"Hybrid search merged {len(merged_results)} results (before dedup)")

            # Deduplicate chunks from the same file (keep best-scoring chunk)
            deduplicated_results = deduplicate_chunks(merged_results, max_chunks_per_file=1, merge_mode="best")
            logger.debug(f"After deduplication: {len(deduplicated_results)} results")

            # Limit final results
            deduplicated_results = deduplicated_results[:limit]

            response = {
                "query": query,
                "results": deduplicated_results,
                "total": len(deduplicated_results),
                "model": self.model_name,
                "search_mode": "hybrid"
            }
            return serialize_datetime_values(response)

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}", exc_info=True)
            raise SynthesisError(f"Hybrid search failed: {e}")

    def archaeology(
        self,
        query: str,
        threshold: float = 0.2,
        exclude_daily: bool = False
    ) -> Dict[str, Any]:
        """
        Perform temporal archaeology analysis.

        Analyzes when interest in a topic peaked across time by examining
        document similarity scores and temporal patterns.

        Args:
            query: Topic to analyze
            threshold: Similarity threshold (0.0-1.0, default: 0.2)
            exclude_daily: If True, filter out daily notes (default: False)

        Returns:
            Dict with temporal analysis data:
            {
                "query": str,
                "threshold": float,
                "entries": [...],
                "intensity_by_month": {...},
                "activity_by_month": {...},
                "peak_periods": [...],
                "dormant_periods": [...],
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
            logger.debug(f"Archaeology: query='{query}', threshold={threshold}, exclude_daily={exclude_daily}")

            # Call the correct method: trace_interest (not analyze_topic)
            timeline = self.archaeologist.trace_interest(
                query=query,
                threshold=threshold,
                exclude_daily=exclude_daily
            )

            # Convert NamedTuple to dict for JSON serialization
            response = {
                "query": timeline.query,
                "threshold": threshold,
                "entries": [
                    {
                        "date": entry[0].isoformat(),
                        "content": entry[1],
                        "similarity_score": entry[2]
                    }
                    for entry in timeline.entries
                ],
                "intensity_by_month": timeline.intensity_by_month,
                "activity_by_month": timeline.activity_by_month,
                "peak_periods": [
                    {"month": month, "intensity": intensity}
                    for month, intensity in timeline.peak_periods
                ],
                "dormant_periods": timeline.dormant_periods,
                "model": self.model_name
            }
            return serialize_datetime_values(response)

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
            logger.info(f"Getting stats from storage_dir: {self.storage_dir}")
            stats = self.pipeline.get_stats()

            if not stats:
                logger.warning(f"No stats returned from pipeline. Checking if files exist...")
                logger.warning(f"Storage directory: {self.storage_dir}")
                logger.warning(f"Directory exists: {self.storage_dir.exists()}")
                if self.storage_dir.exists():
                    import os
                    files = os.listdir(self.storage_dir)
                    logger.warning(f"Files in storage_dir: {files}")

                return {
                    "file_count": 0,
                    "model_info": {"model_name": self.model_name},
                    "error": "No embeddings found"
                }

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            raise SynthesisError(f"Failed to get stats: {e}")

    def _find_changed_files(self) -> Optional[Dict[str, List]]:
        """
        Find new, modified, and deleted files by comparing current vault state
        with file_tracking from the last index.

        Returns:
            Dict with keys "new", "modified", "deleted" containing lists of files,
            or None if no previous index exists (should do full rebuild).

        Implementation notes:
            - Uses modification dates to detect changes
            - Deleted files are detected by absence from current vault
            - New files are detected by absence from file_tracking
        """
        # Load existing index to get file tracking
        _, _, index_info = self.pipeline.store.load_embeddings()

        if not index_info or "file_tracking" not in index_info:
            # No previous index or no tracking data, must do full rebuild
            logger.info("No file_tracking found, full rebuild required")
            return None

        file_tracking = index_info["file_tracking"]
        logger.info(f"Loaded file_tracking with {len(file_tracking)} files")

        # Read current vault state
        vault_content = self.pipeline.reader.read_vault()
        current_files = {c.relative_path: c for c in vault_content}

        new_files = []
        modified_files = []
        deleted_paths = []

        # Find new and modified files
        for path, content in current_files.items():
            if path not in file_tracking:
                # New file - not in previous index
                new_files.append(content)
                logger.debug(f"New file: {path}")
            else:
                # Check if modified by comparing modification dates
                tracked = file_tracking[path]
                current_mtime = content.modified_date
                tracked_mtime = tracked.get("modified_date")

                if current_mtime != tracked_mtime:
                    # File was modified
                    modified_files.append(content)
                    logger.debug(f"Modified file: {path} (old: {tracked_mtime}, new: {current_mtime})")

        # Find deleted files (in tracking but not in current vault)
        for path in file_tracking.keys():
            if path not in current_files:
                deleted_paths.append(path)
                logger.debug(f"Deleted file: {path}")

        logger.info(f"Changes detected: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_paths)} deleted")

        return {
            "new": new_files,
            "modified": modified_files,
            "deleted": deleted_paths
        }

    def _merge_embeddings(
        self,
        new_embeddings: np.ndarray,
        new_metadata: List[Dict[str, Any]],
        changes: Dict[str, List]
    ) -> None:
        """
        Merge new/updated embeddings with existing index.

        CRITICAL: This function modifies array indices. The order of operations
        is EXTREMELY important to avoid data corruption:

        1. DELETE files first (in REVERSE index order)
        2. UPDATE files second (using indices from after deletion)
        3. APPEND new files last (at end of array)

        Do NOT change this order without careful testing! See docs/INCREMENTAL-INDEXING-PLAN.md
        DANGER ZONES section for detailed explanation of failure modes.

        Args:
            new_embeddings: Embeddings for new/modified files (modified first, then new)
            new_metadata: Metadata for new/modified files (same order)
            changes: Dict with "new", "modified", "deleted" file lists

        Raises:
            SynthesisError: If merge fails
        """
        import numpy as np

        # Load existing embeddings
        old_embeddings, old_metadata, index_info = self.pipeline.store.load_embeddings()

        if old_embeddings is None or old_metadata is None:
            # No existing index, just save new ones
            logger.info("No existing embeddings, saving new embeddings directly")
            model_info = {
                "model_name": self.pipeline.engine.model_name,
                "embedding_dim": new_embeddings.shape[1] if len(new_embeddings.shape) > 1 else 0
            }
            self.pipeline.store.save_embeddings(new_embeddings, new_metadata, model_info)
            return

        logger.info(f"Merging: {len(old_embeddings)} existing + {len(changes['new'])} new + {len(changes['modified'])} modified - {len(changes['deleted'])} deleted")

        # Build mapping: path → index position (from BEFORE any changes)
        # This is our source of truth for where things currently are
        path_to_idx = {}
        for i, meta in enumerate(old_metadata):
            path_to_idx[meta["relative_path"]] = i

        # Convert to Python lists (allows dynamic sizing)
        embeddings_list = list(old_embeddings)
        metadata_list = list(old_metadata)

        # =========================================================================
        # STEP 1: DELETE files (REVERSE order - CRITICAL!)
        # =========================================================================
        # WHY REVERSE? When you delete index 5, index 6 becomes 5, 7 becomes 6, etc.
        # If we delete in forward order, our stored indices become invalid.
        # Reverse order means we delete from the end first, keeping earlier indices stable.

        indices_to_delete = []
        for path in changes["deleted"]:
            if path in path_to_idx:
                indices_to_delete.append(path_to_idx[path])

        # Sort descending (largest index first) to maintain index validity
        for idx in sorted(indices_to_delete, reverse=True):
            logger.debug(f"Deleting index {idx}: {metadata_list[idx]['relative_path']}")
            del embeddings_list[idx]
            del metadata_list[idx]

        # =========================================================================
        # STEP 2: UPDATE modified files (rebuild index map after deletions!)
        # =========================================================================
        # IMPORTANT: After deletions, positions have shifted. Rebuild the map.

        path_to_idx_after_delete = {}
        for i, meta in enumerate(metadata_list):
            path_to_idx_after_delete[meta["relative_path"]] = i

        # new_embeddings contains modified files first, then new files
        new_idx = 0
        for content in changes["modified"]:
            path = content.relative_path
            if path in path_to_idx_after_delete:
                current_idx = path_to_idx_after_delete[path]
                logger.debug(f"Updating index {current_idx}: {path}")
                embeddings_list[current_idx] = new_embeddings[new_idx]
                metadata_list[current_idx] = new_metadata[new_idx]
                new_idx += 1

        # =========================================================================
        # STEP 3: APPEND new files (always safe - goes at end)
        # =========================================================================
        for content in changes["new"]:
            logger.debug(f"Appending new file: {content.relative_path}")
            embeddings_list.append(new_embeddings[new_idx])
            metadata_list.append(new_metadata[new_idx])
            new_idx += 1

        # Convert back to numpy array
        merged_embeddings = np.array(embeddings_list)

        logger.info(f"Merge complete: {len(merged_embeddings)} total files in index")

        # Save merged result (save_embeddings will rebuild file_tracking with correct positions)
        model_info = {
            "model_name": self.pipeline.engine.model_name,
            "embedding_dim": merged_embeddings.shape[1] if len(merged_embeddings.shape) > 1 else 0
        }
        self.pipeline.store.save_embeddings(merged_embeddings, metadata_list, model_info)

    def reindex(
        self,
        force: bool = True,
        enable_chunking: bool = False,
        chunk_size: int = 2000,
        chunk_overlap: int = 400,
        chunk_threshold: int = 4000
    ) -> Dict[str, Any]:
        """
        Trigger re-indexing of the vault.

        When force=False (incremental mode):
        - Only processes new/modified files
        - Detects deletions and removes them from index
        - Much faster for daily use (seconds vs minutes)
        - Falls back to full rebuild if no previous index exists

        When force=True (full rebuild):
        - Processes ALL files from scratch
        - Use for first-time indexing, model changes, or troubleshooting

        Args:
            force: Force full rebuild (default: True)
            enable_chunking: Enable adaptive chunking for large files (default: False)
            chunk_size: Target size for each chunk in characters (default: 2000)
            chunk_overlap: Number of overlapping characters between chunks (default: 400)
            chunk_threshold: Minimum file size before chunking is applied (default: 4000)

        Returns:
            Dict with reindexing results:
            {
                "status": "success",
                "files_indexed": int,
                "files_new": int (incremental only),
                "files_modified": int (incremental only),
                "files_deleted": int (incremental only),
                "model": str,
                "chunking_enabled": bool,
                "total_chunks": int (if chunking enabled)
            }

        Raises:
            SynthesisError: If reindexing fails
        """
        try:
            logger.info(f"Starting vault reindex (force={force})...")

            # Check if incremental reindex is possible
            if not force:
                changes = self._find_changed_files()

                if changes is None:
                    # No previous index, fall back to full rebuild
                    logger.info("No existing index found, performing full rebuild")
                    force = True
                elif not changes["new"] and not changes["modified"] and not changes["deleted"]:
                    # No changes detected
                    logger.info("No changes detected, index is up to date")
                    return {
                        "status": "success",
                        "files_indexed": 0,
                        "files_new": 0,
                        "files_modified": 0,
                        "files_deleted": 0,
                        "model": self.model_name,
                        "message": "No changes detected, index already up to date"
                    }

            # Full rebuild path
            if force:
                logger.info("Performing full rebuild...")
                if enable_chunking:
                    logger.info(f"Chunking enabled: size={chunk_size}, overlap={chunk_overlap}, threshold={chunk_threshold}")

                # Read vault content
                logger.info("Reading vault files...")
                vault_content = self.pipeline.reader.read_vault(
                    enable_chunking=enable_chunking,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunk_threshold=chunk_threshold
                )

                if not vault_content:
                    logger.error("No content found in vault")
                    raise SynthesisError("No content found in vault")

                logger.info(f"Read {len(vault_content)} files from vault")

                # Build BM25 index (fast - takes seconds)
                if self.bm25_index is not None:
                    logger.info("Building BM25 keyword index...")
                    print(f"Building BM25 keyword index...")
                    try:
                        documents = []
                        for content_obj in vault_content:
                            doc = {
                                'relative_path': content_obj.relative_path,
                                'title': content_obj.title,
                                'content': content_obj.content,
                                'tags': content_obj.tags,
                                'frontmatter': content_obj.frontmatter
                            }
                            documents.append(doc)

                        self.bm25_index.build(documents)
                        logger.info(f"✓ BM25 index built: {len(documents)} documents")
                        print(f"✓ BM25 index built")
                    except Exception as e:
                        logger.warning(f"BM25 indexing failed: {e}")

                # Build semantic embeddings (slow - takes minutes)
                logger.info("Building semantic embeddings (this may take several minutes)...")
                print(f"Loading embedding model ({self.model_name}) and preparing {len(vault_content)} items...")
                self.pipeline.store.clear()

                texts = [content.content for content in vault_content]
                embeddings = self.pipeline.engine.embed_texts(texts, show_progress=True)

                metadata = []
                for content in vault_content:
                    meta = {
                        "relative_path": content.relative_path,
                        "title": content.title,
                        "tags": content.tags,
                        "created_date": content.created_date,
                        "modified_date": content.modified_date,
                        "content_length": len(content.content),
                        "frontmatter": content.frontmatter,
                        # Chunk metadata
                        "is_chunk": content.is_chunk,
                        "chunk_index": content.chunk_index,
                        "chunk_total": content.chunk_total,
                        "chunk_start": content.chunk_start,
                        "chunk_end": content.chunk_end
                    }
                    metadata.append(meta)

                model_info = {
                    "model_name": self.pipeline.engine.model_name,
                    "embedding_dim": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
                    "vault_path": str(self.vault_path.resolve()),
                    "vault_name": self.vault_path.name,
                    "indexed_at": datetime.now().isoformat(),
                    "chunking_enabled": enable_chunking,
                    "chunk_size": chunk_size if enable_chunking else None,
                    "chunk_overlap": chunk_overlap if enable_chunking else None,
                    "chunk_threshold": chunk_threshold if enable_chunking else None
                }

                self.pipeline.store.save_embeddings(embeddings, metadata, model_info)

                files_indexed = len(vault_content)
                num_chunks = sum(1 for c in vault_content if c.is_chunk)
                num_files = len(set(c.relative_path for c in vault_content))

                if enable_chunking and num_chunks > 0:
                    logger.info(f"✓ Semantic indexing complete: {num_files} files → {files_indexed} content items ({num_chunks} chunks)")
                else:
                    logger.info(f"✓ Semantic indexing complete: {files_indexed} files indexed")

                logger.info(f"✓ Full reindexing complete")

                result = {
                    "status": "success",
                    "files_indexed": files_indexed,
                    "model": self.model_name,
                    "chunking_enabled": enable_chunking
                }

                if enable_chunking and num_chunks > 0:
                    result["total_files"] = num_files
                    result["total_chunks"] = num_chunks
                    result["message"] = f"Successfully reindexed {num_files} files ({num_chunks} chunks, {files_indexed - num_chunks} whole files)"
                else:
                    result["message"] = f"Successfully reindexed {files_indexed} files"

                return result

            # Incremental rebuild path
            else:
                logger.info(f"Performing incremental reindex: {len(changes['new'])} new, {len(changes['modified'])} modified, {len(changes['deleted'])} deleted")
                if enable_chunking:
                    logger.info(f"Chunking enabled: size={chunk_size}, overlap={chunk_overlap}, threshold={chunk_threshold}")

                # Rebuild BM25 index (always full rebuild - it's fast)
                vault_content = self.pipeline.reader.read_vault(
                    enable_chunking=enable_chunking,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    chunk_threshold=chunk_threshold
                )

                if self.bm25_index is not None:
                    logger.info("Rebuilding BM25 keyword index...")
                    print(f"Rebuilding BM25 keyword index...")
                    try:
                        documents = []
                        for content_obj in vault_content:
                            doc = {
                                'relative_path': content_obj.relative_path,
                                'title': content_obj.title,
                                'content': content_obj.content,
                                'tags': content_obj.tags,
                                'frontmatter': content_obj.frontmatter
                            }
                            documents.append(doc)

                        self.bm25_index.build(documents)
                        logger.info(f"✓ BM25 index rebuilt: {len(documents)} documents")
                        print(f"✓ BM25 index rebuilt")
                    except Exception as e:
                        logger.warning(f"BM25 indexing failed: {e}")

                # Embed only changed files
                changed_files = changes["modified"] + changes["new"]

                if changed_files:
                    logger.info(f"Embedding {len(changed_files)} changed files...")
                    print(f"Loading embedding model ({self.model_name}) and preparing {len(changed_files)} items...")
                    texts = [content.content for content in changed_files]
                    embeddings = self.pipeline.engine.embed_texts(texts, show_progress=True)

                    metadata = []
                    for content in changed_files:
                        meta = {
                            "relative_path": content.relative_path,
                            "title": content.title,
                            "tags": content.tags,
                            "created_date": content.created_date,
                            "modified_date": content.modified_date,
                            "content_length": len(content.content),
                            "frontmatter": content.frontmatter,
                            # Chunk metadata
                            "is_chunk": content.is_chunk,
                            "chunk_index": content.chunk_index,
                            "chunk_total": content.chunk_total,
                            "chunk_start": content.chunk_start,
                            "chunk_end": content.chunk_end
                        }
                        metadata.append(meta)

                    # Merge with existing embeddings
                    self._merge_embeddings(embeddings, metadata, changes)
                    logger.info(f"✓ Incremental reindexing complete")
                else:
                    # Only deletions, no new embeddings to create
                    logger.info("Processing deletions only...")
                    self._merge_embeddings(np.array([]), [], changes)

                return {
                    "status": "success",
                    "files_indexed": len(changed_files),
                    "files_new": len(changes["new"]),
                    "files_modified": len(changes["modified"]),
                    "files_deleted": len(changes["deleted"]),
                    "model": self.model_name,
                    "message": f"Incremental reindex: {len(changes['new'])} new, {len(changes['modified'])} modified, {len(changes['deleted'])} deleted"
                }

        except Exception as e:
            logger.error(f"Reindexing failed: {e}", exc_info=True)
            raise SynthesisError(f"Reindexing failed: {e}")

    def __repr__(self) -> str:
        return (
            f"SynthesisClient(vault={self.vault_name}, "
            f"model={self.model_name})"
        )
