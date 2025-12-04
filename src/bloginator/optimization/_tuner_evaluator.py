"""Evaluation logic for prompt optimization."""

import json
import logging
from typing import Any, cast

from jinja2 import Template

from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.optimization._tuner_models import TestCase
from bloginator.quality.slop_detector import SlopDetector


logger = logging.getLogger(__name__)


def count_violations_by_severity(
    all_text: str,
    slop_detector: SlopDetector,
) -> tuple[int, int, int, int]:
    """Count violations by severity level.

    Args:
        all_text: Text to analyze
        slop_detector: SlopDetector instance

    Returns:
        Tuple of (critical, high, medium, low) violation counts
    """
    violations = slop_detector.detect(all_text)
    critical = len([v for v in violations if v.severity == "critical"])
    high = len([v for v in violations if v.severity == "high"])
    medium = len([v for v in violations if v.severity == "medium"])
    low = len([v for v in violations if v.severity == "low"])
    return critical, high, medium, low


def score_draft_basic(draft: Draft, slop_detector: SlopDetector) -> float:
    """Score a draft based on slop violations (basic scoring).

    Args:
        draft: Draft to score
        slop_detector: SlopDetector instance

    Returns:
        Score from 0.0 to 5.0
    """
    all_text = "\n\n".join(section.content for section in draft.sections)

    # Check for slop violations
    violations = slop_detector.detect(all_text)
    critical_violations = [v for v in violations if v.severity == "critical"]
    high_violations = [v for v in violations if v.severity == "high"]

    # Calculate slop penalty
    slop_penalty = 0.0
    slop_penalty += len(critical_violations) * 2.0  # -2.0 per critical
    slop_penalty += len(high_violations) * 0.5  # -0.5 per high

    # Base score starts at 5.0
    score = 5.0 - slop_penalty

    # Ensure score is in valid range
    score = max(0.0, min(5.0, score))

    return score


def get_automated_evaluation(
    test_case: TestCase,
    draft: Draft,
    round_number: int,
    slop_detector: SlopDetector,
) -> dict[str, Any]:
    """Get automated evaluation based on slop detection and heuristics.

    This is a simplified evaluator that doesn't require AI/manual intervention.
    It focuses on measurable metrics: slop violations, length, structure.

    Args:
        test_case: Test case being evaluated
        draft: Generated draft
        round_number: Current round number
        slop_detector: SlopDetector instance

    Returns:
        Evaluation dict with score, violations, and evolutionary strategy
    """
    all_text = "\n\n".join(section.content for section in draft.sections)

    # Detect slop violations
    critical, high, medium, low = count_violations_by_severity(all_text, slop_detector)
    total_violations = critical + high + medium + low

    # Calculate base score (0-5 scale)
    score = 5.0
    score -= critical * 2.0  # Critical violations are severe
    score -= high * 0.5
    score -= medium * 0.2
    score -= low * 0.1
    score = max(0.0, min(5.0, score))  # Clamp to [0, 5]

    # Determine evolutionary strategy based on violations
    if round_number <= 10:
        # Rounds 1-10: Focus on eliminating critical slop
        focus = "slop_elimination"
        if critical > 0:
            prompt_to_modify = "draft"
            priority = "high"
            changes = [
                {
                    "section": "tone_and_style",
                    "current_issue": f"Critical slop violations detected ({critical} instances)",
                    "proposed_change": "Add explicit instruction: 'NEVER use em-dashes (—). Use regular hyphens (-) or restructure sentences.'",
                    "rationale": "Critical violations auto-fail content quality",
                }
            ]
        elif high > 0:
            prompt_to_modify = "draft"
            priority = "high"
            changes = [
                {
                    "section": "tone_and_style",
                    "current_issue": f"High-severity slop detected ({high} instances)",
                    "proposed_change": "Add: 'Avoid corporate jargon. Use concrete, specific language.'",
                    "rationale": "Reduce flowery language",
                }
            ]
        else:
            prompt_to_modify = "draft"
            priority = "medium"
            changes = [
                {
                    "section": "tone_and_style",
                    "current_issue": f"Medium/low slop detected ({medium + low} instances)",
                    "proposed_change": "Add: 'Be direct and specific. Avoid hedging words.'",
                    "rationale": "Improve clarity",
                }
            ]
    else:
        # Rounds 11+: Focus on structure and depth
        focus = "structure_and_depth"
        prompt_to_modify = "outline"
        priority = "medium"
        changes = [
            {
                "section": "structure",
                "current_issue": "Generic outline structure",
                "proposed_change": "Request more specific, topic-relevant section titles",
                "rationale": "Improve content specificity",
            }
        ]

    return {
        "score": score,
        "slop_violations": {
            "critical": [f"violation_{i}" for i in range(critical)],
            "high": [f"violation_{i}" for i in range(high)],
            "medium": [f"violation_{i}" for i in range(medium)],
            "low": [f"violation_{i}" for i in range(low)],
        },
        "voice_analysis": {"authenticity_score": score, "issues": [], "strengths": []},
        "content_quality": {
            "clarity": score,
            "depth": score,
            "nuance": score,
            "specificity": score,
        },
        "evolutionary_strategy": {
            "prompt_to_modify": prompt_to_modify,
            "specific_changes": changes,
            "priority": priority,
            "expected_impact": f"Reduce {focus} issues",
            "focus_area": focus,
        },
        "reasoning": f"Automated evaluation: {total_violations} total violations, score={score:.2f}",
    }


def get_ai_evaluation(
    test_case: TestCase,
    outline: Outline,
    draft: Draft,
    round_number: int,
    meta_prompt_template: Template,
    evaluator_llm_client: Any,  # LLMClient type
) -> dict[str, Any]:
    """Get AI-driven evaluation and evolutionary strategy.

    Args:
        test_case: Test case being evaluated
        outline: Generated outline
        draft: Generated draft
        round_number: Current round number
        meta_prompt_template: Jinja2 template for meta-prompt
        evaluator_llm_client: LLM client for evaluation

    Returns:
        Evaluation dict with score, violations, and evolutionary strategy
    """
    # Prepare draft preview (first 3 sections)
    draft_preview = "\n\n".join(
        f"## {section.title}\n{section.content}" for section in draft.sections[:3]
    )

    # Render meta-prompt
    meta_prompt = meta_prompt_template.render(
        test_case_name=test_case.name,
        title=test_case.title,
        classification=test_case.classification,
        audience=test_case.audience,
        complexity=test_case.complexity,
        nuance=test_case.nuance,
        outline=outline.to_markdown(),
        draft_preview=draft_preview,
        round_number=round_number,
        previous_score="N/A",
        previous_critical=0,
        previous_high=0,
        previous_medium=0,
        previous_low=0,
    )

    # Get AI evaluation using the evaluator LLM client
    logger.info(f"Requesting AI evaluation for round {round_number}...")
    response = evaluator_llm_client.generate(
        prompt=meta_prompt,
        temperature=0.3,  # Lower temperature for more consistent evaluation
        max_tokens=3000,
    )

    # Parse JSON response
    try:
        # Extract JSON from response (may be wrapped in markdown code blocks)
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        evaluation = json.loads(content)
        return cast("dict[str, Any]", evaluation)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to parse AI evaluation: {e}")
        logger.error(f"Response content: {response.content[:500]}")
        # Return fallback evaluation
        return {
            "score": 3.0,
            "slop_violations": {"critical": [], "high": [], "medium": [], "low": []},
            "voice_analysis": {"authenticity_score": 3.0, "issues": [], "strengths": []},
            "content_quality": {
                "clarity": 3.0,
                "depth": 3.0,
                "nuance": 3.0,
                "specificity": 3.0,
            },
            "evolutionary_strategy": {
                "prompt_to_modify": "draft",
                "specific_changes": [],
                "priority": "medium",
                "expected_impact": "Unable to parse AI evaluation",
            },
            "reasoning": f"Fallback evaluation due to parse error: {e}",
        }
