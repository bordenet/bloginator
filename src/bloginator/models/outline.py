"""Outline data models for document generation."""

from datetime import datetime

from pydantic import BaseModel, Field


class OutlineSection(BaseModel):
    """A section in a document outline.

    Attributes:
        title: Section title/heading
        description: Brief description of section content
        coverage_pct: Coverage percentage from corpus (0-100)
        source_count: Number of source documents contributing to this section
        subsections: Nested subsections (recursive)
        notes: Additional notes or warnings (e.g., low coverage)
    """

    title: str = Field(..., description="Section title")
    description: str = Field(default="", description="Section description")
    coverage_pct: float = Field(default=0.0, ge=0.0, le=100.0, description="Coverage from corpus")
    source_count: int = Field(default=0, ge=0, description="Number of source documents")
    subsections: list["OutlineSection"] = Field(default_factory=list)
    notes: str = Field(default="", description="Warnings or notes")

    def has_low_coverage(self, threshold: float = 50.0) -> bool:
        """Check if section has low coverage.

        Args:
            threshold: Coverage percentage threshold (default: 50%)

        Returns:
            True if coverage is below threshold
        """
        return self.coverage_pct < threshold

    def get_all_sections(self) -> list["OutlineSection"]:
        """Get flattened list of all sections including subsections.

        Returns:
            List of all sections (self + all descendants)
        """
        sections = [self]
        for subsection in self.subsections:
            sections.extend(subsection.get_all_sections())
        return sections


class Outline(BaseModel):
    """Document outline with coverage analysis.

    Attributes:
        title: Document title
        thesis: Main thesis or purpose statement
        classification: Content classification (guidance, best-practice, mandate, principle, opinion)
        audience: Target audience (ic-engineers, engineering-leaders, all-disciplines, etc.)
        keywords: Keywords/themes used for generation
        sections: Top-level sections
        created_date: When outline was generated
        total_sources: Total number of unique source documents
        avg_coverage: Average coverage percentage across all sections
        low_coverage_sections: Number of sections with low coverage
    """

    title: str = Field(..., description="Document title")
    thesis: str = Field(default="", description="Main thesis/purpose")
    classification: str = Field(
        default="guidance",
        description="Content classification (tone and authority level)",
    )
    audience: str = Field(
        default="all-disciplines",
        description="Target audience for content",
    )
    keywords: list[str] = Field(default_factory=list, description="Keywords/themes")
    sections: list[OutlineSection] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=datetime.now)
    total_sources: int = Field(default=0, ge=0)
    avg_coverage: float = Field(default=0.0, ge=0.0, le=100.0)
    low_coverage_sections: int = Field(default=0, ge=0)

    def calculate_stats(self, low_coverage_threshold: float = 50.0) -> None:
        """Calculate outline statistics.

        Updates avg_coverage and low_coverage_sections based on all sections.

        Args:
            low_coverage_threshold: Threshold for low coverage warning (default: 50%)
        """
        all_sections = []
        for section in self.sections:
            all_sections.extend(section.get_all_sections())

        if not all_sections:
            self.avg_coverage = 0.0
            self.low_coverage_sections = 0
            return

        # Calculate average coverage
        total_coverage = sum(s.coverage_pct for s in all_sections)
        self.avg_coverage = total_coverage / len(all_sections)

        # Count low coverage sections
        self.low_coverage_sections = sum(
            1 for s in all_sections if s.has_low_coverage(low_coverage_threshold)
        )

    def get_all_sections(self) -> list[OutlineSection]:
        """Get flattened list of all sections.

        Returns:
            List of all sections including nested subsections
        """
        all_sections = []
        for section in self.sections:
            all_sections.extend(section.get_all_sections())
        return all_sections

    def to_markdown(self) -> str:
        """Convert outline to Markdown format.

        Returns:
            Markdown-formatted outline with coverage information
        """
        lines = []

        # Title
        lines.append(f"# {self.title}")
        lines.append("")

        # Classification and Audience as subtitle
        classification_label = self.classification.replace("-", " ").title()
        audience_label = self.audience.replace("-", " ").title()
        lines.append(f"*{classification_label} • For {audience_label}*")
        lines.append("")

        # Thesis
        if self.thesis:
            lines.append(f"**Thesis**: {self.thesis}")
            lines.append("")

        # Keywords
        if self.keywords:
            lines.append(f"**Keywords**: {', '.join(self.keywords)}")
            lines.append("")

        # Stats
        lines.append(f"**Coverage**: {self.avg_coverage:.1f}% average")
        lines.append(f"**Sources**: {self.total_sources} documents")
        if self.low_coverage_sections > 0:
            lines.append(f"**⚠️ Low Coverage**: {self.low_coverage_sections} section(s)")
        lines.append("")

        # Sections
        for section in self.sections:
            lines.extend(self._section_to_markdown(section, level=2))

        return "\n".join(lines)

    def _section_to_markdown(self, section: OutlineSection, level: int = 2) -> list[str]:
        """Convert section to markdown lines.

        Args:
            section: Section to convert
            level: Heading level (2-6)

        Returns:
            List of markdown lines
        """
        lines = []

        # Section heading
        heading = "#" * min(level, 6)
        lines.append(f"{heading} {section.title}")

        # Description
        if section.description:
            lines.append(section.description)

        # Coverage info
        coverage_icon = (
            "✅" if section.coverage_pct >= 70 else "⚠️" if section.coverage_pct >= 50 else "❌"
        )
        lines.append(
            f"{coverage_icon} *Coverage: {section.coverage_pct:.0f}% "
            f"from {section.source_count} document(s)*"
        )

        # Notes
        if section.notes:
            lines.append(f"*Note: {section.notes}*")

        lines.append("")

        # Subsections
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1))

        return lines
