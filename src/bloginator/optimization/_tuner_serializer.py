"""Serialization helpers for prompt tuning results."""

from typing import Any

from bloginator.optimization._tuner_models import RoundResult, TestCase, TuningResult


def test_case_to_dict(test_case: TestCase) -> dict[str, Any]:
    """Convert test case to dict for JSON serialization."""
    return {
        "id": test_case.id,
        "name": test_case.name,
        "title": test_case.title,
        "keywords": test_case.keywords,
        "thesis": test_case.thesis,
        "classification": test_case.classification,
        "audience": test_case.audience,
        "expected_qualities": test_case.expected_qualities,
        "complexity": test_case.complexity,
        "nuance": test_case.nuance,
    }


def round_result_to_dict(result: RoundResult) -> dict[str, Any]:
    """Convert round result to dict for JSON serialization."""
    return {
        "round_number": result.round_number,
        "test_case_id": result.test_case_id,
        "score": result.score,
        "slop_violations": result.slop_violations,
        "critical_violations": result.critical_violations,
        "high_violations": result.high_violations,
        "medium_violations": result.medium_violations,
        "low_violations": result.low_violations,
        "evolutionary_strategy": result.evolutionary_strategy,
        "evaluation_details": result.evaluation_details,
        "timestamp": result.timestamp,
    }


def tuning_result_to_dict(result: TuningResult) -> dict[str, Any]:
    """Convert tuning result to dict for JSON serialization."""
    return {
        "test_case_id": result.test_case_id,
        "baseline_score": result.baseline_score,
        "improved_score": result.improved_score,
        "improvement": result.improvement,
        "slop_violations_before": result.slop_violations_before,
        "slop_violations_after": result.slop_violations_after,
        "voice_score_before": result.voice_score_before,
        "voice_score_after": result.voice_score_after,
        "rounds": [round_result_to_dict(r) for r in result.rounds],
        "timestamp": result.timestamp,
    }
