"""Outline prompt construction and template rendering.

Handles building and customizing prompts for outline generation,
including system prompt rendering and user prompt construction.
"""

from bloginator.prompts.loader import PromptLoader
from bloginator.search import SearchResult


def build_search_queries(
    title: str,
    keywords: list[str],
    thesis: str = "",
) -> list[str]:
    """Build specific, contextualized search queries.

    Creates longer queries that provide better topic discrimination
    by including title, keywords, and thesis context.

    Args:
        title: Document title
        keywords: Topic keywords
        thesis: Optional thesis statement for additional context

    Returns:
        List of search queries with increasing specificity
    """
    queries = []

    # Query 1: Full title (most specific)
    queries.append(title)

    # Query 2: Title + first 2 keywords for context
    if len(keywords) >= 2:
        queries.append(f"{title} {keywords[0]} {keywords[1]}")

    # Query 3: Keywords with thesis context (if available)
    if thesis and len(keywords) >= 1:
        # Extract key phrases from thesis (first 50 chars)
        thesis_snippet = thesis[:50].strip()
        queries.append(f"{keywords[0]} {keywords[1] if len(keywords) > 1 else ''} {thesis_snippet}")

    # Query 4: Longer keyword combination for broader coverage
    if len(keywords) >= 3:
        queries.append(f"{keywords[0]} {keywords[1]} {keywords[2]}")
    elif len(keywords) >= 2:
        queries.append(f"{keywords[0]} {keywords[1]} practices")

    # Remove empty strings and deduplicate
    queries = [q.strip() for q in queries if q.strip()]
    return list(dict.fromkeys(queries))  # Preserve order, remove duplicates


def build_corpus_context(results: list[SearchResult]) -> str:
    """Build rich corpus context with metadata and longer previews.

    Provides LLM with sufficient context to understand corpus content
    and validate topic relevance. Includes similarity scores and source
    metadata to help LLM assess result quality.

    Args:
        results: Search results from corpus searcher

    Returns:
        Formatted corpus context string with metadata
    """
    if not results:
        return "No corpus material found for this topic."

    context_parts = ["CORPUS SEARCH RESULTS (validate topic match!):\n"]

    # Increase from 5 to 8 results for better coverage
    for i, result in enumerate(results[:8], 1):
        # Increase from 200 to 500 characters for better context
        preview = result.content[:500].replace("\n", " ").strip()

        # Add rich metadata
        similarity = f"{result.similarity_score:.3f}" if result.similarity_score else "N/A"
        source = result.metadata.get("filename", "unknown")

        context_parts.append(
            f"[{i}] Similarity: {similarity} | Source: {source}\n" f"{preview}...\n"
        )

    return "\n".join(context_parts)


class OutlinePromptBuilder:
    """Build prompts for outline generation with corpus grounding.

    Handles loading prompt templates, rendering with context,
    and customizing with user-provided templates.
    """

    def __init__(self, prompt_loader: PromptLoader | None = None) -> None:
        """Initialize prompt builder.

        Args:
            prompt_loader: Prompt loader instance (creates default if None)
        """
        self.prompt_loader = prompt_loader or PromptLoader()

    def build_system_prompt(
        self,
        classification: str = "guidance",
        audience: str = "all-disciplines",
    ) -> str:
        """Build system prompt with classification and audience context.

        Args:
            classification: Content classification (guidance, best-practice, etc.)
            audience: Target audience (ic-engineers, engineering-leaders, etc.)

        Returns:
            Rendered system prompt string
        """
        prompt_template = self.prompt_loader.load("outline/base.yaml")

        # Get context mappings
        classification_contexts = prompt_template.parameters.get("classification_contexts", {})
        audience_contexts = prompt_template.parameters.get("audience_contexts", {})

        # Get defaults if not found
        classification_context = classification_contexts.get(classification, "This is guidance.")
        audience_context = audience_contexts.get(
            audience, "TARGET AUDIENCE: General technical audience."
        )

        # Render system prompt with context
        return prompt_template.render_system_prompt(
            classification_context=classification_context,
            audience_context=audience_context,
        )

    def build_user_prompt(
        self,
        title: str,
        keywords: list[str],
        thesis: str = "",
        classification: str = "guidance",
        audience: str = "all-disciplines",
        num_sections: int = 5,
        corpus_context: str = "",
        custom_template: str | None = None,
    ) -> str:
        """Build user prompt with all context and optional customization.

        Args:
            title: Document title
            keywords: Topic keywords
            thesis: Optional thesis statement
            classification: Content classification
            audience: Target audience
            num_sections: Target number of sections
            corpus_context: Corpus search context
            custom_template: Optional custom prompt template

        Returns:
            Rendered user prompt string
        """
        prompt_template = self.prompt_loader.load("outline/base.yaml")

        # Render base prompt
        base_prompt = prompt_template.render_user_prompt(
            title=title,
            classification=classification.replace("-", " ").title(),
            audience=audience.replace("-", " ").title(),
            keywords=", ".join(keywords),
            thesis=thesis if thesis else "",
            num_sections=num_sections,
            corpus_context=corpus_context,
        )

        # Prepend custom template if provided
        if custom_template:
            return f"""{custom_template}

---

{base_prompt}"""

        return base_prompt
