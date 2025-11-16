"""Tests for text chunking."""

import pytest

from bloginator.extraction.chunking import (
    chunk_text_by_paragraphs,
    chunk_text_by_sentences,
    chunk_text_fixed_size,
)


class TestChunkTextFixedSize:
    """Test fixed-size chunking."""

    def test_chunk_text_fixed_size_basic(self) -> None:
        """Test basic fixed-size chunking."""
        text = "a" * 1000  # 1000 characters
        chunks = chunk_text_fixed_size(text, "doc_1", chunk_size=300, overlap=50)

        # Should create 4 chunks: 0-300, 250-550, 500-800, 750-1000
        assert len(chunks) >= 3
        assert all(c.document_id == "doc_1" for c in chunks)
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_chunk_text_fixed_size_no_overlap(self) -> None:
        """Test fixed-size chunking without overlap."""
        text = "a" * 1000
        chunks = chunk_text_fixed_size(text, "doc_1", chunk_size=250, overlap=0)

        # Should create 4 chunks: 0-250, 250-500, 500-750, 750-1000
        assert len(chunks) == 4
        assert chunks[0].char_end - chunks[0].char_start <= 250
        assert chunks[1].char_start == chunks[0].char_end

    def test_chunk_text_fixed_size_invalid_params(self) -> None:
        """Test that invalid parameters raise errors."""
        text = "test"

        with pytest.raises(ValueError):
            chunk_text_fixed_size(text, "doc_1", chunk_size=0)

        with pytest.raises(ValueError):
            chunk_text_fixed_size(text, "doc_1", chunk_size=100, overlap=-1)

        with pytest.raises(ValueError):
            chunk_text_fixed_size(text, "doc_1", chunk_size=100, overlap=100)

    def test_chunk_text_fixed_size_short_text(self) -> None:
        """Test chunking text shorter than chunk_size."""
        text = "Short text"
        chunks = chunk_text_fixed_size(text, "doc_1", chunk_size=100)

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_text_fixed_size_with_heading(self) -> None:
        """Test chunking with section heading."""
        text = "Content here"
        chunks = chunk_text_fixed_size(
            text, "doc_1", chunk_size=100, section_heading="Introduction"
        )

        assert len(chunks) == 1
        assert chunks[0].section_heading == "Introduction"


class TestChunkTextByParagraphs:
    """Test paragraph-based chunking."""

    def test_chunk_text_by_paragraphs_single_para(self) -> None:
        """Test chunking single paragraph."""
        text = "This is a single paragraph."
        chunks = chunk_text_by_paragraphs(text, "doc_1")

        assert len(chunks) == 1
        assert chunks[0].content == text

    def test_chunk_text_by_paragraphs_multiple_paras(self) -> None:
        """Test chunking multiple paragraphs."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = chunk_text_by_paragraphs(text, "doc_1", max_chunk_size=100)

        assert len(chunks) >= 1
        assert all(c.document_id == "doc_1" for c in chunks)

    def test_chunk_text_by_paragraphs_large_para(self) -> None:
        """Test chunking with paragraph exceeding max size."""
        # Create a large paragraph
        large_para = "Sentence. " * 200  # ~2000 chars
        text = f"Small para.\n\n{large_para}\n\nAnother small para."

        chunks = chunk_text_by_paragraphs(text, "doc_1", max_chunk_size=500)

        # Large paragraph should be split
        assert len(chunks) > 2

    def test_chunk_text_by_paragraphs_sequential_indices(self) -> None:
        """Test that chunk indices are sequential."""
        text = "Para 1.\n\nPara 2.\n\nPara 3."
        chunks = chunk_text_by_paragraphs(text, "doc_1")

        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))


class TestChunkTextBySentences:
    """Test sentence-based chunking."""

    def test_chunk_text_by_sentences_basic(self) -> None:
        """Test basic sentence chunking."""
        text = "Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5. Sentence 6."
        chunks = chunk_text_by_sentences(text, "doc_1", sentences_per_chunk=2)

        # Should create 3 chunks (6 sentences / 2 per chunk)
        assert len(chunks) == 3
        assert all(c.document_id == "doc_1" for c in chunks)

    def test_chunk_text_by_sentences_single_sentence(self) -> None:
        """Test chunking single sentence."""
        text = "Single sentence."
        chunks = chunk_text_by_sentences(text, "doc_1", sentences_per_chunk=5)

        assert len(chunks) == 1
        assert chunks[0].content.strip() == text

    def test_chunk_text_by_sentences_various_punctuation(self) -> None:
        """Test chunking with various sentence endings."""
        text = "Question? Exclamation! Normal sentence. Another one."
        chunks = chunk_text_by_sentences(text, "doc_1", sentences_per_chunk=2)

        assert len(chunks) == 2

    def test_chunk_text_by_sentences_sequential_indices(self) -> None:
        """Test that chunk indices are sequential."""
        text = "S1. S2. S3. S4."
        chunks = chunk_text_by_sentences(text, "doc_1", sentences_per_chunk=1)

        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))
