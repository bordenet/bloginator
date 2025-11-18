"""Generation history management service."""

import json
from pathlib import Path

from bloginator.models.history import GenerationHistory, GenerationHistoryEntry


class HistoryManager:
    """Manages generation history persistence and retrieval.

    History is stored as:
    - Index file: .bloginator/history/index.json
    - Individual entries: .bloginator/history/<id>.json
    """

    def __init__(self, history_dir: Path | None = None):
        """Initialize history manager.

        Args:
            history_dir: Directory for history storage (defaults to .bloginator/history/)
        """
        if history_dir is None:
            history_dir = Path.home() / ".bloginator" / "history"

        self.history_dir = Path(history_dir)
        self.index_file = self.history_dir / "index.json"

        # Ensure directory exists
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_entry(self, entry: GenerationHistoryEntry) -> None:
        """Save history entry.

        Args:
            entry: Entry to save
        """
        # Save individual entry file
        entry_file = self.history_dir / f"{entry.id}.json"
        entry_file.write_text(entry.model_dump_json(indent=2))

        # Update index
        history = self.load_history()
        # Remove existing entry with same ID (update case)
        history.delete_entry(entry.id)
        history.add_entry(entry)
        self._save_index(history)

    def load_entry(self, entry_id: str) -> GenerationHistoryEntry | None:
        """Load entry by ID.

        Args:
            entry_id: Entry ID to load

        Returns:
            Entry if found, None otherwise
        """
        entry_file = self.history_dir / f"{entry_id}.json"
        if not entry_file.exists():
            return None

        data = json.loads(entry_file.read_text())
        return GenerationHistoryEntry(**data)

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry by ID.

        Args:
            entry_id: Entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Remove from index
        history = self.load_history()
        if not history.delete_entry(entry_id):
            return False
        self._save_index(history)

        # Remove entry file
        entry_file = self.history_dir / f"{entry_id}.json"
        if entry_file.exists():
            entry_file.unlink()

        return True

    def load_history(self) -> GenerationHistory:
        """Load complete history from index.

        Returns:
            GenerationHistory instance
        """
        if not self.index_file.exists():
            return GenerationHistory()

        data = json.loads(self.index_file.read_text())
        return GenerationHistory(**data)

    def query(
        self,
        generation_type: str | None = None,
        classification: str | None = None,
        audience: str | None = None,
        limit: int | None = None,
    ) -> list[GenerationHistoryEntry]:
        """Query history with filters.

        Args:
            generation_type: Filter by type (outline/draft)
            classification: Filter by classification
            audience: Filter by audience
            limit: Maximum number of results

        Returns:
            List of matching entries
        """
        history = self.load_history()
        results = history.entries

        # Apply filters
        if generation_type:
            results = [e for e in results if e.generation_type == generation_type]
        if classification:
            results = [e for e in results if e.classification == classification]
        if audience:
            results = [e for e in results if e.audience == audience]

        # Sort by timestamp (newest first)
        results = sorted(results, key=lambda e: e.timestamp, reverse=True)

        # Apply limit
        if limit:
            results = results[:limit]

        return results

    def get_recent(self, limit: int = 10) -> list[GenerationHistoryEntry]:
        """Get recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent entries
        """
        history = self.load_history()
        return history.get_recent(limit)

    def _save_index(self, history: GenerationHistory) -> None:
        """Save index file.

        Args:
            history: History to save
        """
        self.index_file.write_text(history.model_dump_json(indent=2))

    def clear_all(self) -> int:
        """Clear all history entries.

        Returns:
            Number of entries cleared
        """
        history = self.load_history()
        count = len(history.entries)

        # Remove all entry files
        for entry in history.entries:
            entry_file = self.history_dir / f"{entry.id}.json"
            if entry_file.exists():
                entry_file.unlink()

        # Clear index
        self._save_index(GenerationHistory())

        return count
