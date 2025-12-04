"""Tests for draft CLI command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.draft import draft


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_outline(tmp_path):
    """Create temporary outline file."""
    outline_file = tmp_path / "outline.json"
    outline_file.write_text(
        """{
        "title": "Test Document",
        "thesis": "Test thesis",
        "keywords": ["test"],
        "sections": [
            {
                "title": "Introduction",
                "description": "Test intro",
                "subsections": []
            }
        ]
    }"""
    )
    return outline_file


@pytest.fixture
def temp_index(tmp_path):
    """Create temporary index directory."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    return index_dir


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output file path."""
    return tmp_path / "draft.md"


class TestDraftCLI:
    """Tests for draft CLI command."""

    def test_draft_requires_outline_or_index(self, runner):
        """Test that draft requires outline file or index."""
        result = runner.invoke(draft, [])
        assert result.exit_code != 0

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_basic_generation(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test basic draft generation."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher

        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_draft = Mock()
        mock_draft.content = "# Test Document\n\nContent here."
        mock_draft.total_words = 100
        mock_draft.total_citations = 5
        mock_draft.get_all_sections.return_value = []
        mock_draft.to_markdown.return_value = "# Test\n\nContent"
        mock_draft.voice_score = 0.8
        mock_draft.has_blocklist_violations = False
        mock_generator.generate.return_value = mock_draft
        mock_generator_class.return_value = mock_generator

        # Run command
        result = runner.invoke(
            draft,
            ["--index", str(temp_index), "--outline", str(temp_outline), "-o", str(temp_output)],
        )

        # Verify
        assert result.exit_code == 0
        assert temp_output.exists()

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_with_invalid_outline(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        tmp_path,
        temp_index,
        temp_output,
    ):
        """Test draft with invalid outline file."""
        invalid_outline = tmp_path / "invalid.json"
        invalid_outline.write_text("{invalid json}")

        result = runner.invoke(
            draft,
            ["--index", str(temp_index), "--outline", str(invalid_outline), "-o", str(temp_output)],
        )

        # Should fail with error
        assert result.exit_code != 0

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_with_missing_outline(
        self, mock_llm, mock_generator_class, mock_searcher_class, runner, temp_index, temp_output
    ):
        """Test draft with missing outline file."""
        missing_outline = Path("/nonexistent/outline.json")

        result = runner.invoke(
            draft,
            ["--index", str(temp_index), "--outline", str(missing_outline), "-o", str(temp_output)],
        )

        # Should fail with error
        assert result.exit_code != 0

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    @patch("bloginator.cli._draft_validators.SafetyValidator")
    def test_draft_blocklist_violation_prevents_output(
        self,
        mock_validator_class,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test that blocklist violations prevent draft output."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher
        mock_llm.return_value = Mock()

        # Setup generator mock
        mock_generator = Mock()
        mock_draft = Mock()
        mock_draft.content = "Content with BlockedTerm here."
        mock_draft.total_words = 100
        mock_draft.total_citations = 5
        mock_draft.get_all_sections.return_value = []
        mock_draft.to_markdown.return_value = "# Test\n\nContent"
        mock_draft.voice_score = 0.8
        mock_draft.has_blocklist_violations = False
        mock_generator.generate.return_value = mock_draft
        mock_generator_class.return_value = mock_generator

        # Setup validator mock - return validation failure
        mock_validator = Mock()
        mock_validator.validate_before_generation.return_value = {
            "is_valid": False,
            "violations": [{"pattern": "BlockedTerm", "matches": ["BlockedTerm"]}],
        }
        mock_validator_class.return_value = mock_validator

        result = runner.invoke(
            draft,
            [
                "--index",
                str(temp_index),
                "--outline",
                str(temp_outline),
                "-o",
                str(temp_output),
                "--validate-safety",
            ],
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert "validation failed" in result.output.lower() or "violation" in result.output.lower()

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_with_citations(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test draft generation with citations enabled."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_draft = Mock()
        mock_draft.content = "Content with citation[^1]."
        mock_draft.total_words = 100
        mock_draft.total_citations = 5
        mock_draft.get_all_sections.return_value = []
        mock_draft.to_markdown.return_value = "# Test\n\nContent"
        mock_draft.voice_score = 0.8
        mock_draft.has_blocklist_violations = False
        mock_generator.generate.return_value = mock_draft
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            draft,
            [
                "--index",
                str(temp_index),
                "--outline",
                str(temp_outline),
                "--citations",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_with_voice_similarity_threshold(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test draft with voice similarity threshold."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_draft = Mock()
        mock_draft.content = "Test content."
        mock_draft.total_words = 100
        mock_draft.total_citations = 5
        mock_draft.get_all_sections.return_value = []
        mock_draft.to_markdown.return_value = "# Test\n\nContent"
        mock_draft.voice_score = 0.8
        mock_draft.has_blocklist_violations = False
        mock_generator.generate.return_value = mock_draft
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            draft,
            [
                "--index",
                str(temp_index),
                "--outline",
                str(temp_outline),
                "--similarity",
                "0.85",
                "-o",
                str(temp_output),
            ],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_handles_llm_timeout(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test draft handles LLM timeout gracefully."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_generator.generate.side_effect = TimeoutError("LLM timeout")
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            draft,
            ["--index", str(temp_index), "--outline", str(temp_outline), "-o", str(temp_output)],
        )

        # Should handle timeout gracefully
        assert result.exit_code != 0
        assert "timeout" in result.output.lower() or "error" in result.output.lower()

    @patch("bloginator.cli._draft_initialization.CorpusSearcher")
    @patch("bloginator.cli.draft.DraftGenerator")
    @patch("bloginator.cli._draft_initialization.create_llm_from_config")
    def test_draft_handles_llm_rate_limiting(
        self,
        mock_llm,
        mock_generator_class,
        mock_searcher_class,
        runner,
        temp_outline,
        temp_index,
        temp_output,
    ):
        """Test draft handles LLM rate limiting."""
        # Setup mocks
        mock_searcher = Mock()
        mock_searcher_class.return_value = mock_searcher
        mock_llm.return_value = Mock()

        mock_generator = Mock()
        mock_generator.generate.side_effect = Exception("Rate limit exceeded")
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            draft,
            ["--index", str(temp_index), "--outline", str(temp_outline), "-o", str(temp_output)],
        )

        # Should handle error gracefully
        assert result.exit_code != 0
