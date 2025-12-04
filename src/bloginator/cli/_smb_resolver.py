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
        share_path: Share path
        smb_url: Full SMB URL
        error_tracker: Error tracker instance

    Returns:
        Local Path or None
    """
    import time

    # Extract the share name (first path component)
    share_name = share_path.split("/")[0] if share_path else ""
    hostname = server.split(".")[0] if "." in server else server

    # Try mount point using share name first (most common on macOS)
    mount_candidates = [
        Path("/Volumes") / share_name,
        Path("/Volumes") / hostname,
        Path("/Volumes") / server,
        Path("/Volumes") / hostname.replace("-", "_"),
    ]

    # Check existing mount points
    for mount_point in mount_candidates:
        if mount_point.exists():
            path_parts = share_path.split("/")[1:] if "/" in share_path else []
            full_path = mount_point.joinpath(*path_parts) if path_parts else mount_point
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
                path_parts = share_path.split("/")[1:] if "/" in share_path else []
                full_path = mount_point.joinpath(*path_parts) if path_parts else mount_point
                if full_path.exists():
                    return full_path
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass

    # As last resort, try to find any volume that matches
    try:
        volumes = Path("/Volumes").iterdir()
        for vol in volumes:
            vol_name_lower = vol.name.lower()
            if (
                (share_name and share_name.lower() in vol_name_lower)
                or hostname.lower() in vol_name_lower
                or server.lower() in vol_name_lower
            ):
                path_parts = share_path.split("/")[1:] if "/" in share_path else []
                full_path = vol.joinpath(*path_parts) if path_parts else vol
                if full_path.exists():
                    return full_path
    except (OSError, PermissionError):
        pass

    error_tracker.record_skip(
        SkipCategory.PATH_NOT_FOUND,
        f"{smb_url} (could not find mounted SMB share - ensure it's mounted in Finder)",
    )
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
