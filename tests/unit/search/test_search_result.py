"""Tests for SearchResult class."""

from bloginator.search._search_result import SearchResult


class TestSearchResultModule:
    """Test SearchResult class from dedicated module."""

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

    def test_search_result_similarity_clamping(self) -> None:
        """Test that similarity score is clamped to [0, 1]."""
        # Distance > 1.0 should result in similarity_score clamped to 0.0
        result = SearchResult(
            chunk_id="test_chunk",
            content="Content",
            metadata={},
            distance=2.5,
        )
        assert result.similarity_score == 0.0
        assert 0.0 <= result.similarity_score <= 1.0

    def test_search_result_negative_distance(self) -> None:
        """Test handling of negative distance (edge case)."""
        result = SearchResult(
            chunk_id="test_chunk",
            content="Content",
            metadata={},
            distance=-0.5,
        )
        # Clamp: max(0.0, min(1.0, 1.0 - (-0.5))) = max(0.0, min(1.0, 1.5)) = 1.0
        assert result.similarity_score == 1.0

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
        assert "0.800" in repr_str  # similarity score (1.0 - 0.2)

    def test_search_result_score_initialization(self) -> None:
        """Test that scoring attributes are initialized correctly."""
        result = SearchResult(
            chunk_id="test",
            content="content",
            metadata={},
            distance=0.4,
        )

        # Check initialized scores
        assert result.recency_score == 0.5  # Default neutral
        assert result.quality_score == 0.5  # Default neutral
        assert result.combined_score == result.similarity_score  # Initially same as similarity
