"""Coverage analysis for outline sections."""

from bloginator.models.outline import OutlineSection
from bloginator.search import CorpusSearcher


def analyze_section_coverage(
    section: OutlineSection,
    keywords: list[str],
    searcher: CorpusSearcher,
    min_coverage_sources: int = 3,
) -> None:
    """Analyze corpus coverage for a section.

    Updates section.coverage_pct and section.source_count based on
    how well the corpus covers this section's topic.

    Args:
        section: Section to analyze
        keywords: Document keywords for context
        searcher: Corpus searcher instance
        min_coverage_sources: Minimum sources for good coverage
    """
    # Build search query from section title + keywords
    query = f"{section.title} {' '.join(keywords[:3])}"

    try:
        # Search corpus for relevant content
        results = searcher.search(
            query=query,
            n_results=10,
        )

        # Calculate coverage based on search results
        if not results:
            section.coverage_pct = 0.0
            section.source_count = 0
            section.notes = "No corpus coverage found for this topic"
        else:
            # Coverage calculation based on:
            # - Best similarity score (top match matters most)
            # - Average similarity across results
            # - Number of results
            #
            # ChromaDB cosine similarity scores (after 1-distance conversion):
            # - 0.5+ = strong match (excellent corpus coverage)
            # - 0.3-0.5 = good match (adequate coverage)
            # - 0.1-0.3 = weak match (limited coverage)
            # - <0.1 = no real match
            #
            # Clamp negative similarities to 0 - they indicate no semantic match
            # and shouldn't drag down the average
            clamped_scores = [max(0.0, r.similarity_score) for r in results]
            best_similarity = max(clamped_scores)

            # Only average positive scores to avoid negative drag
            positive_scores = [s for s in clamped_scores if s > 0]
            avg_similarity = sum(positive_scores) / len(positive_scores) if positive_scores else 0.0

            # Use best match as primary signal (90%) with average as secondary (10%)
            # This ensures a strong single match counts heavily - one good source is enough
            effective_similarity = 0.9 * best_similarity + 0.1 * avg_similarity

            # Generous normalization: 0.25 similarity = 100% coverage
            # Real-world embeddings for matching content typically score 0.2-0.4
            normalized_similarity = min(effective_similarity / 0.25, 1.0)

            # Result factor: having 2+ results with positive scores is full coverage
            positive_count = len(positive_scores)
            result_factor = min(positive_count / 2.0, 1.0)

            section.coverage_pct = (result_factor * normalized_similarity) * 100.0

            # Count unique source documents
            unique_docs = set()
            for result in results:
                doc_id = result.metadata.get("document_id", "")
                if doc_id:
                    unique_docs.add(doc_id)

            section.source_count = len(unique_docs)

            # Add warning for low coverage
            if section.coverage_pct < 50.0:
                section.notes = f"⚠️ Low corpus coverage ({section.coverage_pct:.0f}%)"
            elif section.source_count < min_coverage_sources:
                section.notes = f"Limited sources ({section.source_count} documents)"

    except Exception as e:
        # Fallback on error
        section.coverage_pct = 0.0
        section.source_count = 0
        section.notes = f"Coverage analysis failed: {str(e)}"

    # Recursively analyze subsections
    for subsection in section.subsections:
        analyze_section_coverage(subsection, keywords, searcher, min_coverage_sources)


def filter_sections_by_coverage(
    sections: list[OutlineSection],
    min_coverage: float = 0.01,
) -> list[OutlineSection]:
    """Filter out sections with coverage below minimum threshold.

    Args:
        sections: Sections to filter
        min_coverage: Minimum coverage threshold (default: 0.01%)

    Returns:
        Filtered list of sections (recursively filters subsections too)
    """
    filtered = []
    for section in sections:
        if section.coverage_pct >= min_coverage:
            # Recursively filter subsections
            section.subsections = filter_sections_by_coverage(section.subsections, min_coverage)
            filtered.append(section)
    return filtered


def filter_by_keyword_match(
    sections: list[OutlineSection],
    keywords: list[str],
) -> list[OutlineSection]:
    """Filter sections to keep only those matching keywords.

    Args:
        sections: Sections to filter
        keywords: Keywords to match against

    Returns:
        Filtered list of sections matching keywords
    """
    filtered = []
    for section in sections:
        section_text = f"{section.title} {section.description}".lower()
        if any(kw.lower() in section_text for kw in keywords):
            # Recursively filter subsections
            section.subsections = filter_by_keyword_match(section.subsections, keywords)
            filtered.append(section)
    return filtered
