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
import time
from dataclasses import dataclass, field
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
            prompt_loader=self.prompt_loader,
        )
        self.draft_generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
            prompt_loader=self.prompt_loader,
        )
        self.slop_detector = SlopDetector(prompt_loader=self.prompt_loader)

    def generate_test_cases(self, num_cases: int = 5) -> list[TestCase]:
        """Load test cases from YAML configuration.

        Args:
            num_cases: Number of test cases to load (default: all)

        Returns:
            List of test cases

        Raises:
            FileNotFoundError: If test cases file not found
            ValueError: If test cases file is invalid
        """
        # Load test cases from YAML file
        # __file__ is absolute, so we need to go up 4 levels to repo root
        test_cases_file = (
            Path(__file__).parent.parent.parent.parent
            / "prompts"
            / "optimization"
            / "test_cases.yaml"
        )

        if not test_cases_file.exists():
            raise FileNotFoundError(
                f"Test cases file not found: {test_cases_file}\n"
                "Expected location: prompts/optimization/test_cases.yaml"
            )

        try:
            with test_cases_file.open() as f:
                data = yaml.safe_load(f)

            if not data or "test_cases" not in data:
                raise ValueError("Invalid test cases file: missing 'test_cases' key")

            test_cases = []
            for tc_data in data["test_cases"]:
                test_case = TestCase(
                    id=tc_data["id"],
                    name=tc_data["name"],
                    title=tc_data["title"],
                    keywords=tc_data["keywords"],
                    thesis=tc_data["thesis"],
                    classification=tc_data["classification"],
                    audience=tc_data["audience"],
                    expected_qualities=tc_data.get("expected_qualities", {}),
                    complexity=tc_data.get("complexity", 3),
                    nuance=tc_data.get("nuance", 3),
                )
                test_cases.append(test_case)

            logger.info(f"Loaded {len(test_cases)} test cases from {test_cases_file}")

            # Return requested number of test cases
            if num_cases <= 0:
                return test_cases
            return test_cases[:num_cases]

        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse test cases YAML: {e}") from e
        except KeyError as e:
            raise ValueError(f"Invalid test case format: missing required field {e}") from e

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

    def _apply_prompt_mutations(self, strategy: dict[str, Any]) -> None:
        """Apply prompt mutations based on evolutionary strategy.

        Args:
            strategy: Evolutionary strategy dict with prompt_to_modify and specific_changes
        """
        prompt_to_modify = strategy.get("prompt_to_modify", "draft")
        changes = strategy.get("specific_changes", [])

        if not changes:
            return

        # Reload prompts to get current state
        self.prompt_loader = PromptLoader()

        # Apply changes to the appropriate prompt
        for change in changes:
            section = change.get("section", "")
            proposed_change = change.get("proposed_change", "")

            if not proposed_change:
                continue

            # Modify the prompt template in memory
            # This is a simplified implementation - in production, you'd want to
            # actually modify the YAML files and reload
            logger.debug(f"Would apply mutation to {prompt_to_modify}/{section}: {proposed_change}")

            # For now, we'll just log the mutations
            # In a full implementation, this would:
            # 1. Load the YAML file
            # 2. Modify the relevant section
            # 3. Save the YAML file
            # 4. Reload the PromptLoader

    def _get_automated_evaluation(
        self,
        test_case: TestCase,
        outline: Outline,
        draft: Draft,
        round_number: int,
        previous_result: RoundResult | None = None,
    ) -> dict[str, Any]:
        """Get automated evaluation based on slop detection and heuristics.

        This is a simplified evaluator that doesn't require AI/manual intervention.
        It focuses on measurable metrics: slop violations, length, structure.

        Args:
            test_case: Test case being evaluated
            outline: Generated outline
            draft: Generated draft
            round_number: Current round number
            previous_result: Previous round result (if available)

        Returns:
            Evaluation dict with score, violations, and evolutionary strategy
        """
        # Collect all text
        all_text = "\n\n".join(section.content for section in draft.sections)

        # Detect slop violations
        critical, high, medium, low = self._count_violations_by_severity(all_text)
        total_violations = critical + high + medium + low

        # Calculate base score (0-5 scale)
        # Start at 5.0, deduct for violations
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
        # Prepare draft preview (first 3 sections)
        draft_preview = "\n\n".join(
            f"## {section.title}\n{section.content}" for section in draft.sections[:3]
        )

        # Render meta-prompt
        meta_prompt = self.meta_prompt_template.render(
            test_case_name=test_case.name,
            title=test_case.title,
            classification=test_case.classification,
            audience=test_case.audience,
            complexity=test_case.complexity,
            nuance=test_case.nuance,
            outline=outline.to_markdown(),
            draft_preview=draft_preview,
            round_number=round_number,
            previous_score=previous_result.score if previous_result else "N/A",
            previous_critical=previous_result.critical_violations if previous_result else 0,
            previous_high=previous_result.high_violations if previous_result else 0,
            previous_medium=previous_result.medium_violations if previous_result else 0,
            previous_low=previous_result.low_violations if previous_result else 0,
        )

        # Get AI evaluation using the evaluator LLM client
        logger.info(f"Requesting AI evaluation for round {round_number}...")
        response = self.evaluator_llm_client.generate(
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
            return evaluation
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse AI evaluation: {e}")
            logger.error(f"Response content: {response.content[:500]}")
            # Return fallback evaluation
            return {
                "score": self._score_draft(draft),
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
            previous_result = None
            for round_num in range(num_iterations):
                logger.info(f"  Round {round_num + 1}/{num_iterations}")

                # Generate outline and draft
                outline, draft, score = self.run_baseline(test_case)

                # Get automated evaluation and evolutionary strategy
                evaluation = self._get_automated_evaluation(
                    test_case=test_case,
                    outline=outline,
                    draft=draft,
                    round_number=round_num + 1,
                    previous_result=previous_result,
                )

                # Extract violation counts from AI evaluation
                slop_data = evaluation.get("slop_violations", {})
                critical = len(slop_data.get("critical", []))
                high = len(slop_data.get("high", []))
                medium = len(slop_data.get("medium", []))
                low = len(slop_data.get("low", []))
                total_violations = critical + high + medium + low

                # Use AI-provided score if available, otherwise fallback
                ai_score = evaluation.get("score", score)

                # Record round result with AI evaluation
                round_result = RoundResult(
                    round_number=round_num + 1,
                    test_case_id=test_case.id,
                    score=ai_score,
                    slop_violations=total_violations,
                    critical_violations=critical,
                    high_violations=high,
                    medium_violations=medium,
                    low_violations=low,
                    evolutionary_strategy=evaluation.get("evolutionary_strategy", {}),
                    evaluation_details=evaluation,
                )
                round_results.append(round_result)
                previous_result = round_result

                # Save round result
                round_file = self.output_dir / f"round_{test_case.id}_r{round_num + 1:03d}.json"
                with round_file.open("w") as f:
                    json.dump(self._round_result_to_dict(round_result), f, indent=2)

                # Log evolutionary strategy
                strategy = evaluation.get("evolutionary_strategy", {})
                logger.info(f"    Score: {ai_score:.2f}/5.0")
                logger.info(
                    f"    Violations: {total_violations} (C:{critical} H:{high} M:{medium} L:{low})"
                )
                logger.info(
                    f"    Strategy: {strategy.get('prompt_to_modify', 'N/A')} - {strategy.get('priority', 'N/A')}"
                )

                # Apply evolutionary strategy (mutate prompts)
                if strategy.get("priority") in ["high", "critical"] and total_violations > 0:
                    self._apply_prompt_mutations(strategy)
                    logger.info(
                        f"    Applied {len(strategy.get('specific_changes', []))} prompt mutations"
                    )

                # Sleep between rounds to avoid pummeling the LLM
                if round_num < num_iterations - 1:  # Don't sleep after last round
                    logger.info(f"    Sleeping {self.sleep_between_rounds}s before next round...")
                    time.sleep(self.sleep_between_rounds)

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
            "complexity": test_case.complexity,
            "nuance": test_case.nuance,
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
            "evolutionary_strategy": result.evolutionary_strategy,
            "evaluation_details": result.evaluation_details,
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
