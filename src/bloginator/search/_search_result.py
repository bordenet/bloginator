"""Search result representation with scoring."""

from typing import Any


class SearchResult:
    """Encapsulates a search result with scoring information.

    Attributes:
        chunk_id: ID of the chunk
        content: Text content of the chunk
        metadata: Metadata dictionary
        distance: Cosine distance from query (lower = more similar)
        similarity_score: Similarity score (1 - distance, higher = more similar)
        recency_score: Recency score based on document date
        quality_score: Quality score based on rating
        combined_score: Final weighted score
    """

    def __init__(
        self,
        chunk_id: str,
        content: str,
        metadata: dict[str, Any],
        distance: float,
    ):
        """Initialize search result.

        Args:
            chunk_id: Chunk identifier
            content: Text content
            metadata: Metadata dictionary
            distance: Cosine distance from query
        """
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata
        self.distance = distance
        # Clamp similarity to [0.0, 1.0] to handle edge cases where distance > 1.0
        self.similarity_score = max(0.0, min(1.0, 1.0 - distance))

        # Initialize scoring attributes
        self.recency_score: float = 0.5
        self.quality_score: float = 0.5
        self.combined_score: float = self.similarity_score

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SearchResult(id={self.chunk_id[:8]}..., "
            f"score={self.combined_score:.3f}, "
            f"similarity={self.similarity_score:.3f})"
        )
