"""Refinement engine for iterative draft improvement."""

import logging
from typing import Any

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import LLMClient
from bloginator.generation.safety_validator import SafetyValidator
from bloginator.generation.voice_scorer import VoiceScorer
from bloginator.models.draft import Draft, DraftSection
from bloginator.search import Searcher

logger = logging.getLogger(__name__)


class RefinementEngine:
    """Iterative refinement of draft documents based on natural language feedback.

    The refinement engine:
    1. Parses natural language feedback to understand what to change
    2. Identifies which sections need regeneration
    3. Regenerates targeted sections while preserving overall structure
    4. Optionally re-scores voice and validates safety

    Attributes:
        llm_client: LLM for parsing feedback and generating refinements
        draft_generator: For regenerating sections
        searcher: For finding relevant corpus content
        voice_scorer: Optional voice similarity scorer
        safety_validator: Optional blocklist validator
    """

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: Searcher,
        voice_scorer: VoiceScorer | None = None,
        safety_validator: SafetyValidator | None = None,
    ):
        """Initialize refinement engine.

        Args:
            llm_client: LLM client for refinement
            searcher: Searcher for corpus retrieval
            voice_scorer: Optional voice similarity scorer
            safety_validator: Optional safety validator
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.voice_scorer = voice_scorer
        self.safety_validator = safety_validator

        # Create draft generator for section regeneration
        self.draft_generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
        )

    def parse_feedback(self, draft: Draft, feedback: str) -> dict[str, Any]:
        """Parse natural language feedback to identify refinement actions.

        Args:
            draft: Current draft
            feedback: User's natural language feedback

        Returns:
            Dictionary with:
            - action: 'regenerate', 'tone_change', 'expand', 'condense', 'global'
            - target_sections: List of section titles to modify (empty for global)
            - instructions: Specific instructions for refinement
        """
        # Build prompt to parse feedback
        section_list = "\n".join([f"- {s.title}" for s in draft.sections])

        parse_prompt = f"""You are analyzing user feedback about a draft document to determine what changes are needed.

Document title: {draft.title}
Document sections:
{section_list}

User feedback: "{feedback}"

Determine:
1. What type of change is requested (regenerate, tone_change, expand, condense, or global)
2. Which specific sections should be modified (or "all" for global changes)
3. Specific instructions for how to modify the content

Respond in this exact format:
ACTION: <action_type>
SECTIONS: <comma-separated section titles, or "all">
INSTRUCTIONS: <specific refinement instructions>

Examples:
- "Make the introduction more engaging" → ACTION: tone_change, SECTIONS: Introduction, INSTRUCTIONS: Make tone more engaging and compelling
- "Add more detail about testing" → ACTION: expand, SECTIONS: Testing, INSTRUCTIONS: Add more depth and detail about testing practices
- "The whole document is too technical" → ACTION: global, SECTIONS: all, INSTRUCTIONS: Reduce technical jargon and make more accessible
"""

        try:
            response = self.llm_client.generate(
                prompt=parse_prompt,
                temperature=0.3,  # Lower for more consistent parsing
                max_tokens=500,
            )

            # Parse LLM response
            lines = response.content.strip().split("\n")
            action = "global"
            target_sections: list[str] = []
            instructions = feedback  # Fallback to raw feedback

            for line in lines:
                if line.startswith("ACTION:"):
                    action = line.split(":", 1)[1].strip().lower()
                elif line.startswith("SECTIONS:"):
                    sections_str = line.split(":", 1)[1].strip()
                    if sections_str.lower() == "all":
                        target_sections = []  # Empty list means all sections
                    else:
                        target_sections = [s.strip() for s in sections_str.split(",")]
                elif line.startswith("INSTRUCTIONS:"):
                    instructions = line.split(":", 1)[1].strip()

            return {
                "action": action,
                "target_sections": target_sections,
                "instructions": instructions,
            }

        except Exception as e:
            logger.warning(f"Failed to parse feedback with LLM: {e}, using fallback")
            # Fallback: treat as global change
            return {
                "action": "global",
                "target_sections": [],
                "instructions": feedback,
            }

    def refine_draft(
        self,
        draft: Draft,
        feedback: str,
        validate_safety: bool = True,
        score_voice: bool = True,
    ) -> Draft:
        """Refine a draft based on natural language feedback.

        Args:
            draft: Current draft to refine
            feedback: Natural language feedback
            validate_safety: Whether to validate against blocklist
            score_voice: Whether to score voice similarity

        Returns:
            Refined draft

        Raises:
            ValueError: If safety validation fails
        """
        # Parse feedback to understand what to do
        parsed = self.parse_feedback(draft, feedback)
        action = parsed["action"]
        target_sections = parsed["target_sections"]
        instructions = parsed["instructions"]

        logger.info(
            f"Refinement action: {action}, "
            f"targets: {target_sections if target_sections else 'all'}"
        )

        # Determine which sections to regenerate
        if not target_sections:
            # Global change - regenerate all sections
            sections_to_refine = draft.sections
        else:
            # Find matching sections
            sections_to_refine = [s for s in draft.sections if s.title in target_sections]

        if not sections_to_refine:
            logger.warning("No sections matched for refinement, returning original")
            return draft

        # Create refined draft
        refined_draft = Draft(
            title=draft.title,
            thesis=draft.thesis,
            keywords=draft.keywords,
            sections=[],
        )

        # Regenerate targeted sections
        for section in draft.sections:
            if section in sections_to_refine:
                # Regenerate this section with refinement instructions
                refined_section = self._refine_section(
                    section=section,
                    instructions=instructions,
                    keywords=draft.keywords,
                )
                refined_draft.sections.append(refined_section)
            else:
                # Keep original section unchanged
                refined_draft.sections.append(section)

        # Score voice if requested
        if score_voice and self.voice_scorer:
            self.voice_scorer.score_draft(refined_draft)
        else:
            refined_draft.calculate_stats()

        # Validate safety if requested
        if validate_safety and self.safety_validator:
            self.safety_validator.validate_draft(refined_draft)

        return refined_draft

    def _refine_section(
        self,
        section: DraftSection,
        instructions: str,
        keywords: list[str],
    ) -> DraftSection:
        """Refine a single section based on instructions.

        Args:
            section: Original section
            instructions: Refinement instructions
            keywords: Context keywords

        Returns:
            Refined section
        """
        # Search for relevant content
        search_query = f"{section.title} {' '.join(keywords[:3])}"
        search_results = self.searcher.search(
            query=search_query,
            n_results=5,
        )

        if not search_results:
            logger.warning(f"No search results for section '{section.title}'")
            return section

        # Build context from search results
        context = "\n\n".join(
            [
                f"[Source: {r.metadata.get('filename', 'unknown')}]\n{r.content}"
                for r in search_results[:5]
            ]
        )

        # Build refinement prompt
        refine_prompt = f"""Refine the following section based on the user's feedback.

Section Title: {section.title}

Current Content:
{section.content}

User Feedback: {instructions}

Relevant content from your writing corpus:
{context}

Instructions:
1. Apply the user's feedback to improve the section
2. Maintain the authentic voice from your corpus
3. Keep the section focused and coherent
4. Preserve any important points from the original

Write the refined section content:"""

        try:
            response = self.llm_client.generate(
                prompt=refine_prompt,
                temperature=0.7,
                max_tokens=2000,
                system_prompt="You are refining content to match the author's authentic voice based on their historical writing.",
            )

            # Create refined section
            refined_section = DraftSection(
                title=section.title,
                content=response.content.strip(),
                citations=[],  # Will be populated from search results
                subsections=section.subsections,  # Preserve subsections
            )

            # Add citations from search results
            for result in search_results[:3]:
                citation = {
                    "chunk_id": result.chunk_id,
                    "document_id": result.metadata.get("document_id", ""),
                    "filename": result.metadata.get("filename", "unknown"),
                    "content_preview": result.content[:200],
                    "similarity_score": result.similarity_score,
                }
                from bloginator.models.draft import Citation

                refined_section.citations.append(Citation(**citation))

            return refined_section

        except Exception as e:
            logger.error(f"Failed to refine section '{section.title}': {e}")
            return section  # Return original on error

    def refine_section_only(
        self,
        draft: Draft,
        section_title: str,
        instructions: str,
    ) -> DraftSection | None:
        """Refine a single section by title.

        Args:
            draft: The draft containing the section
            section_title: Title of section to refine
            instructions: Refinement instructions

        Returns:
            Refined section or None if not found
        """
        # Find the section
        target_section = None
        for section in draft.sections:
            if section.title == section_title:
                target_section = section
                break

        if not target_section:
            return None

        return self._refine_section(
            section=target_section,
            instructions=instructions,
            keywords=draft.keywords,
        )
