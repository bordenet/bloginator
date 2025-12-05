"""Extended document extractors for additional file formats.

Handles extraction from:
- PowerPoint (.ppt, .pptx)
- Email (.eml)
- XML (.xml)
- Images (.png, .jpg, .jpeg, .webp) - via OCR when pytesseract is available
"""

import email
from email import policy
from pathlib import Path
from xml.etree import ElementTree


def extract_text_from_pptx(pptx_path: Path) -> str:
    """Extract text content from PowerPoint PPTX file.

    Uses python-pptx to extract text from slides, including:
    - Slide titles
    - Text boxes
    - Notes

    Args:
        pptx_path: Path to PPTX file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If PPTX file does not exist
        ValueError: If file cannot be opened as PPTX
    """
    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

    try:
        from pptx import Presentation
    except ImportError as e:
        raise ValueError("python-pptx not installed") from e

    try:
        prs = Presentation(str(pptx_path))
        text_parts = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_texts = [f"--- Slide {slide_num} ---"]

            # Extract text from shapes (text boxes, titles, etc.)
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_texts.append(shape.text.strip())

            # Extract notes if present
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    slide_texts.append(f"[Notes: {notes}]")

            if len(slide_texts) > 1:  # More than just the slide header
                text_parts.append("\n".join(slide_texts))

        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Failed to extract text from PPTX: {e}") from e


def extract_text_from_ppt(ppt_path: Path) -> str:
    """Extract text from legacy .ppt file via LibreOffice conversion.

    Args:
        ppt_path: Path to legacy .ppt file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If .ppt file does not exist
        ValueError: If conversion fails
    """
    if not ppt_path.exists():
        raise FileNotFoundError(f".ppt file not found: {ppt_path}")

    # Import the LibreOffice helper from doc extractors
    from bloginator.extraction._doc_extractors import extract_doc_with_libreoffice

    try:
        return extract_doc_with_libreoffice(ppt_path)
    except Exception as e:
        raise ValueError(f"Failed to extract text from .ppt: {e}") from e


def extract_text_from_eml(eml_path: Path) -> str:
    """Extract text content from email (.eml) file.

    Parses the email and extracts:
    - Subject
    - From/To headers
    - Plain text body (or stripped HTML)

    Args:
        eml_path: Path to .eml file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If .eml file does not exist
        ValueError: If file cannot be parsed as email
    """
    if not eml_path.exists():
        raise FileNotFoundError(f"Email file not found: {eml_path}")

    try:
        with eml_path.open("rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        text_parts = []

        # Extract headers
        subject = msg.get("Subject", "")
        from_addr = msg.get("From", "")
        to_addr = msg.get("To", "")
        date = msg.get("Date", "")

        if subject:
            text_parts.append(f"Subject: {subject}")
        if from_addr:
            text_parts.append(f"From: {from_addr}")
        if to_addr:
            text_parts.append(f"To: {to_addr}")
        if date:
            text_parts.append(f"Date: {date}")

        text_parts.append("")  # Blank line before body

        # Extract body
        body = msg.get_body(preferencelist=("plain", "html"))
        if body:
            content = body.get_content()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")

            # If HTML, do basic stripping
            if body.get_content_type() == "text/html":
                from bloginator.extraction._doc_extractors import html_to_text

                content = html_to_text(content)

            text_parts.append(content)

        return "\n".join(text_parts).strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from email: {e}") from e


def extract_text_from_xml(xml_path: Path) -> str:
    """Extract text content from XML file.

    Recursively extracts all text content from XML elements.

    Args:
        xml_path: Path to XML file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If XML file does not exist
        ValueError: If file cannot be parsed as XML
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
    except ElementTree.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}") from e
    except Exception as e:
        raise ValueError(f"Failed to extract text from XML: {e}") from e


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image using OCR.

    Uses pytesseract for OCR when available.
    Supports: .png, .jpg, .jpeg, .webp

    Args:
        image_path: Path to image file

    Returns:
        Extracted text content (empty string if OCR unavailable)

    Raises:
        FileNotFoundError: If image file does not exist
        ValueError: If OCR fails
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        # OCR not available - return empty with warning
        return f"[OCR not available for {image_path.name}]"

    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        # Tesseract not installed
        return f"[Tesseract OCR not installed - cannot extract text from {image_path.name}]"
    except Exception as e:
        raise ValueError(f"Failed to extract text from image: {e}") from e

