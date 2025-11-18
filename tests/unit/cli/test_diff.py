"""Tests for diff CLI command."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.diff import diff
from bloginator.models.draft import Draft
from bloginator.models.version import VersionHistory


class TestDiffCLI:
    """Tests for diff CLI command."""

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
        from datetime import datetime

        with patch("bloginator.cli.diff.VersionManager") as mock_vm_cls:
            mock_vm = Mock()
            mock_vm_cls.return_value = mock_vm

            # Create mock history
            mock_history = Mock(spec=VersionHistory)
            mock_history.draft_id = "test-draft"
            mock_history.current_version = 3
            mock_history.versions = [Mock(), Mock(), Mock()]

            mock_vm.load_history.return_value = mock_history

            # Mock versions with all required attributes
            mock_v1 = Mock()
            mock_v1.version_number = 1
            mock_v1.draft = Draft(title="v1", keywords=[])
            mock_v1.timestamp = datetime(2025, 1, 1, 10, 0, 0)
            mock_v1.refinement_feedback = ""

            mock_v2 = Mock()
            mock_v2.version_number = 2
            mock_v2.draft = Draft(title="v2", keywords=[])
            mock_v2.timestamp = datetime(2025, 1, 1, 11, 0, 0)
            mock_v2.refinement_feedback = "Make more engaging"

            mock_v3 = Mock()
            mock_v3.version_number = 3
            mock_v3.draft = Draft(title="v3", keywords=[])
            mock_v3.timestamp = datetime(2025, 1, 1, 12, 0, 0)
            mock_v3.refinement_feedback = ""

            version_map = {1: mock_v1, 2: mock_v2, 3: mock_v3}
            mock_history.get_version.side_effect = lambda n: version_map.get(n)

            # Mock compute_diff and compute_diff_stats
            mock_vm.compute_diff.return_value = "diff content"
            mock_vm.compute_diff_stats.return_value = {
                "additions": 10,
                "deletions": 5,
                "changes": 15,
            }

            # Mock version summaries
            mock_vm.list_versions.return_value = [
                {
                    "version": 1,
                    "timestamp": "2025-01-01T10:00:00",
                    "description": "Initial draft",
                    "feedback": "",
                    "word_count": 100,
                    "voice_score": 0.8,
                },
                {
                    "version": 2,
                    "timestamp": "2025-01-01T11:00:00",
                    "description": "Refinement 1",
                    "feedback": "Make more engaging",
                    "word_count": 120,
                    "voice_score": 0.85,
                },
            ]

            # Mock diff
            mock_vm.compute_diff.return_value = """--- v1
+++ v2
@@ -1,1 +1,1 @@
-Old content
+New content"""

            mock_vm.compute_diff_stats.return_value = {
                "additions": 5,
                "deletions": 3,
                "changes": 8,
            }

            yield mock_vm

    def test_diff_list_versions(self, runner, temp_dir, mock_version_manager):
        """Test listing all versions."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
                "--list-versions",
            ],
        )

        assert result.exit_code == 0
        assert "Versions for" in result.output or "test-draft" in result.output
        assert "Initial draft" in result.output or "Refinement" in result.output

    def test_diff_default_comparison(self, runner, temp_dir, mock_version_manager):
        """Test default diff (current vs previous)."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
            ],
        )

        assert result.exit_code == 0
        # Should show diff output
        mock_version_manager.compute_diff.assert_called_once()

    def test_diff_specific_versions(self, runner, temp_dir, mock_version_manager):
        """Test comparing specific versions."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
                "-v1",
                "1",
                "-v2",
                "2",
            ],
        )

        assert result.exit_code == 0

        # Verify correct versions were compared
        history = mock_version_manager.load_history.return_value
        history.get_version.assert_any_call(1)
        history.get_version.assert_any_call(2)

    def test_diff_show_content(self, runner, temp_dir, mock_version_manager):
        """Test showing full version content."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
                "-v2",
                "1",
                "--show-content",
            ],
        )

        assert result.exit_code == 0
        # Should show version content instead of diff

    def test_diff_nonexistent_history(self, runner, temp_dir, mock_version_manager):
        """Test diff with non-existent draft history."""
        mock_version_manager.load_history.return_value = None

        result = runner.invoke(
            diff,
            [
                "nonexistent-draft",
                "--versions-dir",
                str(temp_dir),
            ],
        )

        assert result.exit_code != 0
        assert "No version history found" in result.output

    def test_diff_invalid_version_number(self, runner, temp_dir, mock_version_manager):
        """Test diff with invalid version number."""
        history = mock_version_manager.load_history.return_value
        history.get_version.return_value = None

        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
                "-v1",
                "99",
            ],
        )

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_diff_custom_context_lines(self, runner, temp_dir, mock_version_manager):
        """Test diff with custom context lines."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
                "--context-lines",
                "5",
            ],
        )

        assert result.exit_code == 0

        # Verify context lines parameter was used
        call_args = mock_version_manager.compute_diff.call_args
        assert call_args.kwargs.get("context_lines") == 5

    def test_diff_displays_stats(self, runner, temp_dir, mock_version_manager):
        """Test that diff displays change statistics."""
        result = runner.invoke(
            diff,
            [
                "test-draft",
                "--versions-dir",
                str(temp_dir),
            ],
        )

        assert result.exit_code == 0
        # Should show statistics
        mock_version_manager.compute_diff_stats.assert_called_once()
