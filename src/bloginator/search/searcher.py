"""Semantic search and retrieval for document corpus."""

import logging
from pathlib import Path
from typing import Any, cast

import chromadb

from bloginator.search._embedding import _get_embedding_model
from bloginator.search._search_helpers import build_where_filter, convert_chromadb_results
from bloginator.search._search_result import SearchResult
from bloginator.search._weighted_search import (
    apply_combined_weights,
    apply_hybrid_scores,
    apply_quality_weights,
    apply_recency_weights,
)
from bloginator.search.bm25 import BM25Index


logger = logging.getLogger(__name__)

# Re-export SearchResult for backward compatibility
__all__ = ["CorpusSearcher", "SearchResult"]


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

        # Initialize embedding model (uses cache to avoid reloading)
        self.embedding_model = _get_embedding_model(embedding_model_name)

        # BM25 index for hybrid search (built lazily)
        self._bm25_index: BM25Index | None = None

    def search(
        self,
        query: str,
        n_results: int = 10,
        quality_filter: str | None = None,
        tags_filter: list[str] | None = None,
        format_filter: str | None = None,
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
        where = build_where_filter(quality_filter, format_filter)

        # Query ChromaDB
        raw_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where if where else None,
        )
        results = cast("dict[str, Any]", raw_results)

        return convert_chromadb_results(results, 0, tags_filter, n_results)

    def batch_search(
        self,
        queries: list[str],
        n_results: int = 10,
        quality_filter: str | None = None,
        tags_filter: list[str] | None = None,
        format_filter: str | None = None,
    ) -> list[list[SearchResult]]:
        """Search corpus with multiple queries in a single batch.

        This is more efficient than calling search() multiple times because
        it encodes all queries at once and makes a single ChromaDB query.

        Args:
            queries: List of natural language search queries
            n_results: Number of results to return per query
            quality_filter: Filter by quality rating (preferred, standard, deprecated)
            tags_filter: Filter by tags (any match)
            format_filter: Filter by document format (pdf, docx, markdown, txt)

        Returns:
            List of search result lists, one per query in original order

        Example:
            >>> searcher = CorpusSearcher(index_dir)
            >>> queries = ["leadership", "code review", "testing"]
            >>> results = searcher.batch_search(queries, n_results=5)
            >>> for query, query_results in zip(queries, results):
            ...     print(f"{query}: {len(query_results)} results")
        """
        if not queries:
            return []

        # Generate all query embeddings at once (much faster than one-by-one)
        query_embeddings = self.embedding_model.encode(queries)

        # Build metadata filter
        where = build_where_filter(quality_filter, format_filter)

        # Query ChromaDB with all embeddings at once
        raw_results = self.collection.query(
            query_embeddings=[emb.tolist() for emb in query_embeddings],
            n_results=n_results,
            where=where if where else None,
        )
        results = cast("dict[str, Any]", raw_results)

        # Convert to SearchResult objects for each query
        return [
            convert_chromadb_results(results, idx, tags_filter, n_results)
            for idx in range(len(queries))
        ]

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
        results = self.search(query, n_results=n_results * 3, **kwargs)
        return apply_recency_weights(results, recency_weight, n_results)

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
        results = self.search(query, n_results=n_results * 3, **kwargs)
        return apply_quality_weights(results, quality_weight, n_results)

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
        results = self.search(query, n_results=n_results * 3, **kwargs)
        return apply_combined_weights(results, recency_weight, quality_weight, n_results)

    def build_bm25_index(self) -> None:
        """Build BM25 index from ChromaDB collection for hybrid search.

        This loads all documents from ChromaDB and builds a BM25 lexical index.
        Call this once before using hybrid_search for best performance.
        """
        # Get all documents from collection
        all_data = self.collection.get()

        documents = []
        if all_data["ids"]:
            for i, chunk_id in enumerate(all_data["ids"]):
                documents.append(
                    {
                        "id": chunk_id,
                        "content": all_data["documents"][i] if all_data["documents"] else "",
                    }
                )

        self._bm25_index = BM25Index()
        self._bm25_index.build(documents)
        logger.info(f"Built BM25 index with {len(documents)} documents")

    def hybrid_search(
        self,
        query: str,
        n_results: int = 10,
        semantic_weight: float = 0.7,
        bm25_weight: float = 0.3,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Search using hybrid of semantic similarity and BM25 keyword matching.

        Combines dense vector similarity with sparse lexical matching for
        improved retrieval on keyword-specific queries.

        Args:
            query: Natural language search query
            n_results: Number of results to return
            semantic_weight: Weight for semantic similarity (0.0-1.0)
            bm25_weight: Weight for BM25 lexical score (0.0-1.0)
            **kwargs: Additional arguments passed to search()

        Returns:
            List of SearchResult objects sorted by hybrid score

        Note:
            If BM25 index is not built, falls back to semantic-only search.
            Call build_bm25_index() first for best hybrid performance.
        """
        semantic_results = self.search(query, n_results=n_results * 3, **kwargs)

        # If no BM25 index, fall back to semantic only
        if self._bm25_index is None:
            logger.debug("No BM25 index available, using semantic search only")
            for result in semantic_results:
                result.hybrid_score = result.similarity_score
            return semantic_results[:n_results]

        # Get BM25 results and normalize scores
        bm25_results = self._bm25_index.search(query, n_results=n_results * 3)
        bm25_scores = self._normalize_bm25_scores(bm25_results)

        return apply_hybrid_scores(
            semantic_results, bm25_scores, semantic_weight, bm25_weight, n_results
        )

    def _normalize_bm25_scores(self, bm25_results: list[dict[str, Any]]) -> dict[str, float]:
        """Normalize BM25 scores to 0-1 range.

        Args:
            bm25_results: Raw BM25 search results

        Returns:
            Dictionary of chunk_id -> normalized score
        """
        if not bm25_results:
            return {}

        max_score = max(r["score"] for r in bm25_results) or 1.0
        return {r["id"]: r["score"] / max_score for r in bm25_results}

    def get_stats(self) -> dict[str, Any]:
        """Get search index statistics.

        Returns:
            Dictionary with index statistics
        """
        stats = {
            "collection_name": self.collection_name,
            "total_chunks": self.collection.count(),
            "index_dir": str(self.index_dir),
        }
        if self._bm25_index is not None:
            stats["bm25_document_count"] = self._bm25_index.document_count
        return stats
