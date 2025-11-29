"""Tests for cross-encoder reranker."""

import pytest
from temoa.reranker import CrossEncoderReranker


def test_reranker_initialization():
    """Test that cross-encoder loads successfully."""
    reranker = CrossEncoderReranker()
    assert reranker.model is not None
    assert reranker.model_name == 'cross-encoder/ms-marco-MiniLM-L-6-v2'


def test_rerank_empty_results():
    """Test reranking with no results returns empty list."""
    reranker = CrossEncoderReranker()
    results = reranker.rerank("test query", [])
    assert results == []


def test_rerank_single_result():
    """Test reranking with single result returns that result."""
    reranker = CrossEncoderReranker()
    results = [
        {"title": "Test doc", "content": "Test content", "similarity_score": 0.8}
    ]
    reranked = reranker.rerank("test", results, top_k=1)
    assert len(reranked) == 1
    assert reranked[0]['title'] == "Test doc"
    assert 'cross_encoder_score' in reranked[0]


def test_rerank_improves_ranking():
    """Test that re-ranking changes order to prioritize relevance."""
    reranker = CrossEncoderReranker()

    # Create results where less relevant doc has higher bi-encoder score
    results = [
        {
            "title": "Unrelated document",
            "content": "This document talks about something completely different and unrelated",
            "similarity_score": 0.8
        },
        {
            "title": "Very relevant document",
            "content": "This is exactly about semantic search and how it works",
            "similarity_score": 0.7
        },
    ]

    reranked = reranker.rerank("semantic search", results, top_k=2)

    assert len(reranked) == 2
    # More relevant doc should now be first
    assert reranked[0]['title'] == "Very relevant document"
    # Cross-encoder score should be higher for relevant doc
    assert reranked[0]['cross_encoder_score'] > reranked[1]['cross_encoder_score']


def test_rerank_respects_top_k():
    """Test that reranker returns only top_k results."""
    reranker = CrossEncoderReranker()

    results = [
        {"title": f"Doc {i}", "content": f"Content {i}", "similarity_score": 0.5}
        for i in range(10)
    ]

    reranked = reranker.rerank("test", results, top_k=3)
    assert len(reranked) == 3


def test_rerank_respects_rerank_top_n():
    """Test that reranker only re-ranks top N candidates."""
    reranker = CrossEncoderReranker()

    # Create 50 results
    results = [
        {"title": f"Doc {i}", "content": f"Content {i}", "similarity_score": 0.5}
        for i in range(50)
    ]

    # Re-rank only top 10, return top 5
    reranked = reranker.rerank("test", results, top_k=5, rerank_top_n=10)

    assert len(reranked) == 5
    # All returned results should have cross_encoder_score
    for result in reranked:
        assert 'cross_encoder_score' in result


def test_rerank_uses_content_when_available():
    """Test that reranker uses content field when available."""
    reranker = CrossEncoderReranker()

    results = [
        {
            "title": "Short title",
            "content": "This is a very long and detailed content about semantic search",
            "relative_path": "test.md",
            "similarity_score": 0.7
        }
    ]

    reranked = reranker.rerank("semantic search", results, top_k=1)
    assert 'cross_encoder_score' in reranked[0]


def test_rerank_falls_back_to_title_path():
    """Test that reranker uses title+path when content unavailable."""
    reranker = CrossEncoderReranker()

    results = [
        {
            "title": "Document about semantic search",
            "relative_path": "notes/semantic_search.md",
            # No content field
            "similarity_score": 0.7
        }
    ]

    reranked = reranker.rerank("semantic search", results, top_k=1)
    assert 'cross_encoder_score' in reranked[0]


def test_rerank_preserves_original_fields():
    """Test that reranking preserves all original fields."""
    reranker = CrossEncoderReranker()

    results = [
        {
            "title": "Test",
            "content": "Content",
            "similarity_score": 0.7,
            "custom_field": "custom_value",
            "tags": ["tag1", "tag2"]
        }
    ]

    reranked = reranker.rerank("test", results, top_k=1)

    # All original fields should be preserved
    assert reranked[0]['title'] == "Test"
    assert reranked[0]['content'] == "Content"
    assert reranked[0]['similarity_score'] == 0.7
    assert reranked[0]['custom_field'] == "custom_value"
    assert reranked[0]['tags'] == ["tag1", "tag2"]

    # Cross-encoder score should be added
    assert 'cross_encoder_score' in reranked[0]
