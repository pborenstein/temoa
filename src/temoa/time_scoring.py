"""Time-aware scoring with recency boost for search results."""

from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class TimeAwareScorer:
    """Applies time-decay boost to search results based on file modification time."""

    def __init__(
        self,
        half_life_days: int = 90,
        max_boost: float = 0.2,
        enabled: bool = True
    ):
        """Initialize time-aware scorer.

        Args:
            half_life_days: Number of days for boost to decay by 50%
            max_boost: Maximum boost factor for most recent docs (e.g., 0.2 = 20% boost)
            enabled: Whether to apply time-aware scoring
        """
        self.half_life_days = half_life_days
        self.max_boost = max_boost
        self.enabled = enabled
        logger.info(
            f"TimeAwareScorer initialized: "
            f"half_life={half_life_days}d, max_boost={max_boost:.1%}, enabled={enabled}"
        )

    def apply_boost(
        self,
        results: List[Dict[str, Any]],
        vault_path: Path
    ) -> List[Dict[str, Any]]:
        """Apply time-decay boost to results based on file modification time.

        Formula: boosted_score = similarity_score * (1 + boost_factor)
        where: boost_factor = max_boost * (0.5 ** (days_old / half_life_days))

        Args:
            results: Search results with similarity_score field
            vault_path: Path to vault (to get file modification times)

        Returns:
            Results with boosted scores, re-sorted by boosted score
        """
        if not self.enabled or not results:
            return results

        now = datetime.now()
        boosted_count = 0

        for result in results:
            # Get file modification time
            file_path = vault_path / result['relative_path']
            if not file_path.exists():
                logger.debug(f"File not found for time boost: {file_path}")
                continue

            try:
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                days_old = (now - modified_time).days

                # Calculate boost factor using exponential decay
                # Recent docs get higher boost, old docs get minimal boost
                decay_factor = 0.5 ** (days_old / self.half_life_days)
                boost = self.max_boost * decay_factor

                # Apply boost to similarity score
                original_score = result.get('similarity_score', 0)
                boosted_score = original_score * (1 + boost)

                # Store both original and boosted scores for transparency
                result['original_score'] = original_score
                result['time_boost'] = boost
                result['similarity_score'] = boosted_score
                result['days_old'] = days_old

                boosted_count += 1

            except Exception as e:
                logger.warning(f"Failed to apply time boost to {file_path}: {e}")
                continue

        if boosted_count > 0:
            logger.debug(f"Applied time boost to {boosted_count}/{len(results)} results")

        # Re-sort by boosted score
        results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)

        return results
