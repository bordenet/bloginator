"""Tests for version manager."""

import json
import tempfile
from pathlib import Path

import pytest

from bloginator.generation.version_manager import VersionManager
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.version import VersionHistory


class TestVersionManager:
    """Tests for VersionManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for version storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def manager(self, temp_dir):
        """Create version manager with temp storage."""
        return VersionManager(storage_dir=temp_dir)

    def test_initialization(self, temp_dir):
        """Test manager initialization."""
        manager = VersionManager(storage_dir=temp_dir)

        assert manager.storage_dir == temp_dir
        assert temp_dir.exists()
        assert temp_dir.is_dir()

    def test_create_history(self, manager):
        """Test creating new version history."""
        draft = Draft(title="Test", keywords=["test"])

        history = manager.create_history("my-draft", draft)

        assert history.draft_id == "my-draft"
        assert len(history.versions) == 1
        assert history.current_version == 1
        assert history.versions[0].draft == draft

    def test_create_history_saves_to_disk(self, manager, temp_dir):
        """Test that create_history persists to disk."""
        draft = Draft(title="Test", keywords=["test"])

        history = manager.create_history("my-draft", draft)

        # Check file exists
        history_path = temp_dir / "my-draft_history.json"
        assert history_path.exists()

        # Verify content
        with open(history_path) as f:
            data = json.load(f)

        assert data["draft_id"] == "my-draft"
        assert len(data["versions"]) == 1

    def test_load_history(self, manager):
        """Test loading history from disk."""
        draft = Draft(title="Test", keywords=["test"])

        # Create and save
        original = manager.create_history("test-draft", draft)

        # Load back
        loaded = manager.load_history("test-draft")

        assert loaded is not None
        assert loaded.draft_id == original.draft_id
        assert len(loaded.versions) == len(original.versions)
        assert loaded.current_version == original.current_version

    def test_load_nonexistent_history(self, manager):
        """Test loading history that doesn't exist."""
        result = manager.load_history("does-not-exist")

        assert result is None

    def test_load_invalid_history(self, manager, temp_dir):
        """Test loading corrupted history file."""
        # Write invalid JSON
        bad_path = temp_dir / "bad_history.json"
        with open(bad_path, "w") as f:
            f.write("not valid json {")

        with pytest.raises(ValueError, match="Failed to load"):
            manager.load_history("bad")

    def test_save_history(self, manager, temp_dir):
        """Test saving history manually."""
        history = VersionHistory(draft_id="test")

        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])

        history.add_version(draft1)
        history.add_version(draft2)

        manager.save_history(history)

        # Verify saved
        saved_path = temp_dir / "test_history.json"
        assert saved_path.exists()

        with open(saved_path) as f:
            data = json.load(f)

        assert len(data["versions"]) == 2

    def test_add_version(self, manager):
        """Test adding version to history."""
        draft1 = Draft(title="v1", keywords=[])
        history = manager.create_history("test", draft1)

        draft2 = Draft(title="v2", keywords=[])
        version = manager.add_version(
            history,
            draft2,
            change_description="Added detail",
            refinement_feedback="More depth needed",
        )

        assert version.version_number == 2
        assert version.change_description == "Added detail"
        assert version.refinement_feedback == "More depth needed"

        # Should be saved automatically
        loaded = manager.load_history("test")
        assert len(loaded.versions) == 2

    def test_compute_diff_basic(self, manager):
        """Test computing diff between versions."""
        section1 = DraftSection(title="Intro", content="This is the introduction.")
        draft1 = Draft(title="Doc", keywords=[], sections=[section1])

        section2 = DraftSection(
            title="Intro",
            content="This is the improved introduction with more detail.",
        )
        draft2 = Draft(title="Doc", keywords=[], sections=[section2])

        history = manager.create_history("test", draft1)
        manager.add_version(history, draft2)

        v1 = history.get_version(1)
        v2 = history.get_version(2)

        diff = manager.compute_diff(v1, v2)

        # Should contain diff markers
        assert "---" in diff or "+++" in diff
        assert "introduction" in diff.lower()

    def test_compute_diff_no_changes(self, manager):
        """Test diff with identical versions."""
        draft = Draft(title="Test", keywords=[])

        history = manager.create_history("test", draft)
        manager.add_version(history, draft)

        v1 = history.get_version(1)
        v2 = history.get_version(2)

        diff = manager.compute_diff(v1, v2)

        # Should be minimal (just headers)
        assert diff == "" or len(diff.split("\n")) <= 3

    def test_compute_diff_stats(self, manager):
        """Test diff statistics."""
        section1 = DraftSection(
            title="Section",
            content="Line 1\nLine 2\nLine 3",
        )
        draft1 = Draft(title="Doc", keywords=[], sections=[section1])

        section2 = DraftSection(
            title="Section",
            content="Line 1\nNew Line 2\nLine 3\nLine 4",
        )
        draft2 = Draft(title="Doc", keywords=[], sections=[section2])

        history = manager.create_history("test", draft1)
        manager.add_version(history, draft2)

        v1 = history.get_version(1)
        v2 = history.get_version(2)

        stats = manager.compute_diff_stats(v1, v2)

        assert "additions" in stats
        assert "deletions" in stats
        assert "changes" in stats
        assert stats["changes"] > 0

    def test_revert(self, manager):
        """Test reverting to previous version."""
        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])
        draft3 = Draft(title="v3", keywords=[])

        history = manager.create_history("test", draft1)
        manager.add_version(history, draft2)
        manager.add_version(history, draft3)

        assert history.current_version == 3

        # Revert
        success = manager.revert(history, 1)

        assert success is True
        assert history.current_version == 1

        # Should be persisted
        loaded = manager.load_history("test")
        assert loaded.current_version == 1

    def test_revert_invalid(self, manager):
        """Test reverting to invalid version."""
        draft = Draft(title="v1", keywords=[])
        history = manager.create_history("test", draft)

        success = manager.revert(history, 99)

        assert success is False
        assert history.current_version == 1

    def test_get_version_summary(self, manager):
        """Test getting version summary."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[
                DraftSection(title="S1", content="Content with five total words")
            ],
        )
        draft.calculate_stats()

        history = manager.create_history("test", draft)
        version = history.get_version(1)

        summary = manager.get_version_summary(version)

        assert summary["version"] == 1
        assert "timestamp" in summary
        assert "description" in summary
        assert "word_count" in summary
        assert summary["section_count"] == 1

    def test_list_versions(self, manager):
        """Test listing all versions."""
        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])

        history = manager.create_history("test", draft1)
        manager.add_version(history, draft2, "Second version")

        summaries = manager.list_versions(history)

        assert len(summaries) == 2
        assert summaries[0]["version"] == 1
        assert summaries[1]["version"] == 2
        assert summaries[1]["description"] == "Second version"

    def test_delete_history(self, manager, temp_dir):
        """Test deleting version history."""
        draft = Draft(title="Test", keywords=[])
        manager.create_history("test", draft)

        # Verify exists
        history_path = temp_dir / "test_history.json"
        assert history_path.exists()

        # Delete
        success = manager.delete_history("test")

        assert success is True
        assert not history_path.exists()

    def test_delete_nonexistent_history(self, manager):
        """Test deleting history that doesn't exist."""
        success = manager.delete_history("does-not-exist")

        assert success is False

    def test_multiple_drafts(self, manager):
        """Test managing multiple draft histories."""
        draft1 = Draft(title="Draft 1", keywords=["a"])
        draft2 = Draft(title="Draft 2", keywords=["b"])

        history1 = manager.create_history("draft-1", draft1)
        history2 = manager.create_history("draft-2", draft2)

        # Both should be loadable
        loaded1 = manager.load_history("draft-1")
        loaded2 = manager.load_history("draft-2")

        assert loaded1.draft_id == "draft-1"
        assert loaded2.draft_id == "draft-2"
        assert loaded1.versions[0].draft.title == "Draft 1"
        assert loaded2.versions[0].draft.title == "Draft 2"

    def test_version_chain_tracking(self, manager):
        """Test that parent version tracking works correctly."""
        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])
        draft3 = Draft(title="v3", keywords=[])

        history = manager.create_history("test", draft1)
        manager.add_version(history, draft2)
        manager.add_version(history, draft3)

        # Reload and verify chain
        loaded = manager.load_history("test")
        chain = loaded.get_version_chain(3)

        assert len(chain) == 3
        assert chain[0].parent_version is None
        assert chain[1].parent_version == 1
        assert chain[2].parent_version == 2
