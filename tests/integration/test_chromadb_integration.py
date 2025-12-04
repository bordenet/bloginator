"""Integration tests for ChromaDB operations.

Tests real ChromaDB operations without mocking, using isolated tmp_path fixtures.

Coder A Assignment (Phase 4):
- Test real ChromaDB operations (not mocked)
- Use tmp_path fixture for isolated index directories
- Verify index persistence and reload
- Test search quality thresholds
"""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating
from bloginator.search import CorpusSearcher


@pytest.mark.integration
class TestChromaDBIntegration:
    """Integration tests for ChromaDB operations.

    Uses real ChromaDB with isolated temporary directories.
    """

    @pytest.fixture
    def sample_documents(self) -> list[tuple[Document, list[Chunk]]]:
        """Create sample documents with chunks for testing."""
        docs = []

        # Document 1: Technical content
        doc1 = Document(
            id="doc1",
            filename="technical_guide.md",
            source_path=Path("/test/technical_guide.md"),
            format="md",
            created_date=datetime(2024, 1, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=["technical", "guide"],
            word_count=500,
        )
        content1 = "Building scalable systems requires careful planning."
        content2 = "Performance optimization starts with understanding bottlenecks."
        chunks1 = [
            Chunk(
                id="doc1_chunk_0",
                document_id="doc1",
                content=content1,
                chunk_index=0,
                char_start=0,
                char_end=len(content1),
            ),
            Chunk(
                id="doc1_chunk_1",
                document_id="doc1",
                content=content2,
                chunk_index=1,
                char_start=len(content1),
                char_end=len(content1) + len(content2),
            ),
        ]
        docs.append((doc1, chunks1))

        # Document 2: Leadership content
        doc2 = Document(
            id="doc2",
            filename="leadership_principles.md",
            source_path=Path("/test/leadership.md"),
            format="md",
            created_date=datetime(2024, 2, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=["leadership"],
            word_count=300,
        )
        content3 = "Effective leaders communicate clearly and set expectations."
        content4 = "Building trust with your team is fundamental to leadership."
        chunks2 = [
            Chunk(
                id="doc2_chunk_0",
                document_id="doc2",
                content=content3,
                chunk_index=0,
                char_start=0,
                char_end=len(content3),
            ),
            Chunk(
                id="doc2_chunk_1",
                document_id="doc2",
                content=content4,
                chunk_index=1,
                char_start=len(content3),
                char_end=len(content3) + len(content4),
            ),
        ]
        docs.append((doc2, chunks2))

        return docs

    def test_index_creation_from_documents(
        self, tmp_path: Path, sample_documents: list[tuple[Document, list[Chunk]]]
    ) -> None:
        """Index should be created successfully from documents."""
        index_dir = tmp_path / "chroma"
        indexer = CorpusIndexer(output_dir=index_dir)

        for doc, chunks in sample_documents:
            indexer.index_document(doc, chunks)

        # Verify chunks were indexed
        total_chunks = indexer.get_total_chunks()
        expected_chunks = sum(len(chunks) for _, chunks in sample_documents)
        assert total_chunks == expected_chunks

    def test_index_persistence_and_reload(
        self, tmp_path: Path, sample_documents: list[tuple[Document, list[Chunk]]]
    ) -> None:
        """Index should persist and be reloadable."""
        index_dir = tmp_path / "chroma"

        # Create and populate index
        indexer1 = CorpusIndexer(output_dir=index_dir)
        for doc, chunks in sample_documents:
            indexer1.index_document(doc, chunks)
        original_count = indexer1.get_total_chunks()

        # Create new indexer pointing to same directory
        indexer2 = CorpusIndexer(output_dir=index_dir)
        reloaded_count = indexer2.get_total_chunks()

        assert reloaded_count == original_count

    def test_search_with_real_embeddings(
        self, tmp_path: Path, sample_documents: list[tuple[Document, list[Chunk]]]
    ) -> None:
        """Search should return relevant results with real embeddings."""
        index_dir = tmp_path / "chroma"
        indexer = CorpusIndexer(output_dir=index_dir)

        for doc, chunks in sample_documents:
            indexer.index_document(doc, chunks)

        # Search for technical content
        searcher = CorpusSearcher(index_dir=index_dir)
        results = searcher.search(query="scalable systems architecture", n_results=5)

        assert len(results) > 0
        # Technical content should be in top results
        top_content = results[0].content.lower()
        assert "scalable" in top_content or "architecture" in top_content

    def test_search_result_relevance_thresholds(
        self, tmp_path: Path, sample_documents: list[tuple[Document, list[Chunk]]]
    ) -> None:
        """Search results should have reasonable relevance scores."""
        index_dir = tmp_path / "chroma"
        indexer = CorpusIndexer(output_dir=index_dir)

        for doc, chunks in sample_documents:
            indexer.index_document(doc, chunks)

        searcher = CorpusSearcher(index_dir=index_dir)
        results = searcher.search(query="leadership team building", n_results=5)

        assert len(results) > 0
        # Check that similarity scores are reasonable (0 to 1 range)
        for result in results:
            assert 0 <= result.similarity_score <= 1

    def test_empty_index_handling(self, tmp_path: Path) -> None:
        """Empty index should handle searches gracefully."""
        index_dir = tmp_path / "chroma"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Verify empty index
        assert indexer.get_total_chunks() == 0

        # Search should return empty results, not error
        searcher = CorpusSearcher(index_dir=index_dir)
        results = searcher.search(query="anything", n_results=5)
        assert len(results) == 0

    def test_batch_indexing_performance(self, tmp_path: Path) -> None:
        """Batch indexing should handle multiple documents efficiently."""
        index_dir = tmp_path / "chroma"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Create batch of documents
        for i in range(10):
            doc = Document(
                id=f"batch_doc_{i}",
                filename=f"doc_{i}.md",
                source_path=Path(f"/test/doc_{i}.md"),
                format="md",
                created_date=datetime(2024, 1, i + 1),
                quality_rating=QualityRating.REFERENCE,
                word_count=100,
            )
            content = f"Content for document {i} with unique identifier batch{i}."
            chunks = [
                Chunk(
                    id=f"batch_doc_{i}_chunk_0",
                    document_id=f"batch_doc_{i}",
                    content=content,
                    chunk_index=0,
                    char_start=0,
                    char_end=len(content),
                ),
            ]
            indexer.index_document(doc, chunks)

        # All documents should be indexed
        assert indexer.get_total_chunks() == 10
