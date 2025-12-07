"""Shared utilities for document extraction."""

import json
from datetime import datetime
from pathlib import Path

from bloginator.utils.cloud_files import (
    CloudFileStatus,
    attempt_hydration,
    get_cloud_file_status,
    hydrate_via_copy,
)


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
    file_path: Path,
    timeout_seconds: float = 30.0,
    attempt_hydration_flag: bool = True,
    use_copy_hydration: bool = True,
) -> tuple[bool, str, Path | None]:
    """Wait for a file to become available, handling cloud-only placeholders.

    This function properly handles OneDrive/iCloud Files-On-Demand on macOS.
    Cloud-only files have st_blocks == 0 even when st_size > 0.

    The function will:
    1. Check if file is already local (st_blocks > 0)
    2. If cloud-only and attempt_hydration_flag is True, try to trigger download
    3. If hydration fails and use_copy_hydration is True, copy to /tmp to force download
    4. Return status, reason, and optional alternate path

    Args:
        file_path: Path to the file to check
        timeout_seconds: Maximum time to wait for hydration (default: 30 seconds)
        attempt_hydration_flag: If True, attempt to trigger cloud download
        use_copy_hydration: If True, copy cloud files to /tmp to force download

    Returns:
        Tuple of (is_available, reason_string, alternate_path)
        - (True, "local", None) - File is available locally
        - (True, "hydrated", None) - File was cloud-only but successfully downloaded
        - (True, "copy_hydrated", Path) - Cloud file copied to temp; use alternate path
        - (False, "cloud_only", None) - File is cloud-only and all hydration failed
        - (False, "not_found", None) - File does not exist

    Raises:
        FileNotFoundError: If file doesn't exist at all
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    # Check current status using st_blocks heuristic
    status = get_cloud_file_status(file_path)

    if status == CloudFileStatus.LOCAL:
        return True, "local", None

    if status == CloudFileStatus.CLOUD_ONLY:
        if not attempt_hydration_flag and not use_copy_hydration:
            return False, "cloud_only", None

        # Try normal hydration first (Quick Look, Spotlight, etc.)
        if attempt_hydration_flag:
            success = attempt_hydration(file_path, timeout_seconds=min(timeout_seconds, 5.0))
            if success:
                return True, "hydrated", None

        # Try copy-based hydration - copying forces OneDrive to download
        if use_copy_hydration:
            temp_copy = hydrate_via_copy(file_path, timeout_seconds=timeout_seconds)
            if temp_copy is not None:
                return True, "copy_hydrated", temp_copy

        return False, "cloud_only", None

    # Unknown status - try to read and see what happens
    try:
        stat_info = file_path.stat()
        if stat_info.st_size > 0 and stat_info.st_blocks > 0:
            return True, "local", None
    except OSError:
        pass

    return False, "unknown", None
