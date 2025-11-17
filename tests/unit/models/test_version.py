"""Tests for version management models."""

from datetime import datetime

import pytest

from bloginator.models.draft import Draft
from bloginator.models.version import DraftVersion, VersionHistory


class TestDraftVersion:
    """Tests for DraftVersion model."""

    def test_create_basic_version(self):
        """Test creating a basic draft version."""
        draft = Draft(title="Test", keywords=["test"])

        version = DraftVersion(
            version_number=1,
            draft=draft,
        )

        assert version.version_number == 1
        assert version.draft == draft
        assert isinstance(version.timestamp, datetime)
        assert version.change_description == ""
        assert version.refinement_feedback == ""
        assert version.parent_version is None

    def test_create_version_with_metadata(self):
        """Test version with full metadata."""
        draft = Draft(title="Test", keywords=["test"])

        version = DraftVersion(
            version_number=2,
            draft=draft,
            change_description="Refined introduction",
            refinement_feedback="Make it more engaging",
            parent_version=1,
        )

        assert version.version_number == 2
        assert version.change_description == "Refined introduction"
        assert version.refinement_feedback == "Make it more engaging"
        assert version.parent_version == 1

    def test_version_number_validation(self):
        """Test version number must be >= 1."""
        draft = Draft(title="Test", keywords=[])

        # Valid
        version = DraftVersion(version_number=1, draft=draft)
        assert version.version_number == 1

        # Invalid: 0
        with pytest.raises(ValueError):
            DraftVersion(version_number=0, draft=draft)

        # Invalid: negative
        with pytest.raises(ValueError):
            DraftVersion(version_number=-1, draft=draft)

    def test_parent_version_validation(self):
        """Test parent version must be >= 1 if provided."""
        draft = Draft(title="Test", keywords=[])

        # Valid: None
        v1 = DraftVersion(version_number=1, draft=draft, parent_version=None)
        assert v1.parent_version is None

        # Valid: positive
        v2 = DraftVersion(version_number=2, draft=draft, parent_version=1)
        assert v2.parent_version == 1

        # Invalid: 0
        with pytest.raises(ValueError):
            DraftVersion(version_number=2, draft=draft, parent_version=0)

        # Invalid: negative
        with pytest.raises(ValueError):
            DraftVersion(version_number=2, draft=draft, parent_version=-1)


class TestVersionHistory:
    """Tests for VersionHistory model."""

    def test_create_empty_history(self):
        """Test creating empty version history."""
        history = VersionHistory(draft_id="test-draft")

        assert history.draft_id == "test-draft"
        assert history.versions == []
        assert history.current_version == 0
        assert history.storage_path is None

    def test_add_first_version(self):
        """Test adding the first version."""
        history = VersionHistory(draft_id="test")
        draft = Draft(title="Test", keywords=["test"])

        version = history.add_version(draft, change_description="Initial draft")

        assert len(history.versions) == 1
        assert history.current_version == 1
        assert version.version_number == 1
        assert version.draft == draft
        assert version.parent_version is None
        assert version.change_description == "Initial draft"

    def test_add_multiple_versions(self):
        """Test adding multiple versions."""
        history = VersionHistory(draft_id="test")

        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])
        draft3 = Draft(title="v3", keywords=[])

        v1 = history.add_version(draft1, "Version 1")
        v2 = history.add_version(draft2, "Version 2", "Add detail")
        v3 = history.add_version(draft3, "Version 3", "Fix tone")

        assert len(history.versions) == 3
        assert history.current_version == 3

        assert v1.version_number == 1
        assert v1.parent_version is None

        assert v2.version_number == 2
        assert v2.parent_version == 1
        assert v2.refinement_feedback == "Add detail"

        assert v3.version_number == 3
        assert v3.parent_version == 2
        assert v3.refinement_feedback == "Fix tone"

    def test_get_version_by_number(self):
        """Test retrieving specific version."""
        history = VersionHistory(draft_id="test")

        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])

        history.add_version(draft1)
        history.add_version(draft2)

        # Valid versions
        v1 = history.get_version(1)
        assert v1 is not None
        assert v1.draft.title == "v1"

        v2 = history.get_version(2)
        assert v2 is not None
        assert v2.draft.title == "v2"

        # Invalid versions
        assert history.get_version(0) is None
        assert history.get_version(3) is None
        assert history.get_version(-1) is None

    def test_get_current_version(self):
        """Test getting current active version."""
        history = VersionHistory(draft_id="test")

        # No versions yet
        assert history.get_current() is None

        # Add versions
        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])

        history.add_version(draft1)
        assert history.get_current().version_number == 1

        history.add_version(draft2)
        assert history.get_current().version_number == 2

    def test_revert_to_previous_version(self):
        """Test reverting to earlier version."""
        history = VersionHistory(draft_id="test")

        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])
        draft3 = Draft(title="v3", keywords=[])

        history.add_version(draft1)
        history.add_version(draft2)
        history.add_version(draft3)

        assert history.current_version == 3

        # Revert to v1
        success = history.revert_to(1)
        assert success is True
        assert history.current_version == 1
        assert history.get_current().draft.title == "v1"

        # Versions still exist
        assert len(history.versions) == 3

    def test_revert_to_invalid_version(self):
        """Test reverting to invalid version."""
        history = VersionHistory(draft_id="test")

        draft = Draft(title="v1", keywords=[])
        history.add_version(draft)

        # Try invalid versions
        assert history.revert_to(0) is False
        assert history.revert_to(2) is False
        assert history.revert_to(-1) is False

        # Current version unchanged
        assert history.current_version == 1

    def test_get_version_chain(self):
        """Test getting version ancestry chain."""
        history = VersionHistory(draft_id="test")

        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])
        draft3 = Draft(title="v3", keywords=[])

        history.add_version(draft1)
        history.add_version(draft2)
        history.add_version(draft3)

        # Get chain for v3
        chain = history.get_version_chain(3)

        assert len(chain) == 3
        assert chain[0].version_number == 1
        assert chain[1].version_number == 2
        assert chain[2].version_number == 3

        # Get chain for v1
        chain = history.get_version_chain(1)
        assert len(chain) == 1
        assert chain[0].version_number == 1

        # Invalid version
        chain = history.get_version_chain(99)
        assert chain == []

    def test_get_stats(self):
        """Test version history statistics."""
        history = VersionHistory(draft_id="test")

        # Empty history
        stats = history.get_stats()
        assert stats["total_versions"] == 0
        assert stats["current_version"] == 0

        # Add versions
        draft1 = Draft(title="v1", keywords=[])
        draft2 = Draft(title="v2", keywords=[])

        history.add_version(draft1)
        history.add_version(draft2)

        stats = history.get_stats()
        assert stats["total_versions"] == 2
        assert stats["current_version"] == 2

        # After revert
        history.revert_to(1)
        stats = history.get_stats()
        assert stats["total_versions"] == 2
        assert stats["current_version"] == 1
