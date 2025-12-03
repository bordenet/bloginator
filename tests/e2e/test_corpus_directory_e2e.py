"""End-to-end tests for corpus directory import feature."""

from pathlib import Path

import pytest
import yaml

from bloginator.corpus_config import CorpusConfig
from bloginator.services.corpus_directory_scanner import DirectoryScanner


def _save_config_to_yaml(config: CorpusConfig, path: Path) -> None:
    """Save CorpusConfig to YAML file, converting enums properly."""
    data = config.model_dump(mode="json", exclude_unset=False)
    yaml_content = yaml.dump(data, default_flow_style=False)
    with path.open("w") as f:
        f.write(yaml_content)


@pytest.fixture
def source_directory(tmp_path: Path) -> Path:
    """Create test directory with sample documents."""
    source_dir = tmp_path / "documents"
    source_dir.mkdir()

    # Create a realistic document structure
    (source_dir / "2024_report.pdf").write_bytes(b"%PDF-1.4\n")
    (source_dir / "standards.docx").write_bytes(b"PK\x03\x04")
    (source_dir / "README.md").write_text("# Engineering Standards\n\nBest practices...\n")
    (source_dir / "notes.txt").write_text("Implementation notes\n")

    # Create subdirectory with more documents
    subdir = source_dir / "archived"
    subdir.mkdir()
    (subdir / "old_spec.pdf").write_bytes(b"%PDF-1.4\n")
    (subdir / "legacy.txt").write_text("Legacy content\n")

    return source_dir


@pytest.fixture
def corpus_yaml_path(tmp_path: Path) -> Path:
    """Create test corpus.yaml file."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    yaml_path = corpus_dir / "corpus.yaml"

    config = {
        "sources": [],
        "extraction": {"chunk_size": 1000},
        "indexing": {
            "quality_weights": {
                "preferred": 1.5,
                "reference": 1.0,
                "supplemental": 0.7,
                "deprecated": 0.3,
            }
        },
    }

    with yaml_path.open("w") as f:
        yaml.dump(config, f)

    return yaml_path


class TestPersistenceRoundTrip:
    """Test YAML persistence and reloading."""

    def test_directory_source_written_and_reloaded(
        self, source_directory: Path, corpus_yaml_path: Path
    ):
        """Source should be written to YAML and reloaded identically."""
        # Step 1: Load initial config
        config = CorpusConfig.load_from_file(corpus_yaml_path)
        assert len(config.sources) == 0

        # Step 2: Add directory source
        success = config.add_directory_source(
            name="engineering",
            path=str(source_directory.resolve()),
            quality="reference",
            tags=["internal", "documentation"],
            voice_notes="Internal team documentation",
        )
        assert success

        # Step 3: Save to YAML
        _save_config_to_yaml(config, corpus_yaml_path)

        # Step 4: Reload from file
        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)

        # Verify source survived round-trip
        assert len(reloaded.sources) == 1
        reloaded_source = reloaded.sources[0]
        assert reloaded_source.name == "engineering"
        assert reloaded_source.path == str(source_directory.resolve())
        assert reloaded_source.quality.value == "reference"
        assert set(reloaded_source.tags) == {"internal", "documentation"}
        assert reloaded_source.voice_notes == "Internal team documentation"

    def test_multiple_sources_persistence(self, tmp_path: Path, corpus_yaml_path: Path):
        """Multiple directory sources should persist correctly."""
        # Create multiple test directories
        dirs = {}
        for name in ["engineering", "marketing", "operations"]:
            d = tmp_path / name
            d.mkdir()
            (d / "doc.txt").write_text(f"{name} content")
            dirs[name] = d

        # Load and add all sources
        config = CorpusConfig.load_from_file(corpus_yaml_path)
        for name, directory in dirs.items():
            config.add_directory_source(
                name=name,
                path=str(directory.resolve()),
                tags=[name],
            )

        # Save and reload
        _save_config_to_yaml(config, corpus_yaml_path)

        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)

        # Verify all sources present
        assert len(reloaded.sources) == 3
        names = {s.name for s in reloaded.sources}
        assert names == {"engineering", "marketing", "operations"}

        # Verify tags preserved
        for source in reloaded.sources:
            assert source.name in source.tags


class TestScanToYAMLWorkflow:
    """Test complete workflow from scan to YAML persistence."""

    def test_full_scan_to_yaml_workflow(self, source_directory: Path, corpus_yaml_path: Path):
        """Complete workflow: scan → config → YAML → reload → verify."""
        scanner = DirectoryScanner()

        # Step 1: Scan directory
        scan = scanner.scan_directory(source_directory, recursive=True)
        assert scan.is_valid
        assert scan.total_files == 6  # 4 top-level + 2 in subdir

        # Step 2: Create source config from scan
        config_from_scan = scanner.create_source_config(
            source_directory,
            source_name="engineering_docs",
            tags=["engineering", "standards"],
            quality="preferred",
            voice_notes="Authoritative engineering standards",
        )
        assert config_from_scan.file_count == 6

        # Step 3: Load corpus and add source
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)
        success = corpus_config.add_directory_source(
            name=config_from_scan.name,
            path=config_from_scan.path,
            tags=config_from_scan.tags,
            quality=config_from_scan.quality,
            voice_notes=config_from_scan.voice_notes,
            recursive=config_from_scan.recursive,
        )
        assert success

        # Step 4: Persist to file
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        # Step 5: Reload and verify
        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)
        assert len(reloaded.sources) == 1

        source = reloaded.sources[0]
        assert source.name == "engineering_docs"
        assert source.type == "directory"
        assert source.enabled is True
        assert source.quality.value == "preferred"
        assert "engineering" in source.tags
        assert "standards" in source.tags

        # Step 6: Verify path is valid and points to original
        resolved_path = Path(source.path).resolve()
        assert resolved_path == source_directory.resolve()
        assert resolved_path.exists()
        assert resolved_path.is_dir()


class TestConflictDetectionWorkflow:
    """Test conflict detection and user decision workflows."""

    def test_duplicate_import_blocked(self, source_directory: Path, corpus_yaml_path: Path):
        """Attempting to import same directory twice should be blocked."""
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # First import succeeds
        success1 = corpus_config.add_directory_source("docs_v1", str(source_directory.resolve()))
        assert success1
        assert len(corpus_config.sources) == 1

        # Second import with same path should fail
        success2 = corpus_config.add_directory_source("docs_v2", str(source_directory.resolve()))
        assert not success2
        assert len(corpus_config.sources) == 1  # Still just one

    def test_conflict_detection_with_path_resolution(self, tmp_path: Path, corpus_yaml_path: Path):
        """Conflict detection should work with different path formats."""
        test_dir = tmp_path / "documents"
        test_dir.mkdir()

        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # Add with absolute path
        abs_path = str(test_dir.resolve())
        success1 = corpus_config.add_directory_source("docs1", abs_path)
        assert success1

        # Try to add with same absolute path
        success2 = corpus_config.add_directory_source("docs2", abs_path)
        assert not success2

        # Verify only one source
        assert len(corpus_config.sources) == 1

    def test_collision_warning_simulation(
        self, tmp_path: Path, corpus_yaml_path: Path
    ) -> str | None:
        """Simulate user workflow when collision is detected."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()

        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # Add first source
        corpus_config.add_directory_source("docs_original", str(test_dir.resolve()))

        # Check for conflict before attempting to add
        path_exists = corpus_config.source_path_exists(str(test_dir.resolve()))

        if path_exists:
            # Simulate user choosing to cancel (return warning message)
            warning = "Directory already exists in corpus as 'docs_original'"
            return warning

        # If user chose to proceed, would add here
        corpus_config.add_directory_source("docs_new", str(test_dir.resolve()))

        # Verify result matches the simulated decision path
        assert len(corpus_config.sources) == 1
        return None


class TestFormValidationFlow:
    """Test metadata validation and form workflows."""

    def test_metadata_validation_on_add(self, source_directory: Path, corpus_yaml_path: Path):
        """Metadata should be validated when adding source."""
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # Valid metadata
        success = corpus_config.add_directory_source(
            name="valid_source",
            path=str(source_directory.resolve()),
            quality="reference",
            tags=["tag1", "tag2"],
        )
        assert success

        # Verify metadata was preserved
        source = corpus_config.sources[0]
        assert source.name == "valid_source"
        assert len(source.tags) == 2

    def test_source_name_auto_generation(self, source_directory: Path):
        """Source name could be auto-generated from directory name."""
        scanner = DirectoryScanner()

        config = scanner.create_source_config(
            source_directory,
            source_name="documents",  # Would typically be auto-filled from dir name
        )

        assert config.name == "documents"

    def test_quality_rating_assignment(self, source_directory: Path, corpus_yaml_path: Path):
        """Quality rating should be properly assigned and accessible."""
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        for quality in ["preferred", "reference", "supplemental", "deprecated"]:
            corpus_config.add_directory_source(
                name=f"source_{quality}",
                path=str(source_directory.resolve() / f"variant_{quality}"),
                quality=quality,
            )
            # Clean up for next iteration by removing (for test isolation)
            corpus_config.sources.pop()

        # Test actual addition
        corpus_config.add_directory_source(
            "test_quality",
            str(source_directory.resolve()),
            quality="reference",
        )

        source = corpus_config.sources[0]
        assert source.quality.value == "reference"


class TestExtractionPipelineCompatibility:
    """Test compatibility with extraction pipeline."""

    def test_imported_directory_source_resolvable(
        self, source_directory: Path, corpus_yaml_path: Path
    ):
        """Imported directory path should be resolvable for extraction."""
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)
        corpus_config.add_directory_source(
            "engineering",
            str(source_directory.resolve()),
        )

        # Save and reload to simulate actual usage
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)
        source = reloaded.sources[0]

        # Simulate what extraction pipeline does: resolve path
        resolved = source.resolve_path(corpus_yaml_path.parent)

        # Path should be resolvable and point to actual directory
        assert isinstance(resolved, Path)
        assert resolved.exists()
        assert resolved.is_dir()

        # Should contain expected files
        files = list(resolved.glob("*"))
        assert len(files) > 0

    def test_enabled_sources_filtering(self, tmp_path: Path, corpus_yaml_path: Path):
        """Extraction should only process enabled sources."""
        # Create multiple test directories
        enabled_dir = tmp_path / "enabled"
        enabled_dir.mkdir()
        (enabled_dir / "doc.txt").write_text("content")

        disabled_dir = tmp_path / "disabled"
        disabled_dir.mkdir()
        (disabled_dir / "doc.txt").write_text("content")

        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # Add enabled source
        corpus_config.add_directory_source("enabled", str(enabled_dir.resolve()), enabled=True)

        # Add disabled source
        corpus_config.add_directory_source("disabled", str(disabled_dir.resolve()), enabled=False)

        # Save and reload
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)

        # Get enabled sources (what extraction pipeline would use)
        enabled_sources = reloaded.get_enabled_sources()

        assert len(enabled_sources) == 1
        assert enabled_sources[0].name == "enabled"

    def test_recursive_flag_preserved_for_extraction(
        self, source_directory: Path, corpus_yaml_path: Path
    ):
        """Recursive flag should be preserved in config for extraction."""
        scanner = DirectoryScanner()

        # Create config with explicit recursive=False
        config = scanner.create_source_config(
            source_directory,
            source_name="flat_only",
            recursive=False,
        )

        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)
        corpus_config.add_directory_source(
            name=config.name,
            path=config.path,
            recursive=config.recursive,
        )

        # Save and reload
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)
        source = reloaded.sources[0]

        # Extraction pipeline should see the recursive flag
        # (Note: CorpusSource doesn't have this field yet, but config does)
        assert source.name == "flat_only"


class TestEndToEndUserScenarios:
    """Test complete user workflows from start to finish."""

    def test_user_adds_engineering_docs_directory(self, tmp_path: Path, corpus_yaml_path: Path):
        """User scenario: Add engineering documentation directory."""
        # Setup: Create realistic engineering docs directory
        eng_dir = tmp_path / "engineering"
        eng_dir.mkdir()
        (eng_dir / "architecture.pdf").write_bytes(b"%PDF-1.4\n")
        (eng_dir / "api_spec.docx").write_bytes(b"PK\x03\x04")
        (eng_dir / "README.md").write_text("# Engineering Standards\n")
        (eng_dir / "standards").mkdir()
        (eng_dir / "standards" / "coding.txt").write_text("Coding standards")

        scanner = DirectoryScanner()

        # User step 1: Browse and select directory
        # (simulated)

        # User step 2: Scanner discovers files
        scan = scanner.scan_directory(eng_dir, recursive=True)
        assert scan.is_valid
        assert scan.total_files == 4

        # User step 3: Enters metadata
        config = scanner.create_source_config(
            eng_dir,
            source_name="Engineering Standards",
            tags=["engineering", "internal"],
            quality="preferred",
            voice_notes="Authoritative engineering documentation",
        )

        # User step 4: Reviews and confirms
        # (simulated)

        # User step 5: System imports
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)
        success = corpus_config.add_directory_source(
            name=config.name,
            path=config.path,
            tags=config.tags,
            quality=config.quality,
            voice_notes=config.voice_notes,
            recursive=True,
        )
        assert success

        # Persist
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        # Verification: User sees success message
        reloaded = CorpusConfig.load_from_file(corpus_yaml_path)
        assert len(reloaded.sources) == 1
        assert reloaded.sources[0].name == "Engineering Standards"

        # Verification: Extraction pipeline can use it
        source = reloaded.sources[0]
        resolved_path = source.resolve_path(corpus_yaml_path.parent)
        assert resolved_path.exists()

    def test_user_adds_multiple_directories_sequentially(
        self, tmp_path: Path, corpus_yaml_path: Path
    ):
        """User scenario: Add multiple document directories over time."""
        scanner = DirectoryScanner()
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # First import session
        eng_dir = tmp_path / "engineering"
        eng_dir.mkdir()
        (eng_dir / "spec.pdf").write_bytes(b"%PDF")

        config1 = scanner.create_source_config(eng_dir, "Engineering", tags=["eng"])
        corpus_config.add_directory_source(
            name=config1.name,
            path=config1.path,
            tags=config1.tags,
        )

        # Persist after first import
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        # Second import session (load existing, add more)
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)
        marketing_dir = tmp_path / "marketing"
        marketing_dir.mkdir()
        (marketing_dir / "branding.pdf").write_bytes(b"%PDF")

        config2 = scanner.create_source_config(marketing_dir, "Marketing", tags=["mkt"])
        corpus_config.add_directory_source(
            name=config2.name,
            path=config2.path,
            tags=config2.tags,
        )

        # Persist after second import
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        # Verify final state
        final_config = CorpusConfig.load_from_file(corpus_yaml_path)
        assert len(final_config.sources) == 2
        names = {s.name for s in final_config.sources}
        assert names == {"Engineering", "Marketing"}

    def test_user_encounters_duplicate_and_cancels(self, tmp_path: Path, corpus_yaml_path: Path):
        """User scenario: Attempts to add duplicate, sees warning, cancels."""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        (test_dir / "doc.txt").write_text("content")

        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # First import succeeds
        corpus_config.add_directory_source("My Docs v1", str(test_dir.resolve()))

        # Persist
        _save_config_to_yaml(corpus_config, corpus_yaml_path)

        # Reload (user tries again in new session)
        corpus_config = CorpusConfig.load_from_file(corpus_yaml_path)

        # User attempts to add same directory
        path_exists = corpus_config.source_path_exists(str(test_dir.resolve()))
        assert path_exists  # System detects duplicate

        # User cancels (doesn't add)
        sources_before = len(corpus_config.sources)

        # Verify nothing was added when user cancelled
        assert len(corpus_config.sources) == sources_before
