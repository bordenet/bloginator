"""Weighted search methods for corpus searcher.

Provides search methods that combine similarity with recency and quality weights.
"""

from datetime import datetime

from bloginator.search._search_helpers import calculate_quality_score, calculate_recency_score
from bloginator.search._search_result import SearchResult


def apply_recency_weights(
    results: list[SearchResult],
    recency_weight: float,
    n_results: int,
) -> list[SearchResult]:
    """Apply recency weighting to search results.

    Args:
        results: Search results to weight
        recency_weight: Weight for recency score (0.0-1.0)
        n_results: Number of results to return

    Returns:
        Sorted results with combined scores
    """
    now = datetime.now()
    for result in results:
        result.recency_score = calculate_recency_score(result.metadata, now)
        result.combined_score = (
            1 - recency_weight
        ) * result.similarity_score + recency_weight * result.recency_score

    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results[:n_results]


def apply_quality_weights(
    results: list[SearchResult],
    quality_weight: float,
    n_results: int,
) -> list[SearchResult]:
    """Apply quality weighting to search results.

    Args:
        results: Search results to weight
        quality_weight: Weight for quality score (0.0-1.0)
        n_results: Number of results to return

    Returns:
        Sorted results with combined scores
    """
    for result in results:
        result.quality_score = calculate_quality_score(result.metadata)
        result.combined_score = (
            1 - quality_weight
        ) * result.similarity_score + quality_weight * result.quality_score

    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results[:n_results]


def apply_combined_weights(
    results: list[SearchResult],
    recency_weight: float,
    quality_weight: float,
    n_results: int,
) -> list[SearchResult]:
    """Apply combined recency and quality weighting.

    Args:
        results: Search results to weight
        recency_weight: Weight for recency score (0.0-1.0)
        quality_weight: Weight for quality score (0.0-1.0)
        n_results: Number of results to return

    Returns:
        Sorted results with combined scores

    Note:
        Weights should sum to <= 1.0. Remaining weight goes to similarity.
    """
    now = datetime.now()
    similarity_weight = 1.0 - recency_weight - quality_weight

    for result in results:
        result.recency_score = calculate_recency_score(result.metadata, now)
        result.quality_score = calculate_quality_score(result.metadata)
        result.combined_score = (
            similarity_weight * result.similarity_score
            + recency_weight * result.recency_score
            + quality_weight * result.quality_score
        )

    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results[:n_results]


def apply_hybrid_scores(
    semantic_results: list[SearchResult],
    bm25_scores: dict[str, float],
    semantic_weight: float,
    bm25_weight: float,
    n_results: int,
) -> list[SearchResult]:
    """Apply hybrid semantic + BM25 scoring.

    Args:
        semantic_results: Semantic search results
        bm25_scores: Dictionary of chunk_id -> normalized BM25 score
        semantic_weight: Weight for semantic similarity (0.0-1.0)
        bm25_weight: Weight for BM25 lexical score (0.0-1.0)
        n_results: Number of results to return

    Returns:
        Sorted results with hybrid scores
    """
    for result in semantic_results:
        bm25_score = bm25_scores.get(result.chunk_id, 0.0)
        result.bm25_score = bm25_score
        result.hybrid_score = semantic_weight * result.similarity_score + bm25_weight * bm25_score

    semantic_results.sort(key=lambda r: r.hybrid_score, reverse=True)
    return semantic_results[:n_results]
