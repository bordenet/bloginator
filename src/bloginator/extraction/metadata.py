"""Metadata extraction utilities for documents."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml


def extract_file_metadata(filepath: Path) -> dict[str, Any]:
    """Extract creation and modification dates from file system metadata.

    Args:
        filepath: Path to file

    Returns:
        Dictionary with created_date, modified_date, and file_size

    Raises:
        FileNotFoundError: If filepath does not exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    stat = filepath.stat()
    return {
        "created_date": datetime.fromtimestamp(stat.st_ctime),
        "modified_date": datetime.fromtimestamp(stat.st_mtime),
        "file_size": stat.st_size,
    }


def extract_yaml_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from Markdown content.

    Looks for YAML frontmatter in the format:
        ---
        title: My Title
        date: 2020-01-15
        tags: [tag1, tag2]
        ---

    Args:
        content: Markdown file content

    Returns:
        Dictionary of frontmatter metadata (empty dict if no frontmatter)
    """
    # Match YAML frontmatter pattern
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}

    frontmatter_str = match.group(1)

    try:
        metadata = yaml.safe_load(frontmatter_str)
        return metadata if isinstance(metadata, dict) else {}
    except yaml.YAMLError:
        return {}


def extract_docx_properties(docx_path: Path) -> dict[str, Any]:
    """Extract document properties from DOCX file.

    Args:
        docx_path: Path to DOCX file

    Returns:
        Dictionary with title, author, created, modified, etc.
    """
    try:
        from docx import Document as DocxDocument
    except ImportError:
        return {}

    try:
        doc = DocxDocument(str(docx_path))
        core_props = doc.core_properties

        metadata: dict[str, Any] = {}

        if core_props.title:
            metadata["title"] = core_props.title
        if core_props.author:
            metadata["author"] = core_props.author
        if core_props.created:
            metadata["created_date"] = core_props.created
        if core_props.modified:
            metadata["modified_date"] = core_props.modified
        if core_props.subject:
            metadata["subject"] = core_props.subject
        if core_props.keywords:
            metadata["keywords"] = core_props.keywords

        return metadata
    except Exception:
        return {}


def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string in various formats.

    Attempts to parse dates in common formats:
    - YYYY-MM-DD
    - YYYY/MM/DD
    - MM-DD-YYYY
    - DD/MM/YYYY
    - ISO 8601

    Args:
        date_str: Date string to parse

    Returns:
        datetime object if successful, None otherwise
    """
    date_formats = [
        "%Y-%m-%d",  # 2020-01-15
        "%Y/%m/%d",  # 2020/01/15
        "%m-%d-%Y",  # 01-15-2020
        "%d/%m/%Y",  # 15/01/2020
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601
        "%Y-%m-%d %H:%M:%S",  # 2020-01-15 10:30:00
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def count_words(text: str) -> int:
    """Count words in text.

    Simple word count by splitting on whitespace and
    filtering empty strings.

    Args:
        text: Text content

    Returns:
        Number of words
    """
    return len([word for word in text.split() if word.strip()])
