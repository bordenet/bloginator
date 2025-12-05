"""SMB path resolution utilities."""

import platform
import subprocess
from pathlib import Path

from bloginator.cli.error_reporting import ErrorTracker, SkipCategory


def resolve_smb_path(smb_url: str, error_tracker: ErrorTracker) -> Path | None:
    """Resolve SMB URL to a mounted local path.

    Attempts to mount the SMB share if not already mounted, then returns
    the local filesystem path.

    Args:
        smb_url: SMB URL (e.g., smb://server/share/path)
        error_tracker: Error tracker instance

    Returns:
        Local Path to mounted share or None if resolution failed
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(smb_url)
        server = parsed.netloc
        share_path = parsed.path.lstrip("/")

        if platform.system() == "Darwin":
            return _resolve_smb_darwin(server, share_path, smb_url, error_tracker)
        elif platform.system() == "Linux":
            return _resolve_smb_linux(share_path, error_tracker)
        else:
            # Windows or other OS - SMB natively supported, just return path
            error_tracker.record_skip(
                SkipCategory.PATH_NOT_FOUND,
                f"{smb_url} (SMB path resolution not implemented for this OS)",
            )
            return None

    except Exception as e:
        error_tracker.record_skip(
            SkipCategory.PATH_NOT_FOUND,
            f"{smb_url} (SMB resolution error: {type(e).__name__})",
        )
        return None


def _resolve_smb_darwin(
    server: str, share_path: str, smb_url: str, error_tracker: ErrorTracker
) -> Path | None:
    """Resolve SMB path on macOS.

    Args:
        server: SMB server name
        share_path: Share path (e.g., "scratch/TL/MattB/Reading")
        smb_url: Full SMB URL
        error_tracker: Error tracker instance

    Returns:
        Local Path or None
    """
    import time

    # Parse mount table to find the exact mount point for this URL
    mounted_path = _find_mounted_smb_path(server, share_path)
    if mounted_path and mounted_path.exists():
        return mounted_path

    # Extract path components for fallback heuristics
    path_parts = share_path.split("/") if share_path else []
    share_name = path_parts[0] if path_parts else ""
    last_component = path_parts[-1] if path_parts else ""
    hostname = server.split(".")[0] if "." in server else server

    # Build mount point candidates - macOS often mounts at last path component
    mount_candidates = [
        Path("/Volumes") / last_component,  # Most common: last path component
        Path("/Volumes") / share_name,  # Share root
        Path("/Volumes") / hostname,
        Path("/Volumes") / server,
        Path("/Volumes") / last_component.replace(" ", "%20"),  # URL-encoded spaces
    ]

    # Check existing mount points
    for mount_point in mount_candidates:
        if mount_point.exists():
            # For last_component mount, the path IS the mount point
            if mount_point.name == last_component:
                return mount_point
            # For share root, need to add remaining path parts
            remaining = path_parts[1:] if len(path_parts) > 1 else []
            full_path = mount_point.joinpath(*remaining) if remaining else mount_point
            if full_path.exists():
                return full_path

    # Try to mount using open command
    try:
        subprocess.run(
            ["open", smb_url],
            check=False,
            timeout=15,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)

        # Check all candidates again after mount attempt
        for mount_point in mount_candidates:
            if mount_point.exists():
                if mount_point.name == last_component:
                    return mount_point
                remaining = path_parts[1:] if len(path_parts) > 1 else []
                full_path = mount_point.joinpath(*remaining) if remaining else mount_point
                if full_path.exists():
                    return full_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    error_tracker.record_skip(
        SkipCategory.PATH_NOT_FOUND,
        f"{smb_url} (could not find mounted SMB share - ensure it's mounted in Finder)",
    )
    return None


def _find_mounted_smb_path(server: str, share_path: str) -> Path | None:
    """Find mounted SMB path by parsing mount table.

    Args:
        server: SMB server name
        share_path: Share path (e.g., "scratch/TL/MattB/Reading")

    Returns:
        Local mounted Path or None
    """
    try:
        result = subprocess.run(
            ["mount"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        # Normalize server name for matching
        server_lower = server.lower()

        for line in result.stdout.splitlines():
            # Format: //user@server/path on /Volumes/name (smbfs, ...)
            if " on /Volumes/" not in line or "smbfs" not in line:
                continue

            parts = line.split(" on ")
            if len(parts) < 2:
                continue

            smb_part = parts[0]  # //user@server/path
            volume_part = parts[1].split(" (")[0]  # /Volumes/name

            # Check if this mount is for our server and path
            if server_lower in smb_part.lower():
                # URL-decode for comparison (spaces become %20 in mount output)
                smb_part_decoded = smb_part.replace("%20", " ")
                # Check if share_path matches
                if share_path and share_path.lower() in smb_part_decoded.lower():
                    mount_path = Path(volume_part)
                    if mount_path.exists():
                        return mount_path

        return None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
        return None


def _resolve_smb_linux(share_path: str, error_tracker: ErrorTracker) -> Path | None:
    """Resolve SMB path on Linux.

    Args:
        share_path: Share path
        error_tracker: Error tracker instance

    Returns:
        Local Path or None
    """
    for mount_base in [Path("/mnt"), Path("/media"), Path("/home")]:
        if mount_base.exists():
            try:
                for mount_point in mount_base.iterdir():
                    try:
                        full_path = mount_point / share_path
                        if full_path.exists():
                            return full_path
                    except (OSError, PermissionError):
                        continue
            except (OSError, PermissionError):
                continue

    return None
