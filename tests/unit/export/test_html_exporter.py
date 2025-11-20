"""Tests for HTML exporter."""

from pathlib import Path

from bloginator.export.html_exporter import HTMLExporter
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection


def _create_draft_with_html_sensitive_content() -> Draft:
    section = DraftSection(
        title="Intro <Section>",
        content="Content with <tags> & ampersands.",
        citations=[],
    )
    draft = Draft(
        title="Draft & Title",
        thesis="Thesis with <angle brackets>",
        keywords=["testing"],
        sections=[section],
    )
    draft.calculate_stats()
    return draft


def _create_outline_with_metadata() -> Outline:
    section = OutlineSection(
        title="Overview",
        description="Overview of <topic>.",
        coverage_pct=75.0,
        source_count=2,
        notes="Important note.",
    )
    outline = Outline(
        title="Outline Title",
        thesis="Outline thesis",
        keywords=["testing"],
        sections=[section],
    )
    outline.calculate_stats()
    return outline


def test_html_exporter_renders_draft_with_metadata(tmp_path: Path) -> None:
    draft = _create_draft_with_html_sensitive_content()
    exporter = HTMLExporter()
    output_path = tmp_path / "draft.html"

    exporter.export_draft(draft, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "<h1>Draft &amp; Title</h1>" in html
    assert "Classification:" in html
    assert "Audience:" in html
    assert "Intro &lt;Section&gt;" in html
    assert "Content with &lt;tags&gt; &amp; ampersands." in html


def test_html_exporter_renders_outline_sections_with_coverage(tmp_path: Path) -> None:
    outline = _create_outline_with_metadata()
    exporter = HTMLExporter()
    output_path = tmp_path / "outline.html"

    exporter.export_outline(outline, output_path)

    html = output_path.read_text(encoding="utf-8")
    assert "<h2>Overview</h2>" in html
    assert "Overview of &lt;topic&gt;." in html
    assert "Coverage: 75%" in html
    assert "2 document(s)" in html
    assert "Important note." in html
