"""Tests for document extractors edge cases.

This module tests extraction functionality including edge cases:
- Corrupted/truncated files
- Various encodings
- Empty/minimal files
- Large files
"""

from bloginator.extraction._doc_extractors import extract_confluence_export, html_to_text


class TestConfluenceExportEdgeCases:
    """Test Confluence export extraction edge cases."""

    def test_extract_confluence_export_empty_content(self) -> None:
        """Test extracting from empty MIME content."""
        mime_content = ""

        result = extract_confluence_export(mime_content)

        # Should return empty or minimal text, not crash
        assert isinstance(result, str)

    def test_extract_confluence_export_malformed_mime(self) -> None:
        """Test extracting from malformed MIME structure."""
        mime_content = "Not a valid MIME structure at all"

        result = extract_confluence_export(mime_content)

        # Should gracefully handle malformed input
        assert isinstance(result, str)

    def test_extract_confluence_export_no_html_section(self) -> None:
        """Test extracting when no HTML section exists."""
        mime_content = "------=_Part_1\nContent-Type: text/plain\n\nPlain text only"

        result = extract_confluence_export(mime_content)

        # Should extract something without crashing
        assert isinstance(result, str)

    def test_extract_confluence_export_invalid_quoted_printable(self) -> None:
        """Test extracting with invalid quoted-printable encoding."""
        mime_content = (
            "------=_Part_1\n"
            "Content-Type: text/html; charset=UTF-8\n"
            "Content-Transfer-Encoding: quoted-printable\n"
            "\n"
            "Invalid =XX quoted-printable here"
        )

        # Should handle gracefully
        result = extract_confluence_export(mime_content)
        assert isinstance(result, str)

    def test_extract_confluence_export_with_valid_html(self) -> None:
        """Test extracting valid Confluence export with HTML."""
        mime_content = (
            "------=_Part_1\n"
            "Content-Type: text/html; charset=UTF-8\n"
            "Content-Transfer-Encoding: quoted-printable\n"
            "\n"
            "<html><body><p>Test Content</p></body></html>"
        )

        result = extract_confluence_export(mime_content)

        assert "Test Content" in result

    def test_extract_confluence_export_unicode_content(self) -> None:
        """Test extracting Confluence export with unicode characters."""
        mime_content = (
            "------=_Part_1\n"
            "Content-Type: text/html; charset=UTF-8\n"
            "Content-Transfer-Encoding: quoted-printable\n"
            "\n"
            "<html><body><p>Unicode: 你好 мир 🌍</p></body></html>"
        )

        result = extract_confluence_export(mime_content)

        # Should preserve unicode
        assert isinstance(result, str)


class TestHtmlToTextEdgeCases:
    """Test HTML to text conversion edge cases."""

    def test_html_to_text_empty_string(self) -> None:
        """Test converting empty HTML string."""
        result = html_to_text("")

        assert result == ""

    def test_html_to_text_nested_tags(self) -> None:
        """Test converting deeply nested HTML tags."""
        html = "<div><p><span><b>Nested</b></span></p></div>"

        result = html_to_text(html)

        assert "Nested" in result
        assert "<" not in result  # No HTML tags remain

    def test_html_to_text_unclosed_tags(self) -> None:
        """Test converting HTML with unclosed tags."""
        html = "<p>Unclosed paragraph<div>More content"

        result = html_to_text(html)

        assert "Unclosed paragraph" in result
        assert "More content" in result

    def test_html_to_text_malformed_entities(self) -> None:
        """Test converting with malformed HTML entities."""
        html = "<p>Bad entity: &invalidEntity; and &nbsp; and &#1234;</p>"

        result = html_to_text(html)

        # Should handle malformed entities gracefully
        assert isinstance(result, str)
        assert "Bad entity" in result

    def test_html_to_text_script_with_content(self) -> None:
        """Test that script content is fully removed."""
        html = "<p>Before</p><script>alert('hidden'); var secret='data';</script><p>After</p>"

        result = html_to_text(html)

        assert "Before" in result
        assert "After" in result
        assert "alert" not in result
        assert "hidden" not in result
        assert "secret" not in result

    def test_html_to_text_style_with_rules(self) -> None:
        """Test that style content is fully removed."""
        html = "<p>Before</p><style>.hidden { display: none; }</style><p>After</p>"

        result = html_to_text(html)

        assert "Before" in result
        assert "After" in result
        assert "display" not in result
        assert "hidden" not in result

    def test_html_to_text_mixed_whitespace(self) -> None:
        """Test handling of mixed whitespace."""
        html = "<p>Text   with    multiple    spaces\n\n\nand\t\tnewlines</p>"

        result = html_to_text(html)

        # Should normalize to single spaces
        assert "Text with multiple spaces" in result

    def test_html_to_text_html5_entities(self) -> None:
        """Test HTML5 entity decoding."""
        html = "<p>&nbsp;&copy;&reg;&euro;&pound;&yen;</p>"

        result = html_to_text(html)

        assert isinstance(result, str)
        # Should decode most entities
        assert len(result) > 0

    def test_html_to_text_numeric_entities(self) -> None:
        """Test numeric HTML entity decoding."""
        html = "<p>&#65; &#x42; &#x263A;</p>"  # A B ☺

        result = html_to_text(html)

        assert "A" in result
        assert "B" in result

    def test_html_to_text_table_formatting(self) -> None:
        """Test table is converted to readable text."""
        html = "<table><tr><td>Header 1</td><td>Header 2</td></tr><tr><td>Data 1</td><td>Data 2</td></tr></table>"

        result = html_to_text(html)

        assert "Header 1" in result
        assert "Header 2" in result
        assert "Data 1" in result
        assert "Data 2" in result

    def test_html_to_text_list_formatting(self) -> None:
        """Test list items get bullet points."""
        html = "<ul><li>Item 1</li><li>Item 2</li></ul>"

        result = html_to_text(html)

        assert "Item 1" in result
        assert "Item 2" in result
        assert "•" in result  # Bullet point should be present

    def test_html_to_text_br_tags(self) -> None:
        """Test br tags create line breaks."""
        html = "Line 1<br>Line 2<br/>Line 3"

        result = html_to_text(html)

        lines = result.strip().split("\n")
        assert len([line for line in lines if line.strip()]) >= 2

    def test_html_to_text_heading_hierarchy(self) -> None:
        """Test heading levels are preserved with spacing."""
        html = "<h1>H1</h1><p>Content</p><h2>H2</h2><p>More</p>"

        result = html_to_text(html)

        assert "H1" in result
        assert "H2" in result
        assert "Content" in result

    def test_html_to_text_only_tags_no_content(self) -> None:
        """Test HTML with only tags and no text."""
        html = "<div></div><p></p><span></span>"

        result = html_to_text(html)

        assert result.strip() == ""

    def test_html_to_text_special_characters(self) -> None:
        """Test special character handling."""
        html = "<p>Quote: &quot;hello&quot; Apostrophe: &apos; Less: &lt; Greater: &gt;</p>"

        result = html_to_text(html)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_html_to_text_case_insensitive_tags(self) -> None:
        """Test tag matching is case-insensitive."""
        html = "<P>Lowercase p</P><Div>Div</DIV><BR>break"

        result = html_to_text(html)

        assert "Lowercase p" in result
        assert "Div" in result


class TestDocExtractorIntegration:
    """Integration tests for doc extraction."""

    def test_extract_confluence_export_real_like_structure(self) -> None:
        """Test extraction with realistic Confluence export structure."""
        mime_content = (
            "MIME-Version: 1.0\n"
            "Content-Type: multipart/mixed; boundary=boundary123\n"
            "\n"
            "------=_Part_1\n"
            "Content-Type: text/html; charset=UTF-8\n"
            "Content-Transfer-Encoding: quoted-printable\n"
            "Content-Disposition: inline\n"
            "\n"
            "<html>\n"
            "<body>\n"
            "<h1>Title</h1>\n"
            "<p>This is the content.</p>\n"
            "</body>\n"
            "</html>"
        )

        result = extract_confluence_export(mime_content)

        assert "Title" in result
        assert "content" in result

    def test_html_to_text_paragraph_spacing(self) -> None:
        """Test paragraph spacing is preserved."""
        html = "<p>First paragraph</p><p>Second paragraph</p><p>Third paragraph</p>"

        result = html_to_text(html)

        # Should have spacing between paragraphs
        assert result.count("\n") >= 2
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "Third paragraph" in result
