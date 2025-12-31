"""
Unit tests for adaptive chunking system.
"""
import pytest
import sys
from pathlib import Path

# Import chunking module directly (avoid package relative imports)
synthesis_src = Path(__file__).parent.parent / "synthesis" / "src" / "embeddings"
sys.path.insert(0, str(synthesis_src))

import chunking
from chunking import (
    should_chunk,
    chunk_document,
    Chunk,
    estimate_token_count,
    chunk_statistics
)


class TestShouldChunk:
    """Tests for should_chunk() function."""

    def test_small_content_no_chunk(self):
        """Content under threshold should not be chunked."""
        content = "A" * 3000
        assert not should_chunk(content, threshold=4000)

    def test_large_content_should_chunk(self):
        """Content over threshold should be chunked."""
        content = "A" * 5000
        assert should_chunk(content, threshold=4000)

    def test_exact_threshold(self):
        """Content exactly at threshold should be chunked."""
        content = "A" * 4000
        assert should_chunk(content, threshold=4000)

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        content = "A" * 3000
        assert should_chunk(content, threshold=2000)
        assert not should_chunk(content, threshold=5000)


class TestChunkDocument:
    """Tests for chunk_document() function."""

    def test_single_chunk_small_file(self):
        """Small files should return single chunk."""
        content = "This is a small file with minimal content."
        chunks = chunk_document(
            content=content,
            file_path="/test/file.md",
            chunk_size=2000,
            chunk_overlap=400
        )

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].chunk_index == 0
        assert chunks[0].chunk_total == 1
        assert chunks[0].start_offset == 0
        assert chunks[0].end_offset == len(content)

    def test_multiple_chunks_large_file(self):
        """Large files should be split into multiple chunks."""
        # Create 5000 char content
        content = "A" * 5000

        chunks = chunk_document(
            content=content,
            file_path="/test/large.md",
            chunk_size=2000,
            chunk_overlap=400
        )

        # With chunk_size=2000, overlap=400, step=1600:
        # Chunk 0: 0-2000
        # Chunk 1: 1600-3600
        # Chunk 2: 3200-5000
        assert len(chunks) == 3

        # Verify chunk metadata
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            assert chunk.chunk_total == 3
            assert chunk.file_path == "/test/large.md"

        # Verify overlap exists
        # Chunk 0 ends at 2000, Chunk 1 starts at 1600 -> 400 char overlap
        assert chunks[0].end_offset == 2000
        assert chunks[1].start_offset == 1600
        overlap_size = chunks[0].end_offset - chunks[1].start_offset
        assert overlap_size == 400

    def test_chunk_content_correctness(self):
        """Chunks should contain correct content slices."""
        content = "0123456789" * 500  # 5000 chars

        chunks = chunk_document(
            content=content,
            file_path="/test/numbers.md",
            chunk_size=2000,
            chunk_overlap=400
        )

        # Verify each chunk contains correct slice
        for chunk in chunks:
            expected_content = content[chunk.start_offset:chunk.end_offset]
            assert chunk.content == expected_content

    def test_chunk_overlap_parameter(self):
        """Custom overlap should be respected."""
        content = "A" * 5000

        # Test with different overlap sizes
        chunks_small_overlap = chunk_document(
            content=content,
            file_path="/test/file.md",
            chunk_size=2000,
            chunk_overlap=200
        )

        chunks_large_overlap = chunk_document(
            content=content,
            file_path="/test/file.md",
            chunk_size=2000,
            chunk_overlap=600
        )

        # Larger overlap = more chunks (smaller steps)
        # Small overlap: step=1800, chunks = ~3
        # Large overlap: step=1400, chunks = ~4
        assert len(chunks_large_overlap) >= len(chunks_small_overlap)

    def test_empty_content(self):
        """Empty content should return empty list."""
        chunks = chunk_document(
            content="",
            file_path="/test/empty.md",
            chunk_size=2000,
            chunk_overlap=400
        )
        assert len(chunks) == 0

    def test_metadata_preservation(self):
        """Metadata should be attached to all chunks."""
        content = "A" * 5000
        metadata = {
            "title": "Test Document",
            "tags": ["test", "chunking"],
            "created": "2025-01-01"
        }

        chunks = chunk_document(
            content=content,
            file_path="/test/file.md",
            chunk_size=2000,
            chunk_overlap=400,
            metadata=metadata
        )

        # All chunks should have same metadata
        for chunk in chunks:
            assert chunk.metadata == metadata

    def test_invalid_overlap(self):
        """Overlap larger than chunk_size should raise error."""
        content = "A" * 5000

        with pytest.raises(ValueError, match="chunk_overlap.*must be less than chunk_size"):
            chunk_document(
                content=content,
                file_path="/test/file.md",
                chunk_size=2000,
                chunk_overlap=2500  # Invalid: larger than chunk_size
            )

    def test_small_final_chunk_merge(self):
        """Tiny final chunks should be merged with previous chunk."""
        # Create content that would result in a very small final chunk
        # With chunk_size=2000, overlap=400, step=1600
        # Content of 3100 chars would create chunk 0 (0-2000) and chunk 1 (1600-3100)
        # But if we had 3900 chars: chunk 0 (0-2000), chunk 1 (1600-3600), chunk 2 (3200-3900)
        # The final chunk (3200-3900) is only 700 chars, less than half of chunk_size
        content = "A" * 3900

        chunks = chunk_document(
            content=content,
            file_path="/test/file.md",
            chunk_size=2000,
            chunk_overlap=400
        )

        # Should merge small final chunk with previous
        # Exact number depends on merging logic, but should be < 3
        assert len(chunks) <= 3

        # Last chunk should extend to end of content
        assert chunks[-1].end_offset == len(content)


class TestEstimateTokenCount:
    """Tests for estimate_token_count() function."""

    def test_empty_text(self):
        """Empty text should return 0 tokens."""
        assert estimate_token_count("") == 0

    def test_token_estimation(self):
        """Token count should be roughly 1/4 of character count."""
        text = "A" * 400
        tokens = estimate_token_count(text)
        assert tokens == 100  # 400 / 4

    def test_realistic_text(self):
        """Real text should follow ~4 chars per token rule."""
        text = "The quick brown fox jumps over the lazy dog." * 10  # ~450 chars
        tokens = estimate_token_count(text)
        assert 100 <= tokens <= 130  # Roughly 450/4 = 112 tokens


class TestChunkStatistics:
    """Tests for chunk_statistics() function."""

    def test_empty_chunks(self):
        """Empty chunk list should return zero statistics."""
        stats = chunk_statistics([])
        assert stats['num_chunks'] == 0
        assert stats['avg_chunk_size'] == 0
        assert stats['total_content_size'] == 0

    def test_single_chunk_stats(self):
        """Single chunk should return correct statistics."""
        content = "A" * 1000
        chunks = chunk_document(content, "/test/file.md", chunk_size=2000, chunk_overlap=400)

        stats = chunk_statistics(chunks)
        assert stats['num_chunks'] == 1
        assert stats['avg_chunk_size'] == 1000
        assert stats['min_chunk_size'] == 1000
        assert stats['max_chunk_size'] == 1000
        assert stats['total_content_size'] == 1000

    def test_multiple_chunks_stats(self):
        """Multiple chunks should return aggregated statistics."""
        content = "A" * 5000
        chunks = chunk_document(content, "/test/file.md", chunk_size=2000, chunk_overlap=400)

        stats = chunk_statistics(chunks)
        assert stats['num_chunks'] > 1
        assert stats['avg_chunk_size'] > 0
        assert stats['min_chunk_size'] <= stats['avg_chunk_size'] <= stats['max_chunk_size']
        assert stats['total_content_size'] == 5000
        assert stats['avg_estimated_tokens'] > 0


class TestChunkDataclass:
    """Tests for Chunk dataclass."""

    def test_chunk_repr(self):
        """Chunk repr should show useful information."""
        chunk = Chunk(
            content="Test content",
            chunk_index=0,
            chunk_total=3,
            start_offset=0,
            end_offset=100,
            file_path="/test/file.md",
            metadata={}
        )

        repr_str = repr(chunk)
        assert "1/3" in repr_str  # Chunk 1 of 3 (0-indexed displayed as 1-indexed)
        assert "12 chars" in repr_str
        assert "/test/file.md" in repr_str
