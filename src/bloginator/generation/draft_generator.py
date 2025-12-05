"""Draft generation with RAG and citation tracking."""

import logging
import time
from collections.abc import Callable

from bloginator.generation.llm_client import LLMClient
from bloginator.models.draft import Citation, Draft, DraftSection
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
        sources_per_section: Number of sources to retrieve per section
    """

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: CorpusSearcher,
        sources_per_section: int = 5,
        prompt_loader: PromptLoader | None = None,
    ):
        """Initialize draft generator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for RAG
            sources_per_section: Sources to retrieve per section
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
        max_section_words: int = 300,
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
        """Generate content for a single section.

        Args:
            outline_section: Section from outline
            keywords: Document keywords for context
            classification: Content classification for tone
            audience: Target audience
            temperature: LLM temperature
            max_words: Target word count
            progress_callback: Optional callback for progress updates
            current_section: Current section number (0-based)
            total_sections: Total number of sections
            search_cache: Optional pre-fetched search results cache (keyed by id(section))

        Returns:
            DraftSection with generated content and citations
        """
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
                f"{outline_section.title} {outline_section.description} {' '.join(keywords[:2])}"
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
        source_context = self._build_source_context(filtered_results)

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
        voice_samples = self._get_voice_samples(keywords)

        # Render system prompt with context and voice samples
        system_prompt = prompt_template.render_system_prompt(
            classification_guidance=classification_guidance,
            audience_context=audience_context,
            voice_samples=voice_samples,
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
        citations = [
            Citation(
                chunk_id=r.chunk_id,
                document_id=r.metadata.get("document_id", "unknown"),
                filename=r.metadata.get("filename", "unknown"),
                content_preview=r.content[:100],
                similarity_score=r.similarity_score,
            )
            for r in filtered_results[:5]  # Keep top 5 citations from filtered results
        ]

        # Generate subsections recursively
        subsections = []
        subsection_offset = (
            current_section + 1
        )  # Current section is done, start counting subsections
        for i, outline_subsection in enumerate(outline_section.subsections):
            # Calculate offset for this subsection (includes all previous subsections and their children)
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

        return DraftSection(
            title=outline_section.title,
            content=response.content.strip(),
            citations=citations,
            subsections=subsections,
        )

    def _build_source_context(self, results: list[SearchResult]) -> str:
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

    def _get_voice_samples(self, keywords: list[str], num_samples: int = 5) -> str:
        """Fetch diverse voice samples from corpus to help LLM emulate author's style.

        Args:
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
                results = self.searcher.search(keywords[0], n_results=2)
                samples.extend(results)

            # Sample 2: Use a general writing query to get different content
            general_results = self.searcher.search("writing style examples", n_results=2)
            samples.extend(general_results)

            # Sample 3: If we have more keywords, use another
            if len(keywords) > 1:
                results = self.searcher.search(keywords[1], n_results=1)
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
        self,
        section: DraftSection,
        feedback: str,
        keywords: list[str],
        temperature: float = 0.7,
    ) -> DraftSection:
        """Refine a section based on feedback.

        Args:
            section: Section to refine
            feedback: Natural language feedback
            keywords: Document keywords
            temperature: LLM temperature

        Returns:
            New DraftSection with refined content

        Example:
            >>> refined = generator.refine_section(
            ...     section,
            ...     "Add more concrete examples from startup experience",
            ...     keywords
            ... )
        """
        # Search for additional content based on feedback
        query = f"{section.title} {feedback} {' '.join(keywords[:2])}"

        search_results = self.searcher.search(
            query=query,
            n_results=self.sources_per_section,
        )

        # Validate and filter search results
        filtered_results, validation_warnings = validate_search_results(
            search_results, expected_keywords=keywords
        )
        for warning in validation_warnings:
            logger.warning(f"Draft refinement validation warning: {warning}")

        source_context = self._build_source_context(filtered_results)

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

        response = self.llm_client.generate(
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
