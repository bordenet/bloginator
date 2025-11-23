"""AI slop detection - identifies and flags AI-generated artifacts."""

import re
from dataclasses import dataclass

from bloginator.prompts.loader import PromptLoader


@dataclass
class SlopViolation:
    """A detected AI slop violation."""

    pattern_name: str
    severity: str  # critical, high, medium, low
    message: str
    matched_text: str
    line_number: int | None = None
    column_number: int | None = None


class SlopDetector:
    """Detect AI-generated slop in text.

    Loads slop patterns from prompt YAML files and detects violations.
    Patterns include:
    - Em-dashes (—)
    - Flowery corporate jargon
    - Hedging words
    - Vague language
    """

    def __init__(self, prompt_loader: PromptLoader | None = None):
        """Initialize slop detector.

        Args:
            prompt_loader: Prompt loader (creates default if None)
        """
        self.prompt_loader = prompt_loader or PromptLoader()
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load AI slop patterns from prompt files."""
        # Load from draft prompt (has comprehensive slop patterns)
        draft_prompt = self.prompt_loader.load("draft/base.yaml")
        self.patterns = draft_prompt.ai_slop_patterns

    def detect(self, text: str) -> list[SlopViolation]:
        """Detect AI slop in text.

        Args:
            text: Text to check

        Returns:
            List of detected violations
        """
        violations: list[SlopViolation] = []

        # Check em-dashes
        if "em_dashes" in self.patterns:
            pattern_config = self.patterns["em_dashes"]
            pattern = pattern_config["pattern"]
            if pattern in text:
                # Find all occurrences with line numbers
                for line_num, line in enumerate(text.split("\n"), 1):
                    if pattern in line:
                        violations.append(
                            SlopViolation(
                                pattern_name="em_dashes",
                                severity=pattern_config["severity"],
                                message=pattern_config["message"],
                                matched_text=pattern,
                                line_number=line_num,
                            )
                        )

        # Check flowery phrases
        if "flowery_phrases" in self.patterns:
            pattern_config = self.patterns["flowery_phrases"]
            patterns_list = pattern_config["patterns"]
            for phrase in patterns_list:
                # Case-insensitive search
                if re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
                    # Find line numbers
                    for line_num, line in enumerate(text.split("\n"), 1):
                        if re.search(rf"\b{re.escape(phrase)}\b", line, re.IGNORECASE):
                            violations.append(
                                SlopViolation(
                                    pattern_name="flowery_phrases",
                                    severity=pattern_config["severity"],
                                    message=f"{pattern_config['message']}: '{phrase}'",
                                    matched_text=phrase,
                                    line_number=line_num,
                                )
                            )

        # Check hedging words
        if "hedging_words" in self.patterns:
            pattern_config = self.patterns["hedging_words"]
            patterns_list = pattern_config["patterns"]
            for phrase in patterns_list:
                if re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
                    for line_num, line in enumerate(text.split("\n"), 1):
                        if re.search(rf"\b{re.escape(phrase)}\b", line, re.IGNORECASE):
                            violations.append(
                                SlopViolation(
                                    pattern_name="hedging_words",
                                    severity=pattern_config["severity"],
                                    message=f"{pattern_config['message']}: '{phrase}'",
                                    matched_text=phrase,
                                    line_number=line_num,
                                )
                            )

        # Check vague language
        if "vague_language" in self.patterns:
            pattern_config = self.patterns["vague_language"]
            patterns_list = pattern_config["patterns"]
            for phrase in patterns_list:
                if re.search(rf"\b{re.escape(phrase)}\b", text, re.IGNORECASE):
                    for line_num, line in enumerate(text.split("\n"), 1):
                        if re.search(rf"\b{re.escape(phrase)}\b", line, re.IGNORECASE):
                            violations.append(
                                SlopViolation(
                                    pattern_name="vague_language",
                                    severity=pattern_config["severity"],
                                    message=f"{pattern_config['message']}: '{phrase}'",
                                    matched_text=phrase,
                                    line_number=line_num,
                                )
                            )

        return violations

    def has_critical_violations(self, text: str) -> bool:
        """Check if text has critical violations.

        Args:
            text: Text to check

        Returns:
            True if critical violations found
        """
        violations = self.detect(text)
        return any(v.severity == "critical" for v in violations)

