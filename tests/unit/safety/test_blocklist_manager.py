"""Tests for BlocklistManager."""

import json
from pathlib import Path

from bloginator.models.blocklist import BlocklistCategory, BlocklistEntry, BlocklistPatternType
from bloginator.safety import BlocklistManager


class TestBlocklistManager:
    """Test BlocklistManager functionality."""

    def test_manager_initialization_new_file(self, tmp_path: Path) -> None:
        """Test initializing manager with non-existent file."""
        blocklist_file = tmp_path / "blocklist.json"

        manager = BlocklistManager(blocklist_file)

        assert manager.blocklist_file == blocklist_file
        assert manager.entries == []

    def test_manager_initialization_existing_file(self, tmp_path: Path) -> None:
        """Test initializing manager with existing file."""
        blocklist_file = tmp_path / "blocklist.json"

        # Create file with sample data
        data = [
            {
                "id": "1",
                "pattern": "Acme Corp",
                "pattern_type": "exact",
                "category": "company_name",
                "added_date": "2025-01-01T00:00:00",
                "notes": "Test",
            }
        ]
        blocklist_file.write_text(json.dumps(data))

        manager = BlocklistManager(blocklist_file)

        assert len(manager.entries) == 1
        assert manager.entries[0].pattern == "Acme Corp"

    def test_manager_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading file with invalid JSON."""
        blocklist_file = tmp_path / "blocklist.json"
        blocklist_file.write_text("{invalid json")

        manager = BlocklistManager(blocklist_file)

        # Should handle gracefully with empty list
        assert manager.entries == []

    def test_manager_load_invalid_entries(self, tmp_path: Path) -> None:
        """Test loading file with some invalid entries."""
        blocklist_file = tmp_path / "blocklist.json"

        # Mix of valid and invalid entries
        data = [
            {
                "id": "1",
                "pattern": "Valid Pattern",
                "pattern_type": "exact",
                "category": "company_name",
                "added_date": "2025-01-01T00:00:00",
                "notes": "Valid",
            },
            {
                # Missing required 'id' field
                "pattern": "Invalid Pattern",
            },
            {
                "id": "2",
                "pattern": "Another Valid",
                "pattern_type": "exact",
                "category": "other",
                "added_date": "2025-01-01T00:00:00",
                "notes": "",
            },
        ]
        blocklist_file.write_text(json.dumps(data))

        manager = BlocklistManager(blocklist_file)

        # Should load only valid entries
        assert len(manager.entries) == 2
        assert manager.entries[0].pattern == "Valid Pattern"
        assert manager.entries[1].pattern == "Another Valid"

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test that save creates parent directory if needed."""
        blocklist_file = tmp_path / "subdir" / "blocklist.json"

        manager = BlocklistManager(blocklist_file)
        entry = BlocklistEntry(id="1", pattern="Test", pattern_type=BlocklistPatternType.EXACT)
        manager.add_entry(entry)

        assert blocklist_file.exists()
        assert blocklist_file.parent.exists()

    def test_save_and_load(self, tmp_path: Path) -> None:
        """Test saving and loading entries."""
        blocklist_file = tmp_path / "blocklist.json"

        # Create and save entries
        manager1 = BlocklistManager(blocklist_file)
        entry1 = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
            notes="Former employer",
        )
        entry2 = BlocklistEntry(
            id="2",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
            category=BlocklistCategory.PROJECT_CODENAME,
        )

        manager1.add_entry(entry1)
        manager1.add_entry(entry2)

        # Load in new manager instance
        manager2 = BlocklistManager(blocklist_file)

        assert len(manager2.entries) == 2
        assert manager2.entries[0].pattern == "Acme Corp"
        assert manager2.entries[1].pattern == r"Project \w+"

    def test_add_entry(self, tmp_path: Path) -> None:
        """Test adding an entry."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern="Test Pattern",
            pattern_type=BlocklistPatternType.EXACT,
        )

        manager.add_entry(entry)

        assert len(manager.entries) == 1
        assert manager.entries[0] == entry
        assert blocklist_file.exists()

    def test_remove_entry_exists(self, tmp_path: Path) -> None:
        """Test removing an existing entry."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry1 = BlocklistEntry(id="1", pattern="Pattern 1")
        entry2 = BlocklistEntry(id="2", pattern="Pattern 2")

        manager.add_entry(entry1)
        manager.add_entry(entry2)

        result = manager.remove_entry("1")

        assert result is True
        assert len(manager.entries) == 1
        assert manager.entries[0].id == "2"

    def test_remove_entry_not_exists(self, tmp_path: Path) -> None:
        """Test removing a non-existent entry."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(id="1", pattern="Pattern 1")
        manager.add_entry(entry)

        result = manager.remove_entry("nonexistent")

        assert result is False
        assert len(manager.entries) == 1

    def test_validate_text_no_violations(self, tmp_path: Path) -> None:
        """Test validating clean text."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )
        manager.add_entry(entry)

        result = manager.validate_text("I worked at a tech company for 5 years.")

        assert result["is_valid"] is True
        assert result["violations"] == []

    def test_validate_text_with_violations(self, tmp_path: Path) -> None:
        """Test validating text with violations."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
            notes="Former employer",
        )
        manager.add_entry(entry)

        result = manager.validate_text("I worked at Acme Corp for 5 years.")

        assert result["is_valid"] is False
        assert len(result["violations"]) == 1

        violation = result["violations"][0]
        assert violation["entry_id"] == "1"
        assert violation["pattern"] == "Acme Corp"
        assert violation["matches"] == ["Acme Corp"]
        assert violation["category"] == BlocklistCategory.COMPANY_NAME
        assert violation["notes"] == "Former employer"

    def test_validate_text_multiple_violations(self, tmp_path: Path) -> None:
        """Test validating text with multiple violations."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry1 = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )
        entry2 = BlocklistEntry(
            id="2",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
            category=BlocklistCategory.PROJECT_CODENAME,
        )

        manager.add_entry(entry1)
        manager.add_entry(entry2)

        text = "I worked at Acme Corp on Project Falcon."
        result = manager.validate_text(text)

        assert result["is_valid"] is False
        assert len(result["violations"]) == 2

    def test_validate_text_empty_blocklist(self, tmp_path: Path) -> None:
        """Test validating with empty blocklist."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        result = manager.validate_text("Any text should be valid.")

        assert result["is_valid"] is True
        assert result["violations"] == []

    def test_validate_text_empty_string(self, tmp_path: Path) -> None:
        """Test validating empty text."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(id="1", pattern="Test")
        manager.add_entry(entry)

        result = manager.validate_text("")

        assert result["is_valid"] is True
        assert result["violations"] == []

    def test_get_entries_by_category(self, tmp_path: Path) -> None:
        """Test filtering entries by category."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry1 = BlocklistEntry(
            id="1", pattern="Acme Corp", category=BlocklistCategory.COMPANY_NAME
        )
        entry2 = BlocklistEntry(
            id="2", pattern="Super Product", category=BlocklistCategory.PRODUCT_NAME
        )
        entry3 = BlocklistEntry(
            id="3", pattern="Another Corp", category=BlocklistCategory.COMPANY_NAME
        )

        manager.add_entry(entry1)
        manager.add_entry(entry2)
        manager.add_entry(entry3)

        company_entries = manager.get_entries_by_category(BlocklistCategory.COMPANY_NAME)

        assert len(company_entries) == 2
        assert all(e.category == BlocklistCategory.COMPANY_NAME for e in company_entries)

    def test_get_entries_by_category_none_found(self, tmp_path: Path) -> None:
        """Test filtering when no entries match category."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(id="1", pattern="Test", category=BlocklistCategory.COMPANY_NAME)
        manager.add_entry(entry)

        person_entries = manager.get_entries_by_category(BlocklistCategory.PERSON_NAME)

        assert person_entries == []

    def test_get_entry_count(self, tmp_path: Path) -> None:
        """Test getting entry count."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        assert manager.get_entry_count() == 0

        manager.add_entry(BlocklistEntry(id="1", pattern="Test 1"))
        assert manager.get_entry_count() == 1

        manager.add_entry(BlocklistEntry(id="2", pattern="Test 2"))
        assert manager.get_entry_count() == 2

        manager.remove_entry("1")
        assert manager.get_entry_count() == 1

    def test_case_insensitive_validation(self, tmp_path: Path) -> None:
        """Test validation with case-insensitive patterns."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern="Acme",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
            category=BlocklistCategory.COMPANY_NAME,
        )
        manager.add_entry(entry)

        # Should match all case variations
        result1 = manager.validate_text("ACME Corporation")
        assert result1["is_valid"] is False

        result2 = manager.validate_text("acme inc")
        assert result2["is_valid"] is False

        result3 = manager.validate_text("Acme Ltd")
        assert result3["is_valid"] is False

    def test_regex_validation(self, tmp_path: Path) -> None:
        """Test validation with regex patterns."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern=r"\b[A-Z]{2,4}-\d{3,5}\b",
            pattern_type=BlocklistPatternType.REGEX,
            category=BlocklistCategory.PROJECT_CODENAME,
            notes="Project code format",
        )
        manager.add_entry(entry)

        # Should match project codes
        result = manager.validate_text("Working on PROJ-1234 and XYZ-567")
        assert result["is_valid"] is False
        assert len(result["violations"]) == 1
        assert len(result["violations"][0]["matches"]) == 2

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        """Test that changes persist across manager instances."""
        blocklist_file = tmp_path / "blocklist.json"

        # First instance: add entries
        manager1 = BlocklistManager(blocklist_file)
        manager1.add_entry(BlocklistEntry(id="1", pattern="Pattern 1"))
        manager1.add_entry(BlocklistEntry(id="2", pattern="Pattern 2"))

        # Second instance: should see both entries
        manager2 = BlocklistManager(blocklist_file)
        assert manager2.get_entry_count() == 2

        # Third instance: remove one entry
        manager3 = BlocklistManager(blocklist_file)
        manager3.remove_entry("1")

        # Fourth instance: should see only one entry
        manager4 = BlocklistManager(blocklist_file)
        assert manager4.get_entry_count() == 1
        assert manager4.entries[0].id == "2"
