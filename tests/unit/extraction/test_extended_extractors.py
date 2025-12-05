"""Tests for extended document extractors (PPTX, EML, XML, Images)."""

from pathlib import Path

import pytest

from bloginator.extraction._extended_extractors import (
    extract_text_from_eml,
    extract_text_from_image,
    extract_text_from_pptx,
    extract_text_from_xml,
)


class TestExtractTextFromPptx:
    """Test PowerPoint PPTX extraction."""

    def test_extract_pptx_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent PPTX file raises error."""
        nonexistent = tmp_path / "nonexistent.pptx"

        with pytest.raises(FileNotFoundError):
            extract_text_from_pptx(nonexistent)

    def test_extract_pptx_basic(self, tmp_path: Path) -> None:
        """Test extracting text from a basic PPTX file."""
        from pptx import Presentation
        from pptx.util import Inches

        # Create a simple PPTX
        prs = Presentation()
        slide_layout = prs.slide_layouts[6]  # Blank layout
        slide = prs.slides.add_slide(slide_layout)

        # Add a text box
        left = Inches(1)
        top = Inches(1)
        width = Inches(5)
        height = Inches(1)
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.text = "Hello from PowerPoint"

        pptx_path = tmp_path / "test.pptx"
        prs.save(str(pptx_path))

        text = extract_text_from_pptx(pptx_path)

        assert "Hello from PowerPoint" in text
        assert "Slide 1" in text


class TestExtractTextFromEml:
    """Test Email (.eml) extraction."""

    def test_extract_eml_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent EML file raises error."""
        nonexistent = tmp_path / "nonexistent.eml"

        with pytest.raises(FileNotFoundError):
            extract_text_from_eml(nonexistent)

    def test_extract_eml_plain_text(self, tmp_path: Path) -> None:
        """Test extracting from plain text email."""
        eml_content = """From: sender@example.com
To: recipient@example.com
Subject: Test Email Subject
Date: Thu, 5 Dec 2024 10:00:00 +0000
Content-Type: text/plain; charset="utf-8"

This is the email body content.
It has multiple lines.
"""
        eml_path = tmp_path / "test.eml"
        eml_path.write_text(eml_content)

        text = extract_text_from_eml(eml_path)

        assert "Subject: Test Email Subject" in text
        assert "From: sender@example.com" in text
        assert "This is the email body content" in text

    def test_extract_eml_html(self, tmp_path: Path) -> None:
        """Test extracting from HTML email."""
        eml_content = """From: sender@example.com
To: recipient@example.com
Subject: HTML Email
Date: Thu, 5 Dec 2024 10:00:00 +0000
Content-Type: text/html; charset="utf-8"

<html><body><h1>Hello</h1><p>This is HTML content.</p></body></html>
"""
        eml_path = tmp_path / "test.eml"
        eml_path.write_text(eml_content)

        text = extract_text_from_eml(eml_path)

        assert "Hello" in text
        assert "HTML content" in text
        assert "<html>" not in text  # HTML should be stripped


class TestExtractTextFromXml:
    """Test XML extraction."""

    def test_extract_xml_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent XML file raises error."""
        nonexistent = tmp_path / "nonexistent.xml"

        with pytest.raises(FileNotFoundError):
            extract_text_from_xml(nonexistent)

    def test_extract_xml_basic(self, tmp_path: Path) -> None:
        """Test extracting text from basic XML."""
        xml_content = """<?xml version="1.0"?>
<document>
    <title>Test Document</title>
    <content>This is the main content.</content>
    <section>
        <paragraph>Nested paragraph text.</paragraph>
    </section>
</document>
"""
        xml_path = tmp_path / "test.xml"
        xml_path.write_text(xml_content)

        text = extract_text_from_xml(xml_path)

        assert "Test Document" in text
        assert "This is the main content" in text
        assert "Nested paragraph text" in text

    def test_extract_xml_invalid(self, tmp_path: Path) -> None:
        """Test extracting from invalid XML raises error."""
        xml_path = tmp_path / "invalid.xml"
        xml_path.write_text("This is not valid XML <unclosed>")

        with pytest.raises(ValueError, match="Failed to parse XML"):
            extract_text_from_xml(xml_path)


class TestExtractTextFromImage:
    """Test image OCR extraction."""

    def test_extract_image_nonexistent(self, tmp_path: Path) -> None:
        """Test extracting from nonexistent image file raises error."""
        nonexistent = tmp_path / "nonexistent.png"

        with pytest.raises(FileNotFoundError):
            extract_text_from_image(nonexistent)

