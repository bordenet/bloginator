"""Document content extractors for various file formats."""

import re
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


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
    elif suffix in [".docx", ".doc"]:
        return extract_text_from_docx(file_path)
    elif suffix in [".md", ".markdown"]:
        return extract_text_from_markdown(file_path)
    elif suffix in [".txt", ".text"]:
        return extract_text_from_txt(file_path)
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
