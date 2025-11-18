"""Plain text exporter for drafts and outlines."""

import re
from pathlib import Path

from bloginator.export.base import Exporter
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline


class PlainTextExporter(Exporter):
    """Exports documents to plain text format.

    Strips Markdown formatting and outputs clean text.
    """

    def export_draft(self, draft: Draft, output_path: Path) -> None:
        """Export draft to plain text file.

        Args:
            draft: Draft document to export
            output_path: Path where text file should be saved
        """
        # Get markdown then strip formatting
        markdown = draft.to_markdown(include_citations=False)
        plain_text = self._strip_markdown(markdown)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plain_text, encoding="utf-8")

    def export_outline(self, outline: Outline, output_path: Path) -> None:
        """Export outline to plain text file.

        Args:
            outline: Outline document to export
            output_path: Path where text file should be saved
        """
        # Get markdown then strip formatting
        markdown = outline.to_markdown()
        plain_text = self._strip_markdown(markdown)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plain_text, encoding="utf-8")

    def get_file_extension(self) -> str:
        """Get file extension for plain text format.

        Returns:
            'txt'
        """
        return "txt"

    def _strip_markdown(self, markdown: str) -> str:
        """Strip Markdown formatting from text.

        Args:
            markdown: Markdown-formatted text

        Returns:
            Plain text without formatting
        """
        text = markdown

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Remove heading markers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

        # Remove emphasis/bold
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Bold
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # Italic
        text = re.sub(r"__(.+?)__", r"\1", text)  # Bold alt
        text = re.sub(r"_(.+?)_", r"\1", text)  # Italic alt

        # Remove links but keep text
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

        # Remove horizontal rules
        text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)

        # Remove citation markers
        text = re.sub(r"\s*\*\[\d+\s+sources?\]\*", "", text)

        # Clean up extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text
