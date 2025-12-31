"""
Adaptive chunking system for large documents.

Splits documents larger than the embedding model's token limit into
overlapping chunks to ensure full document coverage in semantic search.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a document chunk with metadata."""

    content: str
    chunk_index: int  # 0-based index of this chunk
    chunk_total: int  # Total number of chunks for this document
    start_offset: int  # Character offset in original document
    end_offset: int  # Character offset in original document
    file_path: str  # Original file path
    metadata: Dict[str, Any]  # Additional metadata (frontmatter, etc.)

    def __repr__(self):
        return f"Chunk({self.chunk_index + 1}/{self.chunk_total}, {len(self.content)} chars, {self.file_path})"


def should_chunk(content: str, threshold: int = 4000) -> bool:
    """
    Determine if content needs chunking.

    Args:
        content: Full document text
        threshold: Minimum chars before chunking (default: 4000)
                  This is conservative - embedding models have ~512 token limit
                  which is roughly 2,500 chars. Setting threshold at 4,000 ensures
                  we only chunk files that truly need it.

    Returns:
        True if content exceeds threshold
    """
    return len(content) >= threshold


def chunk_document(
    content: str,
    file_path: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 400,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Chunk]:
    """
    Split document into overlapping chunks.

    Strategy:
    - Use sliding window with overlap to preserve context at chunk boundaries
    - Chunk size of 2,000 chars stays well within 512 token limit (~2,500 chars)
    - Overlap of 400 chars ensures sentences split across boundaries appear in both chunks

    Args:
        content: Full document text
        file_path: Path to original file
        chunk_size: Target size for each chunk in characters (default: 2000)
        chunk_overlap: Number of overlapping characters between chunks (default: 400)
        metadata: Optional metadata to attach to each chunk

    Returns:
        List of Chunk objects

    Example:
        Content: 5000 chars, chunk_size=2000, overlap=400
        - Chunk 0: chars 0-2000
        - Chunk 1: chars 1600-3600  (overlap: 1600-2000)
        - Chunk 2: chars 3200-5000  (overlap: 3200-3600)
    """
    if not content or not content.strip():
        logger.warning(f"Empty content for {file_path}, skipping chunking")
        return []

    metadata = metadata or {}
    content_length = len(content)

    # If content fits in one chunk, return single chunk
    if content_length <= chunk_size:
        return [
            Chunk(
                content=content,
                chunk_index=0,
                chunk_total=1,
                start_offset=0,
                end_offset=content_length,
                file_path=file_path,
                metadata=metadata
            )
        ]

    # Calculate number of chunks needed
    # Formula: For content of length L with chunk size C and overlap O:
    # Each chunk advances by (C - O) characters
    # Number of chunks = ceil((L - C) / (C - O)) + 1
    step_size = chunk_size - chunk_overlap

    if step_size <= 0:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be less than chunk_size ({chunk_size})")

    chunks = []
    start = 0
    chunk_index = 0

    while start < content_length:
        end = min(start + chunk_size, content_length)
        chunk_content = content[start:end]

        # Don't create tiny final chunks - merge with previous
        if chunk_index > 0 and (content_length - start) < (chunk_size // 2):
            # Extend previous chunk to include remaining content
            prev_chunk = chunks[-1]
            extended_content = content[prev_chunk.start_offset:content_length]
            chunks[-1] = Chunk(
                content=extended_content,
                chunk_index=prev_chunk.chunk_index,
                chunk_total=prev_chunk.chunk_total,  # Will update later
                start_offset=prev_chunk.start_offset,
                end_offset=content_length,
                file_path=file_path,
                metadata=metadata
            )
            break

        chunks.append(
            Chunk(
                content=chunk_content,
                chunk_index=chunk_index,
                chunk_total=0,  # Will update after all chunks created
                start_offset=start,
                end_offset=end,
                file_path=file_path,
                metadata=metadata
            )
        )

        chunk_index += 1
        start += step_size

    # Update chunk_total for all chunks
    total = len(chunks)
    for chunk in chunks:
        chunk.chunk_total = total

    logger.debug(f"Chunked {file_path}: {content_length} chars -> {total} chunks")

    return chunks


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text.

    Rule of thumb: 1 token ≈ 4 characters for English text
    This is approximate - actual tokenization varies by model.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    return len(text) // 4


def chunk_statistics(chunks: List[Chunk]) -> Dict[str, Any]:
    """
    Calculate statistics for a list of chunks.

    Args:
        chunks: List of Chunk objects

    Returns:
        Dictionary with statistics
    """
    if not chunks:
        return {
            "num_chunks": 0,
            "avg_chunk_size": 0,
            "min_chunk_size": 0,
            "max_chunk_size": 0,
            "total_content_size": 0,
            "avg_estimated_tokens": 0
        }

    chunk_sizes = [len(c.content) for c in chunks]

    # Total content size is the maximum end_offset (for multi-chunk files)
    # or the end_offset of the single chunk
    total_size = max(c.end_offset for c in chunks) if chunks else 0

    return {
        "num_chunks": len(chunks),
        "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
        "min_chunk_size": min(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
        "total_content_size": total_size,
        "avg_estimated_tokens": sum(estimate_token_count(c.content) for c in chunks) / len(chunks)
    }
