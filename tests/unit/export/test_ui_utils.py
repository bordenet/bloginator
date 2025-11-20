"""Tests for Streamlit export UI utilities."""

from pathlib import Path

import pytest


pytest.importorskip("streamlit")

from bloginator.export.factory import ExportFormat  # noqa: E402
from bloginator.export.ui_utils import _get_mime_type, _load_document  # noqa: E402
from bloginator.models.draft import Draft  # noqa: E402
from bloginator.models.outline import Outline  # noqa: E402


def test_get_mime_type_for_supported_formats() -> None:
    assert _get_mime_type(ExportFormat.PDF) == "application/pdf"
    assert _get_mime_type(ExportFormat.DOCX).startswith("application/vnd.openxmlformats")
    assert _get_mime_type(ExportFormat.HTML) == "text/html"
    assert _get_mime_type(ExportFormat.MARKDOWN) == "text/markdown"
    assert _get_mime_type(ExportFormat.TEXT) == "text/plain"


def test_load_document_roundtrips_draft_and_outline(tmp_path: Path) -> None:
    draft = Draft(title="Draft Title", thesis="", keywords=[], sections=[])
    outline = Outline(title="Outline Title", thesis="", keywords=[], sections=[])

    draft_path = tmp_path / "draft.json"
    outline_path = tmp_path / "outline.json"

    draft_path.write_text(draft.model_dump_json(), encoding="utf-8")
    outline_path.write_text(outline.model_dump_json(), encoding="utf-8")

    loaded_draft = _load_document(draft_path, "draft")
    loaded_outline = _load_document(outline_path, "outline")

    assert isinstance(loaded_draft, Draft)
    assert isinstance(loaded_outline, Outline)
    assert loaded_draft.title == draft.title
    assert loaded_outline.title == outline.title
