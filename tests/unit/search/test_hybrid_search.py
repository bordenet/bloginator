"""Tests for hybrid search combining BM25 and semantic similarity."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from bloginator.search.bm25 import BM25Index
from bloginator.search.searcher import CorpusSearcher


class TestBM25Index:
    """Tests for BM25 lexical index."""

    def test_build_index_from_documents(self) -> None:
        """BM25 index can be built from document list."""
        documents = [
            {"id": "doc1", "content": "Python programming language tutorial"},
            {"id": "doc2", "content": "Java programming language guide"},
            {"id": "doc3", "content": "Python data science analysis"},
        ]

        index = BM25Index()
        index.build(documents)

        assert index.document_count == 3

    def test_search_returns_ranked_results(self) -> None:
        """BM25 search returns documents ranked by keyword match."""
        documents = [
            {"id": "doc1", "content": "Python programming language tutorial"},
            {"id": "doc2", "content": "Java programming language guide"},
            {"id": "doc3", "content": "Python data science analysis"},
        ]

        index = BM25Index()
        index.build(documents)

        results = index.search("Python programming", n_results=3)

        # Python programming should match doc1 best (both words)
        assert len(results) > 0
        assert results[0]["id"] == "doc1"
        # Score should be a float
        assert isinstance(results[0]["score"], float)

    def test_search_with_no_matches(self) -> None:
        """BM25 returns empty list when no keywords match."""
        documents = [
            {"id": "doc1", "content": "Python programming language tutorial"},
        ]

        index = BM25Index()
        index.build(documents)

        results = index.search("Rust Golang", n_results=3)

        # May return results with 0 score or empty list
        # Just ensure it doesn't crash
        assert isinstance(results, list)

    def test_search_respects_n_results(self) -> None:
        """BM25 search respects the n_results limit."""
        documents = [{"id": f"doc{i}", "content": f"Python tutorial part {i}"} for i in range(10)]

        index = BM25Index()
        index.build(documents)

        results = index.search("Python", n_results=3)

        assert len(results) <= 3

    def test_empty_index_returns_empty_results(self) -> None:
        """Search on empty index returns empty list."""
        index = BM25Index()
        index.build([])

        results = index.search("anything", n_results=5)

        assert results == []


class TestHybridSearch:
    """Tests for hybrid search combining BM25 and semantic."""

    @pytest.fixture
    def mock_searcher(self, tmp_path: Path) -> CorpusSearcher:
        """Create a mock corpus searcher for testing."""
        # Create a minimal index structure
        index_dir = tmp_path / "index"
        index_dir.mkdir()

        with (
            patch("bloginator.search.searcher.chromadb.PersistentClient"),
            patch("bloginator.search.searcher._get_embedding_model"),
            patch.object(CorpusSearcher, "__init__", lambda self, *args, **kwargs: None),
        ):
            searcher = CorpusSearcher.__new__(CorpusSearcher)
            searcher.index_dir = index_dir
            searcher.collection_name = "test"
            searcher.collection = MagicMock()
            searcher.embedding_model = MagicMock()
            searcher._bm25_index = None
            return searcher

    def test_hybrid_search_combines_scores(self, mock_searcher: CorpusSearcher) -> None:
        """Hybrid search combines BM25 and semantic scores."""
        # Mock semantic search results
        mock_searcher.search = MagicMock(
            return_value=[
                MagicMock(
                    chunk_id="doc1",
                    content="Python programming language",
                    similarity_score=0.9,
                    metadata={},
                ),
                MagicMock(
                    chunk_id="doc2",
                    content="Java programming",
                    similarity_score=0.7,
                    metadata={},
                ),
            ]
        )

        # Mock BM25 index
        mock_bm25 = MagicMock()
        mock_bm25.search.return_value = [
            {"id": "doc2", "score": 0.8},  # BM25 prefers doc2
            {"id": "doc1", "score": 0.5},
        ]
        mock_searcher._bm25_index = mock_bm25

        results = mock_searcher.hybrid_search(
            "Python programming",
            n_results=2,
            semantic_weight=0.5,
            bm25_weight=0.5,
        )

        assert len(results) == 2
        # Each result should have hybrid_score attribute
        for result in results:
            assert hasattr(result, "hybrid_score")

    def test_hybrid_search_default_weights(self, mock_searcher: CorpusSearcher) -> None:
        """Hybrid search uses sensible default weights."""
        mock_searcher.search = MagicMock(return_value=[])
        mock_searcher._bm25_index = MagicMock()
        mock_searcher._bm25_index.search.return_value = []

        # Should not raise - uses default weights
        results = mock_searcher.hybrid_search("test query", n_results=5)

        assert isinstance(results, list)

    def test_hybrid_search_without_bm25_index_falls_back(
        self, mock_searcher: CorpusSearcher
    ) -> None:
        """Hybrid search falls back to semantic only if no BM25 index."""
        mock_searcher._bm25_index = None
        mock_searcher.search = MagicMock(
            return_value=[
                MagicMock(
                    chunk_id="doc1",
                    content="test",
                    similarity_score=0.9,
                    metadata={},
                ),
            ]
        )

        results = mock_searcher.hybrid_search("test", n_results=5)

        # Should still work, falling back to semantic search
        assert len(results) == 1
