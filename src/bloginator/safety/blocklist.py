"""Blocklist manager for validating content against proprietary terms."""

import json
from pathlib import Path
from typing import Any

from bloginator.models.blocklist import BlocklistEntry


class BlocklistManager:
    """Manages blocklist entries and validates text against them.

    The BlocklistManager loads/saves blocklist entries from a JSON file
    and provides validation services to check if text contains any
    blocked terms or patterns.

    Attributes:
        blocklist_file: Path to the JSON file storing blocklist entries
        entries: List of currently loaded blocklist entries

    Example:
        >>> manager = BlocklistManager(Path(".bloginator/blocklist.json"))
        >>> entry = BlocklistEntry(
        ...     id="1",
        ...     pattern="Acme Corp",
        ...     pattern_type=BlocklistPatternType.EXACT,
        ...     category=BlocklistCategory.COMPANY_NAME
        ... )
        >>> manager.add_entry(entry)
        >>> result = manager.validate_text("I worked at Acme Corp")
        >>> result['is_valid']
        False
        >>> len(result['violations'])
        1
    """

    def __init__(self, blocklist_file: Path):
        """Initialize blocklist manager.

        Args:
            blocklist_file: Path to JSON file for storing blocklist entries.
                           Will be created if it doesn't exist.
        """
        self.blocklist_file = blocklist_file
        self.entries: list[BlocklistEntry] = []
        self.load()

    def load(self) -> None:
        """Load blocklist from JSON file.

        If the file doesn't exist, initializes with an empty blocklist.
        Invalid entries in the file are skipped with a warning.
        """
        if self.blocklist_file.exists():
            try:
                data = json.loads(self.blocklist_file.read_text())
                self.entries = []

                for entry_data in data:
                    try:
                        entry = BlocklistEntry(**entry_data)
                        self.entries.append(entry)
                    except Exception:
                        # Skip invalid entries
                        pass

            except json.JSONDecodeError:
                # Invalid JSON, start with empty list
                self.entries = []
        else:
            self.entries = []

    def save(self) -> None:
        """Save blocklist to JSON file.

        Creates parent directories if they don't exist.
        Serializes entries to JSON with pretty formatting.
        """
        # Create parent directory if needed
        self.blocklist_file.parent.mkdir(parents=True, exist_ok=True)

        # Serialize entries
        data = [e.model_dump() for e in self.entries]

        # Write to file with formatting
        self.blocklist_file.write_text(json.dumps(data, indent=2, default=str))

    def add_entry(self, entry: BlocklistEntry) -> None:
        """Add entry to blocklist and persist.

        Args:
            entry: BlocklistEntry to add

        Note:
            Automatically saves the blocklist after adding the entry.
        """
        self.entries.append(entry)
        self.save()

    def remove_entry(self, entry_id: str) -> bool:
        """Remove entry by ID and persist.

        Args:
            entry_id: ID of the entry to remove

        Returns:
            True if entry was found and removed, False otherwise

        Note:
            Automatically saves the blocklist after removing the entry.
        """
        original_length = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]

        removed = len(self.entries) < original_length

        if removed:
            self.save()

        return removed

    def validate_text(self, text: str) -> dict[str, Any]:
        """Check text for blocklist violations.

        Args:
            text: Text content to validate against blocklist

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,  # True if no violations found
                "violations": [
                    {
                        "entry_id": str,    # ID of the blocklist entry
                        "pattern": str,     # The pattern that matched
                        "matches": list,    # List of actual matched strings
                        "category": str,    # Category of the entry
                        "notes": str,       # Notes explaining why blocked
                    },
                    ...
                ]
            }

        Example:
            >>> manager = BlocklistManager(Path("blocklist.json"))
            >>> result = manager.validate_text("Some clean text")
            >>> result['is_valid']
            True
            >>> result['violations']
            []

            >>> result = manager.validate_text("Text with Acme Corp")
            >>> result['is_valid']
            False
            >>> result['violations'][0]['pattern']
            'Acme Corp'
        """
        violations = []

        for entry in self.entries:
            matches = entry.matches(text)
            if matches:
                violations.append(
                    {
                        "entry_id": entry.id,
                        "pattern": entry.pattern,
                        "matches": matches,
                        "category": entry.category,
                        "notes": entry.notes,
                    }
                )

        return {"violations": violations, "is_valid": len(violations) == 0}

    def get_entries_by_category(self, category: str) -> list[BlocklistEntry]:
        """Get all entries of a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of entries matching the category
        """
        return [e for e in self.entries if e.category == category]

    def get_entry_count(self) -> int:
        """Get total number of blocklist entries.

        Returns:
            Number of entries in the blocklist
        """
        return len(self.entries)
