"""Tests for corpus indexer."""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.indexing.indexer import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating


@pytest.mark.slow
class TestCorpusIndexer:
    """Test CorpusIndexer functionality.

    Note: These tests are marked as slow because they involve loading
    the sentence-transformers model and creating embeddings.
    """

    @pytest.fixture
    def indexer(self, tmp_path: Path) -> CorpusIndexer:
        """Create a corpus indexer instance."""
        return CorpusIndexer(output_dir=tmp_path / "index")

    @pytest.fixture
    def test_document(self) -> Document:
        """Create a test document."""
        return Document(
            id="test_doc_1",
            filename="test.md",
            source_path=Path("/test/test.md"),
            format="markdown",
            created_date=datetime(2020, 1, 15),
            modified_date=datetime(2020, 1, 16),
            quality_rating=QualityRating.PREFERRED,
            tags=["test", "sample"],
            word_count=100,
        )

    @pytest.fixture
    def test_chunks(self, test_document: Document) -> list[Chunk]:
        """Create test chunks."""
        return [
            Chunk(
                id="chunk_1",
                document_id=test_document.id,
                content="This is the first test chunk.",
                chunk_index=0,
                section_heading="Introduction",
                char_start=0,
                char_end=29,
            ),
            Chunk(
                id="chunk_2",
                document_id=test_document.id,
                content="This is the second test chunk.",
                chunk_index=1,
                section_heading="Body",
                char_start=30,
                char_end=60,
            ),
        ]

    def test_indexer_initialization(self, tmp_path: Path) -> None:
        """Test indexer initialization."""
        output_dir = tmp_path / "index"
        indexer = CorpusIndexer(output_dir=output_dir)

        assert indexer.output_dir == output_dir
        assert output_dir.exists()
        assert indexer.collection_name == "bloginator_corpus"
        assert indexer.embedding_model is not None

    def test_index_document(
        self, indexer: CorpusIndexer, test_document: Document, test_chunks: list[Chunk]
    ) -> None:
        """Test indexing a document with chunks."""
        indexer.index_document(test_document, test_chunks)

        # Verify chunks were added
        assert indexer.get_total_chunks() == 2

    def test_index_document_empty_chunks(
        self, indexer: CorpusIndexer, test_document: Document
    ) -> None:
        """Test indexing document with no chunks."""
        indexer.index_document(test_document, [])

        # Should not add anything
        assert indexer.get_total_chunks() == 0

    def test_get_collection_info(
        self, indexer: CorpusIndexer, test_document: Document, test_chunks: list[Chunk]
    ) -> None:
        """Test getting collection info."""
        indexer.index_document(test_document, test_chunks)

        info = indexer.get_collection_info()

        assert info["collection_name"] == "bloginator_corpus"
        assert info["total_chunks"] == 2
        assert "output_dir" in info

    def test_delete_document(
        self, indexer: CorpusIndexer, test_document: Document, test_chunks: list[Chunk]
    ) -> None:
        """Test deleting a document from index."""
        indexer.index_document(test_document, test_chunks)
        assert indexer.get_total_chunks() == 2

        indexer.delete_document(test_document.id)

        # Document chunks should be deleted
        assert indexer.get_total_chunks() == 0

    def test_clear_index(
        self, indexer: CorpusIndexer, test_document: Document, test_chunks: list[Chunk]
    ) -> None:
        """Test clearing the entire index."""
        indexer.index_document(test_document, test_chunks)
        assert indexer.get_total_chunks() == 2

        indexer.clear_index()

        assert indexer.get_total_chunks() == 0

    def test_index_multiple_documents(self, indexer: CorpusIndexer) -> None:
        """Test indexing multiple documents."""
        doc1 = Document(
            id="doc_1",
            filename="doc1.md",
            source_path=Path("/doc1.md"),
            format="markdown",
        )
        chunks1 = [
            Chunk(
                id="chunk_1_1",
                document_id="doc_1",
                content="Content 1",
                chunk_index=0,
                char_start=0,
                char_end=9,
            )
        ]

        doc2 = Document(
            id="doc_2",
            filename="doc2.md",
            source_path=Path("/doc2.md"),
            format="markdown",
        )
        chunks2 = [
            Chunk(
                id="chunk_2_1",
                document_id="doc_2",
                content="Content 2",
                chunk_index=0,
                char_start=0,
                char_end=9,
            )
        ]

        indexer.index_document(doc1, chunks1)
        indexer.index_document(doc2, chunks2)

        assert indexer.get_total_chunks() == 2
