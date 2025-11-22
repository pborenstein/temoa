#!/usr/bin/env python3
"""
Temporal Interest Archaeology - Track interest evolution through time

Core insight: Every interest has a lifecycle - birth, growth, dormancy, resurrection.
We trace these patterns using:
1. File timestamps from vault content
2. Semantic embeddings for thematic connections  
3. ASCII timelines because they always work

Architecture decisions:
- Use existing embeddings system (no external dependencies)
- Extract time from file paths and frontmatter
- ASCII visualization over fancy UI (reliability > flashiness)
- Focus on small strategic subset first (199 files)
"""

import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, NamedTuple
import re

from .embeddings import EmbeddingPipeline


class InterestTimeline(NamedTuple):
    """Represents an interest's evolution through time"""
    query: str
    entries: List[Tuple[date, str, float]]  # (date, content, similarity_score)
    intensity_by_month: Dict[str, float]  # "2024-01" -> avg_similarity
    activity_by_month: Dict[str, int]  # "2024-01" -> file_count
    peak_periods: List[Tuple[str, float]]  # month, intensity
    dormant_periods: List[str]  # months with no activity


class TemporalArchaeologist:
    """
    Mine vault for interest evolution patterns.
    
    Why this architecture:
    - Leverages existing embeddings (no rebuild needed)
    - Extracts timestamps from multiple sources (reliable)
    - ASCII output works everywhere (no rendering issues)
    - Focuses on insights over visual polish
    """
    
    def __init__(self, vault_root: Path = None, embeddings_dir: Path = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize with existing embeddings system.
        
        Why reuse embeddings:
        - Already computed semantic relationships
        - Consistent with our 199-file strategic subset
        - No need to rebuild infrastructure
        
        Args:
            vault_root: Path to vault root
            embeddings_dir: Path to embeddings storage
            model_name: Embedding model to use
        """
        if vault_root is None:
            vault_root = Path(__file__).parent.parent.parent.parent
        if embeddings_dir is None:
            embeddings_dir = Path(__file__).parent.parent / "embeddings"
            
        self.pipeline = EmbeddingPipeline(vault_root, embeddings_dir, model_name)
        self.temporal_cache = {}  # Cache for expensive date extractions
        
    def trace_interest(self, query: str, threshold: float = 0.3, exclude_daily: bool = False) -> InterestTimeline:
        """
        Follow an interest's journey through the vault.
        
        Algorithm:
        1. Find all content semantically related to query
        2. Extract timestamps from file paths and metadata
        3. Build chronological timeline with similarity scores
        4. Identify patterns (peaks, dormant periods, evolution)
        
        Args:
            query: Interest to trace
            threshold: Similarity threshold (0.3 captures related content without noise)
            exclude_daily: If True, filter out daily notes (Daily/YYYY/YYYY-MM-DD.md pattern)
        """
        print(f"Tracing interest evolution: '{query}'")
        
        # Get semantically similar content
        results = self.pipeline.find_similar(query, top_k=50)
        
        # Extract temporal data for each result
        timeline_entries = []
        for result in results:
            file_path = result["relative_path"]
            similarity = result["similarity_score"]
            
            # Skip daily notes if exclude_daily is True
            if exclude_daily and self._is_daily_note(result):
                continue
            
            extracted_date = self._extract_date(file_path)
            if extracted_date and similarity >= threshold:
                content = self._get_content_snippet(file_path)
                timeline_entries.append((extracted_date, content, similarity))
        
        # Sort chronologically
        timeline_entries.sort(key=lambda x: x[0])
        
        # Analyze patterns
        intensity_by_month = self._calculate_monthly_intensity(timeline_entries)
        activity_by_month = self._calculate_monthly_activity(timeline_entries)
        peak_periods = self._identify_peaks(intensity_by_month)
        dormant_periods = self._identify_dormant_periods(intensity_by_month)
        
        return InterestTimeline(
            query=query,
            entries=timeline_entries,
            intensity_by_month=intensity_by_month,
            activity_by_month=activity_by_month,
            peak_periods=peak_periods,
            dormant_periods=dormant_periods
        )
    
    def _is_daily_note(self, result: dict) -> bool:
        """
        Check if a search result represents a daily note.
        
        Daily notes are identified by having a #daily tag.
        
        Args:
            result: Search result dictionary with 'tags' field
            
        Returns:
            True if this is a daily note, False otherwise
        """
        tags = result.get('tags', [])
        return 'daily' in tags
    
    def _extract_date(self, file_path: str) -> Optional[date]:
        """
        Extract date from file path or frontmatter.
        
        Why multiple strategies:
        - Daily notes: YYYY-MM-DD in filename
        - References: creation date in frontmatter
        - L/ notes: mix of both
        
        Cache results because this is expensive.
        """
        if file_path in self.temporal_cache:
            return self.temporal_cache[file_path]
        
        extracted_date = None
        
        # Strategy 1: Daily notes pattern (2024-08-28.md)
        daily_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path)
        if daily_match:
            try:
                extracted_date = datetime.strptime(daily_match.group(1), '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Strategy 2: Frontmatter creation date
        if not extracted_date:
            try:
                vault_path = Path(self.pipeline.vault_root)
                full_path = vault_path / file_path
                content = self.pipeline.vault_reader.read_file(full_path)
                if content and 'created' in content.frontmatter:
                    created_str = content.frontmatter['created']
                    # Handle various date formats
                    for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                        try:
                            extracted_date = datetime.strptime(str(created_str), fmt).date()
                            break
                        except (ValueError, TypeError):
                            continue
            except Exception:
                pass
        
        # Strategy 3: File modification time as fallback
        if not extracted_date:
            try:
                mtime = Path(file_path).stat().st_mtime
                extracted_date = datetime.fromtimestamp(mtime).date()
            except OSError:
                pass
        
        self.temporal_cache[file_path] = extracted_date
        return extracted_date
    
    def _get_content_snippet(self, file_path: str, max_length: int = 200) -> str:
        """
        Get representative content snippet for timeline display.
        
        Why snippets:
        - ASCII timelines need concise entries
        - Focus on most relevant content
        - Keep memory usage reasonable
        """
        try:
            vault_path = Path(self.pipeline.vault_root)
            full_path = vault_path / file_path
            content = self.pipeline.vault_reader.read_file(full_path)
            if content:
                # Prefer content over title for context
                text = content.content.strip()
                if len(text) > max_length:
                    text = text[:max_length] + "..."
                return f"{Path(file_path).name}: {text}"
            return Path(file_path).name
        except Exception:
            return Path(file_path).name
    
    def _calculate_monthly_intensity(self, entries: List[Tuple[date, str, float]]) -> Dict[str, float]:
        """
        Calculate interest intensity by month.
        
        Why monthly granularity:
        - Daily too noisy, yearly too coarse
        - Matches natural thinking patterns
        - Good balance for ASCII visualization
        """
        monthly_scores = defaultdict(list)
        
        for entry_date, content, similarity in entries:
            month_key = entry_date.strftime('%Y-%m')
            monthly_scores[month_key].append(similarity)
        
        # Average similarity scores per month
        return {
            month: sum(scores) / len(scores) 
            for month, scores in monthly_scores.items()
        }
    
    def _calculate_monthly_activity(self, entries: List[Tuple[date, str, float]]) -> Dict[str, int]:
        """
        Calculate activity level (file count) by month.
        
        Why track activity separately from intensity:
        - High similarity + low activity = focused deep dive
        - Low similarity + high activity = broad exploration
        - Combined view shows different interest patterns
        """
        monthly_counts = defaultdict(int)
        
        for entry_date, content, similarity in entries:
            month_key = entry_date.strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        return dict(monthly_counts)
    
    def _identify_peaks(self, monthly_intensity: Dict[str, float], threshold: float = 0.5) -> List[Tuple[str, float]]:
        """
        Find peak interest periods.
        
        Why simple threshold:
        - Complex peak detection over-engineers the problem
        - Clear peaks are obvious in the data
        - Focus on insights over algorithmic sophistication
        """
        peaks = [(month, intensity) for month, intensity in monthly_intensity.items() 
                if intensity >= threshold]
        return sorted(peaks, key=lambda x: x[1], reverse=True)
    
    def _identify_dormant_periods(self, monthly_intensity: Dict[str, float]) -> List[str]:
        """
        Find months where interest was dormant.
        
        Why track dormancy:
        - Reveals interest patterns and cycles
        - Identifies potential resurrection candidates
        - Shows natural ebb and flow of curiosity
        """
        if not monthly_intensity:
            return []
        
        # Generate all months in range
        months = sorted(monthly_intensity.keys())
        if not months:
            return []
        
        start_date = datetime.strptime(months[0], '%Y-%m').date()
        end_date = datetime.strptime(months[-1], '%Y-%m').date()
        
        dormant = []
        current = start_date.replace(day=1)
        end = end_date.replace(day=1)
        
        while current <= end:
            month_key = current.strftime('%Y-%m')
            if month_key not in monthly_intensity:
                dormant.append(month_key)
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        return dormant
    
    def ascii_timeline(self, timeline: InterestTimeline, width: int = 80) -> str:
        """
        Beautiful ASCII visualization of interest evolution.
        
        Why ASCII over web UI:
        - Always works (no browser/rendering issues)
        - Fast to generate and view
        - Terminal-native for developer workflow
        - Focus on data over presentation
        
        Timeline format:
        2024-01 ========-- Peak period (0.67)
        2024-02 ---------- Dormant
        2024-03 =====----  Moderate activity (0.45)
        """
        if not timeline.entries:
            return f"No temporal data found for '{timeline.query}'"
        
        lines = [
            f"=== TEMPORAL ARCHAEOLOGY: {timeline.query.upper()} ===",
            f"Found {len(timeline.entries)} entries across {len(timeline.intensity_by_month)} months",
            f"Legend: bars show file count per month, similarity scores in parentheses",
            ""
        ]
        
        # Build monthly visualization
        total_files = sum(timeline.activity_by_month.values()) if timeline.activity_by_month else 0
        should_visualize = total_files >= 10 and len(timeline.activity_by_month) >= 3
        
        if timeline.activity_by_month:
            if should_visualize:
                max_activity = max(timeline.activity_by_month.values())
                lines.append("Activity timeline:")
                
                for month in sorted(timeline.activity_by_month.keys()):
                    activity = timeline.activity_by_month[month]
                    intensity = timeline.intensity_by_month.get(month, 0)
                    
                    # ASCII bar shows ACTIVITY (file count)
                    bar_width = int((activity / max_activity) * (width - 30))
                    filled_blocks = "=" * bar_width
                    empty_blocks = "-" * ((width - 30) - bar_width)
                    bar = filled_blocks + empty_blocks
                    
                    status = f"{activity} files (sim: {intensity:.2f})"
                    lines.append(f"{month} {bar} {status}")
            else:
                lines.append("Activity summary (too sparse for timeline):")
                for month in sorted(timeline.activity_by_month.keys()):
                    activity = timeline.activity_by_month[month]
                    intensity = timeline.intensity_by_month.get(month, 0)
                    lines.append(f"  {month}: {activity} files (similarity: {intensity:.2f})")
        
        # Peak summary
        if timeline.peak_periods:
            lines.extend([
                "",
                "Peak periods:",
                *[f"  {month}: {intensity:.2f}" for month, intensity in timeline.peak_periods[:3]]
            ])
        
        # Sample entries from different periods
        if timeline.entries:
            lines.extend([
                "",
                "Timeline samples:",
                *[f"  {entry[0]}: {entry[1][:60]}..." for entry in timeline.entries[::max(1, len(timeline.entries)//3)]]
            ])
        
        return "\n".join(lines)


def main():
    """CLI interface for Temporal Interest Archaeology"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mine vault for interest evolution patterns")
    parser.add_argument("query", help="Interest to trace (e.g., 'AI', 'productivity', 'writing')")
    parser.add_argument("--threshold", type=float, default=0.3, help="Similarity threshold (default: 0.3)")
    parser.add_argument("--width", type=int, default=80, help="ASCII timeline width (default: 80)")
    
    args = parser.parse_args()
    
    print("Initializing Temporal Archaeologist...")
    archaeologist = TemporalArchaeologist()
    
    print(f"Tracing interest: {args.query}")
    timeline = archaeologist.trace_interest(args.query, threshold=args.threshold)
    
    print("\n" + archaeologist.ascii_timeline(timeline, width=args.width))


if __name__ == "__main__":
    main()