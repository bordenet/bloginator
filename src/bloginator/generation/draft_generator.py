"""Draft generation with RAG and citation tracking."""

import logging
import time
from collections.abc import Callable

from bloginator.config import Config
from bloginator.generation._section_refiner import (
    build_source_context,
    create_citations,
    get_voice_samples,
    refine_section,
)
from bloginator.generation.llm_client import LLMClient
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection
from bloginator.prompts.loader import PromptLoader
from bloginator.search import CorpusSearcher, SearchResult
from bloginator.search.validators import validate_search_results


logger = logging.getLogger(__name__)


class DraftGenerator:
    """Generate document drafts from outlines using RAG.

    Uses corpus search to find relevant content for each section,
    then LLM to synthesize coherent text grounded in sources.

    Attributes:
        llm_client: LLM client for text generation
        searcher: Corpus searcher for RAG
        sources_per_section: Number of sources to retrieve per section (reduced to 3 for brevity)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: CorpusSearcher,
        sources_per_section: int = 3,
        prompt_loader: PromptLoader | None = None,
    ):
        """Initialize draft generator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for RAG
            sources_per_section: Sources to retrieve per section (default: 3, reduced from 5)
            prompt_loader: Prompt loader (creates default if None)
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.sources_per_section = sources_per_section
        self.prompt_loader = prompt_loader or PromptLoader()

    def generate(
        self,
        outline: Outline,
        temperature: float = 0.7,
        max_section_words: int = 70,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> Draft:
        """Generate draft from outline.

        Args:
            outline: Outline to generate from
            temperature: LLM sampling temperature
            max_section_words: Target words per section
            progress_callback: Optional callback(message, current, total) for progress updates

        Returns:
            Draft with generated content and citations

        Example:
            >>> generator = DraftGenerator(llm_client, searcher)
            >>> draft = generator.generate(outline)
            >>> draft.calculate_stats()
            >>> print(f"Generated {draft.total_words} words")
            >>> print(f"Citations: {draft.total_citations}")
        """
        start_time = time.time()

        # Count total sections for progress tracking
        total_sections = len(outline.get_all_sections())
        current_section = 0

        # Pre-fetch all search results using batch search for better performance
        all_sections = outline.get_all_sections()
        queries = [
            f"{section.title} {section.description} {' '.join(outline.keywords[:2])}"
            for section in all_sections
        ]

        if progress_callback:
            progress_callback(
                f"Pre-fetching corpus results for {len(queries)} sections...",
                0,
                total_sections,
            )

        batch_results = self.searcher.batch_search(
            queries=queries,
            n_results=self.sources_per_section,
        )

        # Create a mapping from section ID to search results
        # Use id() as key since OutlineSection is not hashable
        search_cache = {
            id(section): results
            for section, results in zip(all_sections, batch_results, strict=False)
        }

        # Generate sections from outline
        sections = []
        for outline_section in outline.sections:
            draft_section = self._generate_section(
                outline_section=outline_section,
                keywords=outline.keywords,
                classification=outline.classification,
                audience=outline.audience,
                temperature=temperature,
                max_words=max_section_words,
                progress_callback=progress_callback,
                current_section=current_section,
                total_sections=total_sections,
                search_cache=search_cache,
            )
            # Update counter (section + all its subsections)
            current_section += len(outline_section.get_all_sections())
            sections.append(draft_section)

        # Create draft with timing
        generation_time = time.time() - start_time
        draft = Draft(
            title=outline.title,
            thesis=outline.thesis,
            classification=outline.classification,
            audience=outline.audience,
            keywords=outline.keywords,
            sections=sections,
            generation_time_seconds=generation_time,
        )

        # Calculate statistics
        draft.calculate_stats()

        return draft

    def _generate_section(
        self,
        outline_section: OutlineSection,
        keywords: list[str],
        classification: str = "guidance",
        audience: str = "all-disciplines",
        temperature: float = 0.7,
        max_words: int = 300,
        progress_callback: Callable[[str, int, int], None] | None = None,
        current_section: int = 0,
        total_sections: int = 1,
        search_cache: dict[int, list[SearchResult]] | None = None,
    ) -> DraftSection:
        """Generate content for a single section with RAG."""
        # Get search results from cache or perform search
        section_id = id(outline_section)
        if search_cache and section_id in search_cache:
            search_results = search_cache[section_id]
        else:
            # Report progress
            if progress_callback:
                progress_callback(
                    f"Searching corpus for: {outline_section.title}",
                    current_section,
                    total_sections,
                )

            # Search corpus for relevant content
            query = (
                f"{outline_section.title} {outline_section.description} "
                f"{' '.join(keywords[:2])}"
            )

            search_results = self.searcher.search(
                query=query,
                n_results=self.sources_per_section,
            )

        # Validate and filter search results
        filtered_results, validation_warnings = validate_search_results(
            search_results, expected_keywords=keywords
        )
        for warning in validation_warnings:
            logger.warning(f"Draft generation validation warning: {warning}")

        # Report progress
        if progress_callback:
            progress_callback(
                f"Generating content for: {outline_section.title}",
                current_section,
                total_sections,
            )

        # Build context from filtered search results
        source_context = build_source_context(filtered_results)

        # Load prompt template from external YAML file
        prompt_template = self.prompt_loader.load("draft/base.yaml")

        # Get classification and audience context from template
        classification_contexts = prompt_template.parameters.get("classification_contexts", {})
        audience_contexts = prompt_template.parameters.get("audience_contexts", {})

        classification_guidance = classification_contexts.get(
            classification, "Provide helpful guidance"
        )
        audience_context = audience_contexts.get(audience, "general professional audience")

        # Fetch voice samples from corpus to help LLM emulate author's style
        voice_samples = get_voice_samples(self.searcher, keywords)

        # Render system prompt with context, voice samples, and company branding
        system_prompt = prompt_template.render_system_prompt(
            classification_guidance=classification_guidance,
            audience_context=audience_context,
            voice_samples=voice_samples,
            company_name=Config.COMPANY_NAME,
            company_possessive=Config.COMPANY_POSSESSIVE,
        )

        # Render user prompt with variables
        user_prompt = prompt_template.render_user_prompt(
            title=outline_section.title,
            description=outline_section.description,
            max_words=max_words,
            source_context=source_context,
        )

        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_words * 2,  # Rough token estimate
        )

        # Create citations from filtered search results
        citations = create_citations(filtered_results, max_citations=5)

        # Generate subsections recursively
        subsections = self._generate_subsections(
            outline_section=outline_section,
            keywords=keywords,
            classification=classification,
            audience=audience,
            temperature=temperature,
            max_words=max_words,
            progress_callback=progress_callback,
            current_section=current_section,
            total_sections=total_sections,
            search_cache=search_cache,
        )

        return DraftSection(
            title=outline_section.title,
            content=response.content.strip(),
            citations=citations,
            subsections=subsections,
        )

    def _generate_subsections(
        self,
        outline_section: OutlineSection,
        keywords: list[str],
        classification: str,
        audience: str,
        temperature: float,
        max_words: int,
        progress_callback: Callable[[str, int, int], None] | None,
        current_section: int,
        total_sections: int,
        search_cache: dict[int, list[SearchResult]] | None,
    ) -> list[DraftSection]:
        """Generate subsections recursively.

        Args:
            outline_section: Parent section from outline
            keywords: Document keywords for context
            classification: Content classification for tone
            audience: Target audience
            temperature: LLM temperature
            max_words: Target word count for parent
            progress_callback: Optional callback for progress updates
            current_section: Current section number (0-based)
            total_sections: Total number of sections
            search_cache: Optional pre-fetched search results cache

        Returns:
            List of generated DraftSection objects for subsections
        """
        subsections = []
        subsection_offset = current_section + 1

        for i, outline_subsection in enumerate(outline_section.subsections):
            # Calculate offset for this subsection
            subsection_current = subsection_offset + sum(
                len(outline_section.subsections[j].get_all_sections()) for j in range(i)
            )
            draft_subsection = self._generate_section(
                outline_subsection,
                keywords,
                classification,
                audience,
                temperature,
                max_words // 2,  # Subsections get less content
                progress_callback=progress_callback,
                current_section=subsection_current,
                total_sections=total_sections,
                search_cache=search_cache,
            )
            subsections.append(draft_subsection)

        return subsections

    def refine_section(
        self,
        section: DraftSection,
        feedback: str,
        keywords: list[str],
        temperature: float = 0.7,
    ) -> DraftSection:
        """Refine a section based on natural language feedback."""
        return refine_section(
            section=section,
            feedback=feedback,
            keywords=keywords,
            llm_client=self.llm_client,
            searcher=self.searcher,
            sources_per_section=self.sources_per_section,
            temperature=temperature,
        )
