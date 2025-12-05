"""Search result validation and quality checks.

CORPUS PHILOSOPHY:
Keywords and thesis are HINTS, not strict filters. The corpus is the source of truth.
- High similarity scores (>=0.4) bypass keyword validation entirely
- Strong semantic matches are trusted even without exact keyword presence
- We bias for including content rather than filtering it out
"""

import logging

from bloginator.search import SearchResult


logger = logging.getLogger(__name__)


def validate_search_results(
    results: list[SearchResult],
    expected_keywords: list[str],
    similarity_threshold: float = 0.01,
    min_keyword_matches: int = 1,
    high_similarity_threshold: float = 0.4,
) -> tuple[list[SearchResult], list[str]]:
    """Validate search results for topic relevance.

    Filters results based on:
    1. Similarity score threshold
    2. Keyword presence in content (relaxed for high-similarity results)

    High-similarity results (>= high_similarity_threshold) are accepted even
    without keyword matches, since strong semantic similarity indicates relevance.

    Args:
        results: Search results to validate
        expected_keywords: Keywords that should appear in results
        similarity_threshold: Minimum similarity score to accept
        min_keyword_matches: Minimum keywords that must appear in content
        high_similarity_threshold: Above this, skip keyword validation

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

        # High-similarity results bypass keyword validation
        # Strong semantic match is sufficient evidence of relevance
        if result.similarity_score >= high_similarity_threshold:
            filtered_results.append(result)
            continue

        # Check 2: Keyword presence (only for moderate-similarity results)
        # Handle hyphenated keywords by also checking for individual words
        content_lower = result.content.lower()
        matches = 0
        for kw in expected_keywords:
            kw_lower = kw.lower()
            if kw_lower in content_lower:
                matches += 1
            elif "-" in kw_lower:
                # For hyphenated keywords like "product-management",
                # check if all parts appear in the content
                parts = kw_lower.split("-")
                if all(part in content_lower for part in parts):
                    matches += 1

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
