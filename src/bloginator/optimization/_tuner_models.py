"""Dataclasses for prompt tuning."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TestCase:
    """A test case for prompt optimization."""

    id: str
    name: str
    title: str
    keywords: list[str]
    thesis: str
    classification: str
    audience: str
    expected_qualities: dict[str, float] = field(default_factory=dict)
    complexity: int = 3  # 1-5 scale
    nuance: int = 3  # 1-5 scale


@dataclass
class RoundResult:
    """Result of a single optimization round."""

    round_number: int
    test_case_id: str
    score: float
    slop_violations: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    evolutionary_strategy: dict[str, Any] = field(default_factory=dict)
    evaluation_details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TuningResult:
    """Result of prompt tuning run."""

    test_case_id: str
    baseline_score: float
    improved_score: float
    improvement: float
    slop_violations_before: int
    slop_violations_after: int
    voice_score_before: float
    voice_score_after: float
    rounds: list[RoundResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
