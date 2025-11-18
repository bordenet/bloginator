"""Tests for blocklist CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from bloginator.cli.blocklist import blocklist
from bloginator.models.blocklist import BlocklistCategory, BlocklistEntry, BlocklistPatternType
from bloginator.safety import BlocklistManager


class TestBlocklistCLI:
    """Test blocklist CLI commands."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def config_dir(self, tmp_path: Path) -> Path:
        """Create temporary config directory."""
        config_dir = tmp_path / ".bloginator"
        config_dir.mkdir()
        return config_dir

    def test_add_basic(self, runner: CliRunner, config_dir: Path) -> None:
        """Test adding a basic entry."""
        result = runner.invoke(
            blocklist,
            ["add", "--config-dir", str(config_dir), "Acme Corp"],
        )

        assert result.exit_code == 0
        assert "Added 'Acme Corp' to blocklist" in result.output

        # Verify entry was saved
        manager = BlocklistManager(config_dir / "blocklist.json")
        assert manager.get_entry_count() == 1
        assert manager.entries[0].pattern == "Acme Corp"
        assert manager.entries[0].pattern_type == BlocklistPatternType.EXACT

    def test_add_with_options(self, runner: CliRunner, config_dir: Path) -> None:
        """Test adding entry with all options."""
        result = runner.invoke(
            blocklist,
            [
                "add",
                "--config-dir",
                str(config_dir),
                "Acme",
                "--type",
                "case_insensitive",
                "--category",
                "company_name",
                "--notes",
                "Former employer",
            ],
        )

        assert result.exit_code == 0

        manager = BlocklistManager(config_dir / "blocklist.json")
        entry = manager.entries[0]

        assert entry.pattern == "Acme"
        assert entry.pattern_type == BlocklistPatternType.CASE_INSENSITIVE
        assert entry.category == BlocklistCategory.COMPANY_NAME
        assert entry.notes == "Former employer"

    def test_add_regex_pattern(self, runner: CliRunner, config_dir: Path) -> None:
        """Test adding regex pattern."""
        result = runner.invoke(
            blocklist,
            [
                "add",
                "--config-dir",
                str(config_dir),
                r"Project \w+",
                "--type",
                "regex",
                "--category",
                "project",
            ],
        )

        assert result.exit_code == 0

        manager = BlocklistManager(config_dir / "blocklist.json")
        entry = manager.entries[0]

        assert entry.pattern == r"Project \w+"
        assert entry.pattern_type == BlocklistPatternType.REGEX

    def test_list_empty(self, runner: CliRunner, config_dir: Path) -> None:
        """Test listing when blocklist is empty."""
        result = runner.invoke(
            blocklist,
            ["list", "--config-dir", str(config_dir)],
        )

        assert result.exit_code == 0
        assert "No blocklist entries found" in result.output

    def test_list_with_entries(self, runner: CliRunner, config_dir: Path) -> None:
        """Test listing entries."""
        # Add some entries first
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(
                id="1",
                pattern="Acme Corp",
                pattern_type=BlocklistPatternType.EXACT,
                category=BlocklistCategory.COMPANY_NAME,
                notes="Former employer",
            )
        )
        manager.add_entry(
            BlocklistEntry(
                id="2",
                pattern="Project Falcon",
                pattern_type=BlocklistPatternType.EXACT,
                category=BlocklistCategory.PROJECT_CODENAME,
            )
        )

        result = runner.invoke(
            blocklist,
            ["list", "--config-dir", str(config_dir)],
        )

        assert result.exit_code == 0
        assert "Acme Corp" in result.output
        # Table may wrap long patterns across lines, so check separately
        assert "Project" in result.output
        assert "Falcon" in result.output
        assert "2 total" in result.output

    def test_list_with_category_filter(self, runner: CliRunner, config_dir: Path) -> None:
        """Test listing with category filter."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(
                id="1",
                pattern="Acme Corp",
                category=BlocklistCategory.COMPANY_NAME,
            )
        )
        manager.add_entry(
            BlocklistEntry(
                id="2",
                pattern="Super Product",
                category=BlocklistCategory.PRODUCT_NAME,
            )
        )

        result = runner.invoke(
            blocklist,
            ["list", "--config-dir", str(config_dir), "--category", "company_name"],
        )

        assert result.exit_code == 0
        assert "Acme Corp" in result.output
        assert "Super Product" not in result.output

    def test_remove_by_full_id(self, runner: CliRunner, config_dir: Path) -> None:
        """Test removing entry by full ID."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        entry = BlocklistEntry(id="test-id-12345", pattern="Test Pattern")
        manager.add_entry(entry)

        result = runner.invoke(
            blocklist,
            ["remove", "--config-dir", str(config_dir), "test-id-12345"],
        )

        assert result.exit_code == 0
        assert "Removed entry: Test Pattern" in result.output

        manager2 = BlocklistManager(config_dir / "blocklist.json")
        assert manager2.get_entry_count() == 0

    def test_remove_by_short_id(self, runner: CliRunner, config_dir: Path) -> None:
        """Test removing entry by short ID prefix."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        entry = BlocklistEntry(id="abc12345-6789", pattern="Test Pattern")
        manager.add_entry(entry)

        # Should work with just the prefix
        result = runner.invoke(
            blocklist,
            ["remove", "--config-dir", str(config_dir), "abc12345"],
        )

        assert result.exit_code == 0
        assert "Removed entry" in result.output

    def test_remove_not_found(self, runner: CliRunner, config_dir: Path) -> None:
        """Test removing non-existent entry."""
        result = runner.invoke(
            blocklist,
            ["remove", "--config-dir", str(config_dir), "nonexistent"],
        )

        assert result.exit_code == 0
        assert "No entry found" in result.output

    def test_remove_ambiguous_id(self, runner: CliRunner, config_dir: Path) -> None:
        """Test removing with ambiguous ID prefix."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(BlocklistEntry(id="abc123-first", pattern="Pattern 1"))
        manager.add_entry(BlocklistEntry(id="abc456-second", pattern="Pattern 2"))

        # "abc" matches both
        result = runner.invoke(
            blocklist,
            ["remove", "--config-dir", str(config_dir), "abc"],
        )

        assert result.exit_code == 0
        assert "Multiple entries match" in result.output
        assert "Please be more specific" in result.output

    def test_validate_clean_file(self, runner: CliRunner, config_dir: Path, tmp_path: Path) -> None:
        """Test validating a clean file."""
        # Create blocklist
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(id="1", pattern="Acme Corp", category=BlocklistCategory.COMPANY_NAME)
        )

        # Create clean test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("I worked at a tech company for 5 years.")

        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), str(test_file)],
        )

        assert result.exit_code == 0
        assert "No blocklist violations found" in result.output

    def test_validate_file_with_violations(
        self, runner: CliRunner, config_dir: Path, tmp_path: Path
    ) -> None:
        """Test validating file with violations."""
        # Create blocklist
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(
                id="1",
                pattern="Acme Corp",
                category=BlocklistCategory.COMPANY_NAME,
                notes="Former employer",
            )
        )

        # Create test file with violation
        test_file = tmp_path / "test.txt"
        test_file.write_text("I worked at Acme Corp for 5 years.")

        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), str(test_file)],
        )

        assert result.exit_code == 0
        assert "Found 1 blocklist violation" in result.output
        assert "Acme Corp" in result.output

    def test_validate_file_with_verbose(
        self, runner: CliRunner, config_dir: Path, tmp_path: Path
    ) -> None:
        """Test validating with verbose output."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(
                id="1",
                pattern="Acme Corp",
                category=BlocklistCategory.COMPANY_NAME,
                notes="Sensitive company",
            )
        )

        test_file = tmp_path / "test.txt"
        test_file.write_text("I worked at Acme Corp.")

        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), str(test_file), "--verbose"],
        )

        assert result.exit_code == 0
        assert "Violations" in result.output
        assert "Acme Corp" in result.output

    def test_validate_file_multiple_violations(
        self, runner: CliRunner, config_dir: Path, tmp_path: Path
    ) -> None:
        """Test validating file with multiple violations."""
        manager = BlocklistManager(config_dir / "blocklist.json")
        manager.add_entry(
            BlocklistEntry(id="1", pattern="Acme Corp", category=BlocklistCategory.COMPANY_NAME)
        )
        manager.add_entry(
            BlocklistEntry(
                id="2",
                pattern=r"Project \w+",
                pattern_type=BlocklistPatternType.REGEX,
                category=BlocklistCategory.PROJECT_CODENAME,
            )
        )

        test_file = tmp_path / "test.txt"
        test_file.write_text("I worked at Acme Corp on Project Falcon and Project Eagle.")

        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), str(test_file)],
        )

        assert result.exit_code == 0
        assert "Found 2 blocklist violation" in result.output

    def test_validate_file_not_found(self, runner: CliRunner, config_dir: Path) -> None:
        """Test validating non-existent file."""
        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), "nonexistent.txt"],
        )

        # Click should error on missing file
        assert result.exit_code != 0

    def test_default_config_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that default config dir is .bloginator."""
        # Run from tmp_path directory
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(blocklist, ["add", "Test Pattern"])

            assert result.exit_code == 0

            # Should create .bloginator directory
            assert (Path.cwd() / ".bloginator" / "blocklist.json").exists()

    def test_add_creates_config_dir(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that add command creates config directory if needed."""
        config_dir = tmp_path / "nonexistent" / ".bloginator"

        result = runner.invoke(
            blocklist,
            ["add", "--config-dir", str(config_dir), "Test Pattern"],
        )

        assert result.exit_code == 0
        assert config_dir.exists()
        assert (config_dir / "blocklist.json").exists()

    def test_integration_workflow(
        self, runner: CliRunner, config_dir: Path, tmp_path: Path
    ) -> None:
        """Test complete workflow: add, list, validate, remove."""
        # Step 1: Add entries
        runner.invoke(
            blocklist,
            [
                "add",
                "--config-dir",
                str(config_dir),
                "Acme Corp",
                "--category",
                "company_name",
            ],
        )
        runner.invoke(
            blocklist,
            [
                "add",
                "--config-dir",
                str(config_dir),
                "Project Falcon",
                "--category",
                "project",
            ],
        )

        # Step 2: List entries
        result = runner.invoke(blocklist, ["list", "--config-dir", str(config_dir)])
        assert "Acme Corp" in result.output
        assert "Project Falcon" in result.output

        # Step 3: Validate file with violations
        test_file = tmp_path / "test.txt"
        test_file.write_text("I worked at Acme Corp on Project Falcon.")

        result = runner.invoke(
            blocklist,
            ["validate", "--config-dir", str(config_dir), str(test_file)],
        )
        assert "Found 2 blocklist violation" in result.output

        # Step 4: Get an entry ID and remove it
        manager = BlocklistManager(config_dir / "blocklist.json")
        first_id = manager.entries[0].id[:8]

        result = runner.invoke(
            blocklist,
            ["remove", "--config-dir", str(config_dir), first_id],
        )
        assert "Removed entry" in result.output

        # Step 5: Verify only one entry remains
        result = runner.invoke(blocklist, ["list", "--config-dir", str(config_dir)])
        assert "1 total" in result.output
