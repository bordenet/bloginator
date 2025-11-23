"""Outline generation with RAG and coverage analysis."""

from pathlib import Path

from bloginator.generation.llm_client import LLMClient
from bloginator.models.outline import Outline, OutlineSection
from bloginator.prompts.loader import PromptLoader
from bloginator.search import CorpusSearcher


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
        prompt_loader: PromptLoader | None = None,
    ):
        """Initialize outline generator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for coverage analysis
            min_coverage_sources: Minimum sources for good coverage
            prompt_loader: Prompt loader (creates default if None)
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.min_coverage_sources = min_coverage_sources
        self.prompt_loader = prompt_loader or PromptLoader()

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
        # Load prompt template from external YAML file
        prompt_template = self.prompt_loader.load("outline/base.yaml")

        # Get classification and audience context from template
        classification_contexts = prompt_template.parameters.get("classification_contexts", {})
        audience_contexts = prompt_template.parameters.get("audience_contexts", {})

        classification_context = classification_contexts.get(classification, "This is guidance.")
        audience_context = audience_contexts.get(
            audience, "TARGET AUDIENCE: General technical audience."
        )

        # Render system prompt with context
        system_prompt = prompt_template.render_system_prompt(
            classification_context=classification_context, audience_context=audience_context
        )

        # Render user prompt with variables
        base_prompt = prompt_template.render_user_prompt(
            title=title,
            classification=classification.replace("-", " ").title(),
            audience=audience.replace("-", " ").title(),
            keywords=", ".join(keywords),
            thesis=thesis if thesis else "",
            num_sections=num_sections,
        )

        # Prepend custom template if provided
        if custom_prompt_template:
            user_prompt = f"""{custom_prompt_template}

---

{base_prompt}"""
        else:
            user_prompt = base_prompt

        # Generate outline structure with LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=2000,
        )

        # Parse LLM response into sections
        sections = self._parse_outline_response(response.content)

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
