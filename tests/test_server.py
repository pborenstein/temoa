"""Tests for FastAPI server endpoints"""
import pytest
from fastapi.testclient import TestClient
from ixpantilia.server import app

client = TestClient(app)


def test_root_endpoint():
    """Test that root endpoint serves UI or placeholder"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Ixpantilia" in response.text


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "synthesis" in data
    assert data["status"] in ["healthy", "unhealthy"]


def test_search_endpoint_basic():
    """Test basic search endpoint"""
    response = client.get("/search?q=test")
    assert response.status_code == 200

    data = response.json()
    assert "query" in data
    assert "results" in data
    assert "total" in data
    assert "model" in data
    assert data["query"] == "test"


def test_search_endpoint_with_limit():
    """Test search with limit parameter"""
    response = client.get("/search?q=test&limit=5")
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) <= 5


def test_search_endpoint_missing_query():
    """Test that search without query returns error"""
    response = client.get("/search")
    assert response.status_code == 422  # Validation error


def test_search_endpoint_empty_query():
    """Test that search with empty query returns error"""
    response = client.get("/search?q=")
    assert response.status_code == 422  # Validation error (min_length=1)


def test_search_endpoint_invalid_limit():
    """Test that invalid limit values are handled"""
    # Negative limit
    response = client.get("/search?q=test&limit=-1")
    assert response.status_code == 422

    # Zero limit
    response = client.get("/search?q=test&limit=0")
    assert response.status_code == 422


def test_search_result_structure():
    """Test that search results have expected structure"""
    response = client.get("/search?q=semantic+search&limit=1")
    assert response.status_code == 200

    data = response.json()

    # If results found, verify structure
    if data["results"]:
        result = data["results"][0]
        assert "title" in result
        assert "relative_path" in result
        assert "similarity_score" in result
        assert "obsidian_uri" in result
        assert result["obsidian_uri"].startswith("obsidian://vault/")


def test_stats_endpoint():
    """Test stats endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200

    data = response.json()
    # Should have either file_count or total_files
    assert "file_count" in data or "total_files" in data


def test_openapi_docs():
    """Test that OpenAPI docs are available"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
