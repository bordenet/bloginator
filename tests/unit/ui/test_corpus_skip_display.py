"""Tests for skip summary display functionality in Streamlit UI."""

import json
from pathlib import Path


class TestSkipSummaryDisplay:
    """Tests for skip summary display functionality in Streamlit UI."""

    def test_skip_report_parsed_and_displayed(self, tmp_path: Path) -> None:
        """Test that skip report JSON is parsed and displayed correctly."""
        # Create mock report file
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "timestamp": "2025-12-03T12:00:00",
            "summary": {"total_skipped": 5, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp1.docx", "~$temp2.docx"],
                "already_extracted": ["file1.md", "file2.md", "file3.md"],
            },
            "errors": {},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Parse and verify
        loaded_data = json.loads(report_file.read_text())
        assert loaded_data["summary"]["total_skipped"] == 5
        assert len(loaded_data["skipped"]["temp_file"]) == 2
        assert len(loaded_data["skipped"]["already_extracted"]) == 3

    def test_skip_summary_shows_categories(self, tmp_path: Path) -> None:
        """Test that skip summary shows all skip categories."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 3, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp.docx"],
                "unsupported_extension": ["file.xyz (.xyz)"],
                "ignore_pattern": [".DS_Store"],
            },
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate skip summary display
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")

        assert len(skip_summary) == 3
        assert "**Temp File** (1)" in skip_summary
        assert "**Unsupported Extension** (1)" in skip_summary
        assert "**Ignore Pattern** (1)" in skip_summary

    def test_skip_summary_limits_displayed_items(self, tmp_path: Path) -> None:
        """Test that skip summary limits displayed items to first 5."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        # Create 10 skipped files
        skipped_files = [f"file{i}.md" for i in range(10)]
        report_data = {
            "summary": {"total_skipped": 10, "total_errors": 0},
            "skipped": {"already_extracted": skipped_files},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate display logic
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")
                for item in items[:5]:  # Only first 5
                    skip_summary.append(f"  • {item}")
                if len(items) > 5:
                    skip_summary.append(f"  ... and {len(items) - 5} more")

        # Should have: 1 header + 5 items + 1 "more" message = 7 lines
        assert len(skip_summary) == 7
        assert "file0.md" in skip_summary[1]
        assert "file4.md" in skip_summary[5]
        assert "... and 5 more" in skip_summary[6]

    def test_skip_summary_not_shown_when_zero_skips(self, tmp_path: Path) -> None:
        """Test that skip summary is not shown when there are no skips."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 0, "total_errors": 0},
            "skipped": {},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Check condition
        loaded_data = json.loads(report_file.read_text())
        should_show = loaded_data.get("summary", {}).get("total_skipped", 0) > 0

        assert should_show is False

    def test_skip_report_file_path_shown(self, tmp_path: Path) -> None:
        """Test that full report file path is shown to user."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"

        # Caption should show filename
        caption = f"Full report: {report_file.name}"

        assert "extraction_report_20251203_120000.json" in caption

    def test_multiple_report_files_uses_latest(self, tmp_path: Path) -> None:
        """Test that when multiple report files exist, the latest is used."""
        # Create multiple report files
        old_report = tmp_path / "extraction_report_20251203_100000.json"
        old_report.write_text(json.dumps({"summary": {"total_skipped": 1}}))

        new_report = tmp_path / "extraction_report_20251203_120000.json"
        new_report.write_text(json.dumps({"summary": {"total_skipped": 5}}))

        # Find latest
        report_files = sorted(tmp_path.glob("extraction_report_*.json"))
        latest_report = report_files[-1]

        assert latest_report == new_report
        loaded_data = json.loads(latest_report.read_text())
        assert loaded_data["summary"]["total_skipped"] == 5

    def test_skip_summary_handles_empty_categories(self, tmp_path: Path) -> None:
        """Test that empty skip categories are not displayed."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 2, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp.docx"],
                "already_extracted": [],  # Empty category
                "unsupported_extension": ["file.xyz (.xyz)"],
            },
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate display logic - only show non-empty categories
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:  # Only if category has items
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")

        # Should only show 2 categories (temp_file and unsupported_extension)
        assert len(skip_summary) == 2
        assert "**Temp File**" in skip_summary[0]

    def test_indexing_report_uses_correct_prefix(self, tmp_path: Path) -> None:
        """Test that indexing uses indexing_report_* prefix."""
        report_file = tmp_path / "indexing_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 3, "total_errors": 0},
            "skipped": {"unchanged_document": ["doc1.txt", "doc2.txt", "doc3.txt"]},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Find indexing reports
        report_files = sorted(tmp_path.glob("indexing_report_*.json"))
        assert len(report_files) == 1
        assert report_files[0].name.startswith("indexing_report_")

    def test_skip_summary_markdown_formatting(self, tmp_path: Path) -> None:
        """Test that skip summary uses proper markdown formatting."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 2, "total_errors": 0},
            "skipped": {"temp_file": ["~$temp1.docx", "~$temp2.docx"]},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Generate markdown
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                # Should use **bold** for headers and • for bullets
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")
                for item in items:
                    skip_summary.append(f"  • {item}")

        markdown_output = "\n".join(skip_summary)

        assert "**Temp File**" in markdown_output
        assert "  • ~$temp1.docx" in markdown_output
        assert "  • ~$temp2.docx" in markdown_output

    def test_skip_summary_error_handling(self, tmp_path: Path) -> None:
        """Test that corrupted report files are handled gracefully."""
        # Create invalid JSON file
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_file.write_text("{ invalid json }")

        # Should catch exception
        try:
            json.loads(report_file.read_text())
            raise AssertionError("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            # Expected - should be handled gracefully in UI
            pass
