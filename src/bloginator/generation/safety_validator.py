"""Safety validation for generated content using blocklist."""

from pathlib import Path
from typing import Any

from bloginator.models.draft import Draft, DraftSection
from bloginator.safety import BlocklistManager


class SafetyValidator:
    """Validate generated content against blocklist.

    Integrates blocklist validation into generation pipeline to prevent
    proprietary content leakage.

    Attributes:
        blocklist_manager: Manager for blocklist entries
        auto_reject: Whether to automatically reject drafts with violations
    """

    def __init__(
        self,
        blocklist_file: Path,
        auto_reject: bool = True,
    ):
        """Initialize safety validator.

        Args:
            blocklist_file: Path to blocklist JSON file
            auto_reject: Whether to auto-reject drafts with violations
        """
        self.blocklist_manager = BlocklistManager(blocklist_file)
        self.auto_reject = auto_reject

    def validate_draft(self, draft: Draft) -> None:
        """Validate entire draft against blocklist.

        Updates draft.has_blocklist_violations and
        draft.blocklist_validation_result.

        Args:
            draft: Draft to validate (modified in place)

        Raises:
            ValueError: If auto_reject=True and violations found

        Example:
            >>> validator = SafetyValidator(Path(".bloginator/blocklist.json"))
            >>> validator.validate_draft(draft)
            >>> if draft.has_blocklist_violations:
            ...     print("Violations found!")
        """
        all_violations = []

        # Validate each section
        for section in draft.get_all_sections():
            section_result = self._validate_section(section)

            if not section_result["is_valid"]:
                all_violations.extend(section_result["violations"])
                section.has_blocklist_violations = True

        # Update draft
        draft.has_blocklist_violations = len(all_violations) > 0
        draft.blocklist_validation_result = {
            "is_valid": len(all_violations) == 0,
            "violations": all_violations,
            "total_violations": len(all_violations),
        }

        # Auto-reject if configured
        if self.auto_reject and draft.has_blocklist_violations:
            violation_summary = self._format_violation_summary(all_violations)
            raise ValueError(
                f"Draft rejected: {len(all_violations)} blocklist violation(s) found.\n\n"
                f"{violation_summary}\n\n"
                f"Review and remove these terms before regenerating."
            )

    def _validate_section(self, section: DraftSection) -> dict[str, Any]:
        """Validate a section's content.

        Args:
            section: Section to validate

        Returns:
            Validation result dictionary
        """
        if not section.content:
            return {"is_valid": True, "violations": []}

        # Validate content
        result = self.blocklist_manager.validate_text(section.content)

        # Add section context to violations
        for violation in result.get("violations", []):
            violation["section_title"] = section.title

        return result

    def _format_violation_summary(self, violations: list[dict[str, Any]]) -> str:
        """Format violation summary for error message.

        Args:
            violations: List of violation dictionaries

        Returns:
            Formatted summary string
        """
        if not violations:
            return "No violations"

        lines = []
        for i, v in enumerate(violations, 1):
            lines.append(
                f"{i}. Pattern '{v['pattern']}' in section '{v.get('section_title', 'Unknown')}'"
            )
            matches_str = ", ".join(f"'{m}'" for m in v["matches"][:3])
            lines.append(f"   Matched: {matches_str}")
            if v.get("notes"):
                lines.append(f"   Notes: {v['notes']}")

        return "\n".join(lines)

    def get_safe_sections(self, draft: Draft) -> list[DraftSection]:
        """Get list of sections without violations.

        Args:
            draft: Draft to analyze

        Returns:
            List of sections that passed validation
        """
        return [s for s in draft.get_all_sections() if not s.has_blocklist_violations]

    def get_unsafe_sections(self, draft: Draft) -> list[DraftSection]:
        """Get list of sections with violations.

        Args:
            draft: Draft to analyze

        Returns:
            List of sections with blocklist violations
        """
        return [s for s in draft.get_all_sections() if s.has_blocklist_violations]

    def validate_before_generation(
        self, title: str, keywords: list[str], thesis: str = ""
    ) -> dict[str, Any]:
        """Pre-validate inputs before generation.

        Checks if title, keywords, or thesis contain blocklist violations
        before starting expensive generation process.

        Args:
            title: Document title
            keywords: Keywords list
            thesis: Thesis statement

        Returns:
            Validation result dictionary

        Example:
            >>> result = validator.validate_before_generation(
            ...     title="Acme Corp Engineering Culture",
            ...     keywords=["culture", "acme"]
            ... )
            >>> if not result['is_valid']:
            ...     print("Cannot generate: inputs contain violations")
        """
        text_to_validate = f"{title} {' '.join(keywords)} {thesis}"
        result = self.blocklist_manager.validate_text(text_to_validate)

        if not result["is_valid"]:
            # Add context to violations
            for violation in result["violations"]:
                violation["location"] = "input parameters"

        return result

    def add_to_blocklist(
        self,
        pattern: str,
        pattern_type: str = "exact",
        category: str = "other",
        notes: str = "",
    ) -> None:
        """Add entry to blocklist during generation workflow.

        Convenience method for adding entries discovered during generation.

        Args:
            pattern: Pattern to block
            pattern_type: Type of matching (exact, case_insensitive, regex)
            category: Category classification
            notes: Why this is blocked
        """
        import uuid

        from bloginator.models.blocklist import (
            BlocklistCategory,
            BlocklistEntry,
            BlocklistPatternType,
        )

        entry = BlocklistEntry(
            id=str(uuid.uuid4()),
            pattern=pattern,
            pattern_type=BlocklistPatternType(pattern_type),
            category=BlocklistCategory(category),
            notes=notes,
        )

        self.blocklist_manager.add_entry(entry)
