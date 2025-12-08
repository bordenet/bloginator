"""Extended document extractors for additional file formats.

This module re-exports all extended extractors for backwards compatibility.
The actual implementations are in separate modules by file type category:

- _email_extractors: .eml, .msg
- _office_extractors: .pptx, .ppt, .xlsx, .odt
- _markup_extractors: .xml, .html, .rtf
- _image_extractors: .png, .jpg, .jpeg, .webp (OCR)
"""

# Email extractors
from bloginator.extraction._email_extractors import extract_text_from_eml, extract_text_from_msg

# Image extractors
from bloginator.extraction._image_extractors import MIN_IMAGE_SIZE_FOR_OCR, extract_text_from_image

# Markup extractors
from bloginator.extraction._markup_extractors import (
    extract_text_from_html,
    extract_text_from_rtf,
    extract_text_from_xml,
)

# Office extractors
from bloginator.extraction._office_extractors import (
    extract_text_from_odt,
    extract_text_from_ppt,
    extract_text_from_pptx,
    extract_text_from_xlsx,
)


__all__ = [
    # Email
    "extract_text_from_eml",
    "extract_text_from_msg",
    # Office
    "extract_text_from_pptx",
    "extract_text_from_ppt",
    "extract_text_from_xlsx",
    "extract_text_from_odt",
    # Markup
    "extract_text_from_xml",
    "extract_text_from_html",
    "extract_text_from_rtf",
    # Image
    "extract_text_from_image",
    "MIN_IMAGE_SIZE_FOR_OCR",
]
