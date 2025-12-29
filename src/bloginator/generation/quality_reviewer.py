"""Quality review and revision of generated drafts.

Provides final quality control step that enforces strict standards for
brevity, clarity, and professionalism before content is delivered to users.
"""

import json
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

    def _analyze_structure(
        self,
        draft_content: str,
    ) -> dict:
        """Analyze draft for structural and quality issues.

        This is the first call in the 2-call workflow. It identifies specific
        issues without fixing them.

        Args:
            draft_content: Full markdown draft content

        Returns:
            Dictionary with 'issues' list and 'summary' metadata
        """
        logger.info("Analyzing draft structure for quality issues...")

        # Load structural analysis prompt
        prompt_template = self.prompt_loader.load("review/structural-analysis.yaml")

        # Render prompts
        system_prompt = prompt_template.render_system_prompt()
        user_prompt = prompt_template.render_user_prompt(draft_content=draft_content)

        # Get analysis from LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,  # Deterministic analysis
            max_tokens=1000,  # JSON response expected
        )

        # Parse JSON response
        try:
            analysis = json.loads(response.content.strip())
            logger.info(
                "Analysis complete: %d issues found (word count: %d)",
                analysis.get("summary", {}).get("total_issues", 0),
                analysis.get("summary", {}).get("word_count", 0),
            )
            return analysis
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse analysis JSON: {e}")
            # Return default "no issues" structure
            return {
                "issues": [],
                "summary": {
                    "total_issues": 0,
                    "word_count": len(draft_content.split()),
                    "sections_over_limit": 0,
                    "needs_major_revision": False,
                },
            }

    def _revise_content(
        self,
        draft_content: str,
        issues: list[dict],
        temperature: float = 0.3,
    ) -> str:
        """Revise draft content based on identified issues.

        This is the second call in the 2-call workflow. It makes targeted
        fixes based on the analysis.

        Args:
            draft_content: Original markdown draft
            issues: List of issues from structural analysis
            temperature: LLM temperature for revision

        Returns:
            Revised markdown content
        """
        logger.info("Revising content to fix %d identified issues...", len(issues))

        # Load revision prompt
        prompt_template = self.prompt_loader.load("review/base.yaml")

        # Build issue summary for context
        issue_summary = "\n".join(
            [
                f"- [{issue['severity'].upper()}] {issue['type']}: {issue['details']}"
                for issue in issues
            ]
        )

        # Render prompts with issues context
        system_prompt = prompt_template.render_system_prompt()
        user_prompt = prompt_template.render_user_prompt(draft_content=draft_content)

        # Prepend issue summary to user prompt
        user_prompt = f"""IDENTIFIED ISSUES TO FIX:
{issue_summary}

---

{user_prompt}"""

        # Get revised content from LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=8000,  # Allow for full blog rewrite
        )

        revised_content = response.content.strip()

        # Log metrics
        original_words = len(draft_content.split())
        revised_words = len(revised_content.split())
        reduction_pct = int((1 - revised_words / original_words) * 100) if original_words > 0 else 0

        logger.info(
            "Revision complete: %d words → %d words (%d%% reduction)",
            original_words,
            revised_words,
            reduction_pct,
        )

        return revised_content

    def review_and_revise(
        self,
        draft: Draft,
        temperature: float = 0.3,
    ) -> str:
        """Review draft and return revised content using 2-call workflow.

        Uses a two-step process:
        1. Structural analysis to identify specific issues
        2. Targeted revision to fix identified issues

        If no issues are found in analysis, returns original content unchanged
        (optimization to skip unnecessary revision call).

        Args:
            draft: Draft to review and revise
            temperature: LLM temperature for revision (lower = more conservative)

        Returns:
            Revised blog content as markdown string

        Example:
            >>> reviewer = QualityReviewer(llm_client)
            >>> revised_content = reviewer.review_and_revise(draft)
            >>> print(f"Revised to {len(revised_content.split())} words")
        """
        logger.info("Starting 2-call quality review of draft: %s", draft.title)

        # Convert draft to full markdown
        original_content = draft.to_markdown()

        # CALL 1: Structural analysis
        analysis = self._analyze_structure(original_content)

        # If no issues found, skip revision (efficiency optimization)
        issues = analysis.get("issues", [])
        if not issues:
            logger.info("No quality issues found - returning original content")
            return original_content

        # CALL 2: Content revision based on identified issues
        revised_content = self._revise_content(
            draft_content=original_content,
            issues=issues,
            temperature=temperature,
        )

        logger.info("Quality review complete (2-call workflow)")
        return revised_content
