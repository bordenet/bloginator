"""Text chunking strategies for document processing."""

import re
import uuid

from bloginator.models import Chunk


def chunk_text_fixed_size(
    text: str,
    document_id: str,
    chunk_size: int = 512,
    overlap: int = 50,
    section_heading: str | None = None,
) -> list[Chunk]:
    """Chunk text into fixed-size chunks with overlap.

    Chunks text by character count with configurable overlap to
    preserve context across chunk boundaries.

    Args:
        text: Text content to chunk
        document_id: ID of parent document
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        section_heading: Optional section heading for all chunks

    Returns:
        List of Chunk objects

    Raises:
        ValueError: If chunk_size or overlap are invalid
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be less than chunk_size")

    chunks: list[Chunk] = []
    chunk_index = 0
    start = 0

    while start < len(text):
        # Calculate end position
        end = min(start + chunk_size, len(text))

        # Extract chunk content
        content = text[start:end].strip()

        if content:  # Only create chunk if there's content
            chunk = Chunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=content,
                chunk_index=chunk_index,
                section_heading=section_heading,
                char_start=start,
                char_end=end,
            )
            chunks.append(chunk)
            chunk_index += 1

        # Move to next chunk with overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks


def chunk_text_by_paragraphs(
    text: str, document_id: str, max_chunk_size: int = 1000
) -> list[Chunk]:
    """Chunk text by paragraphs.

    Splits text into paragraphs (double newlines) and groups them into
    chunks that don't exceed max_chunk_size. Preserves natural boundaries.

    Args:
        text: Text content to chunk
        document_id: ID of parent document
        max_chunk_size: Maximum size of each chunk in characters

    Returns:
        List of Chunk objects
    """
    # Split into paragraphs (double newline or more)
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: list[Chunk] = []
    chunk_index = 0
    current_chunk_parts: list[str] = []
    current_size = 0
    char_start = 0

    for para in paragraphs:
        para_size = len(para)

        # If single paragraph exceeds max size, split it
        if para_size > max_chunk_size:
            # Flush current chunk first
            if current_chunk_parts:
                content = "\n\n".join(current_chunk_parts)
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=content,
                    chunk_index=chunk_index,
                    section_heading=None,
                    char_start=char_start,
                    char_end=char_start + len(content),
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk_parts = []
                current_size = 0
                char_start += len(content)

            # Split large paragraph by sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sent in sentences:
                sent = sent.strip()
                if sent:
                    if current_size + len(sent) > max_chunk_size and current_chunk_parts:
                        # Flush current chunk
                        content = " ".join(current_chunk_parts)
                        chunk = Chunk(
                            id=str(uuid.uuid4()),
                            document_id=document_id,
                            content=content,
                            chunk_index=chunk_index,
                            section_heading=None,
                            char_start=char_start,
                            char_end=char_start + len(content),
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                        current_chunk_parts = []
                        current_size = 0
                        char_start += len(content)

                    current_chunk_parts.append(sent)
                    current_size += len(sent) + 1  # +1 for space
        else:
            # Normal paragraph
            if current_size + para_size > max_chunk_size and current_chunk_parts:
                # Flush current chunk
                content = "\n\n".join(current_chunk_parts)
                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    content=content,
                    chunk_index=chunk_index,
                    section_heading=None,
                    char_start=char_start,
                    char_end=char_start + len(content),
                )
                chunks.append(chunk)
                chunk_index += 1
                current_chunk_parts = []
                current_size = 0
                char_start += len(content)

            current_chunk_parts.append(para)
            current_size += para_size + 2  # +2 for double newline

    # Flush remaining chunk
    if current_chunk_parts:
        content = "\n\n".join(current_chunk_parts)
        chunk = Chunk(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            section_heading=None,
            char_start=char_start,
            char_end=char_start + len(content),
        )
        chunks.append(chunk)

    return chunks


def chunk_text_by_sentences(
    text: str, document_id: str, sentences_per_chunk: int = 5
) -> list[Chunk]:
    """Chunk text by sentences.

    Groups sentences into chunks of approximately sentences_per_chunk sentences.

    Args:
        text: Text content to chunk
        document_id: ID of parent document
        sentences_per_chunk: Target number of sentences per chunk

    Returns:
        List of Chunk objects
    """
    # Split into sentences (simplified - real implementation might need better splitting)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    chunk_index = 0
    char_position = 0

    for i in range(0, len(sentences), sentences_per_chunk):
        chunk_sentences = sentences[i : i + sentences_per_chunk]
        content = " ".join(chunk_sentences)

        if content.strip():
            chunk = Chunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                content=content,
                chunk_index=chunk_index,
                section_heading=None,
                char_start=char_position,
                char_end=char_position + len(content),
            )
            chunks.append(chunk)
            chunk_index += 1
            char_position += len(content) + 1  # +1 for space

    return chunks
