"""Prompt optimization framework for iterative LLM prompt improvement.

Based on the one-pager repo pattern:
1. Generate test cases from corpus
2. Run baseline with current prompts
3. Score results using voice matching and slop detection
4. Iteratively improve prompts using AI-driven evolutionary strategy
5. Validate improvements
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import LLMClient
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.optimization._tuner_evaluator import (
    get_ai_evaluation,
    get_automated_evaluation,
    score_draft_basic,
)
from bloginator.optimization._tuner_models import RoundResult, TestCase, TuningResult
from bloginator.optimization._tuner_mutator import apply_prompt_mutations
from bloginator.optimization._tuner_optimizer import run_optimization_rounds
from bloginator.optimization._tuner_serializer import test_case_to_dict, tuning_result_to_dict
from bloginator.optimization._tuner_test_generator import get_test_cases
from bloginator.prompts.loader import PromptLoader
from bloginator.quality.slop_detector import SlopDetector
from bloginator.search import CorpusSearcher


logger = logging.getLogger(__name__)


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
        sleep_between_rounds: float = 2.0,
        evaluator_llm_client: LLMClient | None = None,
    ):
        """Initialize prompt tuner.

        Args:
            llm_client: LLM client for content generation
            searcher: Corpus searcher for RAG
            prompt_loader: Prompt loader (creates default if None)
            output_dir: Directory for results (default: ./prompt_tuning_results)
            sleep_between_rounds: Seconds to sleep between rounds (default: 2.0)
            evaluator_llm_client: Separate LLM client for AI evaluation (uses llm_client if None)
        """
        self.llm_client = llm_client
        self.evaluator_llm_client = evaluator_llm_client or llm_client
        self.searcher = searcher
        self.prompt_loader = prompt_loader or PromptLoader()
        self.output_dir = output_dir or Path("./prompt_tuning_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sleep_between_rounds = sleep_between_rounds

        # Load meta-prompt for evaluation
        # __file__ is absolute, so: .../src/bloginator/optimization/prompt_tuner.py
        # We need to go up 4 levels to get to repo root: .parent (optimization) -> .parent (bloginator) -> .parent (src) -> .parent (repo root)
        meta_prompt_file = (
            Path(__file__).parent.parent.parent.parent
            / "prompts"
            / "optimization"
            / "meta_prompt.yaml"
        )
        with meta_prompt_file.open() as f:
            meta_data = yaml.safe_load(f)
            self.meta_prompt_template = Template(meta_data["evaluation_prompt"])

        # Initialize components
        self.outline_generator = OutlineGenerator(
            llm_client=llm_client,
            searcher=searcher,
        )
        self.draft_generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
        )
        self.slop_detector = SlopDetector()

    def generate_test_cases(self, num_cases: int = 5) -> list[TestCase]:
        """Load test cases from YAML configuration.

        Args:
            num_cases: Number of test cases to load (default: 5, 0 = all)

        Returns:
            List of test cases

        Raises:
            FileNotFoundError: If test cases file not found
            ValueError: If test cases file is invalid
        """
        return get_test_cases(num_cases=num_cases)

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
        return score_draft_basic(draft, self.slop_detector)

    def _apply_prompt_mutations(self, strategy: dict[str, Any]) -> None:
        """Apply prompt mutations based on evolutionary strategy.

        Args:
            strategy: Evolutionary strategy dict with prompt_to_modify
                and specific_changes
        """
        apply_prompt_mutations(strategy, self.prompt_loader)

    def _get_automated_evaluation(
        self,
        test_case: TestCase,
        outline: Outline,
        draft: Draft,
        round_number: int,
        previous_result: RoundResult | None = None,
    ) -> dict[str, Any]:
        """Get automated evaluation based on slop detection and heuristics.

        This is a simplified evaluator that doesn't require AI/manual
        intervention. It focuses on measurable metrics: slop violations,
        length, structure.

        Args:
            test_case: Test case being evaluated
            outline: Generated outline
            draft: Generated draft
            round_number: Current round number
            previous_result: Previous round result (if available)

        Returns:
            Evaluation dict with score, violations, and evolutionary strategy
        """
        return get_automated_evaluation(
            test_case=test_case,
            draft=draft,
            round_number=round_number,
            slop_detector=self.slop_detector,
        )

    def _get_ai_evaluation(
        self,
        test_case: TestCase,
        outline: Outline,
        draft: Draft,
        round_number: int,
        previous_result: RoundResult | None = None,
    ) -> dict[str, Any]:
        """Get AI-driven evaluation and evolutionary strategy.

        Args:
            test_case: Test case being evaluated
            outline: Generated outline
            draft: Generated draft
            round_number: Current round number
            previous_result: Previous round result (if available)

        Returns:
            Evaluation dict with score, violations, and evolutionary strategy
        """
        return get_ai_evaluation(
            test_case=test_case,
            outline=outline,
            draft=draft,
            round_number=round_number,
            meta_prompt_template=self.meta_prompt_template,
            evaluator_llm_client=self.evaluator_llm_client,
        )

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
                {"test_cases": [test_case_to_dict(tc) for tc in test_cases]},
                f,
                indent=2,
            )

        results: list[TuningResult] = []

        # Run optimization for each test case
        for test_case in test_cases:
            (
                round_results,
                baseline_score,
                baseline_violations,
                final_score,
                final_violations,
            ) = run_optimization_rounds(
                test_case=test_case,
                num_iterations=num_iterations,
                output_dir=self.output_dir,
                run_baseline_func=self.run_baseline,
                get_evaluation_func=self._get_ai_evaluation,
                apply_mutations_func=self._apply_prompt_mutations,
                sleep_between_rounds=self.sleep_between_rounds,
            )

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
                json.dump(tuning_result_to_dict(result), f, indent=2)

        # Save summary
        summary_file = self.output_dir / "optimization_summary.json"
        with summary_file.open("w") as f:
            json.dump(
                {
                    "num_test_cases": len(test_cases),
                    "num_iterations": num_iterations,
                    "results": [tuning_result_to_dict(r) for r in results],
                    "avg_baseline_score": sum(r.baseline_score for r in results) / len(results),
                    "avg_improved_score": sum(r.improved_score for r in results) / len(results),
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        logger.info(f"Optimization complete. Results saved to {self.output_dir}")

        return results
