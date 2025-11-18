"""Base exporter interface for all export formats."""

from abc import ABC, abstractmethod
from pathlib import Path

from bloginator.models.draft import Draft
from bloginator.models.outline import Outline


class Exporter(ABC):
    """Abstract base class for document exporters.

    All exporters must implement the export_draft and export_outline
    methods to convert documents to their specific format.
    """

    @abstractmethod
    def export_draft(self, draft: Draft, output_path: Path) -> None:
        """Export draft to file in this format.

        Args:
            draft: Draft document to export
            output_path: Path where exported file should be saved
        """
        pass

    @abstractmethod
    def export_outline(self, outline: Outline, output_path: Path) -> None:
        """Export outline to file in this format.

        Args:
            outline: Outline document to export
            output_path: Path where exported file should be saved
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format (without dot).

        Returns:
            File extension string (e.g., 'pdf', 'docx', 'html')
        """
        pass

    def export(self, document: Draft | Outline, output_path: Path) -> None:
        """Export document to file (auto-detects type).

        Args:
            document: Draft or Outline to export
            output_path: Path where exported file should be saved
        """
        if isinstance(document, Draft):
            self.export_draft(document, output_path)
        elif isinstance(document, Outline):
            self.export_outline(document, output_path)
        else:
            raise TypeError(f"Unsupported document type: {type(document)}")
