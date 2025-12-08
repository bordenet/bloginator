"""Markup extractors for XML, HTML, and RTF files."""

import re
import shutil
import subprocess
from pathlib import Path
from xml.etree import ElementTree


def extract_text_from_xml(xml_path: Path) -> str:
    """Extract text content from XML file.

    Recursively extracts all text content from XML elements.
    Returns empty string for malformed XML (graceful degradation).

    Args:
        xml_path: Path to XML file

    Returns:
        Extracted text content (empty if parsing fails)

    Raises:
        FileNotFoundError: If XML file does not exist
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    try:
        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        # Recursively extract all text
        def get_text(element: ElementTree.Element) -> str:
            texts = []
            if element.text and element.text.strip():
                texts.append(element.text.strip())
            for child in element:
                texts.append(get_text(child))
                if child.tail and child.tail.strip():
                    texts.append(child.tail.strip())
            return " ".join(texts)

        return get_text(root)
    except ElementTree.ParseError:
        # Malformed XML - return empty, will be skipped as empty_content
        return ""
    except Exception:
        # Other errors (encoding, etc.) - graceful degradation
        return ""


def extract_text_from_html(html_path: Path) -> str:
    """Extract text content from HTML file.

    Uses BeautifulSoup to parse HTML and extract readable text.

    Args:
        html_path: Path to HTML file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If HTML file does not exist
        ValueError: If file cannot be parsed as HTML
    """
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")

    try:
        from bs4 import BeautifulSoup

        content = html_path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "meta", "link"]):
            element.decompose()

        # Get text
        text: str = soup.get_text(separator="\n", strip=True)
        return text
    except ImportError:
        # Fall back to simple regex stripping
        from bloginator.extraction._doc_extractors import html_to_text

        content = html_path.read_text(encoding="utf-8", errors="replace")
        return html_to_text(content)
    except Exception as e:
        raise ValueError(f"Failed to extract text from HTML: {e}") from e


def extract_text_from_rtf(rtf_path: Path) -> str:
    """Extract text content from Rich Text Format (.rtf) file.

    Tries unrtf CLI first (fast), then falls back to striprtf library.

    Args:
        rtf_path: Path to RTF file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If RTF file does not exist
        ValueError: If extraction fails
    """
    if not rtf_path.exists():
        raise FileNotFoundError(f"RTF file not found: {rtf_path}")

    # Try unrtf CLI first (installed via brew install textract)
    unrtf_path = shutil.which("unrtf")
    if unrtf_path:
        try:
            result = subprocess.run(
                ["unrtf", "--text", str(rtf_path.absolute())],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                # unrtf outputs with some header lines, strip them
                lines = result.stdout.split("\n")
                # Skip header lines that start with ###
                content_lines = [ln for ln in lines if not ln.startswith("###")]
                return "\n".join(content_lines).strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass  # Fall through to other methods

    # Try striprtf library
    try:
        from striprtf.striprtf import rtf_to_text

        raw_content = rtf_path.read_bytes()
        text: str = rtf_to_text(raw_content.decode("utf-8", errors="replace"))
        return text.strip()
    except ImportError:
        pass

    # Last resort: basic regex stripping
    text_content = rtf_path.read_text(encoding="utf-8", errors="replace")

    # Remove RTF control words
    text = re.sub(r"\\[a-z]+\d*\s?", " ", text_content)
    # Remove braces
    text = re.sub(r"[{}]", "", text)
    # Clean up whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()
