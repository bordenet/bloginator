"""Tests for document extractors."""

from pathlib import Path

import pytest

from bloginator.extraction.extractors import (
    extract_section_headings,
    extract_text_from_file,
    extract_text_from_markdown,
    extract_text_from_txt,
)


class TestExtractTextFromTxt:
    """Test plain text extraction."""

    def test_extract_text_from_txt(self, tmp_path: Path) -> None:
        """Test extracting text from txt file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world\nThis is a test.")

        text = extract_text_from_txt(txt_file)

        assert text == "Hello world\nThis is a test."

    def test_extract_text_from_txt_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent file raises error."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            extract_text_from_txt(nonexistent)


class TestExtractTextFromMarkdown:
    """Test Markdown extraction."""

    def test_extract_text_from_markdown_no_frontmatter(self, tmp_path: Path) -> None:
        """Test extracting Markdown without frontmatter."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Heading\n\nContent here.")

        text = extract_text_from_markdown(md_file)

        assert "# Heading" in text
        assert "Content here." in text

    def test_extract_text_from_markdown_with_frontmatter(self, tmp_path: Path) -> None:
        """Test extracting Markdown with YAML frontmatter."""
        md_file = tmp_path / "test.md"
        content = """---
title: Test
date: 2020-01-15
---

# Heading

Content here."""
        md_file.write_text(content)

        text = extract_text_from_markdown(md_file)

        # Frontmatter should be removed
        assert "title: Test" not in text
        assert "date: 2020-01-15" not in text
        # Content should remain
        assert "# Heading" in text
        assert "Content here." in text

    def test_extract_text_from_markdown_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent file raises error."""
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            extract_text_from_markdown(nonexistent)


class TestExtractTextFromFile:
    """Test automatic file type detection."""

    def test_extract_text_from_file_txt(self, tmp_path: Path) -> None:
        """Test extracting from .txt file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test content")

        text = extract_text_from_file(txt_file)

        assert text == "Test content"

    def test_extract_text_from_file_markdown(self, tmp_path: Path) -> None:
        """Test extracting from .md file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Test\n\nContent")

        text = extract_text_from_file(md_file)

        assert "# Test" in text
        assert "Content" in text

    def test_extract_text_from_file_unsupported(self, tmp_path: Path) -> None:
        """Test extracting from unsupported file type raises error."""
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("Content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text_from_file(unsupported)


class TestExtractSectionHeadings:
    """Test section heading extraction."""

    def test_extract_section_headings_single_level(self) -> None:
        """Test extracting single-level headings."""
        text = "# Heading 1\n\nContent\n\n# Heading 2\n\nMore content"

        headings = extract_section_headings(text)

        assert len(headings) == 2
        assert headings[0][0] == "Heading 1"
        assert headings[1][0] == "Heading 2"
        assert headings[0][1] < headings[1][1]  # Position ordering

    def test_extract_section_headings_multiple_levels(self) -> None:
        """Test extracting multi-level headings."""
        text = "# H1\n\n## H2\n\n### H3\n\nContent"

        headings = extract_section_headings(text)

        assert len(headings) == 3
        assert headings[0][0] == "H1"
        assert headings[1][0] == "H2"
        assert headings[2][0] == "H3"

    def test_extract_section_headings_none(self) -> None:
        """Test extracting from text without headings."""
        text = "Just plain text\nwithout any headings."

        headings = extract_section_headings(text)

        assert headings == []

    def test_extract_section_headings_with_formatting(self) -> None:
        """Test extracting headings with inline formatting."""
        text = "# Heading with **bold** and *italic*\n\nContent"

        headings = extract_section_headings(text)

        assert len(headings) == 1
        assert "bold" in headings[0][0]
        assert "italic" in headings[0][0]
