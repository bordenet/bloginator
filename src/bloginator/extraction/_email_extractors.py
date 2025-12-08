"""Email extractors for .eml and .msg files."""

import email
from email import policy
from pathlib import Path


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


def extract_text_from_msg(msg_path: Path) -> str:
    """Extract text content from Outlook MSG file.

    Uses extract-msg library to parse MSG files.

    Args:
        msg_path: Path to MSG file

    Returns:
        Extracted text content

    Raises:
        FileNotFoundError: If MSG file does not exist
        ValueError: If extraction fails
    """
    if not msg_path.exists():
        raise FileNotFoundError(f"MSG file not found: {msg_path}")

    try:
        import extract_msg
    except ImportError as e:
        raise ValueError("extract-msg not installed") from e

    try:
        msg = extract_msg.Message(str(msg_path))
        text_parts = []

        # Extract headers
        if msg.subject:
            text_parts.append(f"Subject: {msg.subject}")
        if msg.sender:
            text_parts.append(f"From: {msg.sender}")
        if msg.to:
            text_parts.append(f"To: {msg.to}")
        if msg.date:
            text_parts.append(f"Date: {msg.date}")

        text_parts.append("")  # Blank line before body

        # Extract body (prefer plain text)
        if msg.body:
            text_parts.append(msg.body)
        elif msg.htmlBody:
            from bloginator.extraction._doc_extractors import html_to_text

            html_body_raw = msg.htmlBody
            html_body_str: str = (
                html_body_raw.decode("utf-8", errors="replace")
                if isinstance(html_body_raw, bytes)
                else html_body_raw
            )
            text_parts.append(html_to_text(html_body_str))

        msg.close()
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from MSG: {e}") from e
