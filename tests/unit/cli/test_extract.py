"""Tests for extract CLI command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from rich.console import Console

from bloginator.cli._extract_config_helpers import _get_shadow_path_for_local, resolve_source_path
from bloginator.cli._smb_resolver import _get_shadow_path_for_smb, resolve_smb_path
from bloginator.cli.error_reporting import ErrorTracker
from bloginator.cli.extract import extract
from bloginator.corpus_config import CorpusSource
from bloginator.utils.shadow_copy import (
    build_shadow_path_for_local,
    build_shadow_path_for_smb,
    create_shadow_copy,
    is_shadow_copy_enabled,
    should_update_shadow_copy,
)


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_source(tmp_path):
    """Create temporary source directory with test files."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create test markdown file
    md_file = source_dir / "test.md"
    md_file.write_text("# Test Document\n\nThis is a test.")

    # Create test text file
    txt_file = source_dir / "test.txt"
    txt_file.write_text("Plain text content.")

    return source_dir


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    return output_dir


class TestExtractCLI:
    """Tests for extract CLI command."""

    def test_extract_requires_output(self, runner, temp_source):
        """Test that extract requires output directory."""
        result = runner.invoke(extract, [str(temp_source)])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_extract_requires_source_or_config(self, runner, temp_output):
        """Test that extract requires either source or config."""
        result = runner.invoke(extract, ["-o", str(temp_output)])
        assert result.exit_code != 0

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_single_source_mode(
        self, mock_extract_single, runner, temp_source, temp_output
    ):
        """Test extract in single source mode."""
        result = runner.invoke(
            extract,
            [str(temp_source), "-o", str(temp_output), "--quality", "preferred"],
        )

        assert result.exit_code == 0
        mock_extract_single.assert_called_once()

        # Verify arguments
        call_args = mock_extract_single.call_args
        assert call_args[0][0] == temp_source
        assert call_args[0][1] == temp_output
        assert call_args[0][2] == "preferred"

    @patch("bloginator.cli.extract.extract_from_config")
    def test_extract_config_mode(self, mock_extract_config, runner, temp_output, tmp_path):
        """Test extract in config mode."""
        # Create dummy config file
        config_file = tmp_path / "corpus.yaml"
        config_file.write_text("sources: []")

        result = runner.invoke(
            extract,
            ["-o", str(temp_output), "--config", str(config_file)],
        )

        assert result.exit_code == 0
        mock_extract_config.assert_called_once()

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_with_tags(self, mock_extract_single, runner, temp_source, temp_output):
        """Test extract with tags option."""
        result = runner.invoke(
            extract,
            [
                str(temp_source),
                "-o",
                str(temp_output),
                "--tags",
                "blog,technical",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_extract_single.call_args
        assert call_args[0][3] == ["blog", "technical"]

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_with_workers(self, mock_extract_single, runner, temp_source, temp_output):
        """Test extract with parallel workers."""
        result = runner.invoke(
            extract,
            [str(temp_source), "-o", str(temp_output), "--workers", "4"],
        )

        assert result.exit_code == 0
        call_args = mock_extract_single.call_args
        assert call_args[0][6] == 4  # workers parameter

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_with_force(self, mock_extract_single, runner, temp_source, temp_output):
        """Test extract with force flag."""
        result = runner.invoke(
            extract,
            [str(temp_source), "-o", str(temp_output), "--force"],
        )

        assert result.exit_code == 0
        call_args = mock_extract_single.call_args
        assert call_args[0][5] is True  # force parameter

    def test_extract_creates_output_directory(self, runner, temp_source, temp_output):
        """Test that extract creates output directory if it doesn't exist."""
        with patch("bloginator.cli.extract.extract_single_source"):
            result = runner.invoke(
                extract,
                [str(temp_source), "-o", str(temp_output)],
            )

            assert result.exit_code == 0
            assert temp_output.exists()

    def test_extract_with_invalid_directory(self, runner, temp_output):
        """Test extract with non-existent source directory."""
        nonexistent = temp_output.parent / "nonexistent"

        result = runner.invoke(
            extract,
            [str(nonexistent), "-o", str(temp_output)],
        )

        # Should fail with error message
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_with_file_instead_of_directory(
        self, mock_extract_single, runner, tmp_path, temp_output
    ):
        """Test extract accepts file path (single file mode)."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        result = runner.invoke(
            extract,
            [str(file_path), "-o", str(temp_output)],
        )

        # Should succeed - extract supports single files
        assert result.exit_code == 0
        mock_extract_single.assert_called_once()

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_with_no_supported_files(
        self, mock_extract_single, runner, tmp_path, temp_output
    ):
        """Test extract with directory containing no supported files."""
        empty_source = tmp_path / "empty"
        empty_source.mkdir()

        # Create unsupported file
        (empty_source / "image.jpg").write_bytes(b"fake image")

        result = runner.invoke(
            extract,
            [str(empty_source), "-o", str(temp_output)],
        )

        # Should succeed but potentially warn
        assert result.exit_code == 0

    @patch("bloginator.cli.extract.extract_single_source")
    def test_extract_handles_special_characters_in_filenames(
        self, mock_extract_single, runner, tmp_path, temp_output
    ):
        """Test extract with special characters in filenames."""
        source = tmp_path / "source"
        source.mkdir()

        # Create files with special characters
        (source / "file with spaces.md").write_text("content")
        (source / "file-with-dashes.txt").write_text("content")
        (source / "file_with_underscores.md").write_text("content")

        result = runner.invoke(
            extract,
            [str(source), "-o", str(temp_output)],
        )

        assert result.exit_code == 0
        mock_extract_single.assert_called_once()


class TestShadowCopyForSMB:
    """Tests for SMB shadow copy fallback functionality."""

    def test_get_shadow_path_for_smb_returns_none_when_not_exists(self):
        """Shadow path returns None when directory doesn't exist."""
        result = _get_shadow_path_for_smb("smb://server/share/path")
        assert result is None

    def test_get_shadow_path_for_smb_returns_path_when_exists(self, tmp_path):
        """Shadow path returns Path when shadow directory exists."""
        # Create shadow directory structure
        shadow_dir = tmp_path / "smb" / "myserver" / "myshare" / "docs"
        shadow_dir.mkdir(parents=True)

        with patch("bloginator.cli._smb_resolver.SHADOW_COPY_ROOT", tmp_path):
            result = _get_shadow_path_for_smb("smb://myserver/myshare/docs")
            assert result is not None
            assert result == shadow_dir

    def test_get_shadow_path_for_smb_parses_url_correctly(self, tmp_path):
        """Shadow path correctly parses SMB URL components."""
        shadow_dir = tmp_path / "smb" / "nas.local" / "backup" / "files"
        shadow_dir.mkdir(parents=True)

        with patch("bloginator.cli._smb_resolver.SHADOW_COPY_ROOT", tmp_path):
            result = _get_shadow_path_for_smb("smb://nas.local/backup/files")
            assert result == shadow_dir

    def test_resolve_smb_path_uses_shadow_when_smb_unavailable(self, tmp_path):
        """resolve_smb_path falls back to shadow copy when SMB unavailable."""
        shadow_dir = tmp_path / "smb" / "server" / "share"
        shadow_dir.mkdir(parents=True)

        error_tracker = ErrorTracker()

        with (
            patch("bloginator.cli._smb_resolver.SHADOW_COPY_ROOT", tmp_path),
            patch("bloginator.cli._smb_resolver.platform.system", return_value="Darwin"),
            patch("bloginator.cli._smb_resolver._resolve_smb_darwin", return_value=None),
        ):
            result = resolve_smb_path("smb://server/share", error_tracker)

        assert result == shadow_dir
        # Should not record skip since shadow copy was found
        assert error_tracker.total_skipped == 0

    def test_resolve_smb_path_records_skip_when_no_fallback(self):
        """resolve_smb_path records skip when neither SMB nor shadow available."""
        error_tracker = ErrorTracker()

        with (
            patch("bloginator.cli._smb_resolver.platform.system", return_value="Darwin"),
            patch("bloginator.cli._smb_resolver._resolve_smb_darwin", return_value=None),
        ):
            result = resolve_smb_path("smb://unavailable/share", error_tracker)

        assert result is None
        assert error_tracker.total_skipped > 0


class TestShadowCopyForLocal:
    """Tests for local path shadow copy fallback functionality."""

    def test_get_shadow_path_for_local_returns_none_when_not_exists(self):
        """Shadow path returns None when directory doesn't exist."""
        result = _get_shadow_path_for_local(Path("/Users/test/OneDrive/docs"))
        assert result is None

    def test_get_shadow_path_for_local_returns_path_when_exists(self, tmp_path):
        """Shadow path returns Path when shadow directory exists."""
        # Create shadow directory structure
        shadow_dir = tmp_path / "local" / "Users" / "test" / "OneDrive" / "docs"
        shadow_dir.mkdir(parents=True)

        with patch("bloginator.cli._extract_config_helpers.SHADOW_COPY_ROOT", tmp_path):
            result = _get_shadow_path_for_local(Path("/Users/test/OneDrive/docs"))
            assert result is not None
            assert result == shadow_dir

    def test_get_shadow_path_strips_leading_slash(self, tmp_path):
        """Shadow path correctly strips leading slash from original path."""
        shadow_dir = tmp_path / "local" / "path" / "to" / "files"
        shadow_dir.mkdir(parents=True)

        with patch("bloginator.cli._extract_config_helpers.SHADOW_COPY_ROOT", tmp_path):
            result = _get_shadow_path_for_local(Path("/path/to/files"))
            assert result == shadow_dir

    def test_resolve_source_path_uses_shadow_for_missing_local(self, tmp_path):
        """resolve_source_path falls back to shadow for missing local paths."""
        # Create shadow directory
        original_path = tmp_path / "original" / "docs"
        shadow_dir = tmp_path / "shadow" / "local" / str(original_path).lstrip("/")
        shadow_dir.mkdir(parents=True)

        # Create mock source config that returns non-existent path
        source_cfg = MagicMock(spec=CorpusSource)
        source_cfg.name = "test-source"
        source_cfg.resolve_path.return_value = original_path

        error_tracker = ErrorTracker()
        console = Console(force_terminal=False)

        with patch(
            "bloginator.cli._extract_config_helpers.SHADOW_COPY_ROOT",
            tmp_path / "shadow",
        ):
            result = resolve_source_path(source_cfg, tmp_path, error_tracker, console)

        assert result == shadow_dir
        assert error_tracker.total_skipped == 0

    def test_resolve_source_path_records_skip_when_no_fallback(self, tmp_path):
        """resolve_source_path records skip when neither path nor shadow exist."""
        original_path = tmp_path / "nonexistent" / "docs"

        source_cfg = MagicMock(spec=CorpusSource)
        source_cfg.name = "test-source"
        source_cfg.resolve_path.return_value = original_path

        error_tracker = ErrorTracker()
        console = Console(force_terminal=False)

        result = resolve_source_path(source_cfg, tmp_path, error_tracker, console)

        assert result is None
        assert error_tracker.total_skipped > 0

    def test_resolve_source_path_returns_existing_path_directly(self, tmp_path):
        """resolve_source_path returns existing path without shadow lookup."""
        existing_path = tmp_path / "existing" / "docs"
        existing_path.mkdir(parents=True)

        source_cfg = MagicMock(spec=CorpusSource)
        source_cfg.name = "test-source"
        source_cfg.resolve_path.return_value = existing_path

        error_tracker = ErrorTracker()
        console = Console(force_terminal=False)

        result = resolve_source_path(source_cfg, tmp_path, error_tracker, console)

        assert result == existing_path
        assert error_tracker.total_skipped == 0


class TestShadowCopyCreation:
    """Tests for shadow copy creation utilities."""

    def test_build_shadow_path_for_local(self, tmp_path):
        """Shadow path builds correctly for local paths."""
        original = tmp_path / "docs" / "file.md"

        with patch("bloginator.utils.shadow_copy.Config") as mock_config:
            mock_config.SHADOW_COPY_ROOT = tmp_path / "shadow"
            result = build_shadow_path_for_local(original)

        # Should include full absolute path under shadow/local/
        assert "local" in str(result)
        assert result.name == "file.md"

    def test_create_shadow_copy_success(self, tmp_path):
        """Shadow copy creation succeeds for valid file."""
        source = tmp_path / "source" / "file.txt"
        source.parent.mkdir(parents=True)
        source.write_text("test content")

        shadow = tmp_path / "shadow" / "file.txt"

        result = create_shadow_copy(source, shadow)

        assert result is True
        assert shadow.exists()
        assert shadow.read_text() == "test content"

    def test_create_shadow_copy_creates_parent_dirs(self, tmp_path):
        """Shadow copy creation creates parent directories."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        shadow = tmp_path / "deep" / "nested" / "path" / "copy.txt"

        result = create_shadow_copy(source, shadow)

        assert result is True
        assert shadow.exists()

    def test_should_update_shadow_copy_when_missing(self, tmp_path):
        """Should update when shadow copy doesn't exist."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        shadow = tmp_path / "shadow.txt"  # doesn't exist

        assert should_update_shadow_copy(source, shadow) is True

    def test_should_update_shadow_copy_when_older(self, tmp_path):
        """Should update when shadow copy is older than source."""
        import time

        shadow = tmp_path / "shadow.txt"
        shadow.write_text("old content")

        time.sleep(0.1)  # Ensure different mtime

        source = tmp_path / "source.txt"
        source.write_text("new content")

        assert should_update_shadow_copy(source, shadow) is True

    def test_should_not_update_shadow_copy_when_newer(self, tmp_path):
        """Should not update when shadow copy is newer than source."""
        import time

        source = tmp_path / "source.txt"
        source.write_text("old content")

        time.sleep(0.1)  # Ensure different mtime

        shadow = tmp_path / "shadow.txt"
        shadow.write_text("new content")

        assert should_update_shadow_copy(source, shadow) is False

    def test_is_shadow_copy_enabled_default(self):
        """Shadow copy is disabled by default."""
        with patch("bloginator.utils.shadow_copy.Config") as mock_config:
            mock_config.CORPUS_MAINTAIN_SHADOW_COPIES = False
            assert is_shadow_copy_enabled() is False

    def test_is_shadow_copy_enabled_when_set(self):
        """Shadow copy enabled when flag is True."""
        with patch("bloginator.utils.shadow_copy.Config") as mock_config:
            mock_config.CORPUS_MAINTAIN_SHADOW_COPIES = True
            assert is_shadow_copy_enabled() is True

    def test_create_shadow_copy_failure(self, tmp_path):
        """Shadow copy creation returns False on failure."""
        source = tmp_path / "nonexistent.txt"  # doesn't exist
        shadow = tmp_path / "shadow.txt"

        result = create_shadow_copy(source, shadow)

        assert result is False
        assert not shadow.exists()

    def test_should_update_shadow_copy_handles_stat_error(self, tmp_path):
        """should_update returns True when stat fails."""
        source = tmp_path / "source.txt"
        source.write_text("content")

        shadow = tmp_path / "shadow.txt"
        shadow.write_text("content")

        # Mock the stat call inside should_update_shadow_copy to raise OSError
        # We need to patch after exists() check passes
        original_stat = Path.stat
        call_count = 0

        def stat_side_effect(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Let the first two calls work (exists() checks for shadow and source)
            # Then fail on the explicit stat() calls for mtime comparison
            if call_count <= 2:
                return original_stat(self, *args, **kwargs)
            raise OSError("Permission denied")

        with patch.object(Path, "stat", stat_side_effect):
            result = should_update_shadow_copy(source, shadow)

        assert result is True

    def test_build_shadow_path_for_smb(self, tmp_path):
        """Shadow path builds correctly for SMB paths."""
        source_root = tmp_path / "mounted" / "share"
        source_root.mkdir(parents=True)
        file_path = source_root / "docs" / "file.md"

        with patch("bloginator.utils.shadow_copy.Config") as mock_config:
            mock_config.SHADOW_COPY_ROOT = tmp_path / "shadow"
            result = build_shadow_path_for_smb("smb://server/share", file_path, source_root)

        assert "smb" in str(result)
        assert "server" in str(result)
        assert "share" in str(result)
        assert result.name == "file.md"

    def test_build_shadow_path_for_smb_file_not_under_root(self, tmp_path):
        """Shadow path handles file not under source root."""
        source_root = tmp_path / "mounted" / "share"
        file_path = tmp_path / "other" / "location" / "file.md"

        with patch("bloginator.utils.shadow_copy.Config") as mock_config:
            mock_config.SHADOW_COPY_ROOT = tmp_path / "shadow"
            result = build_shadow_path_for_smb("smb://server/share", file_path, source_root)

        # Should still produce a valid path
        assert result.name == "file.md"
