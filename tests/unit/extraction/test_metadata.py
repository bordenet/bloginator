"""Tests for metadata extraction."""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction.metadata import (
    count_words,
    extract_file_metadata,
    extract_yaml_frontmatter,
    parse_date_string,
)


class TestExtractFileMetadata:
    """Test file metadata extraction."""

    def test_extract_file_metadata_exists(self, tmp_path: Path) -> None:
        """Test extracting metadata from existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        metadata = extract_file_metadata(test_file)

        assert "created_date" in metadata
        assert "modified_date" in metadata
        assert "file_size" in metadata
        assert isinstance(metadata["created_date"], datetime)
        assert isinstance(metadata["modified_date"], datetime)
        assert metadata["file_size"] == 11  # "Hello world" is 11 bytes

    def test_extract_file_metadata_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting metadata from nonexistent file raises error."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            extract_file_metadata(nonexistent)


class TestExtractYamlFrontmatter:
    """Test YAML frontmatter extraction."""

    def test_extract_yaml_frontmatter_valid(self) -> None:
        """Test extracting valid YAML frontmatter."""
        content = """---
title: My Blog Post
date: 2020-01-15
tags: [agile, culture]
---

# My Blog Post

Content here.
"""
        metadata = extract_yaml_frontmatter(content)

        assert metadata["title"] == "My Blog Post"
        # YAML parser converts date strings to date objects
        assert metadata["date"] == datetime(2020, 1, 15).date()
        assert metadata["tags"] == ["agile", "culture"]

    def test_extract_yaml_frontmatter_no_frontmatter(self) -> None:
        """Test extracting from content without frontmatter."""
        content = "# My Blog Post\n\nNo frontmatter here."

        metadata = extract_yaml_frontmatter(content)

        assert metadata == {}

    def test_extract_yaml_frontmatter_invalid_yaml(self) -> None:
        """Test extracting invalid YAML frontmatter."""
        content = """---
this is not: [valid: yaml
---

Content.
"""
        metadata = extract_yaml_frontmatter(content)

        assert metadata == {}

    def test_extract_yaml_frontmatter_empty(self) -> None:
        """Test extracting empty frontmatter."""
        content = """---
---

Content.
"""
        metadata = extract_yaml_frontmatter(content)

        assert metadata == {} or metadata is None


class TestParseDateString:
    """Test date string parsing."""

    def test_parse_date_string_iso(self) -> None:
        """Test parsing ISO format date."""
        date = parse_date_string("2020-01-15")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 15

    def test_parse_date_string_slash(self) -> None:
        """Test parsing slash-separated date."""
        date = parse_date_string("2020/01/15")
        assert date is not None
        assert date.year == 2020
        assert date.month == 1
        assert date.day == 15

    def test_parse_date_string_with_time(self) -> None:
        """Test parsing date with time."""
        date = parse_date_string("2020-01-15 10:30:00")
        assert date is not None
        assert date.year == 2020
        assert date.hour == 10
        assert date.minute == 30

    def test_parse_date_string_invalid(self) -> None:
        """Test parsing invalid date string."""
        date = parse_date_string("not a date")
        assert date is None

    def test_parse_date_string_empty(self) -> None:
        """Test parsing empty string."""
        date = parse_date_string("")
        assert date is None


class TestCountWords:
    """Test word counting."""

    def test_count_words_simple(self) -> None:
        """Test counting words in simple text."""
        text = "Hello world this is a test"
        assert count_words(text) == 6

    def test_count_words_multiple_spaces(self) -> None:
        """Test counting words with multiple spaces."""
        text = "Hello    world   test"
        assert count_words(text) == 3

    def test_count_words_newlines(self) -> None:
        """Test counting words with newlines."""
        text = "Hello\nworld\n\ntest"
        assert count_words(text) == 3

    def test_count_words_empty(self) -> None:
        """Test counting words in empty string."""
        assert count_words("") == 0

    def test_count_words_whitespace_only(self) -> None:
        """Test counting words in whitespace-only string."""
        assert count_words("   \n  \t  ") == 0


class TestExtractDocxProperties:
    """Test DOCX properties extraction."""

    def test_extract_docx_properties_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting properties from nonexistent DOCX returns empty dict."""
        from bloginator.extraction.metadata import extract_docx_properties

        nonexistent = tmp_path / "nonexistent.docx"
        result = extract_docx_properties(nonexistent)
        assert result == {}

    def test_extract_docx_properties_invalid_file(self, tmp_path: Path) -> None:
        """Test extracting properties from invalid DOCX returns empty dict."""
        from bloginator.extraction.metadata import extract_docx_properties

        invalid_file = tmp_path / "invalid.docx"
        invalid_file.write_text("not a docx file")
        result = extract_docx_properties(invalid_file)
        assert result == {}
