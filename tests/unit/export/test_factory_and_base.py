"""Tests for export factory and base Exporter behavior."""

from pathlib import Path

import pytest

from bloginator.export.base import Exporter
from bloginator.export.factory import ExportFormat, create_exporter
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline


class DummyExporter(Exporter):
    """Simple exporter used to validate base dispatch behavior."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Path]] = []

    def export_draft(self, draft: Draft, output_path: Path) -> None:  # type: ignore[override]
        self.calls.append(("draft", draft.title, output_path))

    def export_outline(self, outline: Outline, output_path: Path) -> None:  # type: ignore[override]
        self.calls.append(("outline", outline.title, output_path))

    def get_file_extension(self) -> str:  # type: ignore[override]
        return "dummy"


def test_exporter_export_dispatches_based_on_document_type(tmp_path: Path) -> None:
    exporter = DummyExporter()
    draft = Draft(title="Draft Title", thesis="", keywords=[], sections=[])
    outline = Outline(title="Outline Title", thesis="", keywords=[], sections=[])

    draft_path = tmp_path / "draft.out"
    outline_path = tmp_path / "outline.out"

    exporter.export(draft, draft_path)
    exporter.export(outline, outline_path)

    assert ("draft", "Draft Title", draft_path) in exporter.calls
    assert ("outline", "Outline Title", outline_path) in exporter.calls


@pytest.mark.parametrize(
    "extension,expected",
    [
        ("md", ExportFormat.MARKDOWN),
        (".md", ExportFormat.MARKDOWN),
        ("markdown", ExportFormat.MARKDOWN),
        ("pdf", ExportFormat.PDF),
        (".pdf", ExportFormat.PDF),
        ("docx", ExportFormat.DOCX),
        (".docx", ExportFormat.DOCX),
        ("html", ExportFormat.HTML),
        ("htm", ExportFormat.HTML),
        ("txt", ExportFormat.TEXT),
        ("text", ExportFormat.TEXT),
    ],
)
def test_export_format_from_extension_valid(extension: str, expected: ExportFormat) -> None:
    assert ExportFormat.from_extension(extension) is expected


def test_export_format_from_extension_invalid() -> None:
    with pytest.raises(ValueError):
        ExportFormat.from_extension(".unknown")


@pytest.mark.parametrize(
    "format_,expected_cls_name",
    [
        (ExportFormat.MARKDOWN, "MarkdownExporter"),
        (ExportFormat.PDF, "PDFExporter"),
        (ExportFormat.DOCX, "DOCXExporter"),
        (ExportFormat.HTML, "HTMLExporter"),
        (ExportFormat.TEXT, "PlainTextExporter"),
    ],
)
def test_create_exporter_returns_correct_concrete_type(
    format_: ExportFormat, expected_cls_name: str
) -> None:
    exporter = create_exporter(format_)
    assert exporter.__class__.__name__ == expected_cls_name
    ext = exporter.get_file_extension()
    assert isinstance(ext, str) and ext
