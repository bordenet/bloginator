"""Tests for init CLI command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.init import init


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


def test_init_basic(runner):
    """Test basic init command."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        # Setup mock
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        # Run command
        result = runner.invoke(init)

        # Verify
        assert result.exit_code == 0
        assert "Initialization complete" in result.output
        mock_get_model.assert_called_once_with("all-MiniLM-L6-v2")


def test_init_custom_model(runner):
    """Test init with custom model."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        # Setup mock
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        # Run command
        result = runner.invoke(
            init,
            [
                "--model",
                "custom-model",
            ],
        )

        # Verify
        assert result.exit_code == 0
        mock_get_model.assert_called_once_with("custom-model")


def test_init_verbose(runner):
    """Test init with verbose flag."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        # Setup mock
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        # Run command
        result = runner.invoke(
            init,
            [
                "--verbose",
            ],
        )

        # Verify
        assert result.exit_code == 0


def test_init_model_download_failure(runner):
    """Test init when model download fails."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        # Setup mock to raise exception
        mock_get_model.side_effect = RuntimeError("Download failed")

        # Run command
        result = runner.invoke(init)

        # Verify
        assert result.exit_code != 0
        assert "Error" in result.output or "Failed" in result.output


def test_init_idempotent(runner):
    """Test that running init twice doesn't break."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        # Setup mock
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        # Run command twice
        result1 = runner.invoke(init)
        result2 = runner.invoke(init)

        # Both should succeed
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        # Model should be loaded twice (no caching in init command)
        assert mock_get_model.call_count == 2


def test_init_shows_progress_feedback(runner):
    """Test that init provides progress feedback to user."""
    with patch("bloginator.cli.init._get_embedding_model") as mock_get_model:
        mock_model = Mock()
        mock_get_model.return_value = mock_model

        result = runner.invoke(init)

        # Should show some kind of progress or feedback
        assert result.exit_code == 0
        assert len(result.output) > 0  # Should output something
        # Check for common progress indicators
        has_feedback = any(
            word in result.output.lower()
            for word in ["loading", "downloading", "initializing", "complete", "success"]
        )
        assert has_feedback, f"Expected progress feedback, got: {result.output}"
