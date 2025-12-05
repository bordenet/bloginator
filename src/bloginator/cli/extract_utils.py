"""Shared utilities for document extraction."""

import json
import time
from datetime import datetime
from pathlib import Path


def load_existing_extractions(output_dir: Path) -> dict[str, tuple[str, datetime]]:
    """Load existing extractions from output directory.

    Scans all *.json metadata files and builds a mapping of:
        source_path → (doc_id, modified_date)

    This allows us to skip files that have already been extracted
    and haven't changed since extraction.

    Args:
        output_dir: Directory containing extracted *.json metadata files

    Returns:
        Dictionary mapping source file paths to (doc_id, modified_date) tuples
    """
    existing: dict[str, tuple[str, datetime]] = {}

    if not output_dir.exists():
        return existing

    # Scan all .json metadata files
    for json_file in output_dir.glob("*.json"):
        try:
            with json_file.open(encoding="utf-8") as f:
                metadata = json.load(f)

            source_path = metadata.get("source_path")
            doc_id = metadata.get("id")
            modified_date_str = metadata.get("modified_date")

            if source_path and doc_id and modified_date_str:
                # Parse the modified date
                modified_date = datetime.fromisoformat(modified_date_str.replace("Z", "+00:00"))
                existing[str(source_path)] = (doc_id, modified_date)
        except (json.JSONDecodeError, ValueError, KeyError):
            # Skip invalid metadata files
            continue

    return existing


def should_skip_file(
    file_path: Path, existing_docs: dict[str, tuple[str, datetime]], force: bool = False
) -> tuple[bool, str | None]:
    """Determine if a file should be skipped during extraction.

    Args:
        file_path: Path to the file being considered
        existing_docs: Dictionary from load_existing_extractions()
        force: If True, never skip (re-extract everything)

    Returns:
        Tuple of (should_skip, reason_or_doc_id)
        - If should_skip is True, reason_or_doc_id contains the doc_id to reuse
        - If should_skip is False, reason_or_doc_id is None
    """
    # Skip temp files (Office/Word temp files starting with ~$)
    if file_path.name.startswith("~$"):
        return True, None

    # Never skip if --force is enabled
    if force:
        return False, None

    # Check if file was already extracted
    source_path_str = str(file_path.absolute())
    if source_path_str not in existing_docs:
        return False, None

    doc_id, extracted_mtime = existing_docs[source_path_str]

    # Get current file modification time
    try:
        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

        # Skip if file hasn't been modified since extraction
        # Use a small tolerance (1 second) to handle filesystem timestamp precision
        if current_mtime <= extracted_mtime:
            return True, doc_id
    except (OSError, ValueError):
        # If we can't stat the file, don't skip it
        return False, None

    # File was modified after extraction, needs re-extraction
    return False, None


def get_supported_extensions() -> set[str]:
    """Get set of supported file extensions.

    Returns:
        Set of supported extensions including the dot (e.g., {'.pdf', '.docx'})
    """
    return {
        # Document formats
        ".pdf",
        ".docx",
        ".doc",
        ".md",
        ".markdown",
        ".txt",
        ".text",
        # Rich text formats
        ".rtf",
        ".odt",
        ".html",
        ".htm",
        # PowerPoint
        ".pptx",
        ".ppt",
        # Spreadsheets
        ".xlsx",
        # Email
        ".eml",
        ".msg",
        # XML
        ".xml",
        # Images (OCR)
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }


def is_temp_file(filename: str) -> bool:
    """Check if a filename represents a temporary file.

    Args:
        filename: Name of the file to check

    Returns:
        True if this is a temporary file that should be skipped
    """
    return filename.startswith("~$")


def wait_for_file_availability(
    file_path: Path, timeout_seconds: float = 10.0, poll_interval: float = 0.2
) -> bool:
    """Wait for a file to become available with non-zero size.

    This is critical for OneDrive files which may appear in directory listings
    but aren't locally available until accessed. OneDrive downloads files on-demand.

    Args:
        file_path: Path to the file to check
        timeout_seconds: Maximum time to wait (default: 10 seconds)
        poll_interval: Time between polls (default: 200ms)

    Returns:
        True if file is available with size > 0, False if timeout reached

    Raises:
        FileNotFoundError: If file doesn't exist at all
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    start_time = time.time()
    elapsed = 0.0

    while elapsed < timeout_seconds:
        try:
            file_size = file_path.stat().st_size

            # File is available if size > 0
            if file_size > 0:
                return True

            # File exists but is 0 bytes - OneDrive placeholder
            # Trigger download by attempting to open it
            try:
                with file_path.open("rb") as f:
                    # Read first byte to trigger download
                    f.read(1)
            except Exception:
                # If open fails, continue polling
                pass

            # Wait before next poll
            time.sleep(poll_interval)
            elapsed = time.time() - start_time

        except (OSError, PermissionError):
            # File stat failed, wait and retry
            time.sleep(poll_interval)
            elapsed = time.time() - start_time

    # Timeout reached - check final state
    try:
        return file_path.stat().st_size > 0
    except (OSError, PermissionError):
        return False
