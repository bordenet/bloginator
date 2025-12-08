"""Semantic search and retrieval for document corpus."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import chromadb

from bloginator.search._embedding import _get_embedding_model
from bloginator.search._search_helpers import (
    build_where_filter,
    calculate_quality_score,
    calculate_recency_score,
    matches_tags,
)
from bloginator.search._search_result import SearchResult
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
                if tags_filter and not matches_tags(result.metadata, tags_filter):
                    continue

                search_results.append(result)

        return search_results[:n_results]

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
        all_search_results = []
        for query_idx in range(len(queries)):
            search_results = []
            if results["ids"] and query_idx < len(results["ids"]) and results["ids"][query_idx]:
                for i, chunk_id in enumerate(results["ids"][query_idx]):
                    result = SearchResult(
                        chunk_id=chunk_id,
                        content=results["documents"][query_idx][i],
                        metadata=results["metadatas"][query_idx][i],
                        distance=results["distances"][query_idx][i],
                    )

                    # Filter by tags if specified
                    if tags_filter and not matches_tags(result.metadata, tags_filter):
                        continue

                    search_results.append(result)

            all_search_results.append(search_results[:n_results])

        return all_search_results

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
            result.recency_score = calculate_recency_score(result.metadata, now)

            # Combined score: (1 - recency_weight) * similarity + recency_weight * recency
            result.combined_score = (
                1 - recency_weight
            ) * result.similarity_score + recency_weight * result.recency_score

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
            result.quality_score = calculate_quality_score(result.metadata)

            # Combined score: (1 - quality_weight) * similarity + quality_weight * quality
            result.combined_score = (
                1 - quality_weight
            ) * result.similarity_score + quality_weight * result.quality_score

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
            result.recency_score = calculate_recency_score(result.metadata, now)
            result.quality_score = calculate_quality_score(result.metadata)

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
        # Get semantic search results
        semantic_results = self.search(query, n_results=n_results * 3, **kwargs)

        # If no BM25 index, fall back to semantic only
        if self._bm25_index is None:
            logger.debug("No BM25 index available, using semantic search only")
            for result in semantic_results:
                result.hybrid_score = result.similarity_score
            return semantic_results[:n_results]

        # Get BM25 results
        bm25_results = self._bm25_index.search(query, n_results=n_results * 3)

        # Create lookup for BM25 scores by chunk_id
        bm25_scores: dict[str, float] = {}
        max_bm25_score = 1.0
        if bm25_results:
            max_bm25_score = max(r["score"] for r in bm25_results) or 1.0
            for r in bm25_results:
                # Normalize BM25 score to 0-1 range
                bm25_scores[r["id"]] = r["score"] / max_bm25_score

        # Combine scores
        for result in semantic_results:
            bm25_score = bm25_scores.get(result.chunk_id, 0.0)
            result.bm25_score = bm25_score
            result.hybrid_score = (
                semantic_weight * result.similarity_score + bm25_weight * bm25_score
            )

        # Sort by hybrid score
        semantic_results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return semantic_results[:n_results]

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
