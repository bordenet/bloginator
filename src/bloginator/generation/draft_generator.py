"""Draft generation with RAG and citation tracking."""

from collections.abc import Callable

from bloginator.generation.llm_client import LLMClient
from bloginator.models.draft import Citation, Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection
from bloginator.search import CorpusSearcher, SearchResult


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
    ):
        """Initialize draft generator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for RAG
            sources_per_section: Sources to retrieve per section
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.sources_per_section = sources_per_section

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
        # Count total sections for progress tracking
        total_sections = len(outline.get_all_sections())
        current_section = 0

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
            )
            # Update counter (section + all its subsections)
            current_section += len(outline_section.get_all_sections())
            sections.append(draft_section)

        # Create draft
        draft = Draft(
            title=outline.title,
            thesis=outline.thesis,
            classification=outline.classification,
            audience=outline.audience,
            keywords=outline.keywords,
            sections=sections,
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

        Returns:
            DraftSection with generated content and citations
        """
        # Report progress
        if progress_callback:
            progress_callback(
                f"Searching corpus for: {outline_section.title}",
                current_section,
                total_sections,
            )

        # Search corpus for relevant content
        query = f"{outline_section.title} {outline_section.description} {' '.join(keywords[:2])}"

        search_results = self.searcher.search(
            query=query,
            n_results=self.sources_per_section,
        )

        # Report progress
        if progress_callback:
            progress_callback(
                f"Generating content for: {outline_section.title}",
                current_section,
                total_sections,
            )

        # Build context from search results
        source_context = self._build_source_context(search_results)

        # Build classification and audience context
        classification_guidance = {
            "guidance": "Provide helpful suggestions and recommendations",
            "best-practice": "Present proven approaches and industry standards",
            "mandate": "State required practices with clear authority",
            "principle": "Explain fundamental concepts and reasoning",
            "opinion": "Share personal perspectives backed by experience",
        }.get(classification, "Provide helpful guidance")

        audience_context = {
            "ic-engineers": "individual contributor engineers",
            "engineering-leaders": "engineering leaders and managers",
            "all-disciplines": "professionals across all disciplines",
            "qa-engineers": "quality assurance and testing engineers",
            "product-managers": "product managers and stakeholders",
        }.get(audience, "general professional audience")

        # Generate content with LLM
        system_prompt = f"""You are a skilled technical writer creating authentic content.
Write in a clear, professional voice based ONLY on the provided source material.
{classification_guidance}.
Write for {audience_context}.
Do not invent facts or examples not present in the sources.
Write naturally without explicitly citing sources in the text."""

        user_prompt = f"""Write content for this section:

Title: {outline_section.title}
Description: {outline_section.description}
Target length: {max_words} words

Source Material:
{source_context}

Write clear, cohesive content that synthesizes the source material.
Focus on the key insights and examples from the sources."""

        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_words * 2,  # Rough token estimate
        )

        # Create citations from search results
        citations = [
            Citation(
                chunk_id=r.chunk_id,
                document_id=r.metadata.get("document_id", "unknown"),
                filename=r.metadata.get("filename", "unknown"),
                content_preview=r.content[:100],
                similarity_score=r.similarity_score,
            )
            for r in search_results[:5]  # Keep top 5 citations
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

        source_context = self._build_source_context(search_results)

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
        for result in search_results[:3]:
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
