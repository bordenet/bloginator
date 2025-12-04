"""Outline generation with RAG and coverage analysis."""

import logging
from pathlib import Path

from bloginator.generation._outline_coverage import (
    analyze_section_coverage,
    filter_by_keyword_match,
    filter_sections_by_coverage,
)
from bloginator.generation._outline_parser import build_outline_from_corpus, parse_outline_response
from bloginator.generation._outline_prompt_builder import (
    OutlinePromptBuilder,
    build_corpus_context,
    build_search_queries,
)
from bloginator.generation.llm_client import LLMClient
from bloginator.models.outline import Outline
from bloginator.search import CorpusSearcher
from bloginator.search.validators import validate_search_results


logger = logging.getLogger(__name__)


class OutlineGenerator:
    """Generate document outlines using RAG with coverage analysis.

    Uses LLM to generate outline structure and corpus search to analyze
    coverage for each section.

    Attributes:
        llm_client: LLM client for outline generation
        searcher: Corpus searcher for coverage analysis
        min_coverage_sources: Minimum sources for good coverage (default: 3)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: CorpusSearcher,
        min_coverage_sources: int = 3,
    ):
        """Initialize outline generator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for coverage analysis
            min_coverage_sources: Minimum sources for good coverage
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.min_coverage_sources = min_coverage_sources
        self.prompt_builder = OutlinePromptBuilder()

    def generate(
        self,
        title: str,
        keywords: list[str],
        thesis: str = "",
        classification: str = "guidance",
        audience: str = "all-disciplines",
        num_sections: int = 5,
        temperature: float = 0.7,
        custom_prompt_template: str | None = None,
    ) -> Outline:
        """Generate outline with coverage analysis.

        Args:
            title: Document title
            keywords: Keywords/themes for the document
            thesis: Optional thesis statement
            classification: Content classification (guidance, best-practice, mandate, principle, opinion)
            audience: Target audience (ic-engineers, engineering-leaders, all-disciplines, etc.)
            num_sections: Target number of top-level sections
            temperature: LLM sampling temperature
            custom_prompt_template: Optional custom prompt template (rendered Jinja2 template with style/tone instructions)

        Returns:
            Outline with coverage statistics

        Example:
            >>> generator = OutlineGenerator(llm_client, searcher)
            >>> outline = generator.generate(
            ...     title="Senior Engineer Career Ladder",
            ...     keywords=["senior engineer", "career ladder", "IC track"],
            ...     thesis="Senior engineers grow through technical mastery AND impact",
            ...     classification="best-practice",
            ...     audience="engineering-leaders"
            ... )
            >>> outline.calculate_stats()
            >>> print(f"Coverage: {outline.avg_coverage:.0f}%")
        """
        # Build system and user prompts with corpus grounding
        system_prompt = self.prompt_builder.build_system_prompt(
            classification=classification, audience=audience
        )

        # GROUNDING: Search corpus multiple times for different keyword angles
        # to build sections directly from corpus rather than LLM hallucination
        search_queries = build_search_queries(title, keywords, thesis)
        logger.info(f"Generated {len(search_queries)} search queries: {search_queries}")

        # Collect all unique chunks to extract natural section boundaries
        all_results = []
        seen_chunk_ids = set()
        for query in search_queries:
            if query.strip():
                results = self.searcher.search(query=query, n_results=3)
                logger.info(f"Search query '{query}' returned {len(results)} results")
                for result in results:
                    if result.chunk_id not in seen_chunk_ids:
                        all_results.append(result)
                        seen_chunk_ids.add(result.chunk_id)

        # Validate and filter search results
        filtered_results, validation_warnings = validate_search_results(
            all_results, expected_keywords=keywords
        )
        for warning in validation_warnings:
            logger.warning(f"Search result validation warning: {warning}")

        # Log top results
        if filtered_results:
            logger.info(
                f"Retrieved {len(filtered_results)} unique results after validation. Top 3:"
            )
            for i, result in enumerate(filtered_results[:3], 1):
                preview = result.content[:100].replace("\n", " ")
                logger.info(
                    f"  Result {i}: similarity={result.similarity_score:.3f}, "
                    f"source={result.metadata.get('filename', 'unknown')}, "
                    f"preview='{preview}...'"
                )
        else:
            logger.warning("No corpus results found for any query after validation.")

        # Build corpus context from results
        corpus_context = build_corpus_context(filtered_results)

        # Render user prompt with variables
        user_prompt = self.prompt_builder.build_user_prompt(
            title=title,
            keywords=keywords,
            thesis=thesis,
            classification=classification,
            audience=audience,
            num_sections=num_sections,
            corpus_context=corpus_context,
            custom_template=custom_prompt_template,
        )

        # Generate outline structure with LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=2000,
        )

        # Parse LLM response into sections
        sections = parse_outline_response(response.content)

        # FALLBACK: If LLM generated mostly off-topic sections,
        # build outline from corpus search results instead
        if sections:
            keyword_match_count = sum(
                1
                for s in sections
                if any(kw.lower() in f"{s.title} {s.description}".lower() for kw in keywords)
            )
            match_ratio = keyword_match_count / len(sections) if sections else 0

            # If <30% match, use corpus-based outline instead
            if match_ratio < 0.3 and filtered_results:
                sections = build_outline_from_corpus(filtered_results, keywords, num_sections)

        # Analyze coverage for each section
        for section in sections:
            analyze_section_coverage(section, keywords, self.searcher, self.min_coverage_sources)

        # Create outline
        outline = Outline(
            title=title,
            thesis=thesis,
            classification=classification,
            audience=audience,
            keywords=keywords,
            sections=sections,
        )

        # Calculate statistics
        all_sections = outline.get_all_sections()
        unique_sources = set()
        for section in all_sections:
            # Track unique source documents
            # Note: We'd need to enhance search to return document IDs
            unique_sources.add(section.source_count)

        outline.total_sources = (
            len(unique_sources)
            if unique_sources
            else (
                sum(s.source_count for s in all_sections) // len(all_sections)
                if all_sections
                else 0
            )
        )

        outline.calculate_stats()

        # CRITICAL CHECK: Validate sections match keywords
        # Count sections that contain at least one keyword
        keyword_matched_sections = 0
        total_sections = len(outline.get_all_sections())

        for section in outline.get_all_sections():
            section_text = f"{section.title} {section.description}".lower()
            if any(kw.lower() in section_text for kw in keywords):
                keyword_matched_sections += 1

        keyword_match_ratio = keyword_matched_sections / total_sections if total_sections > 0 else 0

        # If <50% of sections match keywords, outline is hallucinated
        if keyword_match_ratio < 0.5 and total_sections > 0:
            if outline.validation_notes:
                outline.validation_notes = ""
            outline.validation_notes = (
                f"❌ OUTLINE REJECTED: Only {keyword_matched_sections}/{total_sections} sections "
                f"({keyword_match_ratio*100:.0f}%) match provided keywords.\n\n"
                f"The outline appears to be hallucinated (not grounded in your corpus).\n\n"
                f"Keywords provided: {', '.join(keywords)}\n\n"
                f"Outline generated:\n"
                f"{chr(10).join(f'  - {s.title}' for s in outline.sections[:5])}"
                f"{'...' if len(outline.sections) > 5 else ''}\n\n"
                f"RECOMMENDATION:\n"
                f"1. Search corpus manually for: {keywords[0]}\n"
                f"2. Verify corpus actually contains material about this topic\n"
                f"3. Try with different keywords that better match corpus content\n"
                f"4. Add more source documents if corpus is too sparse"
            )
            # Keep only sections that match keywords
            outline.sections = filter_by_keyword_match(outline.sections, keywords)
            outline.calculate_stats()
            return outline

        # ADDITIONAL FILTERING: Remove sections with very low coverage (<5%)
        # unless they're directly in the keywords
        very_low_coverage_sections = []
        for section in outline.get_all_sections():
            if 0 < section.coverage_pct < 5.0:
                # Check if section title contains any keyword
                section_lower = section.title.lower()
                keyword_match = any(kw.lower() in section_lower for kw in keywords)
                if not keyword_match:
                    very_low_coverage_sections.append(section.title)

        if very_low_coverage_sections:
            old_section_count = len(outline.get_all_sections())
            outline.sections = filter_sections_by_coverage(outline.sections, min_coverage=5.0)
            new_section_count = len(outline.get_all_sections())
            if outline.validation_notes:
                outline.validation_notes += "\n\n"
            outline.validation_notes += (
                f"⚠️ REMOVED {old_section_count - new_section_count} additional sections with very low coverage "
                f"(<5%) unrelated to keywords:\n"
                f"{chr(10).join(f'  - {t}' for t in very_low_coverage_sections[:3])}"
                + (
                    f"\n  ... and {len(very_low_coverage_sections) - 3} more"
                    if len(very_low_coverage_sections) > 3
                    else ""
                )
            )
            outline.calculate_stats()  # Recalculate after filtering

        # Additional warning if overall coverage is still very low
        if outline.avg_coverage < 15.0 and outline.avg_coverage > 0:
            if outline.validation_notes:
                outline.validation_notes += "\n\n"
            outline.validation_notes += (
                f"⚠️ COVERAGE WARNING: Remaining outline still has low corpus coverage ({outline.avg_coverage:.1f}%). "
                f"Consider:\n"
                f"  1. Adding more source documents to corpus\n"
                f"  2. Refining keywords to better match corpus content\n"
                f"  3. Verifying section titles directly relate to the topic"
            )

        return outline

    def generate_from_template(
        self,
        template_path: Path,
        title: str,
        keywords: list[str],
        thesis: str = "",
    ) -> Outline:
        """Generate outline from a template structure.

        Args:
            template_path: Path to outline template file
            title: Document title
            keywords: Keywords/themes
            thesis: Optional thesis statement

        Returns:
            Outline based on template with coverage analysis

        Note:
            Template should be markdown with ## sections and ### subsections
        """
        # Read template
        template_content = template_path.read_text()

        # Parse template into sections
        sections = parse_outline_response(template_content)

        # Analyze coverage for each section
        for section in sections:
            analyze_section_coverage(section, keywords, self.searcher, self.min_coverage_sources)

        # Create outline
        outline = Outline(
            title=title,
            thesis=thesis,
            keywords=keywords,
            sections=sections,
        )

        outline.calculate_stats()

        return outline
