"""Version management for draft documents."""

import difflib
import json
from pathlib import Path

from bloginator.models.draft import Draft
from bloginator.models.version import DraftVersion, VersionHistory


class VersionManager:
    """Manages version control for draft documents.

    Handles:
    - Saving and loading version history
    - Computing diffs between versions
    - Reverting to previous versions
    - Persisting versions to disk

    Attributes:
        storage_dir: Directory where version histories are stored
    """

    def __init__(self, storage_dir: Path):
        """Initialize version manager.

        Args:
            storage_dir: Directory for storing version histories
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_history_path(self, draft_id: str) -> Path:
        """Get the file path for a draft's version history.

        Args:
            draft_id: Unique draft identifier

        Returns:
            Path to the version history JSON file
        """
        return self.storage_dir / f"{draft_id}_history.json"

    def create_history(self, draft_id: str, initial_draft: Draft) -> VersionHistory:
        """Create a new version history for a draft.

        Args:
            draft_id: Unique identifier for this draft lineage
            initial_draft: The first version of the draft

        Returns:
            Newly created VersionHistory with v1
        """
        history = VersionHistory(
            draft_id=draft_id,
            storage_path=self._get_history_path(draft_id),
        )

        history.add_version(
            draft=initial_draft,
            change_description="Initial draft generated",
        )

        self.save_history(history)
        return history

    def load_history(self, draft_id: str) -> VersionHistory | None:
        """Load version history from disk.

        Args:
            draft_id: Draft identifier

        Returns:
            VersionHistory if found, None otherwise
        """
        history_path = self._get_history_path(draft_id)

        if not history_path.exists():
            return None

        try:
            with history_path.open() as f:
                data = json.load(f)

            history = VersionHistory(**data)
            history.storage_path = history_path
            return history

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to load version history: {e}")

    def save_history(self, history: VersionHistory) -> None:
        """Save version history to disk.

        Args:
            history: The version history to save
        """
        if history.storage_path is None:
            history.storage_path = self._get_history_path(history.draft_id)

        with history.storage_path.open("w") as f:
            json.dump(
                history.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )

    def add_version(
        self,
        history: VersionHistory,
        draft: Draft,
        change_description: str = "",
        refinement_feedback: str = "",
    ) -> DraftVersion:
        """Add a new version to history and save.

        Args:
            history: The version history to update
            draft: New draft version
            change_description: What changed
            refinement_feedback: User feedback that triggered this

        Returns:
            The newly created version
        """
        version = history.add_version(
            draft=draft,
            change_description=change_description,
            refinement_feedback=refinement_feedback,
        )

        self.save_history(history)
        return version

    def compute_diff(
        self,
        version1: DraftVersion,
        version2: DraftVersion,
        context_lines: int = 3,
    ) -> str:
        """Compute unified diff between two versions.

        Args:
            version1: Earlier version
            version2: Later version
            context_lines: Number of context lines in diff

        Returns:
            Unified diff string
        """
        # Convert drafts to markdown for diffing
        text1 = version1.draft.to_markdown().splitlines(keepends=True)
        text2 = version2.draft.to_markdown().splitlines(keepends=True)

        diff = difflib.unified_diff(
            text1,
            text2,
            fromfile=f"v{version1.version_number}",
            tofile=f"v{version2.version_number}",
            n=context_lines,
        )

        return "".join(diff)

    def compute_diff_stats(
        self,
        version1: DraftVersion,
        version2: DraftVersion,
    ) -> dict[str, int]:
        """Compute diff statistics between versions.

        Args:
            version1: Earlier version
            version2: Later version

        Returns:
            Dictionary with additions, deletions, and changes counts
        """
        text1 = version1.draft.to_markdown().splitlines()
        text2 = version2.draft.to_markdown().splitlines()

        diff = list(difflib.unified_diff(text1, text2, lineterm=""))

        additions = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        deletions = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
        }

    def revert(self, history: VersionHistory, version_number: int) -> bool:
        """Revert to a previous version and save.

        Args:
            history: The version history to update
            version_number: Version to revert to

        Returns:
            True if successful, False otherwise
        """
        if history.revert_to(version_number):
            self.save_history(history)
            return True

        return False

    def get_version_summary(self, version: DraftVersion) -> dict[str, any]:
        """Get a summary of a version for display.

        Args:
            version: The version to summarize

        Returns:
            Dictionary with version metadata
        """
        return {
            "version": version.version_number,
            "timestamp": version.timestamp.isoformat(),
            "description": version.change_description,
            "feedback": version.refinement_feedback,
            "parent_version": version.parent_version,
            "word_count": version.draft.total_words,
            "section_count": len(version.draft.sections),
            "voice_score": version.draft.voice_score,
        }

    def list_versions(self, history: VersionHistory) -> list[dict[str, any]]:
        """Get summaries of all versions.

        Args:
            history: The version history

        Returns:
            List of version summaries
        """
        return [self.get_version_summary(v) for v in history.versions]

    def delete_history(self, draft_id: str) -> bool:
        """Delete a version history from disk.

        Args:
            draft_id: Draft identifier

        Returns:
            True if deleted, False if not found
        """
        history_path = self._get_history_path(draft_id)

        if history_path.exists():
            history_path.unlink()
            return True

        return False
