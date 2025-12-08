"""Image extractors using OCR."""

from pathlib import Path


# Minimum file size for image OCR (20KB) - smaller images are likely icons/decorations
MIN_IMAGE_SIZE_FOR_OCR = 20 * 1024


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image using OCR.

    Uses pytesseract for OCR when available.
    Supports: .png, .jpg, .jpeg, .webp

    Skips images smaller than 20KB as they're likely icons or decorative
    elements without meaningful text content.

    Args:
        image_path: Path to image file

    Returns:
        Extracted text content (empty string if too small or OCR unavailable)

    Raises:
        FileNotFoundError: If image file does not exist
        ValueError: If OCR fails
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Skip tiny images - likely icons, bullets, or decorative elements
    file_size = image_path.stat().st_size
    if file_size < MIN_IMAGE_SIZE_FOR_OCR:
        return ""  # Return empty - will be skipped as empty_content

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        # OCR not available - return empty with warning
        return f"[OCR not available for {image_path.name}]"

    try:
        image = Image.open(image_path)
        text: str = pytesseract.image_to_string(image)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        # Tesseract not installed
        return f"[Tesseract OCR not installed - cannot extract text from {image_path.name}]"
    except Exception as e:
        raise ValueError(f"Failed to extract text from image: {e}") from e
