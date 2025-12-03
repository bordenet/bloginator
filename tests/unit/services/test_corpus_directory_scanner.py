"""Unit tests for DirectoryScanner service."""

import time
from pathlib import Path

import pytest

from bloginator.services.corpus_directory_scanner import (
    DirectoryScanner,
    FileInfo,
    ScanResult,
    SourceConfig,
)


@pytest.fixture
def scanner() -> DirectoryScanner:
    """Create DirectoryScanner instance."""
    return DirectoryScanner()


class TestPathValidation:
    """Tests for directory path validation."""

    def test_validate_directory_valid(self, tmp_path: Path, scanner: DirectoryScanner):
        """Valid, readable directory should pass validation."""
        test_dir = tmp_path / "test_corpus"
        test_dir.mkdir()

        is_valid, error = scanner.validate_directory(test_dir)

        assert is_valid
        assert error == ""

    def test_validate_directory_not_found(self, tmp_path: Path, scanner: DirectoryScanner):
        """Non-existent directory should fail validation."""
        missing_dir = tmp_path / "missing"

        is_valid, error = scanner.validate_directory(missing_dir)

        assert not is_valid
        assert "not found" in error.lower()

    def test_validate_directory_is_file(self, tmp_path: Path, scanner: DirectoryScanner):
        """Path to file should be rejected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        is_valid, error = scanner.validate_directory(test_file)

        assert not is_valid
        assert "file" in error.lower() or "directory" in error.lower()

    def test_validate_directory_permission_denied(self, tmp_path: Path, scanner: DirectoryScanner):
        """Directory without read permissions should fail gracefully."""
        test_dir = tmp_path / "restricted"
        test_dir.mkdir()
        test_dir.chmod(0o000)

        try:
            is_valid, error = scanner.validate_directory(test_dir)
            assert not is_valid
            assert "permission" in error.lower()
        finally:
            test_dir.chmod(0o755)  # Cleanup


class TestFormatDetection:
    """Tests for file format detection."""

    @pytest.mark.parametrize("ext", [".pdf", ".docx", ".txt", ".md"])
    def test_is_supported_format(self, ext: str, scanner: DirectoryScanner):
        """Supported file extensions should be recognized."""
        assert scanner._is_supported_format(f"document{ext}")
        assert scanner._is_supported_format(f"DOCUMENT{ext.upper()}")

    @pytest.mark.parametrize("ext", [".exe", ".jpg", ".zip", ".html", ".py"])
    def test_is_unsupported_format(self, ext: str, scanner: DirectoryScanner):
        """Unsupported file extensions should be rejected."""
        assert not scanner._is_supported_format(f"file{ext}")

    def test_hidden_files_skipped(self, tmp_path: Path, scanner: DirectoryScanner):
        """Hidden files should not be included in scan."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        (test_dir / "visible.pdf").write_bytes(b"%PDF")
        (test_dir / ".hidden.pdf").write_bytes(b"%PDF")

        result = scanner.scan_directory(test_dir)

        assert result.total_files == 1
        assert any(str(f.path).endswith("visible.pdf") for f in result.files)
        assert not any(".hidden.pdf" in str(f.path) for f in result.files)


class TestDirectoryScanning:
    """Tests for directory scanning."""

    def test_scan_directory_flat(self, tmp_path: Path, scanner: DirectoryScanner):
        """Scanning flat directory should find all documents."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        # Create test files
        (test_dir / "doc1.pdf").write_bytes(b"%PDF")
        (test_dir / "doc2.docx").write_bytes(b"PK")  # ZIP magic bytes
        (test_dir / "doc3.txt").write_text("content")

        result = scanner.scan_directory(test_dir, recursive=False)

        assert result.is_valid
        assert result.total_files == 3
        assert result.by_format.get("pdf", 0) == 1
        assert result.by_format.get("docx", 0) == 1
        assert result.by_format.get("txt", 0) == 1

    def test_scan_directory_recursive(self, tmp_path: Path, scanner: DirectoryScanner):
        """Recursive scan should find documents in subdirectories."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "subdir").mkdir()

        (test_dir / "top.pdf").write_bytes(b"%PDF")
        (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

        result = scanner.scan_directory(test_dir, recursive=True)

        assert result.total_files == 2
        assert any("nested.pdf" in str(f.path) for f in result.files)

    def test_scan_directory_non_recursive(self, tmp_path: Path, scanner: DirectoryScanner):
        """Non-recursive scan should ignore subdirectories."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "subdir").mkdir()

        (test_dir / "top.pdf").write_bytes(b"%PDF")
        (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

        result = scanner.scan_directory(test_dir, recursive=False)

        assert result.total_files == 1
        assert not any("nested.pdf" in str(f.path) for f in result.files)

    def test_scan_performance_large_directory(self, tmp_path: Path, scanner: DirectoryScanner):
        """Scanning 1000+ files should complete in <5 seconds."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        # Create 1000 dummy files
        for i in range(1000):
            (test_dir / f"doc{i:04d}.txt").write_bytes(b"x" * 1000)

        start = time.time()
        result = scanner.scan_directory(test_dir)
        elapsed = time.time() - start

        assert result.total_files == 1000
        assert elapsed < 5.0  # Must complete in <5 seconds

    def test_scan_empty_directory(self, tmp_path: Path, scanner: DirectoryScanner):
        """Scanning empty directory should return valid result with zero files."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        result = scanner.scan_directory(test_dir)

        assert result.is_valid
        assert result.total_files == 0
        assert result.files == []

    def test_scan_mixed_content(self, tmp_path: Path, scanner: DirectoryScanner):
        """Scan should ignore non-supported files."""
        test_dir = tmp_path / "mixed"
        test_dir.mkdir()

        (test_dir / "doc.pdf").write_bytes(b"%PDF")
        (test_dir / "image.jpg").write_bytes(b"JPG")
        (test_dir / "script.py").write_bytes(b"print()")
        (test_dir / "readme.md").write_text("# README")

        result = scanner.scan_directory(test_dir)

        assert result.total_files == 2
        assert result.by_format.get("pdf", 0) == 1
        assert result.by_format.get("md", 0) == 1


class TestPatternFiltering:
    """Tests for pattern-based file filtering."""

    def test_scan_with_pattern_filter(self, tmp_path: Path, scanner: DirectoryScanner):
        """Pattern filter should include/exclude files."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        (test_dir / "2024_report.pdf").write_bytes(b"%PDF")
        (test_dir / "2025_report.pdf").write_bytes(b"%PDF")
        (test_dir / "notes.txt").write_text("content")

        # Only 2024 files
        result = scanner.scan_directory(test_dir, pattern=r"2024")

        assert result.total_files == 1
        assert "2024_report" in str(result.files[0].path)

    def test_scan_pattern_no_matches(self, tmp_path: Path, scanner: DirectoryScanner):
        """Pattern with no matches should return empty result."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        (test_dir / "2024_report.pdf").write_bytes(b"%PDF")

        result = scanner.scan_directory(test_dir, pattern=r"2023")

        assert result.total_files == 0


class TestSymlinkHandling:
    """Tests for symlink handling."""

    def test_symlink_loop_detected(self, tmp_path: Path, scanner: DirectoryScanner):
        """Symlink creating infinite loop should be detected."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        # Create symlink loop
        loop_link = test_dir / "loop"
        loop_link.symlink_to(test_dir)

        # Should not infinitely recurse
        result = scanner.scan_directory(test_dir)

        assert result.is_valid
        # May or may not have files depending on loop detection

    def test_symlinks_not_followed_by_default(self, tmp_path: Path, scanner: DirectoryScanner):
        """By default, symlinks should not be followed."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        external_dir = tmp_path / "external"
        external_dir.mkdir()

        (test_dir / "local.pdf").write_bytes(b"%PDF")
        (external_dir / "external.pdf").write_bytes(b"%PDF")
        (test_dir / "link_to_external").symlink_to(external_dir)

        result = scanner.scan_directory(test_dir, follow_symlinks=False)

        assert result.total_files == 1
        assert "local.pdf" in str(result.files[0].path)

    def test_symlinks_followed_when_enabled(self, tmp_path: Path, scanner: DirectoryScanner):
        """When follow_symlinks=True, symlinks should be traversed."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        external_dir = tmp_path / "external"
        external_dir.mkdir()

        (test_dir / "local.pdf").write_bytes(b"%PDF")
        (external_dir / "external.pdf").write_bytes(b"%PDF")
        (test_dir / "link").symlink_to(external_dir)

        result = scanner.scan_directory(test_dir, follow_symlinks=True)

        assert result.total_files == 2
        assert any("local.pdf" in str(f.path) for f in result.files)
        assert any("external.pdf" in str(f.path) for f in result.files)


class TestConfigurationCreation:
    """Tests for source configuration creation."""

    def test_create_source_config(self, tmp_path: Path, scanner: DirectoryScanner):
        """Source config should be generated with correct metadata."""
        test_dir = tmp_path / "engineering"
        test_dir.mkdir()
        (test_dir / "doc.pdf").write_bytes(b"%PDF")

        config = scanner.create_source_config(
            test_dir,
            source_name="engineering",
            tags=["internal"],
            quality="reference",
        )

        assert config.name == "engineering"
        assert config.tags == ["internal"]
        assert config.quality == "reference"
        assert config.recursive is True
        assert config.file_count == 1

    def test_create_source_config_with_voice_notes(self, tmp_path: Path, scanner: DirectoryScanner):
        """Source config should include voice notes."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        voice_notes = "Important documentation"
        config = scanner.create_source_config(
            test_dir,
            source_name="docs",
            voice_notes=voice_notes,
        )

        assert config.voice_notes == voice_notes

    def test_create_source_config_path_absolute(self, tmp_path: Path, scanner: DirectoryScanner):
        """Path in config should be absolute."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        config = scanner.create_source_config(test_dir, "test")

        # Path should be absolute
        assert Path(config.path).is_absolute()

    def test_create_source_config_empty_directory(self, tmp_path: Path, scanner: DirectoryScanner):
        """Config creation should work for empty directories."""
        test_dir = tmp_path / "empty"
        test_dir.mkdir()

        config = scanner.create_source_config(test_dir, "empty")

        assert config.file_count == 0
        assert config.name == "empty"


class TestScanResultDataclass:
    """Tests for ScanResult dataclass."""

    def test_scan_result_initialization(self, tmp_path: Path):
        """ScanResult should initialize with default values."""
        result = ScanResult(directory=tmp_path, total_files=0)

        assert result.directory == tmp_path
        assert result.total_files == 0
        assert result.files == []
        assert result.by_format == {}
        assert result.total_size == 0
        assert result.is_valid is True
        assert result.error is None

    def test_scan_result_with_files(self, tmp_path: Path):
        """ScanResult should track file information."""
        file_info = FileInfo(
            path=tmp_path / "test.pdf",
            format="pdf",
            size=1000,
            readable=True,
        )
        result = ScanResult(
            directory=tmp_path,
            total_files=1,
            files=[file_info],
            by_format={"pdf": 1},
            total_size=1000,
        )

        assert result.total_files == 1
        assert len(result.files) == 1
        assert result.by_format["pdf"] == 1
        assert result.total_size == 1000


class TestSourceConfigDataclass:
    """Tests for SourceConfig dataclass."""

    def test_source_config_defaults(self):
        """SourceConfig should use sensible defaults."""
        config = SourceConfig(name="test", path="/tmp/test")

        assert config.enabled is True
        assert config.quality == "reference"
        assert config.tags == []
        assert config.is_external is False
        assert config.voice_notes == ""
        assert config.recursive is True

    def test_source_config_custom_values(self):
        """SourceConfig should accept custom values."""
        config = SourceConfig(
            name="engineering",
            path="/path/to/docs",
            enabled=False,
            quality="preferred",
            tags=["internal", "critical"],
            is_external=True,
            voice_notes="Important docs",
            recursive=False,
            file_count=42,
        )

        assert config.name == "engineering"
        assert config.enabled is False
        assert config.quality == "preferred"
        assert config.tags == ["internal", "critical"]
        assert config.is_external is True
        assert config.voice_notes == "Important docs"
        assert config.recursive is False
        assert config.file_count == 42


class TestDepthLimiting:
    """Tests for recursion depth limiting."""

    def test_depth_limit_respected(self, tmp_path: Path):
        """Scanner should respect max_depth parameter."""
        scanner = DirectoryScanner(max_depth=3)
        test_dir = tmp_path / "level0"
        test_dir.mkdir()

        # Create nested structure
        (test_dir / "doc.txt").write_text("0")
        level1 = test_dir / "level1"
        level1.mkdir()
        (level1 / "doc.txt").write_text("1")
        level2 = level1 / "level2"
        level2.mkdir()
        (level2 / "doc.txt").write_text("2")
        level3 = level2 / "level3"
        level3.mkdir()
        (level3 / "doc.txt").write_text("3")

        result = scanner.scan_directory(test_dir, recursive=True)

        # Depth starts at 0, so max_depth=3 allows depths 0,1,2 (3 levels)
        assert result.total_files == 3
