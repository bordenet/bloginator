"""Cloud file detection for OneDrive/iCloud Files-On-Demand on macOS.

Detects cloud-only placeholder files using the st_blocks == 0 heuristic.
Note: OneDrive Personal does NOT support programmatic hydration; users must
manually select "Always Keep on This Device" in Finder.
"""

from __future__ import annotations

import contextlib
import subprocess
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING


# Default temp directory for hydration copies (uses system temp dir)
_DEFAULT_HYDRATION_DIR = Path(tempfile.gettempdir()) / "bloginator_hydration"

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


def hydrate_via_copy(
    file_path: Path,
    temp_dir: Path | None = None,
    timeout_seconds: float = 120.0,
) -> Path | None:
    """Hydrate a cloud-only file by copying it to a temp directory.

    Copying a file forces the OS to read its contents, which triggers OneDrive
    to download the file. This is a reliable workaround for OneDrive Personal
    where the `/pin` CLI is not available.

    Args:
        file_path: Path to the cloud-only file
        temp_dir: Directory for temp copies (default: /tmp/bloginator_hydration)
        timeout_seconds: Maximum time to wait for copy to complete

    Returns:
        Path to the temp copy if successful, None if copy failed
    """
    import hashlib
    import shutil
    import threading

    if temp_dir is None:
        temp_dir = _DEFAULT_HYDRATION_DIR

    # Create temp directory
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Create unique filename using hash of original path
    # nosec B324 - MD5 used for filename uniqueness, not security
    path_hash = hashlib.md5(str(file_path.absolute()).encode(), usedforsecurity=False).hexdigest()[
        :12
    ]
    temp_file = temp_dir / f"{path_hash}_{file_path.name}"

    # Remove existing temp file if present
    if temp_file.exists():
        temp_file.unlink()

    # Use a thread with timeout for the copy operation
    # This prevents blocking if OneDrive fails to download
    copy_result: dict[str, Path | Exception | None] = {"path": None, "error": None}

    def do_copy() -> None:
        try:
            shutil.copy2(str(file_path), str(temp_file))
            # Verify the copy has actual content
            stat_info = temp_file.stat()
            if stat_info.st_blocks > 0 and stat_info.st_size > 0:
                copy_result["path"] = temp_file
            else:
                copy_result["error"] = ValueError("Copy has no content blocks")
        except Exception as e:
            copy_result["error"] = e

    copy_thread = threading.Thread(target=do_copy)
    copy_thread.start()
    copy_thread.join(timeout=timeout_seconds)

    if copy_thread.is_alive():
        # Copy is still running - OneDrive may be downloading
        # We can't kill shutil.copy, but we can give up and return None
        return None

    if copy_result["path"]:
        return copy_result["path"]

    return None


def cleanup_hydration_temp_dir(temp_dir: Path | None = None) -> int:
    """Clean up the temporary hydration directory.

    Args:
        temp_dir: Directory to clean (default: system temp/bloginator_hydration)

    Returns:
        Number of files removed
    """
    import shutil

    if temp_dir is None:
        temp_dir = _DEFAULT_HYDRATION_DIR

    if not temp_dir.exists():
        return 0

    count = sum(1 for _ in temp_dir.iterdir())
    shutil.rmtree(temp_dir, ignore_errors=True)
    return count
