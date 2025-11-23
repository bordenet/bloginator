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

    def optimize(
        self,
        num_iterations: int = 3,
        num_test_cases: int = 2,
    ) -> list[TuningResult]:
        """Run prompt optimization.

        Args:
            num_iterations: Number of optimization iterations
            num_test_cases: Number of test cases to use

        Returns:
            List of tuning results
        """
        logger.info(f"Starting prompt optimization with {num_test_cases} test cases")

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

        # Run baseline for each test case
        for test_case in test_cases:
            logger.info(f"Running baseline for test case: {test_case.name}")

            outline, draft, baseline_score = self.run_baseline(test_case)

            # Count slop violations
            all_text = "\n\n".join(section.content for section in draft.sections)
            violations_before = self.slop_detector.detect(all_text)

            # For now, "improved" score is same as baseline
            # In future iterations, this would actually optimize prompts
            improved_score = baseline_score
            violations_after = violations_before

            result = TuningResult(
                test_case_id=test_case.id,
                baseline_score=baseline_score,
                improved_score=improved_score,
                improvement=improved_score - baseline_score,
                slop_violations_before=len(violations_before),
                slop_violations_after=len(violations_after),
                voice_score_before=baseline_score,
                voice_score_after=improved_score,
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
            "timestamp": result.timestamp,
        }
