"""Directory scanner for corpus source discovery.

Provides functionality to scan directories, discover supported document types,
and generate corpus source configurations.
"""

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path


# Supported file extensions
SUPPORTED_FORMATS = {
    # Document formats
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".text",
    ".md",
    ".markdown",
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


@dataclass
class FileInfo:
    """Information about discovered file.

    Attributes:
        path: Full path to the file
        format: File format (pdf, docx, txt, md)
        size: File size in bytes
        readable: Whether file is readable
    """

    path: Path
    format: str
    size: int
    readable: bool


@dataclass
class ScanResult:
    """Result of directory scan.

    Attributes:
        directory: Directory that was scanned
        total_files: Total number of discovered files
        files: List of discovered files
        by_format: Count of files by format
        total_size: Total size of all files in bytes
        is_valid: Whether scan completed successfully
        error: Error message if scan failed
        scan_time: Time taken to scan in seconds
    """

    directory: Path
    total_files: int
    files: list[FileInfo] = field(default_factory=list)
    by_format: dict[str, int] = field(default_factory=dict)
    total_size: int = 0
    is_valid: bool = True
    error: str | None = None
    scan_time: float = 0.0


@dataclass
class SourceConfig:
    """Configuration for corpus source.

    Attributes:
        name: Unique name for the source
        path: Path to the directory (may be relative or absolute)
        enabled: Whether source should be processed
        quality: Quality rating (preferred, reference, supplemental, deprecated)
        tags: Custom tags for filtering
        is_external: Whether source is external
        voice_notes: Notes about writing voice/style
        recursive: Whether to recurse into subdirectories
        file_count: Number of files discovered
    """

    name: str
    path: str
    enabled: bool = True
    quality: str = "reference"
    tags: list[str] = field(default_factory=list)
    is_external: bool = False
    voice_notes: str = ""
    recursive: bool = True
    file_count: int = 0


class DirectoryScanner:
    """Scans directories for documents and generates corpus sources."""

    def __init__(self, max_depth: int = 10) -> None:
        """Initialize scanner.

        Args:
            max_depth: Maximum recursion depth (prevent infinite loops)
        """
        self.max_depth = max_depth
        self._visited_real_paths: set[str] = set()

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str | None = None,
        follow_symlinks: bool = False,
    ) -> ScanResult:
        """Scan directory for supported documents.

        Args:
            directory: Directory to scan
            recursive: Whether to recurse into subdirectories
            pattern: Optional regex to filter filenames
            follow_symlinks: Whether to follow symlinks

        Returns:
            ScanResult with file list and statistics
        """
        start_time = time.time()
        self._visited_real_paths.clear()

        # Validate directory first
        is_valid, error = self.validate_directory(directory)
        if not is_valid:
            return ScanResult(
                directory=directory,
                total_files=0,
                is_valid=False,
                error=error,
                scan_time=time.time() - start_time,
            )

        # Walk directory and collect files
        files = self._walk_directory(
            directory,
            recursive=recursive,
            pattern=pattern,
            follow_symlinks=follow_symlinks,
        )

        # Calculate statistics
        by_format: dict[str, int] = {}
        total_size = 0
        for file_info in files:
            by_format[file_info.format] = by_format.get(file_info.format, 0) + 1
            total_size += file_info.size

        scan_time = time.time() - start_time

        return ScanResult(
            directory=directory,
            total_files=len(files),
            files=files,
            by_format=by_format,
            total_size=total_size,
            is_valid=True,
            scan_time=scan_time,
        )

    def validate_directory(self, directory: Path) -> tuple[bool, str]:
        """Validate directory is accessible and readable.

        Args:
            directory: Directory to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if path exists
        if not directory.exists():
            return False, f"Directory not found: {directory}"

        # Check if it's actually a directory
        if not directory.is_dir():
            return False, f"Path is a file, not a directory: {directory}"

        # Check if readable
        if not os.access(directory, os.R_OK):
            return False, "Cannot read directory: Permission denied"

        return True, ""

    def create_source_config(
        self,
        directory: Path,
        source_name: str,
        tags: list[str] | None = None,
        quality: str = "reference",
        is_external: bool = False,
        voice_notes: str = "",
        recursive: bool = True,
    ) -> SourceConfig:
        """Create source configuration from directory.

        Args:
            directory: Directory to create config for
            source_name: Name for the source
            tags: Optional list of tags
            quality: Quality rating
            is_external: Whether source is external
            voice_notes: Voice notes
            recursive: Whether to enable recursion

        Returns:
            SourceConfig ready to add to corpus.yaml
        """
        # Scan to get file count
        scan = self.scan_directory(directory, recursive=recursive)
        file_count = scan.total_files if scan.is_valid else 0

        # Format path - store absolute path
        path_str = str(directory.resolve())

        return SourceConfig(
            name=source_name,
            path=path_str,
            enabled=True,
            quality=quality,
            tags=tags or [],
            is_external=is_external,
            voice_notes=voice_notes,
            recursive=recursive,
            file_count=file_count,
        )

    def _is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported.

        Args:
            filename: Name of file to check

        Returns:
            Whether file has supported extension
        """
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_FORMATS

    def _walk_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str | None = None,
        follow_symlinks: bool = False,
        depth: int = 0,
    ) -> list[FileInfo]:
        """Recursively walk directory and collect files.

        Args:
            directory: Directory to walk
            recursive: Whether to recurse
            pattern: Optional regex filter
            follow_symlinks: Whether to follow symlinks
            depth: Current recursion depth

        Returns:
            List of FileInfo for discovered files
        """
        files: list[FileInfo] = []

        # Check depth limit
        if depth >= self.max_depth:
            return files

        # Check for symlink loops
        try:
            real_path = str(directory.resolve())
            if real_path in self._visited_real_paths:
                return files  # Already visited (symlink loop)
            self._visited_real_paths.add(real_path)
        except (OSError, RuntimeError):
            # Can't resolve - skip
            return files

        try:
            entries = sorted(directory.iterdir())
        except (OSError, PermissionError):
            return files

        for entry in entries:
            # Skip hidden files/directories
            if entry.name.startswith("."):
                continue

            try:
                # Handle symlinks
                if entry.is_symlink():
                    if not follow_symlinks:
                        continue
                    # Check if following would create loop
                    try:
                        resolved = entry.resolve()
                        if str(resolved) in self._visited_real_paths:
                            continue
                    except (OSError, RuntimeError):
                        continue

                if entry.is_dir():
                    if recursive:
                        # Recurse into subdirectory
                        sub_files = self._walk_directory(
                            entry,
                            recursive=recursive,
                            pattern=pattern,
                            follow_symlinks=follow_symlinks,
                            depth=depth + 1,
                        )
                        files.extend(sub_files)
                elif (
                    entry.is_file()
                    and self._is_supported_format(entry.name)
                    and (not pattern or re.search(pattern, entry.name))
                ):
                    # Check if readable
                    readable = os.access(entry, os.R_OK)
                    size = entry.stat().st_size if readable else 0

                    file_format = entry.suffix.lower().lstrip(".")
                    files.append(
                        FileInfo(
                            path=entry,
                            format=file_format,
                            size=size,
                            readable=readable,
                        )
                    )
            except (OSError, PermissionError):
                # Skip files/dirs we can't access
                continue

        return files
