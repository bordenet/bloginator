"""Tests for outline models."""

import pytest

from bloginator.models.outline import Outline, OutlineSection


class TestOutlineSection:
    """Tests for OutlineSection model."""

    def test_create_basic_section(self):
        """Test creating a basic section."""
        section = OutlineSection(
            title="Introduction",
            description="Overview of the topic",
        )

        assert section.title == "Introduction"
        assert section.description == "Overview of the topic"
        assert section.coverage_pct == 0.0
        assert section.source_count == 0
        assert section.subsections == []
        assert section.notes == ""

    def test_create_section_with_coverage(self):
        """Test creating section with coverage info."""
        section = OutlineSection(
            title="Section 1",
            description="Test",
            coverage_pct=75.5,
            source_count=10,
            notes="Good coverage",
        )

        assert section.coverage_pct == 75.5
        assert section.source_count == 10
        assert section.notes == "Good coverage"

    def test_coverage_validation(self):
        """Test coverage percentage validation."""
        # Valid range
        section = OutlineSection(title="Test", coverage_pct=50.0)
        assert section.coverage_pct == 50.0

        # Invalid: negative
        with pytest.raises(ValueError):
            OutlineSection(title="Test", coverage_pct=-10.0)

        # Invalid: > 100
        with pytest.raises(ValueError):
            OutlineSection(title="Test", coverage_pct=150.0)

    def test_source_count_validation(self):
        """Test source count validation."""
        # Valid
        section = OutlineSection(title="Test", source_count=5)
        assert section.source_count == 5

        # Invalid: negative
        with pytest.raises(ValueError):
            OutlineSection(title="Test", source_count=-1)

    def test_has_low_coverage_default_threshold(self):
        """Test low coverage detection with default threshold."""
        high_coverage = OutlineSection(title="High", coverage_pct=75.0)
        low_coverage = OutlineSection(title="Low", coverage_pct=25.0)
        borderline = OutlineSection(title="Border", coverage_pct=50.0)

        assert not high_coverage.has_low_coverage()
        assert low_coverage.has_low_coverage()
        assert not borderline.has_low_coverage()  # 50% is NOT low

    def test_has_low_coverage_custom_threshold(self):
        """Test low coverage with custom threshold."""
        section = OutlineSection(title="Test", coverage_pct=60.0)

        assert not section.has_low_coverage(threshold=50.0)
        assert section.has_low_coverage(threshold=70.0)

    def test_get_all_sections_flat(self):
        """Test getting all sections from flat structure."""
        section = OutlineSection(title="Main")
        all_sections = section.get_all_sections()

        assert len(all_sections) == 1
        assert all_sections[0].title == "Main"

    def test_get_all_sections_nested(self):
        """Test getting all sections from nested structure."""
        subsub = OutlineSection(title="SubSub")
        sub = OutlineSection(title="Sub", subsections=[subsub])
        main = OutlineSection(title="Main", subsections=[sub])

        all_sections = main.get_all_sections()

        assert len(all_sections) == 3
        titles = [s.title for s in all_sections]
        assert "Main" in titles
        assert "Sub" in titles
        assert "SubSub" in titles

    def test_nested_subsections(self):
        """Test creating nested subsection hierarchy."""
        subsection1 = OutlineSection(title="Subsection 1")
        subsection2 = OutlineSection(title="Subsection 2")

        section = OutlineSection(
            title="Main Section",
            subsections=[subsection1, subsection2],
        )

        assert len(section.subsections) == 2
        assert section.subsections[0].title == "Subsection 1"
        assert section.subsections[1].title == "Subsection 2"


class TestOutline:
    """Tests for Outline model."""

    def test_create_basic_outline(self):
        """Test creating a basic outline."""
        outline = Outline(
            title="Test Document",
            thesis="Main argument",
            keywords=["test", "document"],
        )

        assert outline.title == "Test Document"
        assert outline.thesis == "Main argument"
        assert outline.keywords == ["test", "document"]
        assert outline.sections == []
        assert outline.total_sources == 0
        assert outline.avg_coverage == 0.0
        assert outline.low_coverage_sections == 0

    def test_create_outline_with_sections(self):
        """Test outline with sections."""
        section1 = OutlineSection(title="Intro", coverage_pct=80.0)
        section2 = OutlineSection(title="Body", coverage_pct=60.0)

        outline = Outline(
            title="Document",
            keywords=["test"],
            sections=[section1, section2],
        )

        assert len(outline.sections) == 2

    def test_calculate_stats_empty(self):
        """Test stats calculation with no sections."""
        outline = Outline(title="Empty", keywords=[])
        outline.calculate_stats()

        assert outline.avg_coverage == 0.0
        assert outline.low_coverage_sections == 0

    def test_calculate_stats_basic(self):
        """Test stats calculation with sections."""
        sections = [
            OutlineSection(title="S1", coverage_pct=80.0),
            OutlineSection(title="S2", coverage_pct=60.0),
            OutlineSection(title="S3", coverage_pct=40.0),  # Low coverage
        ]

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=sections,
        )
        outline.calculate_stats()

        # Average: (80 + 60 + 40) / 3 = 60.0
        assert outline.avg_coverage == pytest.approx(60.0, rel=0.01)
        # One section below 50%
        assert outline.low_coverage_sections == 1

    def test_calculate_stats_nested(self):
        """Test stats calculation with nested sections."""
        subsection = OutlineSection(title="Sub", coverage_pct=30.0)  # Low
        section1 = OutlineSection(
            title="Main1",
            coverage_pct=70.0,
            subsections=[subsection],
        )
        section2 = OutlineSection(title="Main2", coverage_pct=90.0)

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[section1, section2],
        )
        outline.calculate_stats()

        # Should include subsection in stats
        # Average: (70 + 30 + 90) / 3 = 63.33
        assert outline.avg_coverage == pytest.approx(63.33, rel=0.01)
        # One low coverage section (subsection)
        assert outline.low_coverage_sections == 1

    def test_calculate_stats_custom_threshold(self):
        """Test stats with custom low coverage threshold."""
        sections = [
            OutlineSection(title="S1", coverage_pct=80.0),
            OutlineSection(title="S2", coverage_pct=60.0),  # Would be low with threshold=70
        ]

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=sections,
        )

        # Default threshold (50%)
        outline.calculate_stats(low_coverage_threshold=50.0)
        assert outline.low_coverage_sections == 0

        # Higher threshold (70%)
        outline.calculate_stats(low_coverage_threshold=70.0)
        assert outline.low_coverage_sections == 1

    def test_to_markdown_basic(self):
        """Test markdown generation."""
        section = OutlineSection(
            title="Introduction",
            description="Opening remarks",
        )

        outline = Outline(
            title="Test Document",
            thesis="Main thesis",
            keywords=["test"],
            sections=[section],
        )

        markdown = outline.to_markdown()

        assert "# Test Document" in markdown
        assert "**Thesis:** Main thesis" in markdown
        assert "## Introduction" in markdown
        assert "Opening remarks" in markdown

    def test_to_markdown_nested(self):
        """Test markdown with nested sections."""
        subsection = OutlineSection(
            title="Subsection",
            description="Details",
        )
        section = OutlineSection(
            title="Main Section",
            description="Overview",
            subsections=[subsection],
        )

        outline = Outline(
            title="Document",
            keywords=["test"],
            sections=[section],
        )

        markdown = outline.to_markdown()

        assert "## Main Section" in markdown
        assert "### Subsection" in markdown
        assert "Details" in markdown

    def test_to_markdown_with_coverage(self):
        """Test markdown includes coverage info."""
        section = OutlineSection(
            title="Section",
            description="Desc",
            coverage_pct=75.5,
            source_count=5,
        )

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[section],
        )

        markdown = outline.to_markdown()

        assert "Coverage: 75%" in markdown
        assert "Sources: 5" in markdown

    def test_to_markdown_no_thesis(self):
        """Test markdown without thesis."""
        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[],
        )

        markdown = outline.to_markdown()

        assert "**Thesis:**" not in markdown

    def test_get_all_sections(self):
        """Test getting all sections including nested."""
        subsection = OutlineSection(title="Sub")
        section = OutlineSection(title="Main", subsections=[subsection])

        outline = Outline(
            title="Test",
            keywords=["test"],
            sections=[section],
        )

        all_sections = outline.get_all_sections()

        assert len(all_sections) == 2
        titles = [s.title for s in all_sections]
        assert "Main" in titles
        assert "Sub" in titles
