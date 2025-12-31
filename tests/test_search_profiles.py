"""Tests for search profile system"""

import pytest
from src.temoa.search_profiles import (
    SearchProfile,
    SEARCH_PROFILES,
    get_profile,
    list_profiles,
    load_custom_profiles
)


def test_built_in_profiles_exist():
    """Test that all expected built-in profiles are defined"""
    expected_profiles = ['repos', 'recent', 'deep', 'keywords', 'default']

    for profile_name in expected_profiles:
        assert profile_name in SEARCH_PROFILES
        profile = SEARCH_PROFILES[profile_name]
        assert isinstance(profile, SearchProfile)
        assert profile.name == profile_name
        assert profile.display_name
        assert profile.description


def test_get_profile():
    """Test retrieving profiles by name"""
    # Valid profile
    repos_profile = get_profile('repos')
    assert repos_profile.name == 'repos'
    assert repos_profile.display_name == 'Repos & Tech'
    assert repos_profile.hybrid_weight == 0.3
    assert repos_profile.bm25_boost == 2.0

    # Invalid profile should raise KeyError
    with pytest.raises(KeyError):
        get_profile('nonexistent')


def test_repos_profile():
    """Test repos profile configuration"""
    profile = get_profile('repos')

    # Should prefer BM25 over semantic
    assert profile.hybrid_weight == 0.3  # 30% semantic, 70% BM25
    assert profile.bm25_boost == 2.0

    # Should have metadata boosting enabled
    assert 'github_stars' in profile.metadata_boost
    assert profile.metadata_boost['github_stars']['enabled']
    assert 'github_topics' in profile.metadata_boost
    assert 'github_language' in profile.metadata_boost

    # Should disable time decay (recency doesn't matter for repos)
    assert profile.time_decay_config is None

    # Should disable cross-encoder for speed
    assert profile.cross_encoder_enabled is False

    # Should only search gleanings by default
    assert profile.default_include_types == ['gleaning']

    # Gleanings are small, no chunking needed
    assert profile.chunking_enabled is False


def test_recent_profile():
    """Test recent profile configuration"""
    profile = get_profile('recent')

    # Balanced hybrid
    assert profile.hybrid_weight == 0.5

    # Aggressive time decay
    assert profile.time_decay_config is not None
    assert profile.time_decay_config['half_life_days'] == 7  # Prefer this week
    assert profile.time_decay_config['max_boost'] == 0.5  # Up to 50% boost

    # Hard age cutoff
    assert profile.max_age_days == 90

    # Should search recent content types
    assert 'daily' in profile.default_include_types
    assert 'note' in profile.default_include_types

    # Daily notes can be long
    assert profile.chunking_enabled is True


def test_deep_profile():
    """Test deep reading profile configuration"""
    profile = get_profile('deep')

    # Prefer semantic over BM25
    assert profile.hybrid_weight == 0.8  # 80% semantic, 20% BM25

    # Precision over speed
    assert profile.cross_encoder_enabled is True

    # Chunking enabled for long content
    assert profile.chunking_enabled is True
    assert profile.chunk_size == 2000
    assert profile.chunk_overlap == 400

    # Show chunk context
    assert profile.show_chunk_context is True
    assert profile.max_results_per_file == 3  # Top 3 chunks per file

    # Exclude short content types
    assert 'daily' in profile.default_exclude_types
    assert 'gleaning' in profile.default_exclude_types


def test_keywords_profile():
    """Test keywords profile configuration"""
    profile = get_profile('keywords')

    # Prefer BM25 over semantic
    assert profile.hybrid_weight == 0.2  # 20% semantic, 80% BM25
    assert profile.bm25_boost == 1.5

    # Speed over precision
    assert profile.cross_encoder_enabled is False
    assert profile.query_expansion_enabled is False


def test_default_profile():
    """Test default profile (current behavior)"""
    profile = get_profile('default')

    # Balanced
    assert profile.hybrid_weight == 0.5
    assert profile.bm25_boost == 1.0

    # All features enabled
    assert profile.cross_encoder_enabled is True
    assert profile.chunking_enabled is True

    # Standard time decay
    assert profile.time_decay_config is not None
    assert profile.time_decay_config['half_life_days'] == 90
    assert profile.time_decay_config['max_boost'] == 0.2

    # Exclude daily notes by default
    assert profile.default_exclude_types == ['daily']


def test_list_profiles():
    """Test listing all profiles"""
    profiles = list_profiles()

    assert len(profiles) >= 5  # At least 5 built-in profiles

    for p in profiles:
        assert 'name' in p
        assert 'display_name' in p
        assert 'description' in p

    # Check that all built-in profiles are in the list
    profile_names = [p['name'] for p in profiles]
    assert 'repos' in profile_names
    assert 'recent' in profile_names
    assert 'deep' in profile_names
    assert 'keywords' in profile_names
    assert 'default' in profile_names


def test_load_custom_profiles():
    """Test loading custom profiles from configuration"""
    # Save original profiles
    original_profiles = dict(SEARCH_PROFILES)

    try:
        # Load custom profile
        config = {
            "search_profiles": {
                "test_custom": {
                    "display_name": "Test Custom",
                    "description": "Custom test profile",
                    "hybrid_weight": 0.6,
                    "bm25_boost": 1.2
                }
            }
        }

        load_custom_profiles(config)

        # Custom profile should be loaded
        assert 'test_custom' in SEARCH_PROFILES
        custom = get_profile('test_custom')
        assert custom.display_name == "Test Custom"
        assert custom.description == "Custom test profile"
        assert custom.hybrid_weight == 0.6
        assert custom.bm25_boost == 1.2

        # Built-in profiles should still exist
        assert 'repos' in SEARCH_PROFILES
        assert 'default' in SEARCH_PROFILES

    finally:
        # Restore original profiles
        SEARCH_PROFILES.clear()
        SEARCH_PROFILES.update(original_profiles)


def test_load_custom_profiles_no_override_builtin():
    """Test that custom profiles cannot override built-in profiles"""
    # Save original profiles
    original_profiles = dict(SEARCH_PROFILES)

    try:
        # Try to override built-in profile (should be ignored)
        config = {
            "search_profiles": {
                "repos": {  # Built-in profile name
                    "display_name": "Evil Override",
                    "description": "Should not work",
                    "hybrid_weight": 0.9
                }
            }
        }

        load_custom_profiles(config)

        # Built-in profile should be unchanged
        repos = get_profile('repos')
        assert repos.display_name == 'Repos & Tech'  # Original value
        assert repos.hybrid_weight == 0.3  # Original value

    finally:
        # Restore original profiles
        SEARCH_PROFILES.clear()
        SEARCH_PROFILES.update(original_profiles)
