"""Corpus configuration manager with backup and validation.

Provides atomic operations with backup/restore capabilities for corpus.yaml
modifications to prevent data loss.
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


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
        self._validate_config(config)

        temp_path = self.config_path.with_suffix(".yaml.tmp")

        try:
            with temp_path.open("w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            temp_path.replace(self.config_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to save config: {e}") from e

    def delete_source_by_id(self, source_id: str) -> bool:
        """Delete source by ID with backup.

        Args:
            source_id: UUID of source to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion would corrupt config
            IOError: If save fails
        """
        backup_path = self.create_backup()

        try:
            config = self.load_config()
            sources = config.get("sources", [])
            original_count = len(sources)

            config["sources"] = [s for s in sources if s.get("id") != source_id]

            if len(config["sources"]) == original_count:
                self._restore_from_backup(backup_path)
                return False

            self._validate_config(config)
            self.save_config(config)
            return True

        except Exception as e:
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

        return sorted(self.backup_dir.glob("corpus.*.yaml"), reverse=True)

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate corpus configuration integrity."""
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
