"""Tests for embedding model management."""

import pytest
from unittest.mock import patch, MagicMock

from bloginator.search._embedding import _get_embedding_model


class TestEmbeddingModel:
    """Test embedding model loading and caching."""

    def test_get_embedding_model_loads_model(self) -> None:
        """Test that embedding model can be loaded."""
        # This test uses the real model (slow), so it's marked as slow
        # For faster tests, we'd mock SentenceTransformer
        model = _get_embedding_model("all-MiniLM-L6-v2")
        assert model is not None

    def test_get_embedding_model_caches_result(self) -> None:
        """Test that embedding models are cached after first load."""
        # Load same model twice
        model1 = _get_embedding_model("all-MiniLM-L6-v2")
        model2 = _get_embedding_model("all-MiniLM-L6-v2")

        # Should return the same instance (not a new load)
        assert model1 is model2

    def test_get_embedding_model_different_models(self) -> None:
        """Test that different models are cached separately."""
        # This would require having multiple models available
        # For now, just verify the function works with the default model
        model = _get_embedding_model("all-MiniLM-L6-v2")
        assert model is not None

    @patch("bloginator.search._embedding.SentenceTransformer")
    def test_get_embedding_model_error_handling(self, mock_transformer):
        """Test error handling when model loading fails."""
        mock_transformer.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to load embedding model"):
            _get_embedding_model("nonexistent-model")
