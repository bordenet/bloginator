"""HTML exporter for drafts and outlines."""

from pathlib import Path

from bloginator.export.base import Exporter
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection


class HTMLExporter(Exporter):
    """Exports documents to standalone HTML format with embedded CSS."""

    def export_draft(self, draft: Draft, output_path: Path) -> None:
        """Export draft to HTML file.

        Args:
            draft: Draft document to export
            output_path: Path where HTML file should be saved
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html_page(
            title=draft.title,
            content=self._draft_to_html(draft),
            metadata={
                "Classification": draft.classification,
                "Audience": draft.audience,
                "Generated": draft.created_date.strftime("%Y-%m-%d %H:%M"),
                "Voice Score": f"{draft.voice_score:.2f}",
                "Citations": str(draft.total_citations),
                "Words": str(draft.total_words),
            },
        )

        output_path.write_text(html, encoding="utf-8")

    def export_outline(self, outline: Outline, output_path: Path) -> None:
        """Export outline to HTML file.

        Args:
            outline: Outline document to export
            output_path: Path where HTML file should be saved
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        html = self._build_html_page(
            title=outline.title,
            content=self._outline_to_html(outline),
            metadata={
                "Classification": outline.classification,
                "Audience": outline.audience,
                "Created": outline.created_date.strftime("%Y-%m-%d"),
            },
        )

        output_path.write_text(html, encoding="utf-8")

    def get_file_extension(self) -> str:
        """Get file extension for HTML format.

        Returns:
            'html'
        """
        return "html"

    def _build_html_page(self, title: str, content: str, metadata: dict[str, str]) -> str:
        """Build complete HTML page with CSS.

        Args:
            title: Document title
            content: HTML content body
            metadata: Dictionary of metadata key-value pairs

        Returns:
            Complete HTML page string
        """
        escaped_title = self._escape_html(title)

        # Build metadata HTML
        metadata_html = "<div class='metadata'>\n"
        for key, value in metadata.items():
            metadata_html += (
                "  <span><strong>"
                f"{self._escape_html(key)}:"
                "</strong> "
                f"{self._escape_html(value)}</span>\n"
            )
        metadata_html += "</div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escaped_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }}
        h1 {{
            color: #1E88E5;
            border-bottom: 2px solid #1E88E5;
            padding-bottom: 0.5rem;
            text-align: center;
        }}
        h2 {{
            color: #1976D2;
            margin-top: 2rem;
        }}
        h3 {{
            color: #1565C0;
            margin-top: 1.5rem;
        }}
        .thesis {{
            font-style: italic;
            text-align: center;
            color: #666;
            margin: 1.5rem 0;
            font-size: 1.1rem;
        }}
        .metadata {{
            background-color: #f5f5f5;
            border-left: 4px solid #1E88E5;
            padding: 1rem;
            margin: 2rem 0;
            font-size: 0.9rem;
        }}
        .metadata span {{
            display: inline-block;
            margin-right: 1.5rem;
            color: #666;
        }}
        .section-coverage {{
            font-size: 0.85rem;
            color: #666;
            margin: 0.25rem 0 0.5rem 0;
        }}
        .section-notes {{
            font-size: 0.85rem;
            color: #888;
            font-style: italic;
            margin-bottom: 0.75rem;
        }}
        .citation-note {{
            font-size: 0.85rem;
            color: #888;
            font-style: italic;
        }}
        ul {{
            margin: 0.5rem 0;
        }}
        hr {{
            border: none;
            border-top: 1px solid #ddd;
            margin: 2rem 0;
        }}
        @media print {{
            body {{
                max-width: 100%;
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <h1>{escaped_title}</h1>
    {metadata_html}
    <hr>
    {content}
</body>
</html>"""

    def _draft_to_html(self, draft: Draft) -> str:
        """Convert draft to HTML content.

        Args:
            draft: Draft document

        Returns:
            HTML content string
        """
        html_parts = []

        # Thesis
        if draft.thesis:
            html_parts.append(f'<p class="thesis">{self._escape_html(draft.thesis)}</p>')

        # Sections
        for section in draft.sections:
            html_parts.append(self._draft_section_to_html(section, level=2))

        return "\n".join(html_parts)

    def _draft_section_to_html(self, section: DraftSection, level: int) -> str:
        """Convert draft section to HTML.

        Args:
            section: Draft section
            level: Heading level (2-6)

        Returns:
            HTML string
        """
        level = min(level, 6)
        html_parts = []

        # Section heading
        html_parts.append(f"<h{level}>{self._escape_html(section.title)}</h{level}>")

        # Content
        if section.content:
            html_parts.append(f"<p>{self._escape_html(section.content)}</p>")

            # Citation note
            if section.citations:
                html_parts.append(
                    f'<p class="citation-note">[{len(section.citations)} sources]</p>'
                )

        # Subsections
        for subsection in section.subsections:
            html_parts.append(self._draft_section_to_html(subsection, level + 1))

        return "\n".join(html_parts)

    def _outline_to_html(self, outline: Outline) -> str:
        """Convert outline to HTML content.

        Args:
            outline: Outline document

        Returns:
            HTML content string
        """
        html_parts = []

        # Thesis
        if outline.thesis:
            html_parts.append(f'<p class="thesis">{self._escape_html(outline.thesis)}</p>')

        # Sections
        for section in outline.sections:
            html_parts.append(self._outline_section_to_html(section, level=2))

        return "\n".join(html_parts)

    def _outline_section_to_html(self, section: OutlineSection, level: int) -> str:
        """Convert outline section to HTML.

        Args:
            section: Outline section
            level: Heading level (2-6)

        Returns:
            HTML string
        """
        level = min(level, 6)
        html_parts: list[str] = []

        # Section heading
        html_parts.append(f"<h{level}>{self._escape_html(section.title)}</h{level}>")

        # Description
        if section.description:
            html_parts.append(f"<p>{self._escape_html(section.description)}</p>")

        # Coverage and source metadata
        coverage_text = (
            f"Coverage: {section.coverage_pct:.0f}% from {section.source_count} document(s)"
        )
        html_parts.append(f"<p class='section-coverage'>{self._escape_html(coverage_text)}</p>")

        # Notes
        if section.notes:
            html_parts.append(
                "<p class='section-notes'><em>"
                + f"Note: {self._escape_html(section.notes)}</em></p>"
            )

        # Subsections
        for subsection in section.subsections:
            html_parts.append(self._outline_section_to_html(subsection, level + 1))

        return "\n".join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            HTML-safe string
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )
