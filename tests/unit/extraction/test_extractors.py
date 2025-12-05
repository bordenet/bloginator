"""Tests for document extractors."""

from pathlib import Path

import pytest

from bloginator.extraction.extractors import (
    _extract_confluence_export,
    _html_to_text,
    extract_section_headings,
    extract_text_from_doc,
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


class TestExtractTextFromDoc:
    """Test legacy .doc file extraction."""

    def test_extract_plain_text_doc(self, tmp_path: Path) -> None:
        """Test extracting from .doc file that is actually plain text."""
        doc_file = tmp_path / "test.doc"
        doc_file.write_text("This is plain text content\nwith multiple lines.")

        text = extract_text_from_doc(doc_file)

        assert "plain text content" in text
        assert "multiple lines" in text

    def test_extract_confluence_export_doc(self, tmp_path: Path) -> None:
        """Test extracting from Confluence MIME-encoded .doc export."""
        doc_file = tmp_path / "confluence.doc"
        # Simulate Confluence export format
        content = """Date: Mon, 21 Aug 2023 16:21:38 +0000 (UTC)
Subject: Exported From Confluence
MIME-Version: 1.0
Content-Type: multipart/related;
    boundary="----=_Part_10_1050962448.1692634898487"

------=_Part_10_1050962448.1692634898487
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable
Content-Location: file:///C:/exported.html

<html><body><h1>Test Document</h1><p>This is the content.</p></body></html>
------=_Part_10_1050962448.1692634898487--
"""
        doc_file.write_text(content)

        text = extract_text_from_doc(doc_file)

        assert "Test Document" in text
        assert "This is the content" in text

    def test_extract_doc_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent .doc file raises error."""
        nonexistent = tmp_path / "nonexistent.doc"

        with pytest.raises(FileNotFoundError):
            extract_text_from_doc(nonexistent)


class TestHtmlToText:
    """Test HTML to text conversion."""

    def test_html_to_text_basic(self) -> None:
        """Test basic HTML to text conversion."""
        html = "<html><body><h1>Title</h1><p>Paragraph text.</p></body></html>"

        text = _html_to_text(html)

        assert "Title" in text
        assert "Paragraph text" in text
        assert "<h1>" not in text
        assert "<p>" not in text

    def test_html_to_text_with_lists(self) -> None:
        """Test HTML list conversion."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"

        text = _html_to_text(html)

        assert "Item 1" in text
        assert "Item 2" in text
        assert "•" in text  # Bullet points

    def test_html_to_text_with_entities(self) -> None:
        """Test HTML entity decoding."""
        html = "<p>This &amp; that &lt;test&gt;</p>"

        text = _html_to_text(html)

        assert "This & that <test>" in text

    def test_html_to_text_removes_scripts(self) -> None:
        """Test that script tags are removed."""
        html = "<p>Content</p><script>alert('bad');</script><p>More</p>"

        text = _html_to_text(html)

        assert "Content" in text
        assert "More" in text
        assert "alert" not in text


class TestConfluenceExport:
    """Test Confluence MIME export parsing."""

    def test_extract_confluence_export_quoted_printable(self) -> None:
        """Test extracting quoted-printable encoded content."""
        mime_content = """Subject: Exported From Confluence
Content-Type: multipart/related;
    boundary="----=_Part_10_123"

------=_Part_10_123
Content-Type: text/html; charset=UTF-8
Content-Transfer-Encoding: quoted-printable

<html><body><h1>Test</h1><p>Content here.</p></body></html>
------=_Part_10_123--
"""
        text = _extract_confluence_export(mime_content)

        assert "Test" in text
        assert "Content here" in text
