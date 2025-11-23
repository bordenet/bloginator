"""Quality assurance system for blog generation.

This module provides fault detection and retry logic for blog generation,
ensuring high-quality output by detecting poor results and retrying with
alternate LLM prompts until satisfactory content is produced.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.quality.slop_detector import SlopDetector


logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality levels for generated content."""

    EXCELLENT = "excellent"  # Score >= 4.5, no critical violations
    GOOD = "good"  # Score >= 4.0, no critical violations
    ACCEPTABLE = "acceptable"  # Score >= 3.5, no critical violations
    POOR = "poor"  # Score < 3.5 or has critical violations
    FAILED = "failed"  # Unable to generate acceptable content


@dataclass
class QualityAssessment:
    """Assessment of content quality."""

    quality_level: QualityLevel
    score: float
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    total_violations: int
    issues: list[str]
    recommendations: list[str]
    retry_suggested: bool


class QualityAssurance:
    """Quality assurance system for blog generation.

    This system:
    1. Evaluates generated content for quality issues
    2. Detects AI slop and other problems
    3. Determines if retry is needed
    4. Suggests alternate prompts for retry
    5. Tracks retry attempts and convergence
    """

    def __init__(
        self,
        min_acceptable_score: float = 3.5,
        max_retries: int = 3,
        critical_violations_threshold: int = 0,
    ):
        """Initialize quality assurance system.

        Args:
            min_acceptable_score: Minimum score to accept (0-5 scale)
            max_retries: Maximum number of retry attempts
            critical_violations_threshold: Max critical violations allowed
        """
        self.min_acceptable_score = min_acceptable_score
        self.max_retries = max_retries
        self.critical_violations_threshold = critical_violations_threshold
        self.slop_detector = SlopDetector()

    def assess_quality(self, outline: Outline, draft: Draft) -> QualityAssessment:
        """Assess the quality of generated content.

        Args:
            outline: Generated outline
            draft: Generated draft

        Returns:
            QualityAssessment with detailed evaluation
        """
        # Collect all text
        all_text = "\n\n".join(section.content for section in draft.sections)

        # Detect slop violations
        violations = self.slop_detector.detect(all_text)
        critical = len([v for v in violations if v.severity == "critical"])
        high = len([v for v in violations if v.severity == "high"])
        medium = len([v for v in violations if v.severity == "medium"])
        low = len([v for v in violations if v.severity == "low"])
        total = len(violations)

        # Calculate score (0-5 scale)
        score = 5.0
        score -= critical * 2.0  # Critical violations are severe
        score -= high * 0.5
        score -= medium * 0.2
        score -= low * 0.1
        score = max(0.0, min(5.0, score))

        # Collect issues
        issues = []
        if critical > 0:
            issues.append(f"{critical} critical slop violations (em-dashes, etc.)")
        if high > 0:
            issues.append(f"{high} high-severity violations (corporate jargon)")
        if medium > 0:
            issues.append(f"{medium} medium-severity violations (hedging words)")
        if low > 0:
            issues.append(f"{low} low-severity violations (vague language)")

        # Determine quality level
        if critical > self.critical_violations_threshold:
            quality_level = QualityLevel.POOR
        elif score >= 4.5:
            quality_level = QualityLevel.EXCELLENT
        elif score >= 4.0:
            quality_level = QualityLevel.GOOD
        elif score >= self.min_acceptable_score:
            quality_level = QualityLevel.ACCEPTABLE
        else:
            quality_level = QualityLevel.POOR

        # Generate recommendations
        recommendations = self._generate_recommendations(critical, high, medium, low, score)

        # Determine if retry is suggested
        retry_suggested = quality_level == QualityLevel.POOR

        return QualityAssessment(
            quality_level=quality_level,
            score=score,
            critical_violations=critical,
            high_violations=high,
            medium_violations=medium,
            low_violations=low,
            total_violations=total,
            issues=issues,
            recommendations=recommendations,
            retry_suggested=retry_suggested,
        )

    def _generate_recommendations(
        self, critical: int, high: int, medium: int, low: int, score: float
    ) -> list[str]:
        """Generate recommendations for improving content quality."""
        recommendations = []

        if critical > 0:
            recommendations.append(
                "Add explicit instruction: 'NEVER use em-dashes (—). Use hyphens (-) or restructure.'"
            )
        if high > 0:
            recommendations.append(
                "Add: 'Avoid corporate jargon. Use concrete, specific language.'"
            )
        if medium > 0:
            recommendations.append("Add: 'Be direct and specific. Avoid hedging words.'")
        if score < 3.0:
            recommendations.append("Consider using a different LLM model or provider")

        return recommendations
