"""Tests for extract_single CLI module."""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from bloginator.cli.extract_single import _collect_files, _process_files, extract_single_source
from bloginator.cli.extract_utils import get_supported_extensions


@pytest.fixture
def console():
    """Create mock console."""
    return Console(file=MagicMock())


@pytest.fixture
def temp_source_dir(tmp_path):
    """Create temporary source directory with test files."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create test markdown file
    md_file = source_dir / "test.md"
    md_file.write_text("# Test Document\n\nThis is a test.")

    # Create test text file
    txt_file = source_dir / "test.txt"
    txt_file.write_text("Plain text content.")

    # Create nested directory
    nested_dir = source_dir / "nested"
    nested_dir.mkdir()
    nested_file = nested_dir / "nested.md"
    nested_file.write_text("# Nested Document\n\nNested content.")

    # Create temp file (should be skipped)
    temp_file = source_dir / "~$temp.md"
    temp_file.write_text("Temp file")

    return source_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestCollectFiles:
    """Tests for _collect_files function."""

    def test_collect_single_file(self, temp_source_dir):
        """Test collecting a single file."""
        md_file = temp_source_dir / "test.md"
        files = _collect_files(md_file)

        assert len(files) == 1
        assert files[0] == md_file

    def test_collect_directory(self, temp_source_dir):
        """Test collecting files from directory."""
        files = _collect_files(temp_source_dir)

        # Should find .md and .txt files, but not temp files
        assert len(files) >= 2
        assert any(f.name == "test.md" for f in files)
        assert any(f.name == "test.txt" for f in files)
        assert not any(f.name == "~$temp.md" for f in files)

    def test_collect_nested_files(self, temp_source_dir):
        """Test collecting files from nested directories."""
        files = _collect_files(temp_source_dir)

        # Should find nested files
        assert any(f.name == "nested.md" for f in files)


class TestExtractAndSaveDocument:
    """Tests for document extraction and saving."""

    def test_extract_real_file(self, temp_source_dir, temp_output_dir):
        """Test extracting a real file end-to-end."""
        from bloginator.cli.extract_single import _extract_and_save_document

        test_file = temp_source_dir / "test.md"

        # Extract and save
        _extract_and_save_document(
            file_path=test_file,
            output=temp_output_dir,
            quality="preferred",
            tag_list=["test"],
        )

        # Verify files were created
        json_files = list(temp_output_dir.glob("*.json"))
        txt_files = list(temp_output_dir.glob("*.txt"))

        assert len(json_files) == 1
        assert len(txt_files) == 1

        # Verify content
        import json

        metadata = json.loads(json_files[0].read_text())
        assert metadata["filename"] == "test.md"
        assert metadata["quality_rating"] == "preferred"
        assert "test" in metadata["tags"]

        text_content = txt_files[0].read_text()
        assert "Test Document" in text_content


class TestProcessFiles:
    """Tests for _process_files function."""

    def test_process_files_success(self, temp_source_dir, temp_output_dir, console):
        """Test processing files successfully."""
        from bloginator.cli.error_reporting import ErrorTracker

        files = [temp_source_dir / "test.md"]
        error_tracker = ErrorTracker()

        extracted, skipped, failed = _process_files(
            files=files,
            output=temp_output_dir,
            quality="preferred",
            tag_list=["test"],
            existing_docs={},
            force=False,
            error_tracker=error_tracker,
            console=console,
            workers=1,
        )

        assert extracted == 1
        assert skipped == 0
        assert failed == 0

        # Verify files were created
        json_files = list(temp_output_dir.glob("*.json"))
        assert len(json_files) == 1

    def test_process_files_skip_existing(self, temp_source_dir, temp_output_dir, console):
        """Test skipping existing files."""

        from bloginator.cli.error_reporting import ErrorTracker

        files = [temp_source_dir / "test.md"]

        # First extract to create existing document
        error_tracker = ErrorTracker()
        _process_files(
            files=files,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            existing_docs={},
            force=False,
            error_tracker=error_tracker,
            console=console,
            workers=1,
        )

        # Load existing docs
        from bloginator.cli.extract_utils import load_existing_extractions

        existing_docs = load_existing_extractions(temp_output_dir)

        # Try to extract again (should skip)
        extracted, skipped, failed = _process_files(
            files=files,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            existing_docs=existing_docs,
            force=False,
            error_tracker=error_tracker,
            console=console,
            workers=1,
        )

        assert extracted == 0
        assert skipped == 1
        assert failed == 0

    def test_process_files_force_reextract(self, temp_source_dir, temp_output_dir, console):
        """Test force re-extraction of existing files."""
        from bloginator.cli.error_reporting import ErrorTracker

        files = [temp_source_dir / "test.md"]

        # First extract to create existing document
        error_tracker = ErrorTracker()
        _process_files(
            files=files,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            existing_docs={},
            force=False,
            error_tracker=error_tracker,
            console=console,
            workers=1,
        )

        # Load existing docs
        from bloginator.cli.extract_utils import load_existing_extractions

        existing_docs = load_existing_extractions(temp_output_dir)

        # Force re-extraction
        extracted, skipped, failed = _process_files(
            files=files,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            existing_docs=existing_docs,
            force=True,  # Force re-extraction
            error_tracker=error_tracker,
            console=console,
            workers=1,
        )

        assert extracted == 1
        assert skipped == 0
        assert failed == 0


class TestExtractSingleSource:
    """Tests for extract_single_source function."""

    @patch("bloginator.cli.extract_single._process_files")
    @patch("bloginator.cli.extract_single._collect_files")
    def test_extract_single_source_success(
        self, mock_collect, mock_process, temp_source_dir, temp_output_dir, console
    ):
        """Test successful single source extraction."""
        # Mock file collection
        mock_collect.return_value = [temp_source_dir / "test.md"]

        # Mock processing
        mock_process.return_value = (1, 0, 0)  # extracted, skipped, failed

        extract_single_source(
            source=temp_source_dir,
            output=temp_output_dir,
            quality="preferred",
            tag_list=["test"],
            console=console,
            force=False,
            workers=None,
        )

        mock_collect.assert_called_once_with(temp_source_dir)
        mock_process.assert_called_once()

    @patch("bloginator.cli.extract_single._collect_files")
    def test_extract_single_source_no_files(
        self, mock_collect, temp_source_dir, temp_output_dir, console
    ):
        """Test extraction with no files found."""
        # Mock empty file collection
        mock_collect.return_value = []

        extract_single_source(
            source=temp_source_dir,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            console=console,
            force=False,
            workers=None,
        )

        # Should return early without processing
        mock_collect.assert_called_once()

    @patch("bloginator.cli.extract_single._process_files")
    @patch("bloginator.cli.extract_single._collect_files")
    def test_extract_single_source_with_failures(
        self, mock_collect, mock_process, temp_source_dir, temp_output_dir, console
    ):
        """Test extraction with some failures."""
        # Mock file collection
        mock_collect.return_value = [
            temp_source_dir / "test1.md",
            temp_source_dir / "test2.md",
        ]

        # Mock processing with failures
        mock_process.return_value = (1, 0, 1)  # extracted, skipped, failed

        extract_single_source(
            source=temp_source_dir,
            output=temp_output_dir,
            quality="preferred",
            tag_list=[],
            console=console,
            force=False,
            workers=2,
        )

        mock_process.assert_called_once()
        # Verify workers parameter was passed
        call_kwargs = mock_process.call_args.kwargs
        assert call_kwargs["workers"] == 2


class TestSupportedExtensions:
    """Tests for supported file extensions."""

    def test_doc_extension_supported(self):
        """Test that .doc extension is in supported extensions."""
        extensions = get_supported_extensions()
        assert ".doc" in extensions

    def test_docx_extension_supported(self):
        """Test that .docx extension is in supported extensions."""
        extensions = get_supported_extensions()
        assert ".docx" in extensions

    def test_all_expected_extensions_supported(self):
        """Test all expected document formats are supported."""
        extensions = get_supported_extensions()
        # Core document formats that must be supported
        required = {".pdf", ".docx", ".doc", ".md", ".markdown", ".txt"}
        assert required.issubset(
            extensions
        ), f"Missing required extensions: {required - extensions}"


class TestEmptyFileDetection:
    """Tests for empty file and empty content detection."""

    def test_extract_empty_file_raises(self, temp_output_dir):
        """Test that extracting an empty file raises FileNotFoundError (OneDrive timeout)."""
        import tempfile
        from pathlib import Path

        from bloginator.cli.extract_single import _extract_and_save_document

        # Create an empty file (simulates OneDrive placeholder)
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            empty_file = f.name
        # File exists but is 0 bytes - wait_for_file_availability will timeout

        # Empty files trigger wait_for_file_availability timeout (OneDrive protection)
        with pytest.raises(FileNotFoundError) as exc_info:
            _extract_and_save_document(
                file_path=Path(empty_file),
                output=temp_output_dir,
                quality="preferred",
                tag_list=["test"],
            )

        # Check for any of the expected error message patterns
        error_msg = str(exc_info.value).lower()
        assert any(x in error_msg for x in ["onedrive", "timeout", "not available", "cloud"])

        # Cleanup
        Path(empty_file).unlink()

    def test_extract_whitespace_only_file_raises(self, temp_output_dir, tmp_path):
        """Test that extracting a whitespace-only file raises ValueError."""
        from bloginator.cli.extract_single import _extract_and_save_document

        # Create a file with only whitespace
        whitespace_file = tmp_path / "whitespace.txt"
        whitespace_file.write_text("   \n\n\t\t  \n  ")

        with pytest.raises(ValueError) as exc_info:
            _extract_and_save_document(
                file_path=whitespace_file,
                output=temp_output_dir,
                quality="preferred",
                tag_list=["test"],
            )

        assert "no extractable text" in str(exc_info.value).lower()
