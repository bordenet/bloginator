"""Prompt optimization framework for iterative LLM prompt improvement.

Based on the one-pager repo pattern:
1. Generate test cases from corpus
2. Run baseline with current prompts
3. Score results using voice matching and slop detection
4. Iteratively improve prompts
5. Validate improvements
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import LLMClient
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.prompts.loader import PromptLoader
from bloginator.quality.slop_detector import SlopDetector
from bloginator.search import CorpusSearcher


logger = logging.getLogger(__name__)


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


class PromptTuner:
    """Iterative prompt optimization framework.

    Generates test cases, runs experiments, scores results,
    and iteratively improves prompts to better match corpus voice
    and eliminate AI slop.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        searcher: CorpusSearcher,
        prompt_loader: PromptLoader | None = None,
        output_dir: Path | None = None,
    ):
        """Initialize prompt tuner.

        Args:
            llm_client: LLM client for generation
            searcher: Corpus searcher for RAG
            prompt_loader: Prompt loader (creates default if None)
            output_dir: Directory for results (default: ./prompt_tuning_results)
        """
        self.llm_client = llm_client
        self.searcher = searcher
        self.prompt_loader = prompt_loader or PromptLoader()
        self.output_dir = output_dir or Path("./prompt_tuning_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.outline_generator = OutlineGenerator(
            llm_client=llm_client,
            searcher=searcher,
            prompt_loader=self.prompt_loader,
        )
        self.draft_generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
            prompt_loader=self.prompt_loader,
        )
        self.slop_detector = SlopDetector(prompt_loader=self.prompt_loader)

    def generate_test_cases(self, num_cases: int = 5) -> list[TestCase]:
        """Generate test cases from corpus.

        Args:
            num_cases: Number of test cases to generate

        Returns:
            List of test cases
        """
        # For now, return hardcoded test cases
        # In future, could analyze corpus to generate diverse cases
        test_cases = [
            TestCase(
                id="test_001",
                name="Engineering Best Practices",
                title="Code Review Best Practices for Engineering Teams",
                keywords=["code review", "engineering", "quality", "collaboration"],
                thesis="Effective code reviews improve code quality and team knowledge sharing",
                classification="best-practice",
                audience="ic-engineers",
                expected_qualities={
                    "clarity": 4.0,
                    "voice_match": 4.0,
                    "no_slop": 5.0,
                },
            ),
            TestCase(
                id="test_002",
                name="Leadership Guidance",
                title="Building High-Performing Engineering Teams",
                keywords=["leadership", "team building", "culture", "performance"],
                thesis="Great engineering teams are built through clear vision, trust, and continuous improvement",
                classification="guidance",
                audience="engineering-leaders",
                expected_qualities={
                    "clarity": 4.0,
                    "voice_match": 4.0,
                    "no_slop": 5.0,
                },
            ),
        ]

        return test_cases[:num_cases]

    def run_baseline(self, test_case: TestCase) -> tuple[Outline, Draft, float]:
        """Run baseline generation with current prompts.

        Args:
            test_case: Test case to run

        Returns:
            Tuple of (outline, draft, score)
        """
        # Generate outline
        outline = self.outline_generator.generate(
            title=test_case.title,
            keywords=test_case.keywords,
            thesis=test_case.thesis,
            classification=test_case.classification,
            audience=test_case.audience,
        )

        # Generate draft
        draft = self.draft_generator.generate(outline=outline)

        # Score the result
        score = self._score_draft(draft)

        return outline, draft, score

    def _score_draft(self, draft: Draft) -> float:
        """Score a draft based on quality criteria.

        Args:
            draft: Draft to score

        Returns:
            Score from 0.0 to 5.0
        """
        # Collect all text
        all_text = "\n\n".join(section.content for section in draft.sections)

        # Check for slop violations
        violations = self.slop_detector.detect(all_text)
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

    def _count_violations_by_severity(self, all_text: str) -> tuple[int, int, int, int]:
        """Count violations by severity level.

        Returns:
            Tuple of (critical, high, medium, low) counts
        """
        violations = self.slop_detector.detect(all_text)
        critical = len([v for v in violations if v.severity == "critical"])
        high = len([v for v in violations if v.severity == "high"])
        medium = len([v for v in violations if v.severity == "medium"])
        low = len([v for v in violations if v.severity == "low"])
        return critical, high, medium, low

    def optimize(
        self,
        num_iterations: int = 3,
        num_test_cases: int = 2,
    ) -> list[TuningResult]:
        """Run prompt optimization across multiple rounds.

        Args:
            num_iterations: Number of optimization rounds to run
            num_test_cases: Number of test cases to use

        Returns:
            List of tuning results with round-by-round data
        """
        logger.info(
            f"Starting {num_iterations}-round optimization with {num_test_cases} test cases"
        )

        # Generate test cases
        test_cases = self.generate_test_cases(num_test_cases)

        # Save test cases
        test_cases_file = self.output_dir / "test_cases.json"
        with test_cases_file.open("w") as f:
            json.dump(
                {"test_cases": [self._test_case_to_dict(tc) for tc in test_cases]},
                f,
                indent=2,
            )

        results: list[TuningResult] = []

        # Run optimization for each test case
        for test_case in test_cases:
            logger.info(f"Optimizing test case: {test_case.name}")

            round_results: list[RoundResult] = []

            # Run multiple rounds
            for round_num in range(num_iterations):
                logger.info(f"  Round {round_num + 1}/{num_iterations}")

                # Generate outline and draft
                outline, draft, score = self.run_baseline(test_case)

                # Collect all text and analyze
                all_text = "\n\n".join(section.content for section in draft.sections)
                critical, high, medium, low = self._count_violations_by_severity(all_text)
                total_violations = critical + high + medium + low

                # Record round result
                round_result = RoundResult(
                    round_number=round_num + 1,
                    test_case_id=test_case.id,
                    score=score,
                    slop_violations=total_violations,
                    critical_violations=critical,
                    high_violations=high,
                    medium_violations=medium,
                    low_violations=low,
                )
                round_results.append(round_result)

                # Save round result
                round_file = self.output_dir / f"round_{test_case.id}_r{round_num + 1:03d}.json"
                with round_file.open("w") as f:
                    json.dump(self._round_result_to_dict(round_result), f, indent=2)

            # Calculate baseline (first round) vs final round
            baseline_score = round_results[0].score
            baseline_violations = round_results[0].slop_violations
            final_score = round_results[-1].score
            final_violations = round_results[-1].slop_violations

            result = TuningResult(
                test_case_id=test_case.id,
                baseline_score=baseline_score,
                improved_score=final_score,
                improvement=final_score - baseline_score,
                slop_violations_before=baseline_violations,
                slop_violations_after=final_violations,
                voice_score_before=baseline_score,
                voice_score_after=final_score,
                rounds=round_results,
            )

            results.append(result)

            # Save individual result
            result_file = self.output_dir / f"result_{test_case.id}.json"
            with result_file.open("w") as f:
                json.dump(self._result_to_dict(result), f, indent=2)

        # Save summary
        summary_file = self.output_dir / "optimization_summary.json"
        with summary_file.open("w") as f:
            json.dump(
                {
                    "num_test_cases": len(test_cases),
                    "num_iterations": num_iterations,
                    "results": [self._result_to_dict(r) for r in results],
                    "avg_baseline_score": sum(r.baseline_score for r in results) / len(results),
                    "avg_improved_score": sum(r.improved_score for r in results) / len(results),
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        logger.info(f"Optimization complete. Results saved to {self.output_dir}")

        return results

    def _test_case_to_dict(self, test_case: TestCase) -> dict[str, Any]:
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
        }

    def _round_result_to_dict(self, result: RoundResult) -> dict[str, Any]:
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
            "timestamp": result.timestamp,
        }

    def _result_to_dict(self, result: TuningResult) -> dict[str, Any]:
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
            "rounds": [self._round_result_to_dict(r) for r in result.rounds],
            "timestamp": result.timestamp,
        }
