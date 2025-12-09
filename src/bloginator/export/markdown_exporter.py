"""Markdown exporter for drafts and outlines."""

from pathlib import Path

from bloginator.export.base import Exporter
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline


class MarkdownExporter(Exporter):
    """Exports documents to Markdown format.

    Uses the existing to_markdown() methods on Draft and Outline models.
    """

    def export_draft(self, draft: Draft, output_path: Path) -> None:
        """Export draft to Markdown file.

        Args:
            draft: Draft document to export
            output_path: Path where markdown file should be saved
        """
        markdown_content = draft.to_markdown()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")

    def export_outline(self, outline: Outline, output_path: Path) -> None:
        """Export outline to Markdown file.

        Args:
            outline: Outline document to export
            output_path: Path where markdown file should be saved
        """
        markdown_content = outline.to_markdown()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_content, encoding="utf-8")

    def get_file_extension(self) -> str:
        """Get file extension for Markdown format.

        Returns:
            'md'
        """
        return "md"
