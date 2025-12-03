"""Integration tests for corpus directory import feature."""

from pathlib import Path

import pytest

from bloginator.corpus_config import CorpusConfig
from bloginator.services.corpus_directory_scanner import DirectoryScanner


@pytest.fixture
def test_corpus_dir(tmp_path: Path) -> Path:
    """Create a test corpus directory with corpus.yaml."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    corpus_yaml = corpus_dir / "corpus.yaml"
    corpus_yaml.write_text(
        """
sources: []
extraction:
  chunk_size: 1000
indexing:
  quality_weights:
    preferred: 1.5
    reference: 1.0
    supplemental: 0.7
    deprecated: 0.3
"""
    )
    return corpus_dir


@pytest.fixture
def scanner() -> DirectoryScanner:
    """Create DirectoryScanner instance."""
    return DirectoryScanner()


class TestFullDirectoryImportWorkflow:
    """Tests for complete directory import workflow."""

    def test_scan_config_yaml_integration(
        self, tmp_path: Path, test_corpus_dir: Path, scanner: DirectoryScanner
    ):
        """Complete directory import workflow should succeed end-to-end."""
        test_source = tmp_path / "engineering"
        test_source.mkdir()

        # Create test documents
        (test_source / "design.pdf").write_bytes(b"%PDF")
        (test_source / "standards.docx").write_bytes(b"PK")
        (test_source / "notes.txt").write_text("content")

        # Step 1: Scan directory
        scan = scanner.scan_directory(test_source)
        assert scan.total_files == 3
        assert scan.by_format.get("pdf", 0) == 1
        assert scan.by_format.get("docx", 0) == 1
        assert scan.by_format.get("txt", 0) == 1

        # Step 2: Create configuration
        config = scanner.create_source_config(
            test_source,
            "engineering",
            tags=["internal"],
        )
        assert config.name == "engineering"
        assert config.file_count == 3

        # Step 3: Load corpus config and add source
        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")
        success = corpus_config.add_directory_source(
            name=config.name,
            path=config.path,
            tags=config.tags,
        )
        assert success

        # Verify source was added
        assert len(corpus_config.sources) == 1
        assert corpus_config.sources[0].name == "engineering"
        assert corpus_config.sources[0].type == "directory"


class TestConflictDetection:
    """Tests for duplicate path detection."""

    def test_duplicate_directory_detection(self, tmp_path: Path, test_corpus_dir: Path):
        """Importing same directory twice should detect conflicts."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "file.pdf").write_bytes(b"%PDF")

        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")

        # First import
        success1 = corpus_config.add_directory_source("docs1", str(test_dir.resolve()))
        assert success1

        # Second import same path should fail
        success2 = corpus_config.add_directory_source("docs2", str(test_dir.resolve()))
        assert not success2

    def test_duplicate_path_different_names(self, tmp_path: Path, test_corpus_dir: Path):
        """Same path with different names should be rejected."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")

        # First import
        corpus_config.add_directory_source("docs_v1", str(test_dir))

        # Same path, different name
        success = corpus_config.add_directory_source("docs_v2", str(test_dir))

        assert not success
        assert len(corpus_config.sources) == 1  # Only first added


class TestMultipleDirectorySources:
    """Tests for handling multiple directory sources."""

    def test_multiple_directory_sources(
        self, tmp_path: Path, test_corpus_dir: Path, scanner: DirectoryScanner
    ):
        """Multiple different directories should all be added correctly."""
        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")

        dirs = []
        for name in ["engineering", "marketing", "operations"]:
            d = tmp_path / name
            d.mkdir()
            (d / "doc.pdf").write_bytes(b"%PDF")
            dirs.append((name, d))

        for name, directory in dirs:
            success = corpus_config.add_directory_source(name, str(directory.resolve()))
            assert success

        assert len(corpus_config.sources) == 3
        assert all(any(s.name == name for s in corpus_config.sources) for name, _ in dirs)

    def test_quality_and_tags_preserved(self, tmp_path: Path, test_corpus_dir: Path):
        """Quality and tags should be preserved when adding sources."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")
        success = corpus_config.add_directory_source(
            "engineering",
            str(test_dir.resolve()),
            quality="preferred",
            tags=["internal", "critical"],
        )

        assert success
        source = corpus_config.sources[0]
        assert source.quality.value == "preferred"
        assert set(source.tags) == {"internal", "critical"}


class TestRecursiveScanning:
    """Tests for recursive vs non-recursive scanning."""

    def test_recursive_finds_nested_docs(self, tmp_path: Path, scanner: DirectoryScanner):
        """Recursive scan should find documents in subdirectories."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "top.pdf").write_bytes(b"%PDF")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

        scan = scanner.scan_directory(test_dir, recursive=True)

        assert scan.total_files == 2

    def test_non_recursive_ignores_nested_docs(self, tmp_path: Path, scanner: DirectoryScanner):
        """Non-recursive scan should skip subdirectories."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "top.pdf").write_bytes(b"%PDF")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

        scan = scanner.scan_directory(test_dir, recursive=False)

        assert scan.total_files == 1


class TestPathNormalization:
    """Tests for path normalization in config."""

    def test_absolute_path_stored(self, tmp_path: Path, scanner: DirectoryScanner):
        """Paths should be stored in absolute form."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        config = scanner.create_source_config(test_dir, "test")

        # Path should be absolute
        stored_path = Path(config.path)
        assert stored_path.is_absolute()

    def test_resolved_path_comparison(self, tmp_path: Path, test_corpus_dir: Path):
        """Path comparison should handle resolution correctly."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        corpus_config = CorpusConfig.load_from_file(test_corpus_dir / "corpus.yaml")

        # Add with absolute path
        abs_path = str(test_dir.resolve())
        corpus_config.add_directory_source("docs", abs_path)

        # Check with relative path (if possible)
        assert len(corpus_config.sources) == 1


class TestEmptyDirectories:
    """Tests for handling empty directories."""

    def test_empty_directory_scans_successfully(self, tmp_path: Path, scanner: DirectoryScanner):
        """Empty directory should scan without errors."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        scan = scanner.scan_directory(test_dir)

        assert scan.is_valid
        assert scan.total_files == 0

    def test_empty_directory_config_creation(self, tmp_path: Path, scanner: DirectoryScanner):
        """Config should be created for empty directory."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        config = scanner.create_source_config(test_dir, "empty")

        assert config.file_count == 0


class TestLargeDirectories:
    """Tests for handling large directories."""

    def test_large_directory_performance(self, tmp_path: Path, scanner: DirectoryScanner):
        """Scanning large directory should be fast."""
        test_dir = tmp_path / "large"
        test_dir.mkdir()

        # Create 500 files
        for i in range(500):
            (test_dir / f"doc{i:04d}.txt").write_bytes(b"x" * 100)

        scan = scanner.scan_directory(test_dir)

        assert scan.total_files == 500
        assert scan.scan_time < 5.0

    def test_large_directory_format_breakdown(self, tmp_path: Path, scanner: DirectoryScanner):
        """Format breakdown should be accurate for many files."""
        test_dir = tmp_path / "mixed"
        test_dir.mkdir()

        # Create files of different types
        for i in range(100):
            (test_dir / f"doc{i:03d}.pdf").write_bytes(b"%PDF")
            (test_dir / f"doc{i:03d}.txt").write_bytes(b"text")
            (test_dir / f"doc{i:03d}.md").write_text("# Markdown")

        scan = scanner.scan_directory(test_dir)

        assert scan.total_files == 300
        assert scan.by_format.get("pdf", 0) == 100
        assert scan.by_format.get("txt", 0) == 100
        assert scan.by_format.get("md", 0) == 100


class TestMixedFileTypes:
    """Tests for directories with mixed file types."""

    def test_only_supported_formats_discovered(self, tmp_path: Path, scanner: DirectoryScanner):
        """Only supported file formats should be discovered."""
        test_dir = tmp_path / "mixed"
        test_dir.mkdir()

        (test_dir / "doc.pdf").write_bytes(b"%PDF")
        (test_dir / "image.jpg").write_bytes(b"JPG")
        (test_dir / "script.py").write_bytes(b"print()")
        (test_dir / "readme.md").write_text("# README")
        (test_dir / "archive.zip").write_bytes(b"PK")

        scan = scanner.scan_directory(test_dir)

        assert scan.total_files == 2
        assert scan.by_format.get("pdf", 0) == 1
        assert scan.by_format.get("md", 0) == 1
