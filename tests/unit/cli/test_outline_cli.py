"""Tests for outline CLI command."""

from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.outline import outline


def _create_mock_outline():
    """Create a properly structured mock outline object."""
    mock_outline = Mock()
    mock_outline.title = "Test Outline"
    mock_outline.thesis = None
    mock_outline.sections = []
    mock_outline.get_all_sections.return_value = []
    mock_outline.avg_coverage = 75.0
    mock_outline.low_coverage_sections = 0
    mock_outline.total_sources = 5
    mock_outline.model_dump_json.return_value = '{"title": "Test Outline"}'
    mock_outline.to_markdown.return_value = "# Test Outline\n\nContent here"
    return mock_outline


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


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output file path."""
    return tmp_path / "outline.json"


class TestOutlineCLI:
    """Tests for outline CLI command."""

    def test_outline_requires_index_or_template(self, runner):
        """Test that outline requires either index or template."""
        result = runner.invoke(outline, [])
        # Should fail or show help
        assert result.exit_code != 0 or "Usage" in result.output

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_with_keywords(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline generation from keywords."""
        # Setup mocks
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_outline = _create_mock_outline()
        mock_generator.generate.return_value = mock_outline
        mock_generator_class.return_value = mock_generator

        # Run command
        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "agile,leadership",
                "-o",
                str(temp_output),
            ],
        )

        # Verify command succeeded and called generator
        assert result.exit_code == 0
        mock_generator.generate.assert_called_once()

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_with_template(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline generation from template."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_outline = _create_mock_outline()
        mock_generator.generate.return_value = mock_outline
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "test",
                "--template",
                "builtin-blog",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_with_thesis(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline generation with thesis statement."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_outline = _create_mock_outline()
        mock_generator.generate.return_value = mock_outline
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "test",
                "--thesis",
                "Building high-performing teams",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_combining_keywords_and_template(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline combining keywords and template."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_outline = _create_mock_outline()
        mock_generator.generate.return_value = mock_outline
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "agile",
                "--template",
                "builtin-blog",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_with_invalid_template(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline with invalid template ID."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_generator.generate.side_effect = ValueError("Template not found")
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "test",
                "--template",
                "nonexistent",
                "-o",
                str(temp_output),
            ],
        )

        # Should handle error gracefully
        assert result.exit_code != 0

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_generation_timeout(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test outline generation timeout handling."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_generator.generate.side_effect = TimeoutError("LLM timeout")
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "test",
                "-o",
                str(temp_output),
            ],
        )

        # Should handle timeout gracefully
        assert result.exit_code != 0

    @patch("bloginator.cli.outline.CorpusSearcher")
    @patch("bloginator.cli.outline.create_llm_from_config")
    @patch("bloginator.cli.outline.OutlineGenerator")
    def test_outline_structure_saved_to_file(
        self,
        mock_generator_class,
        mock_llm,
        mock_searcher_class,
        runner,
        temp_index,
        temp_output,
    ):
        """Test that outline is saved to output file."""
        mock_searcher_class.return_value = Mock()
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_outline = _create_mock_outline()
        mock_generator.generate.return_value = mock_outline
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            outline,
            [
                "--index",
                str(temp_index),
                "--title",
                "Test",
                "--keywords",
                "test",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0
        # File should be created
        assert temp_output.exists()
        content = temp_output.read_text()
        assert "Test Outline" in content
