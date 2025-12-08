"""Corpus configuration management.

Loads and validates corpus.yaml configuration files that describe
corpus sources with metadata.

This module provides the main corpus configuration manager and settings models.
Models are defined in separate modules under bloginator.models.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from bloginator._config_manager import CorpusConfigManager
from bloginator._corpus_settings import ExtractionSettings, IndexingSettings
from bloginator.models._corpus_source import CorpusSource
from bloginator.models._date_range import DateRange
from bloginator.models.document import QualityRating


# Re-export models for backward compatibility
__all__ = [
    "DateRange",
    "CorpusSource",
    "ExtractionSettings",
    "IndexingSettings",
    "CorpusConfig",
    "CorpusConfigManager",
]


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

    def source_path_exists(self, path: str) -> bool:
        """Check if directory path already exists in corpus.

        Args:
            path: Path to check (normalized)

        Returns:
            True if path already exists in corpus
        """
        normalized_check = Path(path).resolve()
        for source in self.sources:
            try:
                normalized_source = Path(source.path).resolve()
                if normalized_check == normalized_source:
                    return True
            except (OSError, RuntimeError, ValueError):
                # Can't resolve one of the paths, compare as strings
                if Path(path).resolve() == Path(source.path).resolve():
                    return True
        return False

    def add_directory_source(
        self,
        name: str,
        path: str,
        enabled: bool = True,
        quality: str = "reference",
        is_external: bool = False,
        tags: list[str] | None = None,
        voice_notes: str = "",
        recursive: bool = True,
    ) -> bool:
        """Add directory source to corpus configuration.

        Args:
            name: Unique name for the source
            path: Path to the directory
            enabled: Whether source should be processed
            quality: Quality rating
            is_external: Whether source is external
            tags: Optional list of tags
            voice_notes: Voice notes
            recursive: Whether to recurse subdirectories

        Returns:
            True if added successfully, False if path already exists
        """
        # Check for duplicate path
        if self.source_path_exists(path):
            return False

        # Create new source
        quality_rating = QualityRating(quality) if isinstance(quality, str) else quality
        new_source = CorpusSource(
            name=name,
            path=path,
            type="directory",
            enabled=enabled,
            quality=quality_rating,
            date_range=None,
            voice_notes=voice_notes if voice_notes else None,
            tags=tags or [],
        )

        # Add to sources
        self.sources.append(new_source)
        return True
