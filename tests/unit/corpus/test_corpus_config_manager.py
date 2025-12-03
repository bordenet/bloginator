"""Tests for CorpusConfigManager safe deletion operations."""

from pathlib import Path

import pytest
import yaml

from bloginator.corpus_config import CorpusConfigManager


class TestCorpusConfigManager:
    """Tests for safe corpus configuration management."""

    @pytest.fixture
    def corpus_yaml(self, tmp_path: Path) -> Path:
        """Create test corpus.yaml."""
        config = {
            "sources": [
                {
                    "id": "source-1",
                    "name": "blog-archive",
                    "path": "/path/to/archive",
                    "quality": "preferred",
                    "enabled": True,
                    "tags": ["archive"],
                    "voice_notes": "Original voice",
                },
                {
                    "id": "source-2",
                    "name": "recent-posts",
                    "path": "/path/to/recent",
                    "quality": "reference",
                    "enabled": True,
                    "tags": ["recent"],
                },
                {
                    "id": "source-3",
                    "name": "drafts",
                    "path": "/path/to/drafts",
                    "quality": "draft",
                    "enabled": False,
                    "tags": ["draft"],
                },
            ]
        }

        yaml_file = tmp_path / "corpus.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(config, f)

        return yaml_file

    def test_create_backup(self, corpus_yaml: Path) -> None:
        """Test backup file is created."""
        manager = CorpusConfigManager(corpus_yaml)
        backup = manager.create_backup()

        assert backup.exists()
        assert backup.parent == manager.backup_dir
        assert "corpus." in backup.name

    def test_load_config(self, corpus_yaml: Path) -> None:
        """Test loading config from YAML."""
        manager = CorpusConfigManager(corpus_yaml)
        config = manager.load_config()

        assert "sources" in config
        assert len(config["sources"]) == 3

    def test_delete_source_by_id_success(self, corpus_yaml: Path) -> None:
        """Test successful deletion by ID."""
        manager = CorpusConfigManager(corpus_yaml)

        # Delete source-2
        success = manager.delete_source_by_id("source-2")

        assert success
        config = manager.load_config()
        assert len(config["sources"]) == 2
        assert all(s["id"] != "source-2" for s in config["sources"])

    def test_delete_source_preserves_others(self, corpus_yaml: Path) -> None:
        """Test deletion preserves other sources."""
        manager = CorpusConfigManager(corpus_yaml)

        manager.delete_source_by_id("source-1")

        config = manager.load_config()
        names = [s["name"] for s in config["sources"]]

        assert "blog-archive" not in names
        assert "recent-posts" in names
        assert "drafts" in names

    def test_delete_nonexistent_id_fails(self, corpus_yaml: Path) -> None:
        """Test deletion of non-existent source returns False."""
        manager = CorpusConfigManager(corpus_yaml)

        success = manager.delete_source_by_id("nonexistent-id")

        assert not success
        config = manager.load_config()
        assert len(config["sources"]) == 3  # All sources preserved

    def test_backup_created_before_delete(self, corpus_yaml: Path) -> None:
        """Test backup is created before deletion."""
        manager = CorpusConfigManager(corpus_yaml)
        backup_count_before = len(manager.get_backup_files())

        manager.delete_source_by_id("source-2")

        backup_count_after = len(manager.get_backup_files())
        assert backup_count_after > backup_count_before

    def test_restore_from_backup(self, corpus_yaml: Path) -> None:
        """Test restoring config from backup."""
        manager = CorpusConfigManager(corpus_yaml)

        # Get original state
        original = manager.load_config()
        original_count = len(original["sources"])

        # Delete and verify
        manager.delete_source_by_id("source-1")
        assert len(manager.load_config()["sources"]) == original_count - 1

        # Get latest backup and restore
        backups = manager.get_backup_files()
        assert len(backups) > 0

        manager.restore_from_backup(backups[0])
        restored = manager.load_config()

        assert len(restored["sources"]) == original_count

    def test_validate_config_success(self, corpus_yaml: Path) -> None:
        """Test config validation passes for valid config."""
        manager = CorpusConfigManager(corpus_yaml)
        config = manager.load_config()

        # Should not raise
        manager._validate_config(config)

    def test_validate_config_missing_name(self, corpus_yaml: Path) -> None:
        """Test validation fails for missing name."""
        manager = CorpusConfigManager(corpus_yaml)

        config = {
            "sources": [
                {
                    "id": "test",
                    "path": "/path",
                    # Missing name
                }
            ]
        }

        with pytest.raises(ValueError, match="missing required field: name"):
            manager._validate_config(config)

    def test_validate_config_missing_path(self, corpus_yaml: Path) -> None:
        """Test validation fails for missing path."""
        manager = CorpusConfigManager(corpus_yaml)

        config = {
            "sources": [
                {
                    "id": "test",
                    "name": "test",
                    # Missing path
                }
            ]
        }

        with pytest.raises(ValueError, match="missing required field: path"):
            manager._validate_config(config)

    def test_save_config_atomic(self, tmp_path: Path) -> None:
        """Test save uses atomic operations."""
        yaml_file = tmp_path / "corpus.yaml"
        config = {"sources": []}

        manager = CorpusConfigManager(yaml_file)
        manager.save_config(config)

        assert yaml_file.exists()
        loaded = manager.load_config()
        assert loaded == config

    def test_multiline_voice_notes_preserved(self, tmp_path: Path) -> None:
        """Test multiline voice notes are preserved."""
        yaml_file = tmp_path / "corpus.yaml"
        multiline_notes = "Line 1\nLine 2\nLine 3"

        config = {
            "sources": [
                {
                    "id": "test",
                    "name": "test",
                    "path": "/path",
                    "voice_notes": multiline_notes,
                }
            ]
        }

        manager = CorpusConfigManager(yaml_file)
        manager.save_config(config)

        loaded = manager.load_config()
        assert loaded["sources"][0]["voice_notes"] == multiline_notes

    def test_get_backup_files_returns_list(self, corpus_yaml: Path) -> None:
        """Test get_backup_files returns list of backups."""
        manager = CorpusConfigManager(corpus_yaml)
        manager.create_backup()

        backups = manager.get_backup_files()

        assert isinstance(backups, list)
        assert len(backups) >= 1
        assert all(b.suffix == ".yaml" for b in backups)
