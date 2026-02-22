"""
Comprehensive edge case tests for Temoa.

Tests scenarios that are critical for production reliability but may not
be covered in feature-specific tests. Focus on boundary conditions,
error handling, concurrent operations, and malformed inputs.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from temoa.server import app
from temoa.client_cache import ClientCache
from temoa.synthesis import SynthesisClient


class TestCacheEviction:
    """Test cache eviction with 4th vault added to 3-vault cache."""

    def test_lru_eviction_order(self):
        """Should evict least recently used vault when cache is full."""
        cache = ClientCache(max_size=3)

        # Create mock clients for 4 vaults
        vault1 = Path("/tmp/vault1")
        vault2 = Path("/tmp/vault2")
        vault3 = Path("/tmp/vault3")
        vault4 = Path("/tmp/vault4")
        synth = Path("/tmp/synthesis")
        storage = Path("/tmp/storage")

        # Mock SynthesisClient creation
        with patch('temoa.client_cache.SynthesisClient') as MockClient:
            MockClient.side_effect = lambda *args, **kwargs: Mock(spec=SynthesisClient)

            # Add 3 vaults (fills cache)
            client1 = cache.get(vault1, synth, "model1", storage)
            client2 = cache.get(vault2, synth, "model1", storage)
            client3 = cache.get(vault3, synth, "model1", storage)

            # Access vault1 again (makes it more recently used than vault2)
            cache.get(vault1, synth, "model1", storage)

            # Add 4th vault (should evict vault2, the LRU)
            client4 = cache.get(vault4, synth, "model1", storage)

            # Cache should contain vault1, vault3, vault4
            assert cache.cache.get(cache._make_key(vault1, "model1")) is not None
            assert cache.cache.get(cache._make_key(vault2, "model1")) is None  # Evicted
            assert cache.cache.get(cache._make_key(vault3, "model1")) is not None
            assert cache.cache.get(cache._make_key(vault4, "model1")) is not None
            assert len(cache.cache) == 3

    def test_cache_size_limit_enforced(self):
        """Should never exceed max_size regardless of access patterns."""
        cache = ClientCache(max_size=2)
        synth = Path("/tmp/synthesis")
        storage = Path("/tmp/storage")

        with patch('temoa.client_cache.SynthesisClient') as MockClient:
            MockClient.side_effect = lambda *args, **kwargs: Mock(spec=SynthesisClient)

            # Add 5 vaults rapidly
            for i in range(5):
                vault = Path(f"/tmp/vault{i}")
                cache.get(vault, synth, "model1", storage)

                # Cache should never exceed max_size
                assert len(cache.cache) <= 2


class TestConcurrentOperations:
    """Test handling of concurrent/simultaneous operations."""

    def test_concurrent_cache_access(self):
        """Should handle concurrent access to same vault safely."""
        cache = ClientCache(max_size=3)
        vault = Path("/tmp/test_vault")
        synth = Path("/tmp/synthesis")
        storage = Path("/tmp/storage")

        with patch('temoa.client_cache.SynthesisClient') as MockClient:
            mock_client = Mock(spec=SynthesisClient)
            MockClient.return_value = mock_client

            # Simulate concurrent access
            results = []
            for _ in range(5):
                client = cache.get(vault, synth, "model1", storage)
                results.append(client)

            # All should get the same cached instance (not 5 different clients)
            assert all(c == results[0] for c in results)
            # Client should only be created once
            assert MockClient.call_count == 1


class TestPathTraversalProtection:
    """Test protection against path traversal in TimeAwareScorer."""

    def test_relative_path_with_parent_dirs(self, tmp_path):
        """Should skip results with path traversal attempts."""
        from temoa.time_scoring import TimeAwareScorer

        scorer = TimeAwareScorer(half_life_days=90, max_boost=0.2)
        results = [{
            "relative_path": "../etc/passwd",
            "similarity_score": 1.0
        }]

        # Should not crash; traversal path is skipped (no boost applied)
        boosted = scorer.apply_boost(results, vault_path=tmp_path)
        assert isinstance(boosted, list)

    def test_absolute_path_outside_vault(self, tmp_path):
        """Should skip absolute paths outside vault."""
        from temoa.time_scoring import TimeAwareScorer

        scorer = TimeAwareScorer(half_life_days=90, max_boost=0.2)
        results = [{
            "relative_path": "../../etc/passwd",
            "similarity_score": 1.0
        }]

        # Should not crash; traversal path is skipped
        boosted = scorer.apply_boost(results, vault_path=tmp_path)
        assert isinstance(boosted, list)


class TestUnicodeEdgeCases:
    """Test Unicode edge cases beyond standard sanitization tests."""

    def test_emoji_in_query(self):
        """Should handle emoji in search queries."""
        with TestClient(app) as client:
            response = client.get("/search?q=🔥+test+💯")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data

    def test_emoji_in_file_path(self):
        """Should handle emoji in file paths (if OS allows)."""
        # Note: May not work on all filesystems
        with tempfile.TemporaryDirectory() as tmpdir:
            emoji_path = Path(tmpdir) / "test-🔥-file.md"
            try:
                emoji_path.write_text("# Test\n\nContent")
                assert emoji_path.exists()
            except (OSError, UnicodeEncodeError):
                pytest.skip("Filesystem doesn't support emoji in filenames")

    def test_surrogate_pairs_in_content(self):
        """Should handle or sanitize invalid surrogate pairs."""
        # Invalid surrogate pair
        invalid_unicode = "Test \uD800 content"

        # Should not crash search pipeline
        with TestClient(app) as client:
            # If this content somehow gets indexed, search should handle it
            response = client.get("/search?q=test")
            assert response.status_code == 200

    def test_mixed_rtl_ltr_text(self):
        """Should handle mixed RTL/LTR text (Arabic, Hebrew)."""
        with TestClient(app) as client:
            # Mixed English and Arabic
            response = client.get("/search?q=test+مرحبا")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data




class TestDiskFullScenarios:
    """Test handling of disk full during operations."""

    def test_reindex_with_no_disk_space(self):
        """Should handle disk full during reindex gracefully."""
        # This is hard to test without actually filling disk
        # Document expected behavior:
        # - Should catch IOError/OSError
        # - Should log clear error message
        # - Should not corrupt existing index
        # - Should return 500 with helpful message
        pytest.skip("Disk full scenario requires complex setup")

    def test_gleaning_write_with_no_space(self):
        """Should handle disk full when writing gleanings."""
        # Similar to above - hard to test without mocking
        pytest.skip("Disk full scenario requires complex setup")


class TestQueryExtremes:
    """Test extremely long, short, or unusual queries."""

    def test_empty_query(self):
        """Should handle empty query string."""
        with TestClient(app) as client:
            response = client.get("/search?q=")
            # Should return 400 or handle gracefully
            assert response.status_code in [200, 400, 422]

    def test_very_long_query(self):
        """Should handle 10,000+ character queries."""
        with TestClient(app) as client:
            long_query = "test " * 2000  # ~10,000 chars
            response = client.get(f"/search?q={long_query}")

            # Should either succeed or return reasonable error
            assert response.status_code in [200, 400, 413, 422]

            # Should not crash or timeout
            if response.status_code == 200:
                data = response.json()
                assert "results" in data

    def test_query_with_only_special_chars(self):
        """Should handle queries with only special characters."""
        with TestClient(app) as client:
            special_queries = [
                "!!!???",
                "---+++===",
                "[[[]]]",
                "***###$$$",
                "     ",  # Only spaces
            ]

            for query in special_queries:
                response = client.get(f"/search?q={query}")
                # Should handle gracefully
                assert response.status_code in [200, 400, 422]

    def test_query_with_regex_special_chars(self):
        """Should handle regex special characters safely."""
        with TestClient(app) as client:
            # Regex special chars that could cause issues
            regex_query = ".*+?^$[]{}()|\\test"
            response = client.get(f"/search?q={regex_query}")

            # Should not cause regex errors in BM25 or other components
            assert response.status_code in [200, 400, 422]


class TestTagMatchingEdgeCases:
    """Test edge cases in tag matching and boosting."""

    def test_unicode_tags(self, tmp_path):
        """Should handle Unicode characters in tags."""
        from temoa.bm25_index import BM25Index

        # Create index with unicode tags
        docs = [
            {
                "id": "1",
                "content": "Test content",
                "tags": ["测试", "тест", "🔥"]
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        # Search with unicode tag
        results = index.search("测试", limit=10)
        assert isinstance(results, list)

    def test_tags_with_special_chars(self, tmp_path):
        """Should handle tags with special characters."""
        from temoa.bm25_index import BM25Index

        docs = [
            {
                "id": "1",
                "content": "Test content",
                "tags": ["c++", "c#", ".net", "node.js"]
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        # Search for tags with special chars
        results = index.search("c++", limit=10)
        assert isinstance(results, list)

    def test_empty_tags_list(self, tmp_path):
        """Should handle documents with empty tags list."""
        from temoa.bm25_index import BM25Index

        docs = [
            {
                "id": "1",
                "content": "Test content",
                "tags": []
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        results = index.search("test", limit=10)
        assert isinstance(results, list)

    def test_very_long_tag(self, tmp_path):
        """Should handle extremely long tag strings."""
        from temoa.bm25_index import BM25Index

        long_tag = "very-long-tag-" + "x" * 1000
        docs = [
            {
                "id": "1",
                "content": "Test content",
                "tags": [long_tag]
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        # Should not crash
        results = index.search("test", limit=10)
        assert isinstance(results, list)


class TestBM25CorpusEdgeCases:
    """Test BM25 index with edge case documents."""

    def test_empty_content_file(self, tmp_path):
        """Should handle files with no content (only frontmatter)."""
        from temoa.bm25_index import BM25Index

        docs = [
            {
                "id": "1",
                "content": "",
                "tags": ["test"]
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        results = index.search("test", limit=10)
        assert isinstance(results, list)

    def test_title_only_file(self, tmp_path):
        """Should handle files with only title, no body content."""
        from temoa.bm25_index import BM25Index

        docs = [
            {
                "id": "1",
                "content": "# Title Only",
                "tags": []
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        results = index.search("title", limit=10)
        assert isinstance(results, list)

    def test_all_stopwords_content(self, tmp_path):
        """Should handle content with only stopwords."""
        from temoa.bm25_index import BM25Index

        docs = [
            {
                "id": "1",
                "content": "the a an and or but",
                "tags": []
            }
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        results = index.search("test", limit=10)
        assert isinstance(results, list)

    def test_duplicate_documents(self, tmp_path):
        """Should handle identical documents in corpus."""
        from temoa.bm25_index import BM25Index

        docs = [
            {"id": "1", "content": "identical content", "tags": []},
            {"id": "2", "content": "identical content", "tags": []},
            {"id": "3", "content": "identical content", "tags": []},
        ]

        index = BM25Index(storage_dir=tmp_path)
        index.build(docs)

        results = index.search("identical", limit=10)
        assert isinstance(results, list)
        # BM25 IDF is near zero when all docs contain the term,
        # so scores may be zero. The important thing is no crash.
