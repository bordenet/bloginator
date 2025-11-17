"""Outline generation with RAG and coverage analysis."""

from pathlib import Path

from bloginator.generation.llm_client import LLMClient
from bloginator.models.outline import Outline, OutlineSection
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

    def generate(
        self,
        title: str,
        keywords: list[str],
        thesis: str = "",
        classification: str = "guidance",
        audience: str = "all-disciplines",
        num_sections: int = 5,
        temperature: float = 0.7,
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
        # Build classification and audience context
        classification_context = {
            "guidance": "This is GUIDANCE - suggestive, non-prescriptive recommendations. Use language like 'consider', 'might', 'could help'. Present options and trade-offs.",
            "best-practice": "This is a BEST PRACTICE - established patterns with proven value. Use language like 'should', 'recommended', 'proven approach'. Include evidence from experience.",
            "mandate": "This is a MANDATE - required standards or policies. Use language like 'must', 'required', 'shall'. Be clear about consequences of non-compliance.",
            "principle": "This is a PRINCIPLE - fundamental truth or value. Use language that explores 'why' and underlying philosophy. Focus on timeless concepts.",
            "opinion": "This is a PERSONAL OPINION - subjective perspective. Use first-person language, acknowledge other viewpoints exist. Be authentic."
        }.get(classification, "This is guidance.")

        audience_context = {
            "ic-engineers": "TARGET AUDIENCE: Individual Contributor Engineers. Use practical, hands-on examples. Focus on daily work, technical skills, tools and techniques.",
            "senior-engineers": "TARGET AUDIENCE: Senior/Staff/Principal Engineers. Emphasize technical depth, architectural decisions, mentorship, and cross-team impact.",
            "engineering-leaders": "TARGET AUDIENCE: Engineering Managers, Directors, VPs. Focus on people management, team dynamics, org structure, strategic planning.",
            "qa-engineers": "TARGET AUDIENCE: QA and Test Engineers. Emphasize quality practices, testing strategies, automation, and quality culture.",
            "devops-sre": "TARGET AUDIENCE: DevOps and SRE. Focus on infrastructure, reliability, deployment, monitoring, and operational excellence.",
            "product-managers": "TARGET AUDIENCE: Product Managers. Emphasize product thinking, user needs, roadmaps, and cross-functional collaboration.",
            "technical-leadership": "TARGET AUDIENCE: Technical Leads and Architects. Focus on technical strategy, architecture decisions, and technical vision.",
            "all-disciplines": "TARGET AUDIENCE: All Technical Roles. Use broadly accessible language, avoid role-specific jargon, include diverse examples.",
            "executives": "TARGET AUDIENCE: C-level and Senior Leadership. Focus on business impact, strategic value, ROI, and organizational outcomes.",
            "general": "TARGET AUDIENCE: General/Non-Technical. Minimize jargon, explain technical concepts simply, use analogies."
        }.get(audience, "TARGET AUDIENCE: General technical audience.")

        # Build prompt for outline generation
        system_prompt = f"""You are an expert at creating document outlines.
Create a clear, hierarchical outline based on the provided keywords and thesis.
Focus on logical flow and comprehensive coverage of the topic.

{classification_context}

{audience_context}

Return ONLY the outline in this format:

## Section Title
Brief description of what this section covers

### Subsection Title
Brief description

Continue this pattern for all sections."""

        user_prompt = f"""Create a detailed outline for a document with:

Title: {title}
Classification: {classification.replace('-', ' ').title()}
Audience: {audience.replace('-', ' ').title()}
Keywords: {', '.join(keywords)}
{f'Thesis: {thesis}' if thesis else ''}

Create approximately {num_sections} main sections with relevant subsections.
Each section should have a title and brief description of its content.
Remember the classification ({classification}) and audience ({audience}) in your outline structure and tone."""

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
