"""Document extraction module.

This module handles extraction of text content from various document formats:
- PDF files
- Microsoft Word (.docx)
- Markdown (.md)
- Plain text (.txt)
- ZIP archives (recursive extraction)
"""

from bloginator.extraction.chunking import (
    chunk_text_by_paragraphs,
    chunk_text_by_sentences,
    chunk_text_fixed_size,
)
from bloginator.extraction.extractors import (
    extract_section_headings,
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_markdown,
    extract_text_from_pdf,
    extract_text_from_txt,
)
from bloginator.extraction.metadata import (
    count_words,
    extract_docx_properties,
    extract_file_metadata,
    extract_yaml_frontmatter,
    parse_date_string,
)


__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_text_from_markdown",
    "extract_text_from_txt",
    "extract_text_from_file",
    "extract_section_headings",
    "extract_file_metadata",
    "extract_yaml_frontmatter",
    "extract_docx_properties",
    "parse_date_string",
    "count_words",
    "chunk_text_fixed_size",
    "chunk_text_by_paragraphs",
    "chunk_text_by_sentences",
]
