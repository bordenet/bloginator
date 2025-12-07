"""Tests for extract_utils module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from bloginator.cli.extract_utils import wait_for_file_availability


class TestWaitForFileAvailability:
    """Tests for wait_for_file_availability function."""

    def test_local_file_returns_available(self, tmp_path: Path) -> None:
        """Local file should return (True, 'local', None)."""
        test_file = tmp_path / "local.txt"
        test_file.write_text("Hello, World!")

        is_available, reason, alt_path = wait_for_file_availability(test_file)

        assert is_available is True
        assert reason == "local"
        assert alt_path is None

    def test_nonexistent_file_raises_error(self, tmp_path: Path) -> None:
        """Non-existent file should raise FileNotFoundError."""
        test_file = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            wait_for_file_availability(test_file)

    def test_cloud_only_with_copy_hydration_succeeds(self, tmp_path: Path) -> None:
        """Cloud-only file with copy hydration should return temp path."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("cloud content")

        # Mock cloud file detection and hydrate_via_copy
        with (
            patch(
                "bloginator.cli.extract_utils.get_cloud_file_status",
                return_value="cloud_only",
            ),
            patch(
                "bloginator.cli.extract_utils.hydrate_via_copy",
                return_value=tmp_path / "temp_copy.txt",
            ),
        ):
            is_available, reason, alt_path = wait_for_file_availability(
                test_file,
                attempt_hydration_flag=False,
                use_copy_hydration=True,
            )

            assert is_available is True
            assert reason == "copy_hydrated"
            assert alt_path == tmp_path / "temp_copy.txt"

    def test_cloud_only_without_hydration_returns_unavailable(self, tmp_path: Path) -> None:
        """Cloud-only file without hydration should return unavailable."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("cloud content")

        with patch(
            "bloginator.cli.extract_utils.get_cloud_file_status",
            return_value="cloud_only",
        ):
            is_available, reason, alt_path = wait_for_file_availability(
                test_file,
                attempt_hydration_flag=False,
                use_copy_hydration=False,
            )

            assert is_available is False
            assert reason == "cloud_only"
            assert alt_path is None

    def test_cloud_only_with_failed_copy_returns_unavailable(self, tmp_path: Path) -> None:
        """Cloud-only file with failed copy should return unavailable."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("cloud content")

        with (
            patch(
                "bloginator.cli.extract_utils.get_cloud_file_status",
                return_value="cloud_only",
            ),
            patch(
                "bloginator.cli.extract_utils.hydrate_via_copy",
                return_value=None,
            ),
        ):
            is_available, reason, alt_path = wait_for_file_availability(
                test_file,
                attempt_hydration_flag=False,
                use_copy_hydration=True,
            )

            assert is_available is False
            assert reason == "cloud_only"
            assert alt_path is None

    def test_hydration_success_returns_hydrated(self, tmp_path: Path) -> None:
        """Successful hydration should return (True, 'hydrated', None)."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("cloud content")

        with (
            patch(
                "bloginator.cli.extract_utils.get_cloud_file_status",
                return_value="cloud_only",
            ),
            patch(
                "bloginator.cli.extract_utils.attempt_hydration",
                return_value=True,
            ),
        ):
            is_available, reason, alt_path = wait_for_file_availability(
                test_file,
                attempt_hydration_flag=True,
                use_copy_hydration=False,
            )

            assert is_available is True
            assert reason == "hydrated"
            assert alt_path is None
