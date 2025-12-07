"""Cloud file detection for OneDrive Files-On-Demand.

This module handles detection of cloud-only placeholder files on macOS.

OneDrive Files-On-Demand on macOS creates placeholder files that appear in
Finder but aren't actually downloaded. These files:
- Have st_size > 0 (reported size from cloud)
- Have st_blocks == 0 (no local disk blocks allocated)
- Block indefinitely when read with Python's open()

Detection uses the st_blocks == 0 heuristic which is reliable on macOS.

IMPORTANT: OneDrive Personal does NOT support programmatic hydration.
Microsoft only exposes the `/pin` CLI for OneDrive for Business (Intune).
For Personal OneDrive, users must manually right-click in Finder and select
"Always Keep on This Device". The attempt_hydration() function is provided
for completeness but will return False for OneDrive Personal files.
See: https://learn.microsoft.com/en-us/sharepoint/files-on-demand-mac
"""

from __future__ import annotations

import contextlib
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable


class CloudFileStatus:
    """Status of a cloud file check."""

    LOCAL = "local"  # File is fully downloaded locally
    CLOUD_ONLY = "cloud_only"  # File is a cloud placeholder
    UNKNOWN = "unknown"  # Could not determine status


def is_cloud_only_file(file_path: Path) -> bool:
    """Detect if a file is a cloud-only placeholder (not downloaded locally).

    Uses the st_blocks == 0 heuristic which works reliably on macOS for
    OneDrive, iCloud, and other File Provider-based cloud storage.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file is cloud-only (not downloaded), False if local
    """
    try:
        stat_info = file_path.stat()
        # Cloud-only files have size > 0 but blocks == 0
        # Local files have blocks > 0 proportional to their size
        return stat_info.st_size > 0 and stat_info.st_blocks == 0
    except (OSError, AttributeError):
        # If stat fails or st_blocks not available, assume local
        return False


def get_cloud_file_status(file_path: Path) -> str:
    """Get detailed status of a file's cloud/local state.

    Args:
        file_path: Path to check

    Returns:
        One of CloudFileStatus constants
    """
    try:
        stat_info = file_path.stat()

        if stat_info.st_blocks > 0:
            return CloudFileStatus.LOCAL
        elif stat_info.st_size > 0 and stat_info.st_blocks == 0:
            return CloudFileStatus.CLOUD_ONLY
        else:
            return CloudFileStatus.UNKNOWN
    except (OSError, AttributeError):
        return CloudFileStatus.UNKNOWN


def attempt_hydration(
    file_path: Path,
    timeout_seconds: float = 30.0,
    poll_interval: float = 1.0,
) -> bool:
    """Attempt to trigger download of a cloud-only file.

    Tries multiple macOS mechanisms to trigger OneDrive/iCloud hydration:
    1. Quick Look preview (qlmanage) - often triggers download
    2. Spotlight metadata (mdls) - can trigger download
    3. Finder 'reveal' via AppleScript - forces Finder to access the file
    4. Open command with text edit for txt files

    Args:
        file_path: Path to the cloud-only file
        timeout_seconds: Maximum time to wait for hydration
        poll_interval: Time between status checks

    Returns:
        True if file was hydrated successfully, False otherwise
    """
    if not is_cloud_only_file(file_path):
        return True  # Already local

    start_time = time.time()
    file_str = str(file_path.absolute())

    # Strategy 1: Use Quick Look (qlmanage) to trigger download
    # Quick Look often triggers the File Provider to download content
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        subprocess.run(
            ["qlmanage", "-p", file_str],
            capture_output=True,
            timeout=5.0,
            start_new_session=True,  # Don't block on GUI
        )

    # Check if hydrated
    if not is_cloud_only_file(file_path):
        _cleanup_qlmanage()
        return True

    # Strategy 2: Use Spotlight metadata query
    # mdls sometimes triggers File Provider hydration
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        subprocess.run(
            ["mdls", file_str],
            capture_output=True,
            timeout=5.0,
        )

    if not is_cloud_only_file(file_path):
        _cleanup_qlmanage()
        return True

    # Strategy 3: Use AppleScript to reveal file in Finder
    # This forces Finder to access the file, which triggers File Provider
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        applescript = f"""
        tell application "Finder"
            set theFile to POSIX file "{file_str}" as alias
            reveal theFile
        end tell
        """
        subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            timeout=10.0,
        )

    # Strategy 4: Use 'open' command to open file briefly
    # This definitely triggers download but opens an app
    # Open with default app in background, then close
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        subprocess.run(
            ["open", "-g", file_str],  # -g opens in background
            capture_output=True,
            timeout=10.0,
        )

    # Poll for hydration with remaining timeout
    elapsed = time.time() - start_time
    while elapsed < timeout_seconds:
        if not is_cloud_only_file(file_path):
            _cleanup_qlmanage()
            return True

        time.sleep(poll_interval)
        elapsed = time.time() - start_time

    _cleanup_qlmanage()
    return False


def _cleanup_qlmanage() -> None:
    """Clean up any lingering Quick Look processes."""
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        subprocess.run(
            ["pkill", "-f", "qlmanage"],
            capture_output=True,
            timeout=2.0,
        )


def scan_for_cloud_only_files(directory: Path, extensions: set[str] | None = None) -> list[Path]:
    """Scan a directory for cloud-only placeholder files.

    Args:
        directory: Directory to scan recursively
        extensions: Optional set of extensions to check (e.g., {'.pdf', '.docx'})
                   If None, checks all files.

    Returns:
        List of paths that are cloud-only placeholders
    """
    cloud_only: list[Path] = []

    for path in directory.rglob("*"):
        if not path.is_file():
            continue

        if extensions and path.suffix.lower() not in extensions:
            continue

        if is_cloud_only_file(path):
            cloud_only.append(path)

    return cloud_only


def batch_hydrate(
    file_paths: list[Path],
    timeout_per_file: float = 15.0,
    progress_callback: Callable[[Path, bool, int, int], None] | None = None,
) -> dict[Path, bool]:
    """Attempt to hydrate multiple cloud-only files.

    Args:
        file_paths: List of file paths to hydrate
        timeout_per_file: Timeout in seconds for each file
        progress_callback: Optional callback(path, success, index, total)

    Returns:
        Dictionary mapping paths to success status
    """
    results: dict[Path, bool] = {}
    total = len(file_paths)

    for i, path in enumerate(file_paths):
        success = attempt_hydration(path, timeout_seconds=timeout_per_file)
        results[path] = success

        if progress_callback:
            progress_callback(path, success, i + 1, total)

    return results


def get_cloud_file_info(file_path: Path) -> dict:
    """Get detailed information about a file's cloud/local state.

    Args:
        file_path: Path to check

    Returns:
        Dictionary with file info including cloud status
    """
    try:
        stat_info = file_path.stat()
        return {
            "path": str(file_path),
            "exists": True,
            "size": stat_info.st_size,
            "blocks": stat_info.st_blocks,
            "is_cloud_only": stat_info.st_blocks == 0 and stat_info.st_size > 0,
            "status": get_cloud_file_status(file_path),
        }
    except OSError as e:
        return {
            "path": str(file_path),
            "exists": False,
            "error": str(e),
            "status": CloudFileStatus.UNKNOWN,
        }
