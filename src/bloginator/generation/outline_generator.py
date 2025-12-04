"""Outline generation with RAG and coverage analysis."""

from pathlib import Path

from bloginator.generation._outline_prompt_builder import (
    OutlinePromptBuilder,
    build_corpus_context,
    build_search_queries,
)
from bloginator.generation.llm_client import LLMClient
from bloginator.models.outline import Outline, OutlineSection
from bloginator.search import CorpusSearcher, SearchResult


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
        search_queries = build_search_queries(title, keywords)

        # Collect all unique chunks to extract natural section boundaries
        all_results = []
        seen_chunk_ids = set()
        for query in search_queries:
            if query.strip():
                results = self.searcher.search(query=query, n_results=3)
                for result in results:
                    if result.chunk_id not in seen_chunk_ids:
                        all_results.append(result)
                        seen_chunk_ids.add(result.chunk_id)

        # Build corpus context from results
        corpus_context = build_corpus_context(all_results)

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
        sections = self._parse_outline_response(response.content)

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
            if match_ratio < 0.3 and all_results:
                sections = self._build_outline_from_corpus(all_results, keywords, num_sections)

        # Analyze coverage for each section
        for section in sections:
            self._analyze_section_coverage(section, keywords)

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
            outline.sections = self._filter_by_keyword_match(outline.sections, keywords)
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
            outline.sections = self._filter_sections_by_coverage(outline.sections, min_coverage=5.0)
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

    def _parse_outline_response(self, content: str) -> list[OutlineSection]:
        """Parse LLM outline response into OutlineSection objects.

        Args:
            content: LLM generated outline text

        Returns:
            List of top-level OutlineSection objects
        """
        sections = []
        current_section: OutlineSection | None = None
        current_subsection: OutlineSection | None = None

        lines = content.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Main section (## Heading)
            if line.startswith("## "):
                if current_section:
                    sections.append(current_section)
                title = line[3:].strip()
                current_section = OutlineSection(title=title)
                current_subsection = None

            # Subsection (### Heading)
            elif line.startswith("### "):
                if current_section:
                    title = line[4:].strip()
                    current_subsection = OutlineSection(title=title)
                    current_section.subsections.append(current_subsection)

            # Description text (for current section/subsection)
            elif current_subsection:
                current_subsection.description += (
                    " " + line if current_subsection.description else line
                )
            elif current_section:
                current_section.description += " " + line if current_section.description else line

        # Add final section
        if current_section:
            sections.append(current_section)

        return sections

    def _build_outline_from_corpus(
        self,
        results: list[SearchResult],
        keywords: list[str],
        num_sections: int = 5,
    ) -> list[OutlineSection]:
        """Build outline directly from corpus search results.

        This is a fallback when LLM outline generation produces hallucinations.
        Extracts natural sections based on actual corpus content.

        Args:
            results: Search results from corpus
            keywords: Keywords to focus on
            num_sections: Target number of sections

        Returns:
            List of OutlineSection objects based on corpus content
        """
        sections = []

        # Extract first heading or natural topic boundaries from each result
        for result in results[:num_sections]:
            # Try to extract a meaningful title from the content
            lines = result.content.split("\n")
            title = "Untitled Section"

            # Look for markdown headings
            for line in lines[:5]:
                if line.startswith("##"):
                    title = line.replace("##", "").strip()
                    break
                elif line.startswith("#"):
                    title = line.replace("#", "").strip()
                    break

            # Use first non-empty line as fallback
            if title == "Untitled Section":
                for line in lines:
                    if line.strip() and not line.startswith(("[", ">")):
                        title = line.strip()[:80]  # Limit length
                        break

            # Extract description from first 100 chars
            description = result.content[:150].replace("\n", " ").strip()
            if len(description) > 100:
                description = description[:100] + "..."

            # Create section with keyword awareness
            section = OutlineSection(
                title=title,
                description=description,
            )
            sections.append(section)

            if len(sections) >= num_sections:
                break

        return sections if sections else []

    def _filter_by_keyword_match(
        self,
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
                section.subsections = self._filter_by_keyword_match(section.subsections, keywords)
                filtered.append(section)
        return filtered

    def _filter_sections_by_coverage(
        self,
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
                section.subsections = self._filter_sections_by_coverage(
                    section.subsections, min_coverage
                )
                filtered.append(section)
        return filtered

    def _analyze_section_coverage(self, section: OutlineSection, keywords: list[str]) -> None:
        """Analyze corpus coverage for a section.

        Updates section.coverage_pct and section.source_count based on
        how well the corpus covers this section's topic.

        Args:
            section: Section to analyze
            keywords: Document keywords for context
        """
        # Build search query from section title + keywords
        query = f"{section.title} {' '.join(keywords[:3])}"

        try:
            # Search corpus for relevant content
            results = self.searcher.search(
                query=query,
                n_results=10,
            )

            # Calculate coverage based on search results
            if not results:
                section.coverage_pct = 0.0
                section.source_count = 0
                section.notes = "No corpus coverage found for this topic"
            else:
                # Coverage based on:
                # - Number of results (more = better coverage)
                # - Similarity scores (higher = more relevant)
                avg_similarity = sum(r.similarity_score for r in results) / len(results)

                # Scale coverage:
                # - 10+ results with high similarity = 100%
                # - Fewer results or lower similarity = proportionally less
                result_factor = min(len(results) / 10.0, 1.0)
                similarity_factor = avg_similarity

                section.coverage_pct = (result_factor * similarity_factor) * 100.0

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
                elif section.source_count < self.min_coverage_sources:
                    section.notes = f"Limited sources ({section.source_count} documents)"

        except Exception as e:
            # Fallback on error
            section.coverage_pct = 0.0
            section.source_count = 0
            section.notes = f"Coverage analysis failed: {str(e)}"

        # Recursively analyze subsections
        for subsection in section.subsections:
            self._analyze_section_coverage(subsection, keywords)

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
        sections = self._parse_outline_response(template_content)

        # Analyze coverage for each section
        for section in sections:
            self._analyze_section_coverage(section, keywords)

        # Create outline
        outline = Outline(
            title=title,
            thesis=thesis,
            keywords=keywords,
            sections=sections,
        )

        outline.calculate_stats()

        return outline
