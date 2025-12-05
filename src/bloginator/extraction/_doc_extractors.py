"""Legacy .doc file extraction helpers.

This module handles extraction of text from legacy Microsoft Word .doc files,
including MIME-encoded Confluence exports and real MS Word binary documents.
"""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def extract_confluence_export(mime_content: str) -> str:
    """Extract text from Confluence MIME-encoded export.

    Confluence exports pages as .doc files that are actually MIME-encoded
    HTML with quoted-printable encoding.

    Args:
        mime_content: Raw MIME content

    Returns:
        Extracted plain text
    """
    import quopri

    # Find the HTML content part
    html_content = ""

    # Look for quoted-printable HTML section
    parts = mime_content.split("------=_Part_")
    for part in parts:
        if "text/html" in part and "quoted-printable" in part.lower():
            # Find where the HTML content starts (after headers)
            lines = part.split("\n")
            content_start = 0
            for i, line in enumerate(lines):
                if line.strip() == "":
                    content_start = i + 1
                    break

            # Decode quoted-printable content
            encoded_content = "\n".join(lines[content_start:])
            try:
                html_bytes = quopri.decodestring(encoded_content.encode("utf-8"))
                html_content = html_bytes.decode("utf-8", errors="replace")
            except Exception:
                html_content = encoded_content
            break

    if not html_content:
        # Fallback: just strip everything that looks like email headers
        html_content = mime_content

    # Parse HTML to extract text
    return html_to_text(html_content)


def html_to_text(html_content: str) -> str:
    """Convert HTML to plain text.

    Args:
        html_content: HTML string

    Returns:
        Plain text with HTML tags removed
    """
    import html

    # Remove script and style elements
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)

    # Replace common block elements with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<p[^>]*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</p>", "", text, flags=re.I)
    text = re.sub(r"<div[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"</div>", "", text, flags=re.I)
    text = re.sub(r"<h[1-6][^>]*>", "\n\n", text, flags=re.I)
    text = re.sub(r"</h[1-6]>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "\n• ", text, flags=re.I)
    text = re.sub(r"</li>", "", text, flags=re.I)
    text = re.sub(r"<tr[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<td[^>]*>", " | ", text, flags=re.I)

    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Clean up whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


def extract_real_doc_file(doc_path: Path) -> str:
    """Extract text from a real MS Word binary document.

    Args:
        doc_path: Path to MS Word .doc file

    Returns:
        Extracted text content

    Raises:
        ValueError: If conversion fails
    """
    # Try LibreOffice (soffice) first - most reliable
    soffice_path = shutil.which("soffice")
    if soffice_path:
        try:
            return extract_doc_with_libreoffice(doc_path)
        except Exception:
            pass  # Fall through to try other methods

    # Try textract if available
    try:
        import textract

        result = textract.process(str(doc_path)).decode("utf-8")
        return str(result)
    except ImportError:
        pass
    except Exception as e:
        raise ValueError(f"textract failed to extract .doc: {e}") from e

    raise ValueError(
        f"Cannot extract binary .doc file: {doc_path}. "
        "Install LibreOffice (brew install --cask libreoffice) or textract."
    )


def extract_doc_with_libreoffice(doc_path: Path) -> str:
    """Convert .doc to text using LibreOffice headless mode.

    Args:
        doc_path: Path to .doc file

    Returns:
        Extracted text content

    Raises:
        ValueError: If conversion fails
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Convert to text using LibreOffice
        result = subprocess.run(
            [
                "soffice",
                "--headless",
                "--convert-to",
                "txt:Text",
                "--outdir",
                tmpdir,
                str(doc_path.absolute()),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise ValueError(f"LibreOffice conversion failed: {result.stderr}")

        # Find the output file
        txt_files = list(Path(tmpdir).glob("*.txt"))
        if not txt_files:
            raise ValueError("LibreOffice produced no output file")

        # Read the converted text
        text = txt_files[0].read_text(encoding="utf-8", errors="replace")
        return text
