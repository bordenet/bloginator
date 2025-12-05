"""Tests for Markdown and plain text exporters."""

from pathlib import Path

from bloginator.export.markdown_exporter import MarkdownExporter
from bloginator.export.text_exporter import PlainTextExporter
from bloginator.models.draft import Citation, Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection


def _create_sample_draft() -> Draft:
    section = DraftSection(
        title="Section One",
        content="Some **markdown** content",
        citations=[
            Citation(
                chunk_id="c1",
                document_id="d1",
                filename="doc1.md",
                content_preview="Preview",
                similarity_score=0.9,
            )
        ],
    )
    draft = Draft(
        title="Draft Title",
        thesis="Draft thesis",
        keywords=["testing"],
        sections=[section],
    )
    draft.calculate_stats()
    return draft


def _create_sample_outline() -> Outline:
    section = OutlineSection(
        title="Outline Section",
        description="Overview of the topic.",
        coverage_pct=80.0,
        source_count=3,
        notes="Well supported.",
    )
    outline = Outline(
        title="Outline Title",
        thesis="Outline thesis",
        keywords=["testing"],
        sections=[section],
    )
    outline.calculate_stats()
    return outline


def test_markdown_exporter_writes_draft_and_outline(tmp_path: Path) -> None:
    draft = _create_sample_draft()
    outline = _create_sample_outline()
    exporter = MarkdownExporter()

    draft_path = tmp_path / "draft.md"
    outline_path = tmp_path / "outline.md"

    exporter.export_draft(draft, draft_path)
    exporter.export_outline(outline, outline_path)

    draft_text = draft_path.read_text(encoding="utf-8")
    outline_text = outline_path.read_text(encoding="utf-8")

    assert "Draft Title" in draft_text  # Title includes confidence prefix now
    assert "[100-90-02]" in draft_text  # Confidence scores in [XX-YY-ZZ] format
    assert "| Metric | Score | Description |" in draft_text  # Metrics table
    assert "Section One" in draft_text
    assert "## Outline Section" in outline_text
    assert "Coverage" in outline_text


def test_plain_text_exporter_strips_markdown_formatting() -> None:
    markdown = (
        "# Heading\n"
        "Some **bold** and *italic* text with a [link](https://example.com).\n"
        "<!-- comment that should be removed -->\n"
        "---\n"
        "Paragraph with citation *[3 sources]*.\n"
    )

    exporter = PlainTextExporter()
    text = exporter._strip_markdown(markdown)  # type: ignore[attr-defined]

    assert "Heading" in text
    assert "bold" in text and "**" not in text
    assert "italic" in text and "*italic*" not in text
    assert "link" in text and "(" not in text
    assert "sources" not in text  # citation marker removed
    assert "comment" not in text


def test_plain_text_exporter_exports_draft_and_outline(tmp_path: Path) -> None:
    draft = _create_sample_draft()
    outline = _create_sample_outline()
    exporter = PlainTextExporter()

    draft_path = tmp_path / "draft.txt"
    outline_path = tmp_path / "outline.txt"

    exporter.export_draft(draft, draft_path)
    exporter.export_outline(outline, outline_path)

    draft_text = draft_path.read_text(encoding="utf-8")
    outline_text = outline_path.read_text(encoding="utf-8")

    assert "Draft Title" in draft_text
    assert "Outline Section" in outline_text
