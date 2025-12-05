"""Document content extractors for various file formats."""

import os
import re
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import fitz  # PyMuPDF

from bloginator.extraction._doc_extractors import (
    extract_confluence_export,
    extract_real_doc_file,
    html_to_text,
)
from bloginator.extraction._extended_extractors import (
    extract_text_from_eml,
    extract_text_from_html,
    extract_text_from_image,
    extract_text_from_msg,
    extract_text_from_odt,
    extract_text_from_ppt,
    extract_text_from_pptx,
    extract_text_from_rtf,
    extract_text_from_xlsx,
    extract_text_from_xml,
)


# Re-export for backward compatibility with tests
_extract_confluence_export = extract_confluence_export
_html_to_text = html_to_text


@contextmanager
def suppress_stderr() -> Generator[None, None, None]:
    """Context manager to suppress stderr output.

    This is useful for suppressing C-level warnings from PyMuPDF
    that clutter the output but are informational, not errors.
    """
    # Save original stderr
    original_stderr = sys.stderr
    original_stderr_fd = os.dup(2)

    try:
        # Redirect stderr to devnull
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        sys.stderr = os.fdopen(devnull, "w")

        yield

    finally:
        # Restore original stderr
        os.dup2(original_stderr_fd, 2)
        sys.stderr = original_stderr
        os.close(original_stderr_fd)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text content from PDF file.

    Uses PyMuPDF (fitz) to extract text from all pages.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If PDF file does not exist
        ValueError: If file cannot be opened as PDF
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        # Suppress MuPDF stderr warnings (syntax errors in PDF content streams)
        # These are informational C-level warnings, not extraction errors
        with suppress_stderr():
            doc = fitz.open(str(pdf_path))
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}") from e


def extract_text_from_docx(docx_path: Path) -> str:
    """Extract text content from DOCX file.

    Uses python-docx to extract text from paragraphs and tables.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If DOCX file does not exist
        ValueError: If file cannot be opened as DOCX
    """
    if not docx_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    try:
        from docx import Document as DocxDocument
    except ImportError as e:
        raise ValueError("python-docx not installed") from e

    try:
        doc = DocxDocument(str(docx_path))
        text_parts = []

        # Extract paragraph text
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Extract table text
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {e}") from e


def extract_text_from_doc(doc_path: Path) -> str:
    """Extract text content from legacy .doc file.

    Handles multiple .doc formats:
    1. MIME-encoded HTML (common from Confluence exports)
    2. Plain text files with .doc extension
    3. Real MS Word binary documents (via LibreOffice)
    4. Fallback to textract if available

    Args:
        doc_path: Path to legacy .doc file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If .doc file does not exist
        ValueError: If file cannot be converted or no converter available
    """
    if not doc_path.exists():
        raise FileNotFoundError(f".doc file not found: {doc_path}")

    try:
        with doc_path.open("rb") as f:
            # Read first few bytes to check file signature
            header = f.read(512)

            # Check for MS Word OLE signature (D0 CF 11 E0 A1 B1 1A E1)
            ole_signature = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

            if header.startswith(ole_signature):
                # This is a real MS Word document - use LibreOffice
                return extract_real_doc_file(doc_path)

            # Check for MIME-encoded Confluence export
            f.seek(0)
            content = f.read()
            text = content.decode("utf-8", errors="replace")

            if "Exported From Confluence" in text or "multipart/related" in text:
                # This is a MIME-encoded Confluence export
                return extract_confluence_export(text)

            # Otherwise, treat as plain text
            # Clean up any obvious non-content
            if text and any(c.isalpha() for c in text[:1000]):
                return text

            return text

    except Exception as e:
        raise ValueError(f"Failed to extract .doc file: {e}") from e


def extract_text_from_markdown(md_path: Path) -> str:
    """Extract text content from Markdown file.

    Reads file and optionally strips YAML frontmatter.

    Args:
        md_path: Path to Markdown file

    Returns:
        Extracted text content (with frontmatter removed)

    Raises:
        FileNotFoundError: If Markdown file does not exist
    """
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    content = md_path.read_text(encoding="utf-8")

    # Remove YAML frontmatter
    frontmatter_pattern = r"^---\s*\n.*?\n---\s*\n"
    content = re.sub(frontmatter_pattern, "", content, flags=re.DOTALL)

    return content.strip()


def extract_text_from_txt(txt_path: Path) -> str:
    """Extract text content from plain text file.

    Args:
        txt_path: Path to text file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If text file does not exist
    """
    if not txt_path.exists():
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    return txt_path.read_text(encoding="utf-8")


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from file based on extension.

    Automatically detects file type and uses appropriate extractor.

    Args:
        file_path: Path to file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file type is not supported
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix == ".docx":
        return extract_text_from_docx(file_path)
    elif suffix == ".doc":
        return extract_text_from_doc(file_path)
    elif suffix in [".md", ".markdown"]:
        return extract_text_from_markdown(file_path)
    elif suffix in [".txt", ".text"]:
        return extract_text_from_txt(file_path)
    elif suffix == ".pptx":
        return extract_text_from_pptx(file_path)
    elif suffix == ".ppt":
        return extract_text_from_ppt(file_path)
    elif suffix == ".eml":
        return extract_text_from_eml(file_path)
    elif suffix == ".msg":
        return extract_text_from_msg(file_path)
    elif suffix == ".xml":
        return extract_text_from_xml(file_path)
    elif suffix in [".html", ".htm"]:
        return extract_text_from_html(file_path)
    elif suffix == ".xlsx":
        return extract_text_from_xlsx(file_path)
    elif suffix == ".odt":
        return extract_text_from_odt(file_path)
    elif suffix == ".rtf":
        return extract_text_from_rtf(file_path)
    elif suffix in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def extract_section_headings(text: str) -> list[tuple[str, int]]:
    """Extract section headings from Markdown text.

    Finds Markdown headings (# Heading, ## Subheading, etc.) and
    their positions in the text.

    Args:
        text: Markdown text content

    Returns:
        List of (heading_text, char_position) tuples
    """
    headings = []
    pattern = r"^(#{1,6})\s+(.+)$"

    for match in re.finditer(pattern, text, re.MULTILINE):
        heading_text = match.group(2).strip()
        char_position = match.start()
        headings.append((heading_text, char_position))

    return headings
