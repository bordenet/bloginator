"""Semantic search and retrieval for document corpus."""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer


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
        self.similarity_score = 1.0 - distance

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


class CorpusSearcher:
    """Semantic search with recency and quality weighting.

    Attributes:
        index_dir: Directory containing ChromaDB index
        collection_name: Name of ChromaDB collection
        client: ChromaDB client
        collection: ChromaDB collection
        embedding_model: Sentence transformer model
    """

    def __init__(
        self,
        index_dir: Path,
        collection_name: str = "bloginator_corpus",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        """Initialize corpus searcher.

        Args:
            index_dir: Directory containing ChromaDB index
            collection_name: Name of ChromaDB collection
            embedding_model_name: Sentence transformer model name

        Raises:
            ValueError: If index directory doesn't exist or collection not found
        """
        self.index_dir = index_dir
        self.collection_name = collection_name

        if not index_dir.exists():
            raise ValueError(f"Index directory not found: {index_dir}")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(index_dir))

        # Get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception as e:
            raise ValueError(f"Collection '{collection_name}' not found: {e}") from e

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def search(
        self,
        query: str,
        n_results: int = 10,
        quality_filter: Optional[str] = None,
        tags_filter: Optional[list[str]] = None,
        format_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """Search corpus with basic semantic similarity.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            quality_filter: Filter by quality rating (preferred, standard, deprecated)
            tags_filter: Filter by tags (any match)
            format_filter: Filter by document format (pdf, docx, markdown, txt)

        Returns:
            List of SearchResult objects sorted by similarity
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]

        # Build metadata filter
        where = self._build_where_filter(quality_filter, format_filter)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where if where else None,
        )

        # Convert to SearchResult objects
        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                result = SearchResult(
                    chunk_id=chunk_id,
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    distance=results["distances"][0][i],
                )

                # Filter by tags if specified
                if tags_filter and not self._matches_tags(result.metadata, tags_filter):
                    continue

                search_results.append(result)

        return search_results[:n_results]

    def _build_where_filter(
        self, quality_filter: Optional[str], format_filter: Optional[str]
    ) -> Optional[dict[str, Any]]:
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

    def _matches_tags(self, metadata: dict[str, Any], tags_filter: list[str]) -> bool:
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

    def search_with_recency(
        self,
        query: str,
        n_results: int = 10,
        recency_weight: float = 0.3,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search with recency weighting (prefer recent documents).

        Args:
            query: Natural language search query
            n_results: Number of results to return
            recency_weight: Weight for recency score (0.0-1.0)
            **kwargs: Additional arguments passed to search()

        Returns:
            List of SearchResult objects sorted by combined score
        """
        # Get more results than needed for re-ranking
        results = self.search(query, n_results=n_results * 3, **kwargs)

        # Calculate recency scores
        now = datetime.now()
        for result in results:
            result.recency_score = self._calculate_recency_score(result.metadata, now)

            # Combined score: (1 - recency_weight) * similarity + recency_weight * recency
            result.combined_score = (
                (1 - recency_weight) * result.similarity_score + recency_weight * result.recency_score
            )

        # Sort by combined score and return top n
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[:n_results]

    def search_with_quality(
        self,
        query: str,
        n_results: int = 10,
        quality_weight: float = 0.2,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search with quality weighting (prefer PREFERRED content).

        Args:
            query: Natural language search query
            n_results: Number of results to return
            quality_weight: Weight for quality score (0.0-1.0)
            **kwargs: Additional arguments passed to search()

        Returns:
            List of SearchResult objects sorted by combined score
        """
        # Get more results than needed for re-ranking
        results = self.search(query, n_results=n_results * 3, **kwargs)

        # Calculate quality scores
        for result in results:
            result.quality_score = self._calculate_quality_score(result.metadata)

            # Combined score: (1 - quality_weight) * similarity + quality_weight * quality
            result.combined_score = (
                (1 - quality_weight) * result.similarity_score + quality_weight * result.quality_score
            )

        # Sort by combined score and return top n
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[:n_results]

    def search_with_weights(
        self,
        query: str,
        n_results: int = 10,
        recency_weight: float = 0.2,
        quality_weight: float = 0.1,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search with combined similarity, recency, and quality weighting.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            recency_weight: Weight for recency score (0.0-1.0)
            quality_weight: Weight for quality score (0.0-1.0)
            **kwargs: Additional arguments passed to search()

        Returns:
            List of SearchResult objects sorted by combined score

        Note:
            Weights should sum to <= 1.0. Remaining weight goes to similarity.
            Example: recency=0.2, quality=0.1 means similarity gets 0.7 weight.
        """
        # Get more results than needed for re-ranking
        results = self.search(query, n_results=n_results * 3, **kwargs)

        now = datetime.now()

        # Calculate all scores
        for result in results:
            result.recency_score = self._calculate_recency_score(result.metadata, now)
            result.quality_score = self._calculate_quality_score(result.metadata)

            # Combined score: normalize weights to sum to 1.0
            similarity_weight = 1.0 - recency_weight - quality_weight
            result.combined_score = (
                similarity_weight * result.similarity_score
                + recency_weight * result.recency_score
                + quality_weight * result.quality_score
            )

        # Sort by combined score and return top n
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results[:n_results]

    def _calculate_recency_score(self, metadata: dict[str, Any], now: datetime) -> float:
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

    def _calculate_quality_score(self, metadata: dict[str, Any]) -> float:
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

    def get_stats(self) -> dict[str, Any]:
        """Get search index statistics.

        Returns:
            Dictionary with index statistics
        """
        return {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "index_dir": str(self.index_dir),
        }
