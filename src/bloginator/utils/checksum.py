"""Checksum utilities for incremental indexing.

Provides functions to calculate and verify content checksums for detecting
changes in documents.
"""

import hashlib


def calculate_content_checksum(content: str) -> str:
    """Calculate SHA256 checksum of text content.

    Args:
        content: Text content to checksum

    Returns:
        Hex-encoded SHA256 checksum

    Example:
        >>> checksum = calculate_content_checksum("Hello, world!")
        >>> len(checksum)
        64
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def content_has_changed(content: str, previous_checksum: str | None) -> bool:
    """Check if content has changed compared to previous checksum.

    Args:
        content: Current content
        previous_checksum: Previous checksum (None if first time)

    Returns:
        True if content has changed or no previous checksum exists

    Example:
        >>> content_has_changed("new content", None)
        True
        >>> checksum = calculate_content_checksum("test")
        >>> content_has_changed("test", checksum)
        False
        >>> content_has_changed("changed", checksum)
        True
    """
    if previous_checksum is None:
        return True

    current_checksum = calculate_content_checksum(content)
    return current_checksum != previous_checksum
