"""PDF exporter for drafts and outlines."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from bloginator.export.base import Exporter
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection


class PDFExporter(Exporter):
    """Exports documents to PDF format using ReportLab."""

    def export_draft(self, draft: Draft, output_path: Path) -> None:
        """Export draft to PDF file.

        Args:
            draft: Draft document to export
            output_path: Path where PDF file should be saved
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build story (content elements)
        story = []
        styles = getSampleStyleSheet()
        self._add_custom_styles(styles)

        # Title
        story.append(Paragraph(draft.title, styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        # Thesis
        if draft.thesis:
            story.append(Paragraph(f"<i>{draft.thesis}</i>", styles["BodyText"]))
            story.append(Spacer(1, 0.3 * inch))

        # Metadata
        metadata = "<font size=9 color='gray'>"
        metadata += f"Classification: {draft.classification} | "
        metadata += f"Audience: {draft.audience} | "
        metadata += f"Generated: {draft.created_date.strftime('%Y-%m-%d')}"
        metadata += "</font>"
        story.append(Paragraph(metadata, styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.3 * inch))

        # Sections
        for section in draft.sections:
            self._add_draft_section(story, section, styles, level=2)

        # Build PDF
        doc.build(story)

    def export_outline(self, outline: Outline, output_path: Path) -> None:
        """Export outline to PDF file.

        Args:
            outline: Outline document to export
            output_path: Path where PDF file should be saved
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build story
        story = []
        styles = getSampleStyleSheet()
        self._add_custom_styles(styles)

        # Title
        story.append(Paragraph(outline.title, styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        # Thesis
        if outline.thesis:
            story.append(Paragraph(f"<i>{outline.thesis}</i>", styles["BodyText"]))
            story.append(Spacer(1, 0.3 * inch))

        # Metadata
        metadata = "<font size=9 color='gray'>"
        metadata += f"Classification: {outline.classification} | "
        metadata += f"Audience: {outline.audience} | "
        metadata += f"Created: {outline.created_date.strftime('%Y-%m-%d')}"
        metadata += "</font>"
        story.append(Paragraph(metadata, styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        story.append(Spacer(1, 0.3 * inch))

        # Sections
        for section in outline.sections:
            self._add_outline_section(story, section, styles, level=2)

        # Build PDF
        doc.build(story)

    def get_file_extension(self) -> str:
        """Get file extension for PDF format.

        Returns:
            'pdf'
        """
        return "pdf"

    def _add_custom_styles(self, styles):
        """Add custom paragraph styles.

        Args:
            styles: StyleSheet to add styles to
        """
        # Heading styles for different levels
        styles.add(
            ParagraphStyle(
                name="Heading2",
                parent=styles["Heading1"],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor("#1E88E5"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="Heading3",
                parent=styles["Heading2"],
                fontSize=14,
                spaceAfter=10,
            )
        )
        styles.add(
            ParagraphStyle(
                name="Heading4",
                parent=styles["Heading3"],
                fontSize=12,
                spaceAfter=8,
            )
        )

    def _add_draft_section(self, story, section: DraftSection, styles, level: int):
        """Add draft section to story.

        Args:
            story: List to append elements to
            section: Draft section to add
            styles: StyleSheet with paragraph styles
            level: Heading level (2-6)
        """
        # Section heading
        heading_style = self._get_heading_style(styles, level)
        story.append(Paragraph(section.title, heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Content
        if section.content:
            # Escape HTML special characters
            content = (
                section.content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            story.append(Paragraph(content, styles["BodyText"]))

            # Citation note
            if section.citations:
                citation_note = (
                    f"<font size=8 color='gray'><i>[{len(section.citations)} sources]</i></font>"
                )
                story.append(Spacer(1, 0.05 * inch))
                story.append(Paragraph(citation_note, styles["BodyText"]))

            story.append(Spacer(1, 0.2 * inch))

        # Subsections
        for subsection in section.subsections:
            self._add_draft_section(story, subsection, styles, level + 1)

    def _add_outline_section(self, story, section: OutlineSection, styles, level: int):
        """Add outline section to story.

        Args:
            story: List to append elements to
            section: Outline section to add
            styles: StyleSheet with paragraph styles
            level: Heading level (2-6)
        """
        # Section heading
        heading_style = self._get_heading_style(styles, level)
        story.append(Paragraph(section.title, heading_style))
        story.append(Spacer(1, 0.1 * inch))

        # Key points
        if section.key_points:
            for point in section.key_points:
                bullet_text = f"• {point}"
                story.append(Paragraph(bullet_text, styles["BodyText"]))
            story.append(Spacer(1, 0.2 * inch))

        # Subsections
        for subsection in section.subsections:
            self._add_outline_section(story, subsection, styles, level + 1)

    def _get_heading_style(self, styles, level: int):
        """Get appropriate heading style for level.

        Args:
            styles: StyleSheet with paragraph styles
            level: Heading level (2-6)

        Returns:
            ParagraphStyle for heading
        """
        level = min(level, 4)  # Cap at level 4
        if level == 2:
            return styles["Heading2"]
        elif level == 3:
            return styles["Heading3"]
        else:
            return styles["Heading4"]
