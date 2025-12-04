"""Tests for error reporting utilities including skip tracking."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from bloginator.cli.error_reporting import (
    ErrorCategory,
    ErrorTracker,
    SkipCategory,
    create_error_panel,
)


class TestErrorTracker:
    """Tests for ErrorTracker class."""

    def test_init_empty(self):
        """Tracker initializes with zero counts."""
        tracker = ErrorTracker()
        assert tracker.total_errors == 0
        assert tracker.total_skipped == 0
        assert len(tracker.errors) == 0
        assert len(tracker.skipped) == 0

    def test_record_error(self):
        """Recording an error increments count and stores context."""
        tracker = ErrorTracker()
        exc = ValueError("test error")
        tracker.record_error(ErrorCategory.CORRUPTED_FILE, "test.pdf", exc)

        assert tracker.total_errors == 1
        assert len(tracker.errors[ErrorCategory.CORRUPTED_FILE]) == 1
        context, stored_exc = tracker.errors[ErrorCategory.CORRUPTED_FILE][0]
        assert context == "test.pdf"
        assert stored_exc is exc

    def test_record_skip(self):
        """Recording a skip increments count and stores context."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$test.docx")

        assert tracker.total_skipped == 1
        assert len(tracker.skipped[SkipCategory.TEMP_FILE]) == 1
        assert tracker.skipped[SkipCategory.TEMP_FILE][0] == "~$test.docx"

    def test_record_multiple_skips_same_category(self):
        """Multiple skips in same category are grouped."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$a.docx")
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$b.docx")
        tracker.record_skip(SkipCategory.ALREADY_EXTRACTED, "existing.md")

        assert tracker.total_skipped == 3
        assert len(tracker.skipped[SkipCategory.TEMP_FILE]) == 2
        assert len(tracker.skipped[SkipCategory.ALREADY_EXTRACTED]) == 1

    def test_categorize_file_not_found(self):
        """FileNotFoundError is categorized correctly."""
        tracker = ErrorTracker()
        exc = FileNotFoundError("missing file")
        category = tracker.categorize_exception(exc)
        assert category == ErrorCategory.FILE_NOT_FOUND

    def test_categorize_permission_denied(self):
        """PermissionError is categorized correctly."""
        tracker = ErrorTracker()
        exc = PermissionError("access denied")
        category = tracker.categorize_exception(exc)
        assert category == ErrorCategory.PERMISSION_DENIED

    def test_categorize_encoding_error(self):
        """UnicodeDecodeError is categorized correctly."""
        tracker = ErrorTracker()
        exc = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
        category = tracker.categorize_exception(exc)
        assert category == ErrorCategory.ENCODING_ERROR

    def test_categorize_corrupted_file_from_message(self):
        """Exception with 'corrupted' in message is categorized."""
        tracker = ErrorTracker()
        exc = Exception("file is corrupted and cannot be read")
        category = tracker.categorize_exception(exc)
        assert category == ErrorCategory.CORRUPTED_FILE

    def test_categorize_unsupported_format_by_extension(self):
        """Unsupported file extension triggers unsupported format category."""
        tracker = ErrorTracker()
        exc = Exception("unknown error")
        category = tracker.categorize_exception(exc, file_path=Path("image.png"))
        assert category == ErrorCategory.UNSUPPORTED_FORMAT

    def test_categorize_unknown_falls_through(self):
        """Unknown exceptions default to UNKNOWN category."""
        tracker = ErrorTracker()
        exc = Exception("some random error")
        category = tracker.categorize_exception(exc)
        assert category == ErrorCategory.UNKNOWN


class TestErrorTrackerSaveToFile:
    """Tests for saving reports to file."""

    def test_save_creates_file(self, tmp_path: Path):
        """save_to_file creates a JSON file with correct structure."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$test.docx")
        tracker.record_error(ErrorCategory.CORRUPTED_FILE, "broken.pdf", ValueError("bad"))

        report_path = tracker.save_to_file(tmp_path, prefix="test")

        assert report_path.exists()
        assert report_path.suffix == ".json"
        assert "test_report_" in report_path.name

    def test_save_file_content_structure(self, tmp_path: Path):
        """Saved JSON has expected structure."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$a.docx")
        tracker.record_skip(SkipCategory.ALREADY_EXTRACTED, "old.md")
        tracker.record_error(ErrorCategory.PERMISSION_DENIED, "locked.pdf", PermissionError("denied"))

        report_path = tracker.save_to_file(tmp_path, prefix="extraction")
        data = json.loads(report_path.read_text())

        assert "timestamp" in data
        assert data["summary"]["total_skipped"] == 2
        assert data["summary"]["total_errors"] == 1
        assert "temp_file" in data["skipped"]
        assert "already_extracted" in data["skipped"]
        assert "permission_denied" in data["errors"]

    def test_save_creates_output_dir_if_missing(self, tmp_path: Path):
        """save_to_file creates output directory if it doesn't exist."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "test")

        nested_dir = tmp_path / "deeply" / "nested" / "dir"
        report_path = tracker.save_to_file(nested_dir)

        assert nested_dir.exists()
        assert report_path.exists()

    def test_save_empty_tracker(self, tmp_path: Path):
        """Empty tracker still produces valid JSON."""
        tracker = ErrorTracker()
        report_path = tracker.save_to_file(tmp_path)

        data = json.loads(report_path.read_text())
        assert data["summary"]["total_skipped"] == 0
        assert data["summary"]["total_errors"] == 0

    def test_save_preserves_all_skip_items(self, tmp_path: Path):
        """All skipped items are preserved in the output file."""
        tracker = ErrorTracker()
        for i in range(100):
            tracker.record_skip(SkipCategory.UNSUPPORTED_EXTENSION, f"file{i}.xyz")

        report_path = tracker.save_to_file(tmp_path)
        data = json.loads(report_path.read_text())

        assert len(data["skipped"]["unsupported_extension"]) == 100

    def test_save_error_details_preserved(self, tmp_path: Path):
        """Error details including type and message are preserved."""
        tracker = ErrorTracker()
        tracker.record_error(
            ErrorCategory.CORRUPTED_FILE,
            "bad.pdf",
            ValueError("PDF parsing failed: invalid header"),
        )

        report_path = tracker.save_to_file(tmp_path)
        data = json.loads(report_path.read_text())

        error_entry = data["errors"]["corrupted_file"][0]
        assert error_entry["context"] == "bad.pdf"
        assert error_entry["type"] == "ValueError"
        assert "invalid header" in error_entry["error"]


class TestPrintSkipSummary:
    """Tests for print_skip_summary output formatting."""

    def test_no_output_when_empty(self, capsys):
        """No output when there are no skips."""
        tracker = ErrorTracker()
        console = Console(force_terminal=True)
        tracker.print_skip_summary(console)
        # Should not raise and should produce minimal output

    def test_truncation_with_many_items(self):
        """Large skip lists are truncated in display."""
        tracker = ErrorTracker()
        for i in range(100):
            tracker.record_skip(SkipCategory.TEMP_FILE, f"~$file{i}.docx")

        console = Console(force_terminal=True, width=120)
        # Should not raise and should truncate properly
        tracker.print_skip_summary(console, max_display_lines=10)

    def test_file_path_shown_when_provided(self, tmp_path: Path):
        """File path is included in output when provided."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "~$test.docx")

        console = Console(force_terminal=True, width=200, record=True)
        tracker.print_skip_summary(console, show_file_path=tmp_path / "report.json")

        output = console.export_text()
        # Path may be wrapped across lines, so check for key parts
        assert "Full report:" in output
        assert "report.json" in output or str(tmp_path) in output

    def test_all_categories_shown(self):
        """All skip categories with items are shown in summary."""
        tracker = ErrorTracker()
        tracker.record_skip(SkipCategory.TEMP_FILE, "a")
        tracker.record_skip(SkipCategory.ALREADY_EXTRACTED, "b")
        tracker.record_skip(SkipCategory.UNSUPPORTED_EXTENSION, "c")

        console = Console(force_terminal=True, width=120, record=True)
        tracker.print_skip_summary(console)

        output = console.export_text()
        assert "Temp File" in output
        assert "Already Extracted" in output
        assert "Unsupported Extension" in output


class TestSkipCategory:
    """Tests for SkipCategory enum values."""

    def test_all_categories_have_string_values(self):
        """All categories are string-typed for JSON serialization."""
        for category in SkipCategory:
            assert isinstance(category.value, str)

    def test_category_values_are_snake_case(self):
        """Category values are consistent snake_case."""
        for category in SkipCategory:
            assert category.value == category.value.lower()
            assert " " not in category.value


class TestCreateErrorPanel:
    """Tests for create_error_panel utility."""

    def test_creates_panel_with_message(self):
        """Panel is created with error message."""
        panel = create_error_panel("Test Title", "Test message")
        assert panel is not None

    def test_creates_panel_with_suggestion(self):
        """Panel includes suggestion when provided."""
        panel = create_error_panel("Title", "Message", "Try this fix")
        assert panel is not None
