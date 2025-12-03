"""Tests for extract CLI command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from bloginator.cli.extract import extract


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
