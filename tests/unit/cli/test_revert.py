"""Tests for revert CLI command."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.revert import revert
from bloginator.models.draft import Draft
from bloginator.models.version import VersionHistory


class TestRevertCLI:
    """Tests for revert CLI command."""

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
    def mock_version_manager(self):
        """Create mock version manager."""
        with patch("bloginator.cli.revert.VersionManager") as mock_vm_cls:
            mock_vm = Mock()
            mock_vm_cls.return_value = mock_vm

            # Create mock history
            mock_history = Mock(spec=VersionHistory)
            mock_history.draft_id = "test-draft"
            mock_history.current_version = 3
            mock_history.versions = [Mock(), Mock(), Mock()]

            mock_vm.load_history.return_value = mock_history

            # Mock versions
            mock_v1 = Mock()
            mock_v1.version_number = 1
            mock_v1.draft = Draft(title="v1", keywords=[])
            mock_v1.draft.calculate_stats()
            mock_v1.timestamp = Mock()
            mock_v1.timestamp.strftime.return_value = "2025-01-01 10:00"
            mock_v1.change_description = "Initial draft"

            mock_v3 = Mock()
            mock_v3.version_number = 3
            mock_v3.draft = Draft(title="v3", keywords=[])
            mock_v3.draft.calculate_stats()
            mock_v3.timestamp = Mock()
            mock_v3.timestamp.strftime.return_value = "2025-01-01 12:00"
            mock_v3.change_description = "Refinement 2"

            def get_version_side_effect(n):
                if n == 1:
                    return mock_v1
                elif n == 3:
                    return mock_v3
                return None

            mock_history.get_version.side_effect = get_version_side_effect
            mock_history.get_current.return_value = mock_v3

            # Mock revert
            mock_vm.revert.return_value = True

            yield mock_vm

    def test_revert_basic(self, runner, temp_dir, mock_version_manager):
        """Test basic revert operation."""
        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",  # Skip confirmation
            ],
        )

        assert result.exit_code == 0
        assert "Reverted to version 1" in result.output
        assert output_path.exists()

        # Verify revert was called
        mock_version_manager.revert.assert_called_once()

    def test_revert_with_confirmation(self, runner, temp_dir, mock_version_manager):
        """Test revert with user confirmation."""
        output_path = temp_dir / "draft.json"

        # Simulate user confirming
        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
            ],
            input="y\n",
        )

        assert result.exit_code == 0
        assert output_path.exists()

    def test_revert_cancelled(self, runner, temp_dir, mock_version_manager):
        """Test revert when user cancels."""
        output_path = temp_dir / "draft.json"

        # Simulate user cancelling
        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
            ],
            input="n\n",
        )

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()
        assert not output_path.exists()

    def test_revert_nonexistent_history(self, runner, temp_dir, mock_version_manager):
        """Test revert with non-existent draft history."""
        mock_version_manager.load_history.return_value = None

        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "nonexistent-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code != 0
        assert "No version history found" in result.output

    def test_revert_invalid_version(self, runner, temp_dir, mock_version_manager):
        """Test revert to invalid version number."""
        history = mock_version_manager.load_history.return_value
        history.get_version.return_value = None

        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "99",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_revert_saves_draft(self, runner, temp_dir, mock_version_manager):
        """Test that revert saves the draft JSON."""
        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert output_path.exists()

        # Verify it's valid JSON
        with output_path.open() as f:
            data = json.load(f)
        assert "title" in data

    def test_revert_displays_info(self, runner, temp_dir, mock_version_manager):
        """Test that revert displays version information."""
        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code == 0
        # Should display version info table
        assert "Revert Information" in result.output or "Version" in result.output

    def test_revert_shows_next_steps(self, runner, temp_dir, mock_version_manager):
        """Test that revert shows helpful next steps."""
        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Next steps" in result.output or "bloginator" in result.output

    def test_revert_failure(self, runner, temp_dir, mock_version_manager):
        """Test handling of revert failure."""
        mock_version_manager.revert.return_value = False

        output_path = temp_dir / "draft.json"

        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--output",
                str(output_path),
                "--force",
            ],
        )

        assert result.exit_code != 0
        assert "Revert failed" in result.output or "Error" in result.output

    def test_revert_missing_output_path(self, runner, temp_dir, mock_version_manager):
        """Test revert without output path (should fail - output is required)."""
        result = runner.invoke(
            revert,
            [
                "test-draft",
                "1",
                "--versions-dir",
                str(temp_dir),
                "--force",
            ],
        )

        # Should fail because --output is required
        assert result.exit_code != 0
