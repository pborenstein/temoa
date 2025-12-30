"""
Search Profile System

Defines search profiles optimized for different content types and use cases.
Each profile configures search weights, boosting, and features to optimize
for specific scenarios (repos, recent work, deep reading, keywords).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class SearchProfile:
    """Configuration for a search mode optimized for specific use cases"""

    name: str
    display_name: str
    description: str

    # Core search weights
    hybrid_weight: float  # 0.0-1.0, where 0=pure BM25, 1=pure semantic
    bm25_boost: float = 1.0  # Multiplier for BM25 scores

    # Metadata boosting configuration
    metadata_boost: Dict[str, Any] = field(default_factory=dict)

    # Time weighting configuration
    time_decay_config: Optional[Dict[str, Any]] = None
    max_age_days: Optional[int] = None  # Hard filter for content age

    # Quality/speed tradeoffs
    cross_encoder_enabled: bool = True
    query_expansion_enabled: bool = False

    # Content filtering defaults
    default_include_types: Optional[List[str]] = None
    default_exclude_types: Optional[List[str]] = None

    # Chunking configuration
    chunking_enabled: bool = True
    chunk_size: int = 2000
    chunk_overlap: int = 400

    # Result presentation
    show_chunk_context: bool = False
    max_results_per_file: int = 1  # For chunked results


# Built-in search profiles
SEARCH_PROFILES: Dict[str, SearchProfile] = {
    "repos": SearchProfile(
        name="repos",
        display_name="Repos & Tech",
        description="Find GitHub repos, libraries, tools by keywords and popularity",
        hybrid_weight=0.3,  # 30% semantic, 70% BM25
        bm25_boost=2.0,
        metadata_boost={
            "github_stars": {
                "enabled": True,
                "scale": "log",  # logarithmic scale for diminishing returns
                "max_boost": 0.5  # Up to 50% boost
            },
            "github_topics": {
                "enabled": True,
                "match_boost": 3.0  # 3x boost when query matches topic
            },
            "github_language": {
                "enabled": True,
                "match_boost": 1.5  # 1.5x boost when language matches query
            }
        },
        time_decay_config=None,  # Recency doesn't matter for repos
        cross_encoder_enabled=False,  # Speed over precision
        query_expansion_enabled=False,
        default_include_types=["gleaning"],
        chunking_enabled=False,  # Gleanings are small
        show_chunk_context=False
    ),

    "recent": SearchProfile(
        name="recent",
        display_name="Recent Work",
        description="Find what you wrote or saved recently (last 90 days)",
        hybrid_weight=0.5,  # Balanced
        bm25_boost=1.0,
        time_decay_config={
            "half_life_days": 7,  # Aggressive - prefer this week
            "max_boost": 0.5  # Up to 50% boost for today
        },
        max_age_days=90,  # Hard cutoff - ignore older content
        cross_encoder_enabled=True,
        query_expansion_enabled=False,
        default_include_types=["daily", "note", "writering"],
        chunking_enabled=True,  # Daily notes can be long
        show_chunk_context=False
    ),

    "deep": SearchProfile(
        name="deep",
        display_name="Deep Reading",
        description="Search long-form content with full context (articles, books, essays)",
        hybrid_weight=0.8,  # 80% semantic, 20% BM25
        bm25_boost=1.0,
        cross_encoder_enabled=True,
        query_expansion_enabled=False,
        chunking_enabled=True,
        chunk_size=2000,
        chunk_overlap=400,
        show_chunk_context=True,
        max_results_per_file=3,  # Show top 3 chunks per file
        default_exclude_types=["daily", "gleaning"]  # Focus on long content
    ),

    "keywords": SearchProfile(
        name="keywords",
        display_name="Keyword Search",
        description="Exact keyword matching for technical terms, names, phrases",
        hybrid_weight=0.2,  # 20% semantic, 80% BM25
        bm25_boost=1.5,
        cross_encoder_enabled=False,  # Speed
        query_expansion_enabled=False,
        chunking_enabled=True,
        show_chunk_context=False
    ),

    "default": SearchProfile(
        name="default",
        display_name="Balanced",
        description="General-purpose search (current behavior)",
        hybrid_weight=0.5,  # 50/50 hybrid
        bm25_boost=1.0,
        cross_encoder_enabled=True,
        query_expansion_enabled=False,
        time_decay_config={
            "half_life_days": 90,
            "max_boost": 0.2
        },
        default_exclude_types=["daily"],
        chunking_enabled=True,
        show_chunk_context=False
    )
}


def get_profile(name: str) -> SearchProfile:
    """
    Get a search profile by name.

    Args:
        name: Profile name (repos, recent, deep, keywords, default)

    Returns:
        SearchProfile instance

    Raises:
        KeyError: If profile name not found
    """
    if name not in SEARCH_PROFILES:
        raise KeyError(f"Unknown profile: {name}. Available profiles: {list(SEARCH_PROFILES.keys())}")

    return SEARCH_PROFILES[name]


def list_profiles() -> List[Dict[str, str]]:
    """
    List all available search profiles.

    Returns:
        List of dicts with profile metadata (name, display_name, description)
    """
    return [
        {
            "name": profile.name,
            "display_name": profile.display_name,
            "description": profile.description
        }
        for profile in SEARCH_PROFILES.values()
    ]


def load_custom_profiles(config: Dict[str, Any]) -> None:
    """
    Load custom profiles from configuration.

    Args:
        config: Configuration dict with 'search_profiles' section
    """
    if "search_profiles" not in config:
        return

    for name, profile_config in config["search_profiles"].items():
        # Skip if it would override built-in profile
        if name in SEARCH_PROFILES:
            print(f"Warning: Skipping custom profile '{name}' - name conflicts with built-in profile")
            continue

        # Create SearchProfile from config
        try:
            profile = SearchProfile(
                name=name,
                display_name=profile_config.get("display_name", name.title()),
                description=profile_config.get("description", "Custom search profile"),
                hybrid_weight=profile_config.get("hybrid_weight", 0.5),
                bm25_boost=profile_config.get("bm25_boost", 1.0),
                metadata_boost=profile_config.get("metadata_boost", {}),
                time_decay_config=profile_config.get("time_decay_config"),
                max_age_days=profile_config.get("max_age_days"),
                cross_encoder_enabled=profile_config.get("cross_encoder_enabled", True),
                query_expansion_enabled=profile_config.get("query_expansion_enabled", False),
                default_include_types=profile_config.get("default_include_types"),
                default_exclude_types=profile_config.get("default_exclude_types"),
                chunking_enabled=profile_config.get("chunking_enabled", True),
                chunk_size=profile_config.get("chunk_size", 2000),
                chunk_overlap=profile_config.get("chunk_overlap", 400),
                show_chunk_context=profile_config.get("show_chunk_context", False),
                max_results_per_file=profile_config.get("max_results_per_file", 1)
            )

            SEARCH_PROFILES[name] = profile
            print(f"Loaded custom profile: {name}")

        except Exception as e:
            print(f"Error loading custom profile '{name}': {e}")
