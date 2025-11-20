"""Blocklist data models for preventing proprietary content leakage."""

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class BlocklistPatternType(str, Enum):
    """Type of pattern matching to use."""

    EXACT = "exact"
    REGEX = "regex"
    CASE_INSENSITIVE = "case_insensitive"


class BlocklistCategory(str, Enum):
    """Category of blocklist entry for organization."""

    COMPANY_NAME = "company_name"
    PRODUCT_NAME = "product_name"
    PROJECT_CODENAME = "project"
    METHODOLOGY = "methodology"
    PERSON_NAME = "person"
    OTHER = "other"


class BlocklistEntry(BaseModel):
    """A blocklist entry representing a term or pattern to prevent from appearing in generated content.

    Attributes:
        id: Unique identifier for this entry
        pattern: The term or regex pattern to block
        pattern_type: How to match the pattern (exact, regex, case_insensitive)
        category: Category for organization purposes
        added_date: When this entry was added
        notes: Explanation of why this is blocked
    """

    id: str = Field(..., description="Unique entry ID")
    pattern: str = Field(..., description="Term or regex pattern to block")
    pattern_type: BlocklistPatternType = BlocklistPatternType.EXACT
    category: BlocklistCategory = BlocklistCategory.OTHER
    added_date: datetime = Field(default_factory=datetime.now)
    notes: str = Field(default="", description="Why this is blocked")

    def matches(self, text: str) -> list[str]:
        r"""Check if pattern appears in text.

        Args:
            text: Text to search for pattern matches

        Returns:
            List of actual matched strings found in the text.
            Empty list if no matches.

        Examples:
            >>> entry = BlocklistEntry(
            ...     id="1",
            ...     pattern="Acme Corp",
            ...     pattern_type=BlocklistPatternType.EXACT
            ... )
            >>> entry.matches("I worked at Acme Corp")
            ['Acme Corp']
            >>> entry.matches("I worked at acme corp")
            []

            >>> entry2 = BlocklistEntry(
            ...     id="2",
            ...     pattern="Acme",
            ...     pattern_type=BlocklistPatternType.CASE_INSENSITIVE
            ... )
            >>> entry2.matches("ACME and acme")
            ['ACME', 'acme']

            >>> entry3 = BlocklistEntry(
            ...     id="3",
            ...     pattern=r"Project \\w+",
            ...     pattern_type=BlocklistPatternType.REGEX
            ... )
            >>> entry3.matches("Project Falcon was secret")
            ['Project Falcon']
        """
        if self.pattern_type == BlocklistPatternType.EXACT:
            # Exact match - case-sensitive substring search
            if self.pattern in text:
                return [self.pattern]
            return []

        elif self.pattern_type == BlocklistPatternType.CASE_INSENSITIVE:
            # Case-insensitive matching - find all occurrences
            matches = re.findall(re.escape(self.pattern), text, re.IGNORECASE)
            return matches

        elif self.pattern_type == BlocklistPatternType.REGEX:
            # Regex matching
            try:
                matches = re.findall(self.pattern, text)
                return matches if matches else []
            except re.error:
                # Invalid regex pattern
                return []

        return []
