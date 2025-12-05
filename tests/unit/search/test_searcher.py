"""Tests for corpus searcher."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating
from bloginator.search import CorpusSearcher, SearchResult


@pytest.mark.slow
class TestCorpusSearcher:
    """Test CorpusSearcher functionality.

    Note: These tests are marked as slow because they involve loading
    the sentence-transformers model and creating embeddings.
    """

    @pytest.fixture
    def test_index(self, tmp_path: Path) -> Path:
        """Create a test index with sample documents."""
        index_dir = tmp_path / "index"

        # Create indexer
        indexer = CorpusIndexer(output_dir=index_dir)

        # Create test documents with different dates and qualities
        now = datetime.now()

        # Recent preferred document
        doc1 = Document(
            id="doc_1",
            filename="recent_preferred.md",
            source_path=Path("/test/doc1.md"),
            format="markdown",
            created_date=now - timedelta(days=30),
            quality_rating=QualityRating.PREFERRED,
            tags=["agile", "culture"],
        )
        chunks1 = [
            Chunk(
                id="chunk_1",
                document_id="doc_1",
                content="Agile transformation requires cultural change and leadership commitment.",
                chunk_index=0,
                char_start=0,
                char_end=70,
            )
        ]

        # Old standard document
        doc2 = Document(
            id="doc_2",
            filename="old_standard.md",
            source_path=Path("/test/doc2.md"),
            format="markdown",
            created_date=now - timedelta(days=730),  # 2 years old
            quality_rating=QualityRating.REFERENCE,
            tags=["agile"],
        )
        chunks2 = [
            Chunk(
                id="chunk_2",
                document_id="doc_2",
                content="Agile methodologies improve team collaboration and delivery speed.",
                chunk_index=0,
                char_start=0,
                char_end=70,
            )
        ]

        # Recent deprecated document
        doc3 = Document(
            id="doc_3",
            filename="recent_deprecated.md",
            source_path=Path("/test/doc3.md"),
            format="markdown",
            created_date=now - timedelta(days=60),
            quality_rating=QualityRating.DEPRECATED,
            tags=["hiring"],
        )
        chunks3 = [
            Chunk(
                id="chunk_3",
                document_id="doc_3",
                content="Hiring practices should focus on cultural fit and technical skills.",
                chunk_index=0,
                char_start=0,
                char_end=70,
            )
        ]

        # Index all documents
        indexer.index_document(doc1, chunks1)
        indexer.index_document(doc2, chunks2)
        indexer.index_document(doc3, chunks3)

        return index_dir

    def test_searcher_initialization(self, test_index: Path) -> None:
        """Test searcher initialization."""
        searcher = CorpusSearcher(index_dir=test_index)

        assert searcher.index_dir == test_index
        assert searcher.collection_name == "bloginator_corpus"
        assert searcher.embedding_model is not None

    def test_searcher_initialization_invalid_dir(self, tmp_path: Path) -> None:
        """Test that invalid directory raises error."""
        invalid_dir = tmp_path / "nonexistent"

        with pytest.raises(ValueError, match="Index directory not found"):
            CorpusSearcher(index_dir=invalid_dir)

    def test_basic_search(self, test_index: Path) -> None:
        """Test basic semantic search."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search(query="agile transformation", n_results=5)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(hasattr(r, "chunk_id") for r in results)
        assert all(hasattr(r, "content") for r in results)
        assert all(hasattr(r, "similarity_score") for r in results)

    def test_search_with_quality_filter(self, test_index: Path) -> None:
        """Test search with quality filter."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search(query="agile", n_results=5, quality_filter="preferred")

        assert len(results) > 0
        for result in results:
            assert result.metadata.get("quality_rating") == "preferred"

    def test_search_with_format_filter(self, test_index: Path) -> None:
        """Test search with format filter."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search(query="agile", n_results=5, format_filter="markdown")

        assert len(results) > 0
        for result in results:
            assert result.metadata.get("format") == "markdown"

    def test_search_with_tags_filter(self, test_index: Path) -> None:
        """Test search with tags filter."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search(query="agile", n_results=5, tags_filter=["culture"])

        # Should only return results with "culture" tag
        assert len(results) > 0
        for result in results:
            tags = result.metadata.get("tags", "")
            assert "culture" in tags.lower()

    def test_search_with_recency(self, test_index: Path) -> None:
        """Test search with recency weighting."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search_with_recency(query="agile", n_results=3, recency_weight=0.8)

        assert len(results) > 0
        # All results should have recency scores
        for result in results:
            assert hasattr(result, "recency_score")
            assert 0.0 <= result.recency_score <= 1.0
            assert hasattr(result, "combined_score")

        # Results should be sorted by combined score
        scores = [r.combined_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_with_quality(self, test_index: Path) -> None:
        """Test search with quality weighting."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search_with_quality(query="agile", n_results=3, quality_weight=0.8)

        assert len(results) > 0
        # All results should have quality scores
        for result in results:
            assert hasattr(result, "quality_score")
            assert 0.0 <= result.quality_score <= 1.0

        # With high quality weight, preferred should rank higher
        # (if semantically similar)
        if len(results) > 1:
            # First result should ideally be preferred quality
            # (though this depends on semantic similarity too)
            scores = [r.combined_score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_search_with_weights(self, test_index: Path) -> None:
        """Test search with combined weighting."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.search_with_weights(
            query="agile",
            n_results=3,
            recency_weight=0.3,
            quality_weight=0.2,
        )

        assert len(results) > 0
        for result in results:
            assert hasattr(result, "similarity_score")
            assert hasattr(result, "recency_score")
            assert hasattr(result, "quality_score")
            assert hasattr(result, "combined_score")

            # Similarity score is 1 - distance, can be negative for high distances
            # Combined score is weighted average including similarity, can also be negative
            # Recency and quality scores should be in [0, 1]
            assert 0.0 <= result.recency_score <= 1.0
            assert 0.0 <= result.quality_score <= 1.0

    def test_get_stats(self, test_index: Path) -> None:
        """Test getting search statistics."""
        searcher = CorpusSearcher(index_dir=test_index)

        stats = searcher.get_stats()

        assert "collection_name" in stats
        assert "total_chunks" in stats
        assert "index_dir" in stats
        assert stats["total_chunks"] == 3  # We indexed 3 chunks
        assert stats["collection_name"] == "bloginator_corpus"

    def test_batch_search(self, test_index: Path) -> None:
        """Test batch search with multiple queries."""
        searcher = CorpusSearcher(index_dir=test_index)

        queries = ["agile", "leadership", "engineering"]
        results = searcher.batch_search(queries, n_results=2)

        assert len(results) == 3  # One result list per query
        for query_results in results:
            assert isinstance(query_results, list)
            assert len(query_results) <= 2

    def test_batch_search_empty_queries(self, test_index: Path) -> None:
        """Test batch search with empty query list."""
        searcher = CorpusSearcher(index_dir=test_index)

        results = searcher.batch_search([], n_results=5)

        assert results == []


class TestSearchResult:
    """Test SearchResult class."""

    def test_search_result_creation(self) -> None:
        """Test creating a search result."""
        result = SearchResult(
            chunk_id="test_chunk",
            content="Test content",
            metadata={"filename": "test.md"},
            distance=0.3,
        )

        assert result.chunk_id == "test_chunk"
        assert result.content == "Test content"
        assert result.distance == 0.3
        assert result.similarity_score == 0.7  # 1.0 - 0.3

    def test_search_result_repr(self) -> None:
        """Test search result string representation."""
        result = SearchResult(
            chunk_id="test_chunk_id_12345",
            content="Content",
            metadata={},
            distance=0.2,
        )

        repr_str = repr(result)
        assert "SearchResult" in repr_str
        assert "test_chu" in repr_str  # First 8 chars of ID
        assert "0.800" in repr_str  # similarity score
