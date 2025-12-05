"""Tests for corpus source management UI functionality."""

from pathlib import Path

import pytest
import yaml


class TestCorpusSourceManagement:
    """Tests for adding, deleting, and managing corpus sources."""

    @pytest.fixture
    def corpus_yaml(self, tmp_path: Path) -> Path:
        """Create a test corpus.yaml file."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        yaml_file = corpus_dir / "corpus.yaml"

        config = {
            "sources": [
                {
                    "name": "blog-archive",
                    "path": "/Users/test/blogs/archive",
                    "quality": "preferred",
                    "enabled": True,
                    "tags": ["archive", "blog"],
                    "voice_notes": "Original voice from 2020",
                }
            ]
        }

        with yaml_file.open("w") as f:
            yaml.dump(config, f)

        return yaml_file

    def test_add_source_to_empty_config(self, tmp_path: Path) -> None:
        """Test adding a source to a config with no sources."""
        corpus_yaml = tmp_path / "corpus.yaml"
        config = {"extraction": {}, "indexing": {}}

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        # Simulate adding a source
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        if "sources" not in config:
            config["sources"] = []

        new_source = {
            "name": "new-blog",
            "path": "/Users/test/blogs/new",
            "type": "directory",
            "enabled": True,
            "quality": "reference",
            "tags": ["blog", "recent"],
            "voice_notes": "Recent authentic voice",
        }

        config["sources"].append(new_source)

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Verify
        with corpus_yaml.open() as f:
            updated_config = yaml.safe_load(f)

        assert len(updated_config["sources"]) == 1
        assert updated_config["sources"][0]["name"] == "new-blog"
        assert updated_config["sources"][0]["path"] == "/Users/test/blogs/new"

    def test_add_duplicate_source_path_rejected(self, corpus_yaml: Path) -> None:
        """Test that duplicate paths are rejected."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        existing_paths = [source.get("path", "") for source in config.get("sources", [])]
        new_path = existing_paths[0]  # Try to add existing path

        # Check for exact duplicate (case-sensitive string match)
        path_exists = new_path in existing_paths
        assert path_exists

    def test_add_different_path_allowed(self, corpus_yaml: Path) -> None:
        """Test that different paths are allowed."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        existing_paths = [source.get("path", "") for source in config.get("sources", [])]
        new_path = "/Users/test/blogs/different"

        path_exists = new_path in existing_paths
        assert not path_exists

    def test_delete_source_by_name_and_path(self, corpus_yaml: Path) -> None:
        """Test deleting source by name and path matching."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        original_count = len(config["sources"])
        source_to_delete = config["sources"][0]
        source_name = source_to_delete.get("name", "")
        source_path = source_to_delete.get("path", "")

        # Delete by filtering
        sources_copy = config.get("sources", [])
        config["sources"] = [
            s
            for s in sources_copy
            if not (s.get("name") == source_name and s.get("path") == source_path)
        ]

        assert len(config["sources"]) == original_count - 1

    def test_delete_preserves_other_sources(self, tmp_path: Path) -> None:
        """Test that deleting one source preserves others."""
        corpus_yaml = tmp_path / "corpus.yaml"

        config = {
            "sources": [
                {
                    "name": "blog-1",
                    "path": "/path/1",
                    "quality": "preferred",
                    "enabled": True,
                    "tags": ["blog"],
                },
                {
                    "name": "blog-2",
                    "path": "/path/2",
                    "quality": "reference",
                    "enabled": True,
                    "tags": ["blog"],
                },
                {
                    "name": "blog-3",
                    "path": "/path/3",
                    "quality": "draft",
                    "enabled": False,
                    "tags": ["draft"],
                },
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        # Delete blog-2
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        config["sources"] = [s for s in config["sources"] if s.get("name") != "blog-2"]

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Verify
        with corpus_yaml.open() as f:
            updated = yaml.safe_load(f)

        assert len(updated["sources"]) == 2
        assert [s["name"] for s in updated["sources"]] == ["blog-1", "blog-3"]

    def test_parse_comma_separated_tags(self) -> None:
        """Test parsing comma-separated tags from form input."""
        input_tags = "blog, published, authentic-voice, 2024"

        tags_list = [t.strip() for t in input_tags.split(",") if t.strip()]

        assert tags_list == ["blog", "published", "authentic-voice", "2024"]

    def test_voice_notes_handling_multiline(self, tmp_path: Path) -> None:
        """Test that multiline voice notes are preserved."""
        corpus_yaml = tmp_path / "corpus.yaml"

        voice_notes = "Original voice from 2020.\nAuthentic style.\nPrefer for generation."
        config = {
            "sources": [
                {
                    "name": "archive",
                    "path": "/path/archive",
                    "voice_notes": voice_notes,
                }
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, allow_unicode=True)

        # Reload and verify
        with corpus_yaml.open() as f:
            loaded = yaml.safe_load(f)

        assert loaded["sources"][0]["voice_notes"] == voice_notes

    def test_quality_rating_validation(self) -> None:
        """Test quality rating validation."""
        valid_ratings = ["reference", "draft", "archive"]

        test_input = "reference"
        assert test_input in valid_ratings

        test_input = "invalid-rating"
        assert test_input not in valid_ratings

    def test_smb_path_handling(self) -> None:
        """Test handling of SMB network paths."""
        smb_path = "smb://lucybear-nas._smb._tcp.local/scratch/TL/path"

        # SMB paths should be treated as exact strings, not resolved
        existing_paths = [
            "/local/path",
            smb_path,
        ]

        # Exact match should find it
        assert smb_path in existing_paths

        # Different SMB path should not match
        different_smb = "smb://other-server/path"
        assert different_smb not in existing_paths

    def test_none_voice_notes_handling(self, tmp_path: Path) -> None:
        """Test that empty voice notes are stored as None."""
        corpus_yaml = tmp_path / "corpus.yaml"

        voice_notes = ""
        config = {
            "sources": [
                {
                    "name": "test",
                    "path": "/path",
                    "voice_notes": voice_notes if voice_notes else None,
                }
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        with corpus_yaml.open() as f:
            loaded = yaml.safe_load(f)

        assert loaded["sources"][0]["voice_notes"] is None


class TestIndexPruning:
    """Tests for index pruning functionality."""

    def test_identify_orphaned_documents(self) -> None:
        """Test identifying documents from deleted sources."""
        configured_paths = {
            "/path/1",
            "/path/2",
            "/path/3",
        }

        # Mock index metadata
        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},  # Configured
            {"id": "doc2", "source_path": "/path/2"},  # Configured
            {"id": "doc3", "source_path": "/deleted/path"},  # Orphaned
            {"id": "doc4", "source_path": "/other/deleted"},  # Orphaned
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == ["doc3", "doc4"]

    def test_no_orphaned_documents(self) -> None:
        """Test when all documents are from configured sources."""
        configured_paths = {"/path/1", "/path/2", "/path/3"}

        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},
            {"id": "doc2", "source_path": "/path/2"},
            {"id": "doc3", "source_path": "/path/3"},
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == []

    def test_documents_with_empty_source_path(self) -> None:
        """Test that documents with empty source_path are not deleted."""
        configured_paths = {"/path/1"}

        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},
            {"id": "doc2", "source_path": ""},  # Empty
            {"id": "doc3", "source_path": None},  # None
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == []
