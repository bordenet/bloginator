"""Search helper functions and utilities."""

from datetime import datetime
from typing import Any


def build_where_filter(
    quality_filter: str | None, format_filter: str | None
) -> dict[str, Any] | None:
    """Build ChromaDB where filter from parameters.

    Args:
        quality_filter: Quality rating filter
        format_filter: Document format filter

    Returns:
        Where filter dictionary or None
    """
    where: dict[str, Any] = {}

    if quality_filter:
        where["quality_rating"] = quality_filter

    if format_filter:
        where["format"] = format_filter

    return where if where else None


def matches_tags(metadata: dict[str, Any], tags_filter: list[str]) -> bool:
    """Check if metadata matches any of the tag filters.

    Args:
        metadata: Chunk metadata
        tags_filter: List of tags to match

    Returns:
        True if any tag matches
    """
    tags_str = metadata.get("tags", "")
    if not tags_str:
        return False

    doc_tags = [t.strip().lower() for t in tags_str.split(",")]
    filter_tags = [t.strip().lower() for t in tags_filter]

    return any(tag in doc_tags for tag in filter_tags)


def calculate_recency_score(metadata: dict[str, Any], now: datetime) -> float:
    """Calculate recency score based on document date.

    Uses exponential decay: more recent = higher score.
    - Today: 1.0
    - 1 year ago: ~0.5
    - 5 years ago: ~0.1

    Args:
        metadata: Chunk metadata containing dates
        now: Current datetime

    Returns:
        Recency score between 0.0 and 1.0
    """
    created_date_str = metadata.get("created_date", "")

    if not created_date_str:
        # No date available, use neutral score
        return 0.5

    try:
        created_date = datetime.fromisoformat(created_date_str)
        days_old = (now - created_date).days

        # Exponential decay: 1.0 / (1.0 + days_old / 365.0)
        # This gives roughly 0.5 for 1 year old, 0.1 for 9 years old
        recency_score = 1.0 / (1.0 + days_old / 365.0)

        return max(0.0, min(1.0, recency_score))  # Clamp to [0, 1]
    except (ValueError, AttributeError):
        return 0.5  # Invalid date, use neutral score


def calculate_quality_score(metadata: dict[str, Any]) -> float:
    """Calculate quality score based on quality rating.

    Args:
        metadata: Chunk metadata containing quality_rating

    Returns:
        Quality score between 0.0 and 1.0
    """
    quality_ratings = {
        "preferred": 1.0,
        "standard": 0.5,
        "deprecated": 0.1,
    }

    quality_rating = metadata.get("quality_rating", "standard")
    return quality_ratings.get(quality_rating, 0.5)
