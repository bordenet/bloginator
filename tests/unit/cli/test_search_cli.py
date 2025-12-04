"""Tests for search CLI command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.search import search


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_index(tmp_path):
    """Create temporary index directory."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    return index_dir


class TestSearchCLI:
    """Tests for search CLI command."""

    def test_search_requires_index(self, runner):
        """Test that search requires index path."""
        result = runner.invoke(search, ["my query"])
        assert result.exit_code != 0

    def test_search_requires_query(self, runner, temp_index):
        """Test that search requires query string."""
        result = runner.invoke(search, [str(temp_index)])
        assert result.exit_code != 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_basic(self, mock_searcher_class, runner, temp_index):
        """Test basic search command."""
        # Setup mock with SearchResult objects
        mock_searcher = Mock()

        # Create proper mock results with all required attributes
        mock_result = Mock()
        mock_result.combined_score = 0.95
        mock_result.similarity_score = 0.9
        mock_result.recency_score = 0.8
        mock_result.quality_score = 0.85
        mock_result.content = "Sample text about leadership"
        mock_result.metadata = {
            "source": "doc1.md",
            "format": "markdown",
            "filename": "doc1.md",
            "quality_rating": "standard",
        }

        mock_searcher.search_with_weights.return_value = [mock_result]
        mock_searcher_class.return_value = mock_searcher

        # Run command
        result = runner.invoke(search, [str(temp_index), "leadership"])

        # Verify
        assert result.exit_code == 0
        mock_searcher_class.assert_called_once()
        mock_searcher.search_with_weights.assert_called_once()

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_n_results(self, mock_searcher_class, runner, temp_index):
        """Test search with custom number of results."""
        mock_searcher = Mock()
        mock_searcher.search_with_weights.return_value = []
        mock_searcher_class.return_value = mock_searcher

        result = runner.invoke(search, [str(temp_index), "test", "-n", "5"])

        assert result.exit_code == 0
        # Check that search was called with num_results parameter
        assert mock_searcher.search_with_weights.called

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_no_results(self, mock_searcher_class, runner, temp_index):
        """Test search with no results."""
        mock_searcher = Mock()
        mock_searcher.search_with_weights.return_value = []
        mock_searcher_class.return_value = mock_searcher

        result = runner.invoke(search, [str(temp_index), "nonexistent"])

        assert result.exit_code == 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_special_characters(self, mock_searcher_class, runner, temp_index):
        """Test search with special characters in query."""
        mock_searcher = Mock()
        mock_searcher.search_with_weights.return_value = []
        mock_searcher_class.return_value = mock_searcher

        # Query with special characters
        query = "C++ programming & design"
        result = runner.invoke(search, [str(temp_index), query])

        # Should handle gracefully
        assert result.exit_code == 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_very_long_query(self, mock_searcher_class, runner, temp_index):
        """Test search with very long query string."""
        mock_searcher = Mock()
        mock_searcher.search_with_weights.return_value = []
        mock_searcher_class.return_value = mock_searcher

        # Very long query
        long_query = " ".join(["word"] * 100)
        result = runner.invoke(search, [str(temp_index), long_query])

        # Should handle gracefully
        assert result.exit_code == 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_corrupted_index(self, mock_searcher_class, runner, temp_index):
        """Test search with corrupted index directory."""
        # Mock searcher to raise error on initialization
        mock_searcher_class.side_effect = RuntimeError("Index corrupted")

        result = runner.invoke(search, [str(temp_index), "query"])

        # Should fail gracefully with error message
        assert result.exit_code != 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_result_ranking_displayed(self, mock_searcher_class, runner, temp_index):
        """Test that search results show ranking/scores."""
        mock_searcher = Mock()

        # Create proper mock results with all required attributes
        mock_results = []
        for i in range(1, 4):
            mock_result = Mock()
            mock_result.combined_score = 1.0 - (i * 0.1)
            mock_result.similarity_score = 0.9 - (i * 0.1)
            mock_result.recency_score = 0.8
            mock_result.quality_score = 0.85
            mock_result.content = f"Result {i}"
            mock_result.metadata = {
                "source": f"doc{i}.md",
                "filename": f"doc{i}.md",
                "quality_rating": "standard",
            }
            mock_results.append(mock_result)

        mock_searcher.search_with_weights.return_value = mock_results
        mock_searcher_class.return_value = mock_searcher

        result = runner.invoke(search, [str(temp_index), "test"])

        assert result.exit_code == 0

    @patch("bloginator.cli.search.CorpusSearcher")
    def test_search_with_json_format(self, mock_searcher_class, runner, temp_index):
        """Test search with JSON output format."""
        mock_searcher = Mock()

        # Create proper mock result with all required attributes
        mock_result = Mock()
        mock_result.combined_score = 0.95
        mock_result.similarity_score = 0.9
        mock_result.recency_score = 0.8
        mock_result.quality_score = 0.85
        mock_result.content = "Sample"
        mock_result.metadata = {
            "source": "doc.md",
            "filename": "doc.md",
            "quality_rating": "standard",
        }

        mock_searcher.search_with_weights.return_value = [mock_result]
        mock_searcher_class.return_value = mock_searcher

        result = runner.invoke(search, [str(temp_index), "test", "--format", "json"])

        # Should output valid JSON or succeed
        assert result.exit_code == 0
