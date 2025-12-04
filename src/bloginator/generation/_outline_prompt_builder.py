"""Outline prompt construction and template rendering.

Handles building and customizing prompts for outline generation,
including system prompt rendering and user prompt construction.
"""

from bloginator.prompts.loader import PromptLoader
from bloginator.search import SearchResult


def build_search_queries(
    title: str,
    keywords: list[str],
) -> list[str]:
    """Build multiple search queries for corpus grounding.

    Generates variations to find different aspects of the topic
    (implementation, best practices, guides, etc.).

    Args:
        title: Document title
        keywords: Topic keywords

    Returns:
        List of search queries
    """
    return [
        title,  # Full title first
        f"{keywords[0]} {keywords[1]}" if len(keywords) > 1 else keywords[0],
        f"{keywords[0]} implementation" if keywords else "",
        f"{keywords[0]} best practices" if keywords else "",
        f"{' '.join(keywords[:2])} guide" if len(keywords) > 1 else "",
    ]


def build_corpus_context(results: list[SearchResult]) -> str:
    """Build corpus context string from search results.

    Extracts preview text from search results to ground outline
    generation in actual corpus content.

    Args:
        results: Search results from corpus searcher

    Returns:
        Formatted corpus context string
    """
    if not results:
        return ""

    context = "Key topics found in corpus:\n\n"
    for i, result in enumerate(results[:5], 1):
        preview = result.content[:200].replace("\n", " ").strip()
        context += f"{i}. {preview}...\n\n"

    return context


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
