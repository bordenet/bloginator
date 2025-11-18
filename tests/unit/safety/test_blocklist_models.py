"""Tests for blocklist data models."""

from datetime import datetime

from bloginator.models.blocklist import BlocklistCategory, BlocklistEntry, BlocklistPatternType


class TestBlocklistEntry:
    """Test BlocklistEntry model and pattern matching."""

    def test_entry_creation(self) -> None:
        """Test creating a blocklist entry."""
        entry = BlocklistEntry(
            id="test_id",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
            notes="Test company",
        )

        assert entry.id == "test_id"
        assert entry.pattern == "Acme Corp"
        assert entry.pattern_type == BlocklistPatternType.EXACT
        assert entry.category == BlocklistCategory.COMPANY_NAME
        assert entry.notes == "Test company"
        assert isinstance(entry.added_date, datetime)

    def test_entry_defaults(self) -> None:
        """Test entry creation with default values."""
        entry = BlocklistEntry(id="test_id", pattern="Test")

        assert entry.pattern_type == BlocklistPatternType.EXACT
        assert entry.category == BlocklistCategory.OTHER
        assert entry.notes == ""
        assert isinstance(entry.added_date, datetime)

    def test_exact_match_positive(self) -> None:
        """Test exact matching finds the pattern."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )

        matches = entry.matches("I worked at Acme Corp for 5 years.")
        assert matches == ["Acme Corp"]

    def test_exact_match_case_sensitive(self) -> None:
        """Test exact matching is case-sensitive."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )

        # Should not match different case
        matches = entry.matches("I worked at acme corp for 5 years.")
        assert matches == []

        # EXACT does substring matching, so "Acme Corp" matches in "Acme Corporation"
        matches = entry.matches("I worked at Acme Corporation.")
        assert matches == ["Acme Corp"]

    def test_exact_match_no_match(self) -> None:
        """Test exact matching when pattern not present."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
        )

        matches = entry.matches("I worked at a tech company.")
        assert matches == []

    def test_case_insensitive_match(self) -> None:
        """Test case-insensitive matching."""
        entry = BlocklistEntry(
            id="2",
            pattern="Acme",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
            category=BlocklistCategory.COMPANY_NAME,
        )

        # Should match all case variations
        matches = entry.matches("ACME and acme and Acme")
        assert len(matches) == 3
        assert "ACME" in matches
        assert "acme" in matches
        assert "Acme" in matches

    def test_case_insensitive_single_match(self) -> None:
        """Test case-insensitive with single occurrence."""
        entry = BlocklistEntry(
            id="2",
            pattern="Project",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
        )

        matches = entry.matches("I worked on project falcon.")
        assert matches == ["project"]

    def test_case_insensitive_no_match(self) -> None:
        """Test case-insensitive when not found."""
        entry = BlocklistEntry(
            id="2",
            pattern="Acme",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
        )

        matches = entry.matches("No company names here.")
        assert matches == []

    def test_regex_match(self) -> None:
        """Test regex pattern matching."""
        entry = BlocklistEntry(
            id="3",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
            category=BlocklistCategory.PROJECT_CODENAME,
        )

        matches = entry.matches("Project Falcon was a secret initiative.")
        assert matches == ["Project Falcon"]

    def test_regex_multiple_matches(self) -> None:
        """Test regex with multiple matches."""
        entry = BlocklistEntry(
            id="3",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
        )

        text = "Project Falcon and Project Eagle were both classified."
        matches = entry.matches(text)
        assert len(matches) == 2
        assert "Project Falcon" in matches
        assert "Project Eagle" in matches

    def test_regex_no_match(self) -> None:
        """Test regex when pattern doesn't match."""
        entry = BlocklistEntry(
            id="3",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
        )

        matches = entry.matches("No projects mentioned here.")
        assert matches == []

    def test_regex_invalid_pattern(self) -> None:
        """Test handling of invalid regex pattern."""
        entry = BlocklistEntry(
            id="3",
            pattern=r"[invalid(regex",  # Invalid regex
            pattern_type=BlocklistPatternType.REGEX,
        )

        # Should return empty list instead of raising exception
        matches = entry.matches("Some text")
        assert matches == []

    def test_regex_complex_pattern(self) -> None:
        """Test complex regex pattern."""
        entry = BlocklistEntry(
            id="4",
            pattern=r"\b[A-Z]{2,5}-\d{3,5}\b",  # Pattern like ABC-123
            pattern_type=BlocklistPatternType.REGEX,
            category=BlocklistCategory.PROJECT_CODENAME,
        )

        text = "Projects PROJ-1234 and XYZ-567 are confidential."
        matches = entry.matches(text)
        assert len(matches) == 2
        assert "PROJ-1234" in matches
        assert "XYZ-567" in matches

    def test_all_categories_valid(self) -> None:
        """Test all category enum values are valid."""
        categories = [
            BlocklistCategory.COMPANY_NAME,
            BlocklistCategory.PRODUCT_NAME,
            BlocklistCategory.PROJECT_CODENAME,
            BlocklistCategory.METHODOLOGY,
            BlocklistCategory.PERSON_NAME,
            BlocklistCategory.OTHER,
        ]

        for category in categories:
            entry = BlocklistEntry(
                id="test",
                pattern="test",
                category=category,
            )
            assert entry.category == category

    def test_all_pattern_types_valid(self) -> None:
        """Test all pattern type enum values are valid."""
        pattern_types = [
            BlocklistPatternType.EXACT,
            BlocklistPatternType.CASE_INSENSITIVE,
            BlocklistPatternType.REGEX,
        ]

        for pattern_type in pattern_types:
            entry = BlocklistEntry(
                id="test",
                pattern="test",
                pattern_type=pattern_type,
            )
            assert entry.pattern_type == pattern_type

    def test_empty_text(self) -> None:
        """Test matching against empty text."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme",
        )

        matches = entry.matches("")
        assert matches == []

    def test_empty_pattern_exact(self) -> None:
        """Test empty pattern with exact match."""
        entry = BlocklistEntry(
            id="1",
            pattern="",
            pattern_type=BlocklistPatternType.EXACT,
        )

        # Empty pattern in any text technically matches
        matches = entry.matches("Some text")
        assert matches == [""]

    def test_unicode_handling(self) -> None:
        """Test handling of unicode characters."""
        entry = BlocklistEntry(
            id="1",
            pattern="Café",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
        )

        matches = entry.matches("I visited the CAFÉ yesterday.")
        assert len(matches) > 0

    def test_special_characters_in_exact(self) -> None:
        """Test special regex characters in exact mode."""
        entry = BlocklistEntry(
            id="1",
            pattern="C++ Developer",
            pattern_type=BlocklistPatternType.EXACT,
        )

        matches = entry.matches("Looking for C++ Developer")
        assert matches == ["C++ Developer"]

    def test_multiline_text(self) -> None:
        """Test matching in multiline text."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
        )

        text = """
        I worked at several companies.
        Acme Corp was the best.
        Now I work elsewhere.
        """

        matches = entry.matches(text)
        assert matches == ["Acme Corp"]
