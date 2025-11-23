"""Retry orchestrator for blog generation with quality assurance.

This module orchestrates the retry logic for blog generation, using quality
assurance to detect poor results and retry with alternate prompts until
satisfactory content is produced.
"""

import logging
from dataclasses import dataclass
from typing import Any

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import LLMClient
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.prompts.loader import PromptLoader
from bloginator.quality.quality_assurance import QualityAssessment, QualityAssurance, QualityLevel
from bloginator.search.searcher import CorpusSearcher

logger = logging.getLogger(__name__)


@dataclass
class GenerationAttempt:
    """Record of a generation attempt."""

    attempt_number: int
    outline: Outline
    draft: Draft
    assessment: QualityAssessment
    prompt_variant: str


@dataclass
class GenerationResult:
    """Final result of generation with retries."""

    success: bool
    final_attempt: GenerationAttempt
    all_attempts: list[GenerationAttempt]
    total_attempts: int
    final_quality: QualityLevel


class RetryOrchestrator:
    """Orchestrates blog generation with quality assurance and retry logic."""

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: CorpusSearcher,
        quality_assurance: QualityAssurance | None = None,
        max_retries: int = 3,
    ):
        """Initialize retry orchestrator.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for RAG
            quality_assurance: Quality assurance system (creates default if None)
            max_retries: Maximum number of retry attempts
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.qa = quality_assurance or QualityAssurance(max_retries=max_retries)
        self.max_retries = max_retries

    def generate_with_retry(
        self,
        title: str,
        keywords: list[str],
        thesis: str,
        classification: str,
        audience: str,
    ) -> GenerationResult:
        """Generate blog content with quality assurance and retry logic.

        Args:
            title: Blog post title
            keywords: Keywords for the post
            thesis: Thesis statement
            classification: Content classification (best-practice, guidance, etc.)
            audience: Target audience

        Returns:
            GenerationResult with final content and quality assessment
        """
        attempts: list[GenerationAttempt] = []
        prompt_variants = self._get_prompt_variants()

        for attempt_num in range(self.max_retries + 1):
            # Select prompt variant
            variant_name = prompt_variants[min(attempt_num, len(prompt_variants) - 1)]
            logger.info(f"Generation attempt {attempt_num + 1}/{self.max_retries + 1} using variant: {variant_name}")

            # Load prompts with variant
            prompt_loader = self._load_prompt_variant(variant_name)

            # Generate content
            outline_gen = OutlineGenerator(
                llm_client=self.llm_client,
                searcher=self.searcher,
                prompt_loader=prompt_loader,
            )
            draft_gen = DraftGenerator(
                llm_client=self.llm_client,
                searcher=self.searcher,
                prompt_loader=prompt_loader,
            )

            outline = outline_gen.generate(
                title=title,
                keywords=keywords,
                thesis=thesis,
                classification=classification,
                audience=audience,
            )

            draft = draft_gen.generate(
                outline=outline,
                classification=classification,
                audience=audience,
            )

            # Assess quality
            assessment = self.qa.assess_quality(outline, draft)

            # Record attempt
            attempt = GenerationAttempt(
                attempt_number=attempt_num + 1,
                outline=outline,
                draft=draft,
                assessment=assessment,
                prompt_variant=variant_name,
            )
            attempts.append(attempt)

            logger.info(
                f"Attempt {attempt_num + 1}: Quality={assessment.quality_level.value}, "
                f"Score={assessment.score:.2f}, Violations={assessment.total_violations}"
            )

            # Check if quality is acceptable
            if not assessment.retry_suggested:
                logger.info(f"Acceptable quality achieved on attempt {attempt_num + 1}")
                return GenerationResult(
                    success=True,
                    final_attempt=attempt,
                    all_attempts=attempts,
                    total_attempts=len(attempts),
                    final_quality=assessment.quality_level,
                )

            # Log retry reason
            if attempt_num < self.max_retries:
                logger.warning(
                    f"Quality below threshold. Issues: {', '.join(assessment.issues)}. "
                    f"Retrying with variant: {prompt_variants[min(attempt_num + 1, len(prompt_variants) - 1)]}"
                )

        # Max retries exceeded
        logger.error(f"Failed to achieve acceptable quality after {len(attempts)} attempts")
        return GenerationResult(
            success=False,
            final_attempt=attempts[-1],
            all_attempts=attempts,
            total_attempts=len(attempts),
            final_quality=attempts[-1].assessment.quality_level,
        )

    def _get_prompt_variants(self) -> list[str]:
        """Get list of prompt variants to try in order."""
        return [
            "default",  # Standard prompts
            "strict_no_slop",  # Explicit anti-slop instructions
            "minimal",  # Minimal, direct prompts
        ]

    def _load_prompt_variant(self, variant: str) -> PromptLoader:
        """Load prompt variant.

        For now, returns default PromptLoader.
        In production, this would load different prompt templates.
        """
        # TODO: Implement actual prompt variant loading
        return PromptLoader()

