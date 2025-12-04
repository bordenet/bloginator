"""Corpus source model with validation and path resolution.

Handles configuration and validation of individual corpus sources with support
for local paths, URLs, and UNC paths.
"""

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from bloginator.models._date_range import DateRange
from bloginator.models.document import QualityRating


class CorpusSource(BaseModel):
    """Configuration for a corpus source.

    Attributes:
        id: Unique identifier for this source (UUID)
        name: Unique name for this source
        path: Path to source (local path, URL, UNC path)
        type: Source type (directory, symlink, file, url)
        enabled: Whether this source should be processed
        quality: Quality rating for documents from this source
        date_range: Time period for content in this source
        voice_notes: Notes about writing voice/style
        tags: Custom tags for filtering and weighting
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique ID for this source",
    )
    name: str = Field(..., description="Unique name for this source")
    path: str = Field(..., description="Path to source (local, URL, UNC)")
    type: str = Field(
        default="directory",
        description="Source type: directory, symlink, file, url",
    )
    enabled: bool = Field(
        default=True,
        description="Whether to process this source",
    )
    quality: QualityRating = Field(
        default=QualityRating.REFERENCE,
        description="Quality rating for this source",
    )
    date_range: DateRange | None = Field(
        None,
        description="Content time period",
    )
    voice_notes: str | None = Field(
        None,
        description="Voice/style notes",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Custom tags",
    )

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate source type.

        Args:
            v: Source type to validate

        Returns:
            Validated type string

        Raises:
            ValueError: If type is not in valid set
        """
        valid_types = {"directory", "symlink", "file", "url"}
        if v not in valid_types:
            raise ValueError(f"Invalid type: {v}. Must be one of {valid_types}")
        return v

    @field_validator("quality", mode="before")
    @classmethod
    def parse_quality(cls, v: Any) -> QualityRating:
        """Parse quality rating from string.

        Args:
            v: Quality value (string or QualityRating enum)

        Returns:
            Parsed QualityRating

        Raises:
            ValueError: If quality format is invalid
        """
        if isinstance(v, QualityRating):
            return v
        if isinstance(v, str):
            try:
                return QualityRating(v.lower())
            except ValueError as e:
                valid = ", ".join(q.value for q in QualityRating)
                msg = f"Invalid quality: {v}. Must be one of: {valid}"
                raise ValueError(msg) from e
        raise ValueError(f"Invalid quality type: {type(v)}")

    def resolve_path(self, config_dir: Path) -> Path | str:
        """Resolve path relative to config file location.

        Args:
            config_dir: Directory containing corpus.yaml

        Returns:
            Resolved absolute path (Path) or URL (str)
        """
        path_str = self.path

        # Handle URLs
        if self.is_url():
            return path_str

        # Handle Windows UNC paths (\\server\share)
        if path_str.startswith("\\\\"):
            return Path(path_str)

        # Handle Windows drive letters (C:\, D:\, etc.)
        if re.match(r"^[A-Za-z]:[/\\]", path_str):
            return Path(path_str)

        # Convert to Path and resolve
        path = Path(path_str)

        # If absolute, return as-is
        if path.is_absolute():
            return path.resolve()

        # Relative path - resolve relative to config directory
        return (config_dir / path).resolve()

    def is_url(self) -> bool:
        """Check if path is a URL.

        Returns:
            True if path is a URL, False otherwise
        """
        result = urlparse(self.path)
        return result.scheme in ("http", "https", "ftp", "smb")

    def is_local_path(self) -> bool:
        """Check if path is a local file system path.

        Returns:
            True if path is a local file path, False otherwise
        """
        return not self.is_url()
