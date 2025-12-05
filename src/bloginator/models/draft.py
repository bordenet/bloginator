"""Draft document data models with citations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Source citation for generated content.

    Attributes:
        chunk_id: ID of the source chunk
        document_id: ID of the source document
        filename: Source document filename
        content_preview: Preview of cited content (first 100 chars)
        similarity_score: Similarity score to generated content (0-1)
    """

    chunk_id: str = Field(..., description="Source chunk ID")
    document_id: str = Field(..., description="Source document ID")
    filename: str = Field(..., description="Source filename")
    content_preview: str = Field(default="", description="Content preview")
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)

    def __repr__(self) -> str:
        """String representation."""
        return f"Citation(file={self.filename}, similarity={self.similarity_score:.2f})"


class DraftSection(BaseModel):
    """A section in a draft document.

    Attributes:
        title: Section title/heading
        content: Generated text content for this section
        citations: Source citations for this section
        voice_score: Voice similarity score (0-1, higher = more authentic)
        has_blocklist_violations: Whether blocklist violations were found
        subsections: Nested subsections (recursive)
    """

    title: str = Field(..., description="Section title")
    content: str = Field(default="", description="Generated content")
    citations: list[Citation] = Field(default_factory=list)
    voice_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Voice similarity")
    has_blocklist_violations: bool = Field(default=False)
    subsections: list["DraftSection"] = Field(default_factory=list)

    def get_all_sections(self) -> list["DraftSection"]:
        """Get flattened list of all sections.

        Returns:
            List of all sections including subsections
        """
        sections = [self]
        for subsection in self.subsections:
            sections.extend(subsection.get_all_sections())
        return sections

    def get_word_count(self) -> int:
        """Get word count for this section's content.

        Returns:
            Number of words in content
        """
        return len(self.content.split())


class Draft(BaseModel):
    """Complete draft document with citations and metadata.

    Attributes:
        title: Document title
        thesis: Main thesis/purpose
        classification: Content classification (guidance, best-practice, mandate, principle, opinion)
        audience: Target audience (ic-engineers, engineering-leaders, all-disciplines, etc.)
        keywords: Keywords used for generation
        sections: Top-level sections
        created_date: When draft was generated
        voice_score: Overall voice similarity score (0-1)
        total_citations: Total number of unique citations
        total_words: Total word count
        confidence_score: Confidence index 0-100 based on source coverage and quality
        has_blocklist_violations: Whether any section has violations
        blocklist_validation_result: Detailed validation results if checked
    """

    title: str = Field(..., description="Document title")
    thesis: str = Field(default="", description="Main thesis")
    classification: str = Field(
        default="guidance",
        description="Content classification (tone and authority level)",
    )
    audience: str = Field(
        default="all-disciplines",
        description="Target audience for content",
    )
    keywords: list[str] = Field(default_factory=list)
    sections: list[DraftSection] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=datetime.now)
    voice_score: float = Field(default=0.0, ge=0.0, le=1.0)
    total_citations: int = Field(default=0, ge=0)
    total_words: int = Field(default=0, ge=0)
    citation_coverage_score: int = Field(
        default=0, ge=0, le=100, description="% of sections with at least one citation"
    )
    citation_quality_score: int = Field(
        default=0, ge=0, le=100, description="Average similarity score of citations (0-100)"
    )
    content_completeness_score: int = Field(
        default=0, ge=0, le=100, description="Content density score based on words per section"
    )
    has_blocklist_violations: bool = Field(default=False)
    blocklist_validation_result: dict[str, Any] | None = None

    def calculate_stats(self) -> None:
        """Calculate draft statistics.

        Updates voice_score, total_citations, total_words, confidence scores,
        and has_blocklist_violations based on all sections.
        """
        all_sections = self.get_all_sections()

        if not all_sections:
            self.voice_score = 0.0
            self.total_citations = 0
            self.total_words = 0
            self.citation_coverage_score = 0
            self.citation_quality_score = 0
            self.content_completeness_score = 0
            self.has_blocklist_violations = False
            return

        # Average voice score across all sections
        voice_scores = [s.voice_score for s in all_sections if s.voice_score > 0]
        self.voice_score = sum(voice_scores) / len(voice_scores) if voice_scores else 0.0

        # Unique citations
        all_citation_ids = set()
        all_citations = []
        for section in all_sections:
            for citation in section.citations:
                all_citation_ids.add(citation.chunk_id)
                all_citations.append(citation)
        self.total_citations = len(all_citation_ids)

        # Total words
        self.total_words = sum(s.get_word_count() for s in all_sections)

        # Blocklist violations
        self.has_blocklist_violations = any(s.has_blocklist_violations for s in all_sections)

        # === CONFIDENCE SCORES ===

        # Citation Coverage: % of sections with at least one citation
        sections_with_citations = sum(1 for s in all_sections if s.citations)
        self.citation_coverage_score = int((sections_with_citations / len(all_sections)) * 100)

        # Citation Quality: Average similarity score of all citations (scaled 0-100)
        if all_citations:
            avg_similarity = sum(c.similarity_score for c in all_citations) / len(all_citations)
            self.citation_quality_score = int(avg_similarity * 100)
        else:
            self.citation_quality_score = 0

        # Content Completeness: Based on words per section (target ~150 words = 100%)
        target_words_per_section = 150
        avg_words = self.total_words / len(all_sections) if all_sections else 0
        completeness_ratio = min(avg_words / target_words_per_section, 1.0)
        self.content_completeness_score = int(completeness_ratio * 100)

    def get_all_sections(self) -> list[DraftSection]:
        """Get flattened list of all sections.

        Returns:
            List of all sections including subsections
        """
        all_sections = []
        for section in self.sections:
            all_sections.extend(section.get_all_sections())
        return all_sections

    def to_markdown(self, include_citations: bool = True) -> str:
        """Convert draft to Markdown format.

        Args:
            include_citations: Whether to include citation annotations

        Returns:
            Markdown-formatted draft
        """
        lines = []

        # Confidence metrics table at the TOP
        lines.append("| Metric | Score | Description |")
        lines.append("|--------|-------|-------------|")
        lines.append(
            f"| **Citation Coverage** | {self.citation_coverage_score}% "
            f"| % of sections with ≥1 citation |"
        )
        lines.append(
            f"| **Citation Quality** | {self.citation_quality_score}% "
            f"| Average similarity score of citations |"
        )
        lines.append(
            f"| **Content Completeness** | {self.content_completeness_score}% "
            f"| Content density (target: 150 words/section) |"
        )
        lines.append(f"| **Total Words** | {self.total_words} | |")
        lines.append(f"| **Total Citations** | {self.total_citations} | |")
        if self.has_blocklist_violations:
            lines.append("| ⚠️ **Blocklist Violations** | YES | Review required |")
        lines.append("")

        # Title with confidence scores: [XX-YY-ZZ] Title
        confidence_prefix = (
            f"[{self.citation_coverage_score:02d}-"
            f"{self.citation_quality_score:02d}-"
            f"{self.content_completeness_score:02d}]"
        )
        lines.append(f"# {confidence_prefix} {self.title}")
        lines.append("")

        if self.thesis:
            lines.append(f"*{self.thesis}*")
            lines.append("")

        # Metadata in hidden comment
        lines.append("<!--")
        lines.append(f"Generated: {self.created_date.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Classification: {self.classification}")
        lines.append(f"Audience: {self.audience}")
        lines.append(f"Voice Score: {self.voice_score:.2f}")
        lines.append("-->")
        lines.append("")

        # Sections
        for section in self.sections:
            lines.extend(
                self._section_to_markdown(section, level=2, include_citations=include_citations)
            )

        # Citations appendix (if requested)
        if include_citations:
            all_citations = []
            for section in self.get_all_sections():
                all_citations.extend(section.citations)

            if all_citations:
                lines.append("")
                lines.append("---")
                lines.append("")
                lines.append("## Sources")
                lines.append("")

                # Unique citations by chunk_id
                unique_citations = {}
                for citation in all_citations:
                    if citation.chunk_id not in unique_citations:
                        unique_citations[citation.chunk_id] = citation

                for i, citation in enumerate(
                    sorted(unique_citations.values(), key=lambda c: c.filename), 1
                ):
                    lines.append(f"{i}. {citation.filename}")
                    if citation.content_preview:
                        lines.append(f'   *"{citation.content_preview}..."*')

        return "\n".join(lines)

    def _section_to_markdown(
        self, section: DraftSection, level: int = 2, include_citations: bool = True
    ) -> list[str]:
        """Convert section to markdown lines.

        Args:
            section: Section to convert
            level: Heading level
            include_citations: Whether to include citation markers

        Returns:
            List of markdown lines
        """
        lines = []

        # Section heading
        heading = "#" * min(level, 6)
        lines.append(f"{heading} {section.title}")
        lines.append("")

        # Content
        if section.content:
            content = section.content

            # Add citation markers if requested
            if include_citations and section.citations:
                content += f" *[{len(section.citations)} sources]*"

            lines.append(content)
            lines.append("")

        # Subsections
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1, include_citations))

        return lines
