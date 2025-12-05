"""Search result validation and quality checks."""

import logging

from bloginator.search import SearchResult


logger = logging.getLogger(__name__)


def validate_search_results(
    results: list[SearchResult],
    expected_keywords: list[str],
    similarity_threshold: float = 0.01,
    min_keyword_matches: int = 1,
) -> tuple[list[SearchResult], list[str]]:
    """Validate search results for topic relevance.

    Filters results based on:
    1. Similarity score threshold
    2. Keyword presence in content

    Args:
        results: Search results to validate
        expected_keywords: Keywords that should appear in results
        similarity_threshold: Minimum similarity score to accept
        min_keyword_matches: Minimum keywords that must appear in content

    Returns:
        Tuple of (filtered_results, warnings)
    """
    filtered_results = []
    warnings = []

    for result in results:
        # Check 1: Similarity threshold
        if result.similarity_score < similarity_threshold:
            warnings.append(
                f"Low similarity ({result.similarity_score:.3f}) for: " f"{result.content[:50]}..."
            )
            continue

        # Check 2: Keyword presence
        content_lower = result.content.lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in content_lower)

        if matches < min_keyword_matches:
            warnings.append(
                f"Insufficient keyword matches ({matches}/{min_keyword_matches}) "
                f"in: {result.content[:50]}..."
            )
            continue

        filtered_results.append(result)

    # Log overall quality
    if len(filtered_results) < len(results) / 2:
        logger.warning(
            f"Search quality concern: {len(filtered_results)}/{len(results)} "
            f"results passed validation"
        )

    return filtered_results, warnings
