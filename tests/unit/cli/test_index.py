"""Tests for index CLI command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from bloginator.cli.index import index


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_source(tmp_path):
    """Create temporary source directory with extracted documents."""
    source_dir = tmp_path / "extracted"
    source_dir.mkdir()

    # Create test document metadata
    doc_data = {
        "id": "test-doc-1",
        "title": "Test Document",
        "content": "This is test content.",
        "source_path": "test.md",
        "quality": "preferred",
        "tags": ["test"],
        "written_date": "2024-01-01",
        "extracted_date": "2024-01-15",
    }

    # Write metadata JSON
    meta_file = source_dir / "test-doc-1.json"
    meta_file.write_text(json.dumps(doc_data))

    # Write content TXT
    txt_file = source_dir / "test-doc-1.txt"
    txt_file.write_text("This is test content.")

    return source_dir


@pytest.fixture
def temp_output(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "index"
    return output_dir


class TestIndexCLI:
    """Tests for index CLI command."""

    def test_index_requires_output(self, runner, temp_source):
        """Test that index requires output directory."""
        result = runner.invoke(index, [str(temp_source)])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_index_requires_source(self, runner, temp_output):
        """Test that index requires source directory."""
        result = runner.invoke(index, ["-o", str(temp_output)])
        assert result.exit_code != 0

    @patch("bloginator.cli.index.CorpusIndexer")
    def test_index_no_documents_found(self, mock_indexer_class, runner, tmp_path, temp_output):
        """Test index with empty source directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = runner.invoke(index, [str(empty_dir), "-o", str(temp_output)])

        assert result.exit_code == 0
        assert "No Documents Found" in result.output or "No extracted documents" in result.output

    @patch("bloginator.cli.index.CorpusIndexer")
    @patch("bloginator.cli.index.chunk_text_by_paragraphs")
    def test_index_success(self, mock_chunk, mock_indexer_class, runner, temp_source, temp_output):
        """Test successful indexing."""
        # Setup mocks
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer
        mock_indexer.document_needs_reindexing.return_value = True
        mock_indexer.get_document_checksum.return_value = None
        mock_chunk.return_value = ["chunk1", "chunk2"]

        result = runner.invoke(index, [str(temp_source), "-o", str(temp_output)])

        # Just verify it ran without crashing
        assert result.exit_code == 0
        mock_indexer_class.assert_called_once()

    @patch("bloginator.cli.index.CorpusIndexer")
    def test_index_with_custom_chunk_size(
        self, mock_indexer_class, runner, temp_source, temp_output
    ):
        """Test index with custom chunk size."""
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer
        mock_indexer.document_needs_reindexing.return_value = False

        result = runner.invoke(
            index,
            [str(temp_source), "-o", str(temp_output), "--chunk-size", "500"],
        )

        assert result.exit_code == 0

    @patch("bloginator.cli.index.CorpusIndexer")
    @patch("bloginator.cli.index.chunk_text_by_paragraphs")
    def test_index_skips_unchanged_documents(
        self, mock_chunk, mock_indexer_class, runner, temp_source, temp_output
    ):
        """Test that index skips documents that don't need reindexing."""
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer
        mock_indexer.document_needs_reindexing.return_value = False

        result = runner.invoke(index, [str(temp_source), "-o", str(temp_output)])

        assert result.exit_code == 0
        mock_indexer.index_document.assert_not_called()

    @patch("bloginator.cli.index.CorpusIndexer")
    @patch("bloginator.cli.index.chunk_text_by_paragraphs")
    def test_index_reindexes_changed_documents(
        self, mock_chunk, mock_indexer_class, runner, temp_source, temp_output
    ):
        """Test that index reindexes changed documents."""
        mock_indexer = MagicMock()
        mock_indexer_class.return_value = mock_indexer
        mock_indexer.document_needs_reindexing.return_value = True
        mock_indexer.get_document_checksum.return_value = "old_checksum"
        mock_chunk.return_value = ["chunk1"]

        result = runner.invoke(index, [str(temp_source), "-o", str(temp_output)])

        # Just verify it ran without crashing
        assert result.exit_code == 0

    @patch("bloginator.cli.index.CorpusIndexer")
    def test_index_handles_initialization_error(
        self, mock_indexer_class, runner, temp_source, temp_output
    ):
        """Test index handles indexer initialization errors."""
        mock_indexer_class.side_effect = Exception("Initialization failed")

        result = runner.invoke(index, [str(temp_source), "-o", str(temp_output)])

        assert result.exit_code != 0
        assert "Initialization Failed" in result.output or "Failed to initialize" in result.output
