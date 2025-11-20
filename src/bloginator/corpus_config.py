"""Corpus configuration management.

Loads and validates corpus.yaml configuration files that describe
corpus sources with metadata.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, field_validator

from bloginator.models.document import QualityRating


class DateRange(BaseModel):
    """Date range for corpus source content.

    Attributes:
        start: Start date (inclusive)
        end: End date (inclusive)
    """

    start: datetime | None = None
    end: datetime | None = None

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime | None:
        """Parse date from string (YYYY-MM-DD format)."""
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD.") from e
        raise ValueError(f"Invalid date type: {type(v)}")


class CorpusSource(BaseModel):
    """Configuration for a corpus source.

    Attributes:
        name: Unique name for this source
        path: Path to source (local path, URL, UNC path)
        type: Source type (directory, symlink, file, url)
        enabled: Whether this source should be processed
        quality: Quality rating for documents from this source
        date_range: Time period for content in this source
        voice_notes: Notes about writing voice/style
        tags: Custom tags for filtering and weighting
    """

    name: str = Field(..., description="Unique name for this source")
    path: str = Field(..., description="Path to source (local, URL, UNC)")
    type: str = Field(
        default="directory",
        description="Source type: directory, symlink, file, url",
    )
    enabled: bool = Field(default=True, description="Whether to process this source")
    quality: QualityRating = Field(
        default=QualityRating.REFERENCE,
        description="Quality rating for this source",
    )
    date_range: DateRange | None = Field(None, description="Content time period")
    voice_notes: str | None = Field(None, description="Voice/style notes")
    tags: list[str] = Field(default_factory=list, description="Custom tags")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate source type."""
        valid_types = {"directory", "symlink", "file", "url"}
        if v not in valid_types:
            raise ValueError(f"Invalid type: {v}. Must be one of {valid_types}")
        return v

    @field_validator("quality", mode="before")
    @classmethod
    def parse_quality(cls, v: Any) -> QualityRating:
        """Parse quality rating from string."""
        if isinstance(v, QualityRating):
            return v
        if isinstance(v, str):
            try:
                return QualityRating(v.lower())
            except ValueError as e:
                valid = ", ".join(q.value for q in QualityRating)
                raise ValueError(f"Invalid quality: {v}. Must be one of: {valid}") from e
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
            # Convert to pathlib-compatible format on Windows
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
        """Check if path is a URL."""
        result = urlparse(self.path)
        return result.scheme in ("http", "https", "ftp")

    def is_local_path(self) -> bool:
        """Check if path is a local file system path."""
        return not self.is_url()


class ExtractionSettings(BaseModel):
    """Global extraction settings.

    Attributes:
        chunk_size: Maximum characters per chunk
        follow_symlinks: Whether to follow symbolic links
        recursive: Whether to scan subdirectories
        include_extensions: File extensions to include
        ignore_patterns: Glob patterns to ignore
    """

    chunk_size: int = Field(default=1000, description="Maximum characters per chunk")
    follow_symlinks: bool = Field(default=True, description="Follow symbolic links")
    recursive: bool = Field(default=True, description="Scan subdirectories")
    include_extensions: list[str] = Field(
        default_factory=lambda: [".md", ".markdown", ".txt", ".pdf", ".docx"],
        description="File extensions to include",
    )
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [".*", "_*", "draft_*", "TODO.md", "README.md"],
        description="Glob patterns to ignore",
    )


class IndexingSettings(BaseModel):
    """Indexing and search weighting settings.

    Attributes:
        quality_weights: Multipliers for each quality level
        recency_decay: Weight reduction per year old (0.0-1.0)
        tag_boosts: Multipliers for specific tags
    """

    quality_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "preferred": 1.5,
            "reference": 1.0,
            "supplemental": 0.7,
            "deprecated": 0.3,
        },
        description="Quality level multipliers",
    )
    recency_decay: float = Field(
        default=0.1,
        description="Weight reduction per year old",
    )
    tag_boosts: dict[str, float] = Field(
        default_factory=dict,
        description="Tag-based boost multipliers",
    )


class CorpusConfig(BaseModel):
    """Complete corpus configuration.

    Attributes:
        sources: List of corpus sources
        extraction: Extraction settings
        indexing: Indexing and weighting settings
    """

    sources: list[CorpusSource] = Field(..., description="Corpus sources")
    extraction: ExtractionSettings = Field(
        default_factory=ExtractionSettings,
        description="Extraction settings",
    )
    indexing: IndexingSettings = Field(
        default_factory=IndexingSettings,
        description="Indexing settings",
    )

    @classmethod
    def load_from_file(cls, config_path: Path) -> "CorpusConfig":
        """Load configuration from YAML file.

        Args:
            config_path: Path to corpus.yaml

        Returns:
            Parsed corpus configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If YAML is invalid or doesn't match schema
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open() as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty config file: {config_path}")

        try:
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Invalid corpus config: {e}") from e

    def get_enabled_sources(self) -> list[CorpusSource]:
        """Get list of enabled sources.

        Returns:
            List of sources where enabled=True
        """
        return [source for source in self.sources if source.enabled]

    def get_sources_by_quality(self, quality: QualityRating) -> list[CorpusSource]:
        """Get sources with specific quality rating.

        Args:
            quality: Quality rating to filter by

        Returns:
            List of sources with matching quality
        """
        return [source for source in self.sources if source.quality == quality]

    def get_quality_weight(self, quality: QualityRating) -> float:
        """Get weight multiplier for quality level.

        Args:
            quality: Quality rating

        Returns:
            Weight multiplier (default 1.0 if not configured)
        """
        return self.indexing.quality_weights.get(quality.value, 1.0)

    def get_tag_boost(self, tag: str) -> float:
        """Get boost multiplier for tag.

        Args:
            tag: Tag name

        Returns:
            Boost multiplier (default 1.0 if not configured)
        """
        return self.indexing.tag_boosts.get(tag, 1.0)
