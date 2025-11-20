"""Export factory for creating format-specific exporters."""

from enum import Enum

from bloginator.export.base import Exporter
from bloginator.export.docx_exporter import DOCXExporter
from bloginator.export.html_exporter import HTMLExporter
from bloginator.export.markdown_exporter import MarkdownExporter
from bloginator.export.pdf_exporter import PDFExporter
from bloginator.export.text_exporter import PlainTextExporter


class ExportFormat(str, Enum):
    """Supported export formats."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    TEXT = "text"

    @classmethod
    def from_extension(cls, extension: str) -> "ExportFormat":
        """Get format from file extension.

        Args:
            extension: File extension (with or without dot)

        Returns:
            ExportFormat enum value

        Raises:
            ValueError: If extension is not supported
        """
        ext = extension.lstrip(".").lower()
        mapping = {
            "md": cls.MARKDOWN,
            "markdown": cls.MARKDOWN,
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
            "html": cls.HTML,
            "htm": cls.HTML,
            "txt": cls.TEXT,
            "text": cls.TEXT,
        }

        if ext not in mapping:
            raise ValueError(
                f"Unsupported export format: {extension}. "
                f"Supported: {', '.join(mapping.keys())}"
            )

        return mapping[ext]


def create_exporter(format: ExportFormat) -> Exporter:
    """Create exporter for specified format.

    Args:
        format: Export format to use

    Returns:
        Exporter instance for the format

    Raises:
        ValueError: If format is not supported
    """
    if format is ExportFormat.MARKDOWN:
        return MarkdownExporter()
    if format is ExportFormat.PDF:
        return PDFExporter()
    if format is ExportFormat.DOCX:
        return DOCXExporter()
    if format is ExportFormat.HTML:
        return HTMLExporter()
    if format is ExportFormat.TEXT:
        return PlainTextExporter()

    raise ValueError(f"Unsupported export format: {format}")
