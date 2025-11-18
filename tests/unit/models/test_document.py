"""Tests for document models."""

import json
from datetime import datetime
from pathlib import Path

from bloginator.models import Chunk, Document, QualityRating


class TestQualityRating:
    """Test QualityRating enum."""

    def test_quality_rating_values(self) -> None:
        """Test that QualityRating has expected values."""
        assert QualityRating.PREFERRED == "preferred"
        assert QualityRating.REFERENCE == "standard"
        assert QualityRating.DEPRECATED == "deprecated"

    def test_quality_rating_from_string(self) -> None:
        """Test creating QualityRating from string."""
        rating = QualityRating("preferred")
        assert rating == QualityRating.PREFERRED


class TestDocument:
    """Test Document model."""

    def test_document_creation_minimal(self) -> None:
        """Test creating document with minimal required fields."""
        doc = Document(
            id="test_123",
            filename="blog.md",
            source_path=Path("/corpus/blog.md"),
            format="markdown",
        )

        assert doc.id == "test_123"
        assert doc.filename == "blog.md"
        assert doc.source_path == Path("/corpus/blog.md")
        assert doc.format == "markdown"
        assert doc.quality_rating == QualityRating.REFERENCE
        assert doc.indexed_date is not None
        assert doc.tags == []
        assert doc.is_external_source is False
        assert doc.attribution_required is False
        assert doc.word_count == 0
        assert doc.chunk_ids == []

    def test_document_creation_full(self) -> None:
        """Test creating document with all fields."""
        created = datetime(2020, 1, 15, 10, 30)
        modified = datetime(2020, 1, 16, 14, 45)
        indexed = datetime(2025, 11, 16, 12, 0)

        doc = Document(
            id="test_456",
            filename="guide.pdf",
            source_path=Path("/corpus/guide.pdf"),
            format="pdf",
            created_date=created,
            modified_date=modified,
            indexed_date=indexed,
            quality_rating=QualityRating.PREFERRED,
            tags=["agile", "transformation"],
            is_external_source=True,
            attribution_required=True,
            word_count=5000,
            chunk_ids=["chunk_1", "chunk_2"],
        )

        assert doc.id == "test_456"
        assert doc.filename == "guide.pdf"
        assert doc.quality_rating == QualityRating.PREFERRED
        assert doc.tags == ["agile", "transformation"]
        assert doc.is_external_source is True
        assert doc.attribution_required is True
        assert doc.word_count == 5000
        assert doc.chunk_ids == ["chunk_1", "chunk_2"]

    def test_document_serialization(self) -> None:
        """Test document serialization to/from JSON."""
        doc = Document(
            id="test_789",
            filename="test.md",
            source_path=Path("/test.md"),
            format="markdown",
            quality_rating=QualityRating.PREFERRED,
            tags=["test"],
        )

        # Serialize to JSON
        json_str = doc.model_dump_json()
        json_data = json.loads(json_str)

        # Check enum is serialized as value
        assert json_data["quality_rating"] == "preferred"
        assert json_data["tags"] == ["test"]

        # Deserialize from JSON
        doc2 = Document.model_validate_json(json_str)
        assert doc2.id == doc.id
        assert doc2.filename == doc.filename
        assert doc2.quality_rating == doc.quality_rating

    def test_document_dict_conversion(self) -> None:
        """Test document conversion to/from dict."""
        doc = Document(
            id="test_dict",
            filename="test.md",
            source_path=Path("/test.md"),
            format="markdown",
        )

        # Convert to dict
        doc_dict = doc.model_dump()
        assert isinstance(doc_dict, dict)
        assert doc_dict["id"] == "test_dict"
        assert doc_dict["quality_rating"] == "standard"

        # Create from dict
        doc2 = Document(**doc_dict)
        assert doc2.id == doc.id


class TestChunk:
    """Test Chunk model."""

    def test_chunk_creation_minimal(self) -> None:
        """Test creating chunk with minimal required fields."""
        chunk = Chunk(
            id="chunk_1",
            document_id="doc_1",
            content="This is a test chunk.",
            chunk_index=0,
            char_start=0,
            char_end=21,
        )

        assert chunk.id == "chunk_1"
        assert chunk.document_id == "doc_1"
        assert chunk.content == "This is a test chunk."
        assert chunk.chunk_index == 0
        assert chunk.section_heading is None
        assert chunk.char_start == 0
        assert chunk.char_end == 21

    def test_chunk_creation_with_heading(self) -> None:
        """Test creating chunk with section heading."""
        chunk = Chunk(
            id="chunk_2",
            document_id="doc_1",
            content="Content under heading.",
            chunk_index=1,
            section_heading="Introduction",
            char_start=100,
            char_end=122,
        )

        assert chunk.section_heading == "Introduction"
        assert chunk.chunk_index == 1

    def test_chunk_serialization(self) -> None:
        """Test chunk serialization to/from JSON."""
        chunk = Chunk(
            id="chunk_3",
            document_id="doc_2",
            content="Test content.",
            chunk_index=5,
            section_heading="Testing",
            char_start=500,
            char_end=513,
        )

        # Serialize to JSON
        json_str = chunk.model_dump_json()
        assert isinstance(json_str, str)

        # Deserialize from JSON
        chunk2 = Chunk.model_validate_json(json_str)
        assert chunk2.id == chunk.id
        assert chunk2.content == chunk.content
        assert chunk2.section_heading == chunk.section_heading

    def test_chunk_ordering(self) -> None:
        """Test that chunks can be ordered by chunk_index."""
        chunks = [
            Chunk(
                id=f"chunk_{i}",
                document_id="doc_1",
                content=f"Content {i}",
                chunk_index=i,
                char_start=i * 100,
                char_end=(i + 1) * 100,
            )
            for i in [2, 0, 1, 3]
        ]

        # Sort by chunk_index
        sorted_chunks = sorted(chunks, key=lambda c: c.chunk_index)
        assert [c.chunk_index for c in sorted_chunks] == [0, 1, 2, 3]
