"""Section refinement logic for draft generation."""

import logging

from bloginator.generation.llm_client import LLMClient
from bloginator.models.draft import Citation, DraftSection
from bloginator.search import CorpusSearcher, SearchResult
from bloginator.search.validators import validate_search_results


logger = logging.getLogger(__name__)


def build_source_context(results: list[SearchResult]) -> str:
    """Build context string from search results.

    Args:
        results: Search results to use as sources

    Returns:
        Formatted source context for LLM
    """
    if not results:
        return "No source material found. Please write general content on this topic."

    context_parts = []
    for i, result in enumerate(results, 1):
        context_parts.append(f"[Source {i}]")
        context_parts.append(result.content)
        context_parts.append("")  # Blank line

    return "\n".join(context_parts)


def create_citations(results: list[SearchResult], max_citations: int = 5) -> list[Citation]:
    """Create citations from search results.

    Args:
        results: Search results to create citations from
        max_citations: Maximum number of citations to create

    Returns:
        List of Citation objects
    """
    return [
        Citation(
            chunk_id=r.chunk_id,
            document_id=r.metadata.get("document_id", "unknown"),
            filename=r.metadata.get("filename", "unknown"),
            content_preview=r.content[:100],
            similarity_score=r.similarity_score,
        )
        for r in results[:max_citations]
    ]


def get_voice_samples(searcher: CorpusSearcher, keywords: list[str], num_samples: int = 5) -> str:
    """Fetch diverse voice samples from corpus to help LLM emulate author's style.

    Args:
        searcher: Corpus searcher to use
        keywords: Keywords to use for sampling context
        num_samples: Number of diverse samples to fetch

    Returns:
        Formatted voice samples string for inclusion in prompt
    """
    try:
        # Get a diverse sample by using different query strategies
        samples = []

        # Sample 1: Use first keyword
        if keywords:
            results = searcher.search(keywords[0], n_results=2)
            samples.extend(results)

        # Sample 2: Use a general writing query to get different content
        general_results = searcher.search("writing style examples", n_results=2)
        samples.extend(general_results)

        # Sample 3: If we have more keywords, use another
        if len(keywords) > 1:
            results = searcher.search(keywords[1], n_results=1)
            samples.extend(results)

        # Deduplicate by chunk_id and limit
        seen_ids = set()
        unique_samples = []
        for sample in samples:
            if sample.chunk_id not in seen_ids:
                seen_ids.add(sample.chunk_id)
                unique_samples.append(sample)
                if len(unique_samples) >= num_samples:
                    break

        if not unique_samples:
            return ""

        # Format samples for the prompt
        sample_parts = []
        for i, sample in enumerate(unique_samples, 1):
            # Truncate long samples to ~200 words
            content = sample.content
            words = content.split()
            if len(words) > 200:
                content = " ".join(words[:200]) + "..."
            sample_parts.append(f"[Sample {i}]\n{content}\n")

        return "\n".join(sample_parts)

    except Exception as e:
        logger.warning(f"Failed to fetch voice samples: {e}")
        return ""


def refine_section(
    section: DraftSection,
    feedback: str,
    keywords: list[str],
    llm_client: LLMClient,
    searcher: CorpusSearcher,
    sources_per_section: int = 5,
    temperature: float = 0.7,
) -> DraftSection:
    """Refine a section based on feedback.

    Args:
        section: Section to refine
        feedback: Natural language feedback
        keywords: Document keywords
        llm_client: LLM client for generation
        searcher: Corpus searcher for RAG
        sources_per_section: Number of sources to retrieve
        temperature: LLM temperature

    Returns:
        New DraftSection with refined content
    """
    # Search for additional content based on feedback
    query = f"{section.title} {feedback} {' '.join(keywords[:2])}"

    search_results = searcher.search(
        query=query,
        n_results=sources_per_section,
    )

    # Validate and filter search results
    filtered_results, validation_warnings = validate_search_results(
        search_results, expected_keywords=keywords
    )
    for warning in validation_warnings:
        logger.warning(f"Draft refinement validation warning: {warning}")

    source_context = build_source_context(filtered_results)

    # Refine with LLM
    system_prompt = """You are refining content based on feedback.
Keep the core message but incorporate the requested changes.
Use only information from the provided sources."""

    user_prompt = f"""Original content:
{section.content}

Feedback: {feedback}

Additional source material:
{source_context}

Revise the content to address the feedback while maintaining coherence."""

    response = llm_client.generate(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=len(section.content.split()) * 2,
    )

    # Update citations
    new_citations = section.citations.copy()
    for result in filtered_results[:3]:  # Use filtered results for citations
        citation = Citation(
            chunk_id=result.chunk_id,
            document_id=result.metadata.get("document_id", "unknown"),
            filename=result.metadata.get("filename", "unknown"),
            content_preview=result.content[:100],
            similarity_score=result.similarity_score,
        )
        # Avoid duplicates
        if not any(c.chunk_id == citation.chunk_id for c in new_citations):
            new_citations.append(citation)

    return DraftSection(
        title=section.title,
        content=response.content.strip(),
        citations=new_citations,
        subsections=section.subsections,  # Keep original subsections
    )
