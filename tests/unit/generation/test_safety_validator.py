"""Tests for safety validator."""

import tempfile
from pathlib import Path

import pytest

from bloginator.generation.safety_validator import SafetyValidator
from bloginator.models.blocklist import BlocklistCategory, BlocklistEntry, BlocklistPatternType
from bloginator.models.draft import Draft, DraftSection


class TestSafetyValidator:
    """Tests for SafetyValidator."""

    @pytest.fixture
    def blocklist_file(self):
        """Create temporary blocklist file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"version": "1.0", "entries": []}')
            path = Path(f.name)

        yield path

        # Cleanup
        if path.exists():
            path.unlink()

    @pytest.fixture
    def validator(self, blocklist_file):
        """Create safety validator."""
        return SafetyValidator(
            blocklist_file=blocklist_file,
            auto_reject=True,
        )

    def test_initialization(self, blocklist_file):
        """Test validator initialization."""
        validator = SafetyValidator(
            blocklist_file=blocklist_file,
            auto_reject=False,
        )

        assert validator.blocklist_manager is not None
        assert validator.auto_reject is False

    def test_validate_draft_clean(self, validator):
        """Test validating draft with no violations."""
        draft = Draft(
            title="Clean Document",
            keywords=["clean", "safe"],
            sections=[
                DraftSection(
                    title="Section 1",
                    content="This is clean content.",
                ),
                DraftSection(
                    title="Section 2",
                    content="No proprietary terms here.",
                ),
            ],
        )

        # Should not raise
        validator.validate_draft(draft)

        assert draft.has_blocklist_violations is False
        assert draft.blocklist_validation_result["is_valid"] is True
        assert len(draft.blocklist_validation_result["violations"]) == 0

    def test_validate_draft_with_violations(self, validator):
        """Test validating draft with violations."""
        # Add blocklist entry
        entry = BlocklistEntry(
            id="test1",
            pattern="ProprietaryTerm",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
            notes="Test entry",
        )
        validator.blocklist_manager.add_entry(entry)

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[
                DraftSection(
                    title="Section 1",
                    content="This mentions ProprietaryTerm in the text.",
                ),
            ],
        )

        # Should raise with auto_reject=True
        with pytest.raises(ValueError, match="Draft rejected"):
            validator.validate_draft(draft)

        # Draft should still be marked with violations
        assert draft.has_blocklist_violations is True

    def test_validate_draft_no_auto_reject(self, blocklist_file):
        """Test validation without auto-rejection."""
        validator = SafetyValidator(
            blocklist_file=blocklist_file,
            auto_reject=False,
        )

        # Add blocklist entry
        entry = BlocklistEntry(
            id="test1",
            pattern="BadTerm",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.PRODUCT_NAME,
        )
        validator.blocklist_manager.add_entry(entry)

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[
                DraftSection(
                    title="Section 1",
                    content="This has BadTerm in it.",
                ),
            ],
        )

        # Should not raise
        validator.validate_draft(draft)

        # But should mark violations
        assert draft.has_blocklist_violations is True
        assert len(draft.blocklist_validation_result["violations"]) > 0

    def test_validate_draft_multiple_sections(self, validator):
        """Test validation across multiple sections."""
        # Add entries
        entry1 = BlocklistEntry(
            id="test1",
            pattern="Term1",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )
        entry2 = BlocklistEntry(
            id="test2",
            pattern="Term2",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.PRODUCT_NAME,
        )
        validator.blocklist_manager.add_entry(entry1)
        validator.blocklist_manager.add_entry(entry2)

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[
                DraftSection(
                    title="Section 1",
                    content="This has Term1.",
                ),
                DraftSection(
                    title="Section 2",
                    content="This has Term2.",
                ),
                DraftSection(
                    title="Section 3",
                    content="This is clean.",
                ),
            ],
        )

        # Disable auto_reject for testing
        validator.auto_reject = False
        validator.validate_draft(draft)

        # Check section-level violations
        assert draft.sections[0].has_blocklist_violations is True
        assert draft.sections[1].has_blocklist_violations is True
        assert draft.sections[2].has_blocklist_violations is False

        # Check overall result
        assert draft.has_blocklist_violations is True
        assert len(draft.blocklist_validation_result["violations"]) == 2

    def test_validate_draft_nested_sections(self, validator):
        """Test validation with nested sections."""
        entry = BlocklistEntry(
            id="test1",
            pattern="Secret",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.PROJECT,
        )
        validator.blocklist_manager.add_entry(entry)

        subsection = DraftSection(
            title="Subsection",
            content="Contains Secret term.",
        )

        section = DraftSection(
            title="Main Section",
            content="Clean content.",
            subsections=[subsection],
        )

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[section],
        )

        validator.auto_reject = False
        validator.validate_draft(draft)

        # Subsection should have violation
        assert draft.sections[0].subsections[0].has_blocklist_violations is True
        # Overall draft should have violation
        assert draft.has_blocklist_violations is True

    def test_validate_before_generation_clean(self, validator):
        """Test pre-validation with clean inputs."""
        result = validator.validate_before_generation(
            title="Clean Title",
            keywords=["safe", "clean"],
            thesis="Clean thesis statement",
        )

        assert result["is_valid"] is True
        assert len(result["violations"]) == 0

    def test_validate_before_generation_violations(self, validator):
        """Test pre-validation with violations."""
        entry = BlocklistEntry(
            id="test1",
            pattern="Acme",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.COMPANY_NAME,
        )
        validator.blocklist_manager.add_entry(entry)

        result = validator.validate_before_generation(
            title="Acme Corporation Guide",
            keywords=["corporate", "guide"],
            thesis="",
        )

        assert result["is_valid"] is False
        assert len(result["violations"]) > 0
        # Should have location context
        assert result["violations"][0]["location"] == "input parameters"

    def test_validate_before_generation_in_keywords(self, validator):
        """Test pre-validation catches violations in keywords."""
        entry = BlocklistEntry(
            id="test1",
            pattern="proprietary",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
            category=BlocklistCategory.METHODOLOGY,
        )
        validator.blocklist_manager.add_entry(entry)

        result = validator.validate_before_generation(
            title="Guide",
            keywords=["standard", "Proprietary"],
            thesis="",
        )

        assert result["is_valid"] is False

    def test_add_to_blocklist(self, validator):
        """Test adding to blocklist via validator."""
        validator.add_to_blocklist(
            pattern="NewTerm",
            pattern_type="exact",
            category="company_name",
            notes="Added during generation",
        )

        # Should be in blocklist
        entries = validator.blocklist_manager.entries
        assert len(entries) == 1
        assert entries[0].pattern == "NewTerm"
        assert entries[0].pattern_type == BlocklistPatternType.EXACT
        assert entries[0].category == BlocklistCategory.COMPANY_NAME
        assert entries[0].notes == "Added during generation"

    def test_get_safe_sections(self, validator):
        """Test getting safe sections."""
        entry = BlocklistEntry(
            id="test1",
            pattern="Bad",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.OTHER,
        )
        validator.blocklist_manager.add_entry(entry)

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[
                DraftSection(title="Safe", content="Clean content"),
                DraftSection(title="Unsafe", content="Has Bad term"),
                DraftSection(title="Also Safe", content="More clean content"),
            ],
        )

        validator.auto_reject = False
        validator.validate_draft(draft)

        safe_sections = validator.get_safe_sections(draft)

        assert len(safe_sections) == 2
        assert safe_sections[0].title == "Safe"
        assert safe_sections[1].title == "Also Safe"

    def test_get_unsafe_sections(self, validator):
        """Test getting unsafe sections."""
        entry = BlocklistEntry(
            id="test1",
            pattern="Violation",
            pattern_type=BlocklistPatternType.EXACT,
            category=BlocklistCategory.OTHER,
        )
        validator.blocklist_manager.add_entry(entry)

        draft = Draft(
            title="Document",
            keywords=["test"],
            sections=[
                DraftSection(title="Clean", content="Safe content"),
                DraftSection(title="Problem", content="Has Violation"),
            ],
        )

        validator.auto_reject = False
        validator.validate_draft(draft)

        unsafe_sections = validator.get_unsafe_sections(draft)

        assert len(unsafe_sections) == 1
        assert unsafe_sections[0].title == "Problem"

    def test_format_violation_summary(self, validator):
        """Test violation summary formatting."""
        violations = [
            {
                "pattern": "Term1",
                "matches": ["Term1", "term1"],
                "category": "company_name",
                "notes": "Former employer",
                "section_title": "Introduction",
            },
            {
                "pattern": "Term2",
                "matches": ["Term2"],
                "category": "product_name",
                "notes": "",
                "section_title": "Background",
            },
        ]

        summary = validator._format_violation_summary(violations)

        assert "1. Pattern 'Term1' in section 'Introduction'" in summary
        assert "Matched: 'Term1', 'term1'" in summary
        assert "Notes: Former employer" in summary
        assert "2. Pattern 'Term2' in section 'Background'" in summary

    def test_format_violation_summary_empty(self, validator):
        """Test formatting empty violations."""
        summary = validator._format_violation_summary([])
        assert summary == "No violations"
