"""Quality review and revision of generated drafts.

Provides final quality control step that enforces strict standards for
brevity, clarity, and professionalism before content is delivered to users.
"""

import logging

from bloginator.generation.llm_client import LLMClient
from bloginator.models.draft import Draft
from bloginator.prompts.loader import PromptLoader


logger = logging.getLogger(__name__)


class QualityReviewer:
    """Reviews and revises blog drafts to enforce quality standards.

    Acts as a senior editor with limited time who demands wiki-style brevity,
    eliminates redundancy, and converts PowerPoint-style content to prose/tables.

    Attributes:
        llm_client: LLM client for generating revisions
        prompt_loader: Loader for quality review prompts
    """

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_loader: PromptLoader | None = None,
    ):
        """Initialize quality reviewer.

        Args:
            llm_client: LLM client for revision generation
            prompt_loader: Prompt loader (creates default if None)
        """
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader or PromptLoader()

    def review_and_revise(
        self,
        draft: Draft,
        temperature: float = 0.3,
    ) -> str:
        """Review draft and return revised content.

        Args:
            draft: Draft to review and revise
            temperature: LLM temperature (lower = more conservative edits)

        Returns:
            Revised blog content as markdown string

        Example:
            >>> reviewer = QualityReviewer(llm_client)
            >>> revised_content = reviewer.review_and_revise(draft)
            >>> print(f"Revised to {len(revised_content.split())} words")
        """
        logger.info("Starting quality review of draft: %s", draft.title)

        # Convert draft to full markdown
        original_content = draft.to_markdown()

        # Load review prompt
        prompt_template = self.prompt_loader.load("review/base.yaml")

        # Render prompts
        system_prompt = prompt_template.render_system_prompt()
        user_prompt = prompt_template.render_user_prompt(
            draft_content=original_content
        )

        # Get LLM revision
        logger.info("Requesting quality review from LLM...")
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=8000,  # Allow for full blog rewrite
        )

        revised_content = response.content.strip()

        # Log metrics
        original_words = len(original_content.split())
        revised_words = len(revised_content.split())
        reduction_pct = int((1 - revised_words / original_words) * 100)

        logger.info(
            "Quality review complete: %d words → %d words (%d%% reduction)",
            original_words,
            revised_words,
            reduction_pct,
        )

        return revised_content
