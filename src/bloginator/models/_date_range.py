"""Date range model for corpus sources.

Handles parsing and validation of date ranges in YYYY-MM-DD format.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class DateRange(BaseModel):
    """Date range for corpus source content.

    Attributes:
        start: Start date (inclusive)
        end: End date (inclusive)
    """

    start: datetime | None = None
    end: datetime | None = None

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_date(cls, v: Any) -> datetime | None:
        """Parse date from string (YYYY-MM-DD format).

        Args:
            v: Date value (string, datetime, or None)

        Returns:
            Parsed datetime or None

        Raises:
            ValueError: If date format is invalid
        """
        if v is None or isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD.") from e
        raise ValueError(f"Invalid date type: {type(v)}")
