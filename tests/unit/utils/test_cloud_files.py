"""Tests for cloud file detection and hydration utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from bloginator.utils.cloud_files import (
    CloudFileStatus,
    cleanup_hydration_temp_dir,
    get_cloud_file_status,
    hydrate_via_copy,
    is_cloud_only_file,
)


class TestIsCloudOnlyFile:
    """Tests for is_cloud_only_file function."""

    def test_local_file_returns_false(self, tmp_path: Path) -> None:
        """Local file with content should return False."""
        test_file = tmp_path / "local.txt"
        test_file.write_text("Hello, World!")

        assert is_cloud_only_file(test_file) is False

    def test_empty_file_returns_false(self, tmp_path: Path) -> None:
        """Empty file (size=0) should return False (not cloud-only)."""
        test_file = tmp_path / "empty.txt"
        test_file.touch()

        assert is_cloud_only_file(test_file) is False

    def test_nonexistent_file_returns_false(self, tmp_path: Path) -> None:
        """Non-existent file should return False."""
        test_file = tmp_path / "nonexistent.txt"

        assert is_cloud_only_file(test_file) is False

    def test_cloud_only_detection_with_mock(self, tmp_path: Path) -> None:
        """Simulate cloud-only file with st_blocks=0 but st_size>0."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("content")

        # Mock stat to simulate cloud-only file
        mock_stat = MagicMock()
        mock_stat.st_size = 1000
        mock_stat.st_blocks = 0

        with patch.object(Path, "stat", return_value=mock_stat):
            assert is_cloud_only_file(test_file) is True


class TestGetCloudFileStatus:
    """Tests for get_cloud_file_status function."""

    def test_local_file_status(self, tmp_path: Path) -> None:
        """Local file should return LOCAL status."""
        test_file = tmp_path / "local.txt"
        test_file.write_text("Hello, World!")

        assert get_cloud_file_status(test_file) == CloudFileStatus.LOCAL

    def test_cloud_only_status_with_mock(self, tmp_path: Path) -> None:
        """Simulated cloud-only file should return CLOUD_ONLY status."""
        test_file = tmp_path / "cloud.txt"
        test_file.write_text("content")

        mock_stat = MagicMock()
        mock_stat.st_size = 1000
        mock_stat.st_blocks = 0

        with patch.object(Path, "stat", return_value=mock_stat):
            assert get_cloud_file_status(test_file) == CloudFileStatus.CLOUD_ONLY

    def test_unknown_status_on_error(self, tmp_path: Path) -> None:
        """OSError should return UNKNOWN status."""
        test_file = tmp_path / "error.txt"

        with patch.object(Path, "stat", side_effect=OSError("stat failed")):
            assert get_cloud_file_status(test_file) == CloudFileStatus.UNKNOWN


class TestHydrateViaCopy:
    """Tests for hydrate_via_copy function."""

    def test_copy_local_file_succeeds(self, tmp_path: Path) -> None:
        """Copying a local file should succeed and return temp path."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("Hello, World!")
        temp_dir = tmp_path / "hydration"

        result = hydrate_via_copy(source_file, temp_dir=temp_dir, timeout_seconds=10.0)

        assert result is not None
        assert result.exists()
        assert result.read_text() == "Hello, World!"
        assert result.parent == temp_dir

    def test_copy_creates_temp_dir(self, tmp_path: Path) -> None:
        """hydrate_via_copy should create temp directory if needed."""
        source_file = tmp_path / "source.txt"
        source_file.write_text("test content")
        temp_dir = tmp_path / "new_hydration_dir"

        assert not temp_dir.exists()

        result = hydrate_via_copy(source_file, temp_dir=temp_dir, timeout_seconds=10.0)

        assert temp_dir.exists()
        assert result is not None

    def test_copy_nonexistent_file_returns_none(self, tmp_path: Path) -> None:
        """Copying non-existent file should return None."""
        source_file = tmp_path / "nonexistent.txt"
        temp_dir = tmp_path / "hydration"

        result = hydrate_via_copy(source_file, temp_dir=temp_dir, timeout_seconds=10.0)

        assert result is None


class TestCleanupHydrationTempDir:
    """Tests for cleanup_hydration_temp_dir function."""

    def test_cleanup_removes_files(self, tmp_path: Path) -> None:
        """Cleanup should remove all files and return count."""
        temp_dir = tmp_path / "hydration"
        temp_dir.mkdir()
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")

        count = cleanup_hydration_temp_dir(temp_dir=temp_dir)

        assert count == 2
        assert not temp_dir.exists()

    def test_cleanup_nonexistent_dir_returns_zero(self, tmp_path: Path) -> None:
        """Cleanup of non-existent directory should return 0."""
        temp_dir = tmp_path / "nonexistent"

        count = cleanup_hydration_temp_dir(temp_dir=temp_dir)

        assert count == 0
