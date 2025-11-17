"""Tests for refine CLI command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.refine import refine
from bloginator.models.draft import Draft, DraftSection


class TestRefineCLI:
    """Tests for refine CLI command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def draft_file(self, temp_dir):
        """Create draft JSON file."""
        draft = Draft(
            title="Test Document",
            keywords=["test"],
            sections=[
                DraftSection(title="Introduction", content="Original intro"),
                DraftSection(title="Body", content="Original body"),
            ],
        )

        draft_path = temp_dir / "draft.json"
        with open(draft_path, "w") as f:
            json.dump(draft.model_dump(mode="json"), f, default=str)

        return draft_path

    @pytest.fixture
    def index_dir(self, temp_dir):
        """Create mock index directory."""
        index_path = temp_dir / "index"
        index_path.mkdir()
        return index_path

    @pytest.fixture
    def mock_components(self):
        """Create mock components for refinement."""
        with (
            patch("bloginator.cli.refine.Searcher") as mock_searcher_cls,
            patch("bloginator.cli.refine.create_llm_client") as mock_llm_fn,
            patch("bloginator.cli.refine.RefinementEngine") as mock_engine_cls,
            patch("bloginator.cli.refine.VersionManager") as mock_vm_cls,
        ):
            # Setup mocks
            mock_searcher = Mock()
            mock_llm = Mock()
            mock_engine = Mock()
            mock_vm = Mock()

            mock_searcher_cls.return_value = mock_searcher
            mock_llm_fn.return_value = mock_llm
            mock_engine_cls.return_value = mock_engine
            mock_vm_cls.return_value = mock_vm

            # Mock parse_feedback
            mock_engine.parse_feedback.return_value = {
                "action": "tone_change",
                "target_sections": ["Introduction"],
                "instructions": "Make more engaging",
            }

            # Mock refined draft
            refined_draft = Draft(
                title="Test Document",
                keywords=["test"],
                sections=[
                    DraftSection(title="Introduction", content="Refined intro"),
                    DraftSection(title="Body", content="Original body"),
                ],
            )
            refined_draft.calculate_stats()
            mock_engine.refine_draft.return_value = refined_draft

            # Mock version history
            mock_history = Mock()
            mock_history.current_version = 2
            mock_history.versions = [Mock(), Mock()]
            mock_vm.load_history.return_value = mock_history
            mock_vm.create_history.return_value = mock_history

            # Mock version objects for diff
            mock_v1 = Mock()
            mock_v2 = Mock()
            mock_history.get_version.side_effect = lambda n: mock_v1 if n == 1 else mock_v2
            mock_vm.compute_diff.return_value = "mock diff output"

            yield {
                "searcher": mock_searcher,
                "llm": mock_llm,
                "engine": mock_engine,
                "version_manager": mock_vm,
                "history": mock_history,
            }

    def test_refine_basic(self, runner, draft_file, index_dir, temp_dir, mock_components):
        """Test basic refinement."""
        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Make introduction more engaging",
                "--versions-dir",
                str(temp_dir / "versions"),
                "--no-validate-safety",
                "--no-score-voice",
                "--no-show-diff",
            ],
        )

        assert result.exit_code == 0
        assert "Refinement complete" in result.output

        # Verify engine was called
        engine = mock_components["engine"]
        engine.refine_draft.assert_called_once()

    def test_refine_with_output_path(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test refinement with custom output path."""
        output_path = temp_dir / "refined.json"

        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Improve it",
                "--output",
                str(output_path),
                "--versions-dir",
                str(temp_dir / "versions"),
                "--no-validate-safety",
                "--no-score-voice",
                "--no-show-diff",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_refine_with_voice_scoring(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test refinement with voice scoring enabled."""
        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(temp_dir / "versions"),
                "--no-validate-safety",
                "--score-voice",
                "--no-show-diff",
            ],
        )

        assert result.exit_code == 0

        # Verify voice scoring was requested
        engine = mock_components["engine"]
        call_args = engine.refine_draft.call_args
        assert call_args.kwargs["score_voice"] is True

    def test_refine_missing_draft(self, runner, index_dir, temp_dir):
        """Test refinement with non-existent draft file."""
        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                "nonexistent.json",
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(temp_dir / "versions"),
            ],
        )

        assert result.exit_code != 0

    def test_refine_invalid_draft_json(
        self,
        runner,
        index_dir,
        temp_dir,
    ):
        """Test refinement with invalid draft JSON."""
        bad_draft = temp_dir / "bad.json"
        with open(bad_draft, "w") as f:
            f.write("not valid json {")

        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(bad_draft),
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(temp_dir / "versions"),
            ],
        )

        assert result.exit_code != 0

    def test_refine_creates_version_history(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test that refinement creates/updates version history."""
        versions_dir = temp_dir / "versions"

        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(versions_dir),
                "--no-validate-safety",
                "--no-score-voice",
                "--no-show-diff",
            ],
        )

        assert result.exit_code == 0

        # Verify version manager was used
        vm = mock_components["version_manager"]
        vm.load_history.assert_called_once()
        vm.add_version.assert_called_once()

    def test_refine_displays_results(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test that refinement displays results table."""
        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(temp_dir / "versions"),
                "--no-validate-safety",
                "--no-score-voice",
                "--no-show-diff",
            ],
        )

        assert result.exit_code == 0
        assert "Refinement Results" in result.output or "Word Count" in result.output

    def test_refine_shows_diff(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test that refinement shows diff when requested."""
        result = runner.invoke(
            refine,
            [
                "--index",
                str(index_dir),
                "--draft",
                str(draft_file),
                "--feedback",
                "Improve it",
                "--versions-dir",
                str(temp_dir / "versions"),
                "--no-validate-safety",
                "--no-score-voice",
                "--show-diff",
            ],
        )

        assert result.exit_code == 0

        # Verify diff was computed
        vm = mock_components["version_manager"]
        vm.compute_diff.assert_called_once()

    def test_refine_with_custom_llm_model(
        self,
        runner,
        draft_file,
        index_dir,
        temp_dir,
        mock_components,
    ):
        """Test refinement with custom LLM model."""
        with patch("bloginator.cli.refine.create_llm_client") as mock_llm_fn:
            mock_llm_fn.return_value = Mock()

            runner.invoke(
                refine,
                [
                    "--index",
                    str(index_dir),
                    "--draft",
                    str(draft_file),
                    "--feedback",
                    "Improve it",
                    "--llm-model",
                    "custom-model",
                    "--versions-dir",
                    str(temp_dir / "versions"),
                    "--no-validate-safety",
                    "--no-score-voice",
                    "--no-show-diff",
                ],
            )

            # Verify custom model was requested
            mock_llm_fn.assert_called_once_with(model="custom-model")
