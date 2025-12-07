"""Shadow copy utilities for offline corpus access.

This module provides functions for creating and managing shadow copies of
corpus files in /tmp/bloginator/corpus_shadow. Shadow copies enable offline
access to SMB shares and OneDrive paths when traveling or disconnected.

Shadow copy structure:
- /tmp/bloginator/corpus_shadow/smb/<server>/<share_path>/  - for SMB sources
- /tmp/bloginator/corpus_shadow/local/<path>/  - for local paths (OneDrive)
"""

import shutil
from pathlib import Path

from bloginator.config import Config


def get_shadow_copy_root() -> Path:
    """Get the root directory for shadow copies.

    Returns:
        Path to shadow copy root directory
    """
    return Config.SHADOW_COPY_ROOT


def is_shadow_copy_enabled() -> bool:
    """Check if shadow copy creation is enabled.

    Returns:
        True if CORPUS_MAINTAIN_SHADOW_COPIES is enabled
    """
    return Config.CORPUS_MAINTAIN_SHADOW_COPIES


def build_shadow_path_for_local(original_path: Path) -> Path:
    """Build the shadow path for a local filesystem path.

    Args:
        original_path: Original local path (e.g., OneDrive path)

    Returns:
        Path where shadow copy should be stored
    """
    relative_part = str(original_path.absolute()).lstrip("/")
    return get_shadow_copy_root() / "local" / relative_part


def build_shadow_path_for_smb(smb_url: str, file_path: Path, source_root: Path) -> Path:
    """Build the shadow path for an SMB file.

    Args:
        smb_url: Original SMB URL of the source
        file_path: Path to the actual file
        source_root: Root directory of the mounted SMB share

    Returns:
        Path where shadow copy should be stored
    """
    from urllib.parse import urlparse

    parsed = urlparse(smb_url)
    server = parsed.netloc
    share_path = parsed.path.lstrip("/")

    # Calculate relative path from source root
    try:
        relative = file_path.relative_to(source_root)
    except ValueError:
        # File not under source root - use absolute path
        relative = Path(str(file_path.absolute()).lstrip("/"))

    return get_shadow_copy_root() / "smb" / server / share_path / relative


def create_shadow_copy(source_file: Path, shadow_path: Path) -> bool:
    """Create a shadow copy of a source file.

    Args:
        source_file: Path to the source file
        shadow_path: Path where shadow copy should be created

    Returns:
        True if shadow copy was created successfully, False otherwise
    """
    try:
        # Create parent directories
        shadow_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file with metadata
        shutil.copy2(str(source_file), str(shadow_path))
        return True
    except (OSError, shutil.Error):
        return False


def should_update_shadow_copy(source_file: Path, shadow_path: Path) -> bool:
    """Check if a shadow copy needs to be updated.

    A shadow copy should be updated if:
    - It doesn't exist
    - Source file is newer than shadow copy

    Args:
        source_file: Path to the source file
        shadow_path: Path to the shadow copy

    Returns:
        True if shadow copy should be updated
    """
    if not shadow_path.exists():
        return True

    try:
        source_mtime = source_file.stat().st_mtime
        shadow_mtime = shadow_path.stat().st_mtime
        return source_mtime > shadow_mtime
    except OSError:
        return True
