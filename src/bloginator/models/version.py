"""Version management models for draft tracking and history."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from bloginator.models.draft import Draft


class DraftVersion(BaseModel):
    """A single version of a draft document.

    Attributes:
        version_number: Sequential version number (1, 2, 3, ...)
        draft: The draft content at this version
        timestamp: When this version was created
        change_description: Human-readable description of changes
        refinement_feedback: Optional user feedback that led to this version
        parent_version: Version number this was derived from (None for v1)
    """

    version_number: int = Field(ge=1)
    draft: Draft
    timestamp: datetime = Field(default_factory=datetime.now)
    change_description: str = ""
    refinement_feedback: str = ""
    parent_version: Optional[int] = Field(default=None, ge=1)

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class VersionHistory(BaseModel):
    """Complete version history for a draft document.

    Attributes:
        draft_id: Unique identifier for this draft lineage
        versions: List of all versions in chronological order
        current_version: The active version number
        storage_path: Optional path where versions are persisted
    """

    draft_id: str
    versions: list[DraftVersion] = Field(default_factory=list)
    current_version: int = Field(default=0, ge=0)
    storage_path: Optional[Path] = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def add_version(
        self,
        draft: Draft,
        change_description: str = "",
        refinement_feedback: str = "",
    ) -> DraftVersion:
        """Add a new version to history.

        Args:
            draft: The new draft version
            change_description: Description of what changed
            refinement_feedback: User feedback that triggered this version

        Returns:
            The newly created DraftVersion
        """
        version_number = len(self.versions) + 1
        parent_version = self.current_version if self.current_version > 0 else None

        version = DraftVersion(
            version_number=version_number,
            draft=draft,
            change_description=change_description,
            refinement_feedback=refinement_feedback,
            parent_version=parent_version,
        )

        self.versions.append(version)
        self.current_version = version_number

        return version

    def get_version(self, version_number: int) -> Optional[DraftVersion]:
        """Get a specific version by number.

        Args:
            version_number: Version to retrieve (1-indexed)

        Returns:
            The requested version or None if not found
        """
        if version_number < 1 or version_number > len(self.versions):
            return None

        return self.versions[version_number - 1]

    def get_current(self) -> Optional[DraftVersion]:
        """Get the current active version.

        Returns:
            The current version or None if no versions exist
        """
        if self.current_version == 0:
            return None

        return self.get_version(self.current_version)

    def revert_to(self, version_number: int) -> bool:
        """Revert to a previous version.

        This makes the specified version the current one without deleting history.

        Args:
            version_number: Version to revert to

        Returns:
            True if revert succeeded, False if version not found
        """
        if version_number < 1 or version_number > len(self.versions):
            return False

        self.current_version = version_number
        return True

    def get_version_chain(self, version_number: int) -> list[DraftVersion]:
        """Get the ancestry chain for a version.

        Args:
            version_number: Version to trace back from

        Returns:
            List of versions from v1 to specified version
        """
        version = self.get_version(version_number)
        if not version:
            return []

        chain: list[DraftVersion] = [version]
        current = version

        # Walk back through parent versions
        while current.parent_version is not None:
            parent = self.get_version(current.parent_version)
            if parent:
                chain.insert(0, parent)
                current = parent
            else:
                break

        return chain

    def get_stats(self) -> dict[str, int]:
        """Get statistics about version history.

        Returns:
            Dictionary with version count and current version
        """
        return {
            "total_versions": len(self.versions),
            "current_version": self.current_version,
        }
