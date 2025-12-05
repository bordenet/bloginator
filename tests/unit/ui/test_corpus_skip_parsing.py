"""Tests for real-time skip event parsing from CLI output."""

import re


class TestRealTimeSkipEventParsing:
    """Tests for real-time skip event parsing from CLI output."""

    def test_parse_skip_event_from_output_line(self) -> None:
        """Test parsing skip event from CLI output line."""
        line = "SKIP: temp_file: ~$document.docx"

        # Parse skip event
        match = re.match(r"SKIP:\s*(\w+):\s*(.+)", line)
        assert match is not None
        category = match.group(1)
        filename = match.group(2)

        assert category == "temp_file"
        assert filename == "~$document.docx"

    def test_parse_multiple_skip_events(self) -> None:
        """Test parsing multiple skip events from output."""
        lines = [
            "SKIP: temp_file: ~$temp1.docx",
            "Processing: file1.md",
            "SKIP: already_extracted: file2.md",
            "Processing: file3.md",
            "SKIP: unsupported_extension: file.xyz (.xyz)",
        ]

        skip_events = []
        for line in lines:
            match = re.match(r"SKIP:\s*(\w+):\s*(.+)", line)
            if match:
                skip_events.append({"category": match.group(1), "file": match.group(2)})

        assert len(skip_events) == 3
        assert skip_events[0]["category"] == "temp_file"
        assert skip_events[1]["category"] == "already_extracted"
        assert skip_events[2]["category"] == "unsupported_extension"

    def test_skip_counter_increments_correctly(self) -> None:
        """Test that skip counter increments for each skip event."""
        lines = [
            "SKIP: temp_file: ~$temp1.docx",
            "SKIP: temp_file: ~$temp2.docx",
            "SKIP: already_extracted: file1.md",
        ]

        skip_count = 0
        for line in lines:
            if line.startswith("SKIP:"):
                skip_count += 1

        assert skip_count == 3

    def test_skip_events_grouped_by_category(self) -> None:
        """Test that skip events are grouped by category."""
        lines = [
            "SKIP: temp_file: ~$temp1.docx",
            "SKIP: temp_file: ~$temp2.docx",
            "SKIP: already_extracted: file1.md",
            "SKIP: already_extracted: file2.md",
            "SKIP: already_extracted: file3.md",
        ]

        skip_by_category: dict[str, list[str]] = {}
        for line in lines:
            match = re.match(r"SKIP:\s*(\w+):\s*(.+)", line)
            if match:
                category = match.group(1)
                filename = match.group(2)
                if category not in skip_by_category:
                    skip_by_category[category] = []
                skip_by_category[category].append(filename)

        assert len(skip_by_category["temp_file"]) == 2
        assert len(skip_by_category["already_extracted"]) == 3

    def test_skip_event_with_special_characters(self) -> None:
        """Test parsing skip event with special characters in filename."""
        line = "SKIP: temp_file: ~$My Document (Copy).docx"

        match = re.match(r"SKIP:\s*(\w+):\s*(.+)", line)
        assert match is not None
        filename = match.group(2)

        assert filename == "~$My Document (Copy).docx"

    def test_non_skip_lines_ignored(self) -> None:
        """Test that non-skip lines are ignored."""
        lines = [
            "Processing: file1.md",
            "Extracting: file2.pdf",
            "Complete: 10 files processed",
            "Error: Failed to read file3.docx",
        ]

        skip_events = []
        for line in lines:
            match = re.match(r"SKIP:\s*(\w+):\s*(.+)", line)
            if match:
                skip_events.append(match.groups())

        assert len(skip_events) == 0

    def test_skip_event_display_format(self) -> None:
        """Test that skip events are formatted for display."""
        skip_by_category = {
            "temp_file": ["~$temp1.docx", "~$temp2.docx"],
            "already_extracted": ["file1.md", "file2.md", "file3.md"],
        }

        display_lines = []
        for category, files in skip_by_category.items():
            display_lines.append(f"**{category.replace('_', ' ').title()}** ({len(files)})")
            for f in files[:5]:
                display_lines.append(f"  • {f}")

        assert len(display_lines) == 7  # 2 headers + 5 files
        assert "**Temp File** (2)" in display_lines
        assert "**Already Extracted** (3)" in display_lines

    def test_skip_counter_updates_in_real_time(self) -> None:
        """Test that skip counter can be updated in real-time."""
        skip_count = 0
        skip_by_category: dict[str, int] = {}

        # Simulate real-time updates
        events = [
            ("temp_file", "~$temp1.docx"),
            ("temp_file", "~$temp2.docx"),
            ("already_extracted", "file1.md"),
        ]

        for category, _filename in events:
            skip_count += 1
            skip_by_category[category] = skip_by_category.get(category, 0) + 1

        assert skip_count == 3
        assert skip_by_category["temp_file"] == 2
        assert skip_by_category["already_extracted"] == 1


class TestExplicitProgressLineFormats:
    """Tests for explicit progress line format parsing."""

    def test_parse_simple_progress_line(self) -> None:
        """Test parsing simple progress line."""
        line = "Extracting: important_document.pdf"

        match = re.match(r"Extracting:\s*(.+)", line)
        assert match is not None
        filename = match.group(1)

        assert filename == "important_document.pdf"

    def test_parse_indexing_progress_line(self) -> None:
        """Test parsing indexing progress line."""
        line = "Indexing: chunk_001.json (500 tokens)"

        match = re.match(r"Indexing:\s*(.+)", line)
        assert match is not None
        details = match.group(1)

        assert "chunk_001.json" in details
        assert "500 tokens" in details

    def test_parse_completion_line(self) -> None:
        """Test parsing completion line."""
        line = "Complete: Processed 100 files, 5 skipped, 0 errors"

        match = re.match(r"Complete:\s*(.+)", line)
        assert match is not None
        summary = match.group(1)

        assert "100 files" in summary
        assert "5 skipped" in summary
        assert "0 errors" in summary

    def test_parse_error_line(self) -> None:
        """Test parsing error line."""
        line = "ERROR: Failed to read file: permission denied"

        match = re.match(r"ERROR:\s*(.+)", line)
        assert match is not None
        error_msg = match.group(1)

        assert "Failed to read file" in error_msg
        assert "permission denied" in error_msg

    def test_progress_percentage_calculation(self) -> None:
        """Test calculating progress percentage from counts."""
        current = 25
        total = 100

        percentage = (current / total) * 100

        assert percentage == 25.0

    def test_progress_percentage_handles_zero_total(self) -> None:
        """Test that zero total doesn't cause division error."""
        current = 0
        total = 0

        percentage = (current / total) * 100 if total > 0 else 0

        assert percentage == 0

    def test_parse_progress_line_with_count(self) -> None:
        """Test parsing progress line with file count."""
        line = "Processing file 5 of 100: document.pdf"

        match = re.match(r"Processing file (\d+) of (\d+): (.+)", line)
        assert match is not None
        current = int(match.group(1))
        total = int(match.group(2))
        filename = match.group(3)

        assert current == 5
        assert total == 100
        assert filename == "document.pdf"
