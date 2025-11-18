"""Generation history tracking models."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class GenerationType(str, Enum):
    """Type of generation."""

    OUTLINE = "outline"
    DRAFT = "draft"


class GenerationHistoryEntry(BaseModel):
    """Single generation history entry.

    Attributes:
        id: Unique identifier for this entry
        timestamp: When the generation completed
        generation_type: Type of generation (outline/draft)
        title: Document title
        classification: Content classification
        audience: Target audience
        input_params: Input parameters used for generation
        output_path: Path to generated file
        output_format: Format of output (markdown, pdf, etc.)
        metadata: Additional metadata (chunks, LLM model, etc.)
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    generation_type: GenerationType = Field(..., description="Type of generation")
    title: str = Field(..., description="Document title")
    classification: str = Field(default="guidance")
    audience: str = Field(default="all-disciplines")
    input_params: dict = Field(default_factory=dict)
    output_path: str = Field(..., description="Path to output file")
    output_format: str = Field(default="markdown")
    metadata: dict = Field(default_factory=dict)

    def __repr__(self) -> str:
        """String representation."""
        return f"GenerationHistoryEntry(type={self.generation_type}, title={self.title}, timestamp={self.timestamp})"


class GenerationHistory(BaseModel):
    """Complete generation history.

    Attributes:
        entries: List of history entries
    """

    entries: list[GenerationHistoryEntry] = Field(default_factory=list)

    def add_entry(self, entry: GenerationHistoryEntry) -> None:
        """Add entry to history.

        Args:
            entry: Entry to add
        """
        self.entries.append(entry)

    def get_entry(self, entry_id: str) -> GenerationHistoryEntry | None:
        """Get entry by ID.

        Args:
            entry_id: Entry ID to find

        Returns:
            Entry if found, None otherwise
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None

    def delete_entry(self, entry_id: str) -> bool:
        """Delete entry by ID.

        Args:
            entry_id: Entry ID to delete

        Returns:
            True if deleted, False if not found
        """
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                self.entries.pop(i)
                return True
        return False

    def filter_by_type(self, generation_type: GenerationType) -> list[GenerationHistoryEntry]:
        """Filter entries by generation type.

        Args:
            generation_type: Type to filter by

        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.generation_type == generation_type]

    def filter_by_classification(self, classification: str) -> list[GenerationHistoryEntry]:
        """Filter entries by classification.

        Args:
            classification: Classification to filter by

        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.classification == classification]

    def filter_by_audience(self, audience: str) -> list[GenerationHistoryEntry]:
        """Filter entries by audience.

        Args:
            audience: Audience to filter by

        Returns:
            List of matching entries
        """
        return [e for e in self.entries if e.audience == audience]

    def get_recent(self, limit: int = 10) -> list[GenerationHistoryEntry]:
        """Get most recent entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent entries sorted by timestamp (newest first)
        """
        sorted_entries = sorted(self.entries, key=lambda e: e.timestamp, reverse=True)
        return sorted_entries[:limit]
