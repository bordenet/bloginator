"""Corpus configuration management.

Loads and validates corpus.yaml configuration files that describe
corpus sources with metadata.

This module provides the main corpus configuration manager and settings models.
Models are defined in separate modules under bloginator.models.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

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


class CorpusConfigManager:
    """Safe corpus configuration management with backups and validation.

    Provides atomic operations with backup/restore capabilities for corpus.yaml
    modifications to prevent data loss.
    """

    def __init__(self, config_path: Path) -> None:
        """Initialize manager with corpus config path.

        Args:
            config_path: Path to corpus.yaml file
        """
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / ".backups"
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self) -> Path:
        """Create timestamped backup of corpus.yaml.

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"corpus.{timestamp}.yaml"

        if self.config_path.exists():
            shutil.copy2(self.config_path, backup_path)

        return backup_path

    def load_config(self) -> dict[str, Any]:
        """Load corpus configuration from YAML.

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If corpus.yaml does not exist
            yaml.YAMLError: If YAML is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Corpus config not found: {self.config_path}")

        with self.config_path.open() as f:
            config = yaml.safe_load(f)

        return config or {}

    def save_config(self, config: dict[str, Any]) -> None:
        """Save configuration to YAML with atomic operations.

        Uses temp file + rename to ensure atomicity and prevent corruption.

        Args:
            config: Configuration dictionary to save

        Raises:
            ValueError: If config fails validation
            IOError: If write fails
        """
        # Validate before writing
        self._validate_config(config)

        # Write to temp file first
        temp_path = self.config_path.with_suffix(".yaml.tmp")

        try:
            with temp_path.open("w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            # Atomic rename
            temp_path.replace(self.config_path)
        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to save config: {e}") from e

    def delete_source_by_id(self, source_id: str) -> bool:
        """Delete source by ID with backup.

        Safe deletion:
        1. Create backup
        2. Load config
        3. Find source by ID
        4. Remove from list
        5. Validate modified config
        6. Write atomically

        Args:
            source_id: UUID of source to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion would corrupt config
            IOError: If save fails
        """
        # Create backup before any modifications
        backup_path = self.create_backup()

        try:
            config = self.load_config()

            # Find and remove source
            sources = config.get("sources", [])
            original_count = len(sources)

            config["sources"] = [s for s in sources if s.get("id") != source_id]

            if len(config["sources"]) == original_count:
                # Not found - restore from backup and return False
                self._restore_from_backup(backup_path)
                return False

            # Validate before writing
            self._validate_config(config)

            # Save atomically
            self.save_config(config)

            return True

        except Exception as e:
            # Restore from backup on any error
            self._restore_from_backup(backup_path)
            raise ValueError(f"Failed to delete source: {e}") from e

    def restore_from_backup(self, backup_path: Path) -> None:
        """Restore corpus.yaml from backup file.

        Args:
            backup_path: Path to backup file to restore from

        Raises:
            FileNotFoundError: If backup does not exist
            IOError: If restore fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        try:
            shutil.copy2(backup_path, self.config_path)
        except Exception as e:
            raise OSError(f"Failed to restore from backup: {e}") from e

    def get_backup_files(self) -> list[Path]:
        """Get list of available backups sorted by date (newest first).

        Returns:
            List of backup file paths
        """
        if not self.backup_dir.exists():
            return []

        backups = sorted(self.backup_dir.glob("corpus.*.yaml"), reverse=True)
        return backups

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate corpus configuration integrity.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If config is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Config must be a dictionary")

        sources = config.get("sources", [])
        if not isinstance(sources, list):
            raise ValueError("sources must be a list")

        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                raise ValueError(f"Source {idx} must be a dictionary")

            if "name" not in source:
                raise ValueError(f"Source {idx} missing required field: name")

            if "path" not in source:
                raise ValueError(f"Source {idx} missing required field: path")

    def _restore_from_backup(self, backup_path: Path) -> None:
        """Internal helper to restore from backup."""
        try:
            if backup_path.exists():
                self.restore_from_backup(backup_path)
        except Exception:
            pass  # Silent failure for cleanup
