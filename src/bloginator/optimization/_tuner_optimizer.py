"""Optimization loop execution for prompt tuning."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from bloginator.optimization._tuner_models import RoundResult, TestCase
from bloginator.optimization._tuner_serializer import round_result_to_dict


logger = logging.getLogger(__name__)


def run_optimization_rounds(
    test_case: TestCase,
    num_iterations: int,
    output_dir: Path,
    run_baseline_func: Any,
    get_evaluation_func: Any,
    apply_mutations_func: Any,
    sleep_between_rounds: float,
) -> tuple[list[RoundResult], float, int, float, int]:
    """Execute optimization rounds for a single test case.

    Args:
        test_case: Test case to optimize
        num_iterations: Number of rounds to run
        output_dir: Directory to save results
        run_baseline_func: Function to generate outline and draft
        get_evaluation_func: Function to evaluate results
        apply_mutations_func: Function to apply prompt mutations
        sleep_between_rounds: Seconds to sleep between rounds

    Returns:
        Tuple of (round_results, baseline_score, baseline_violations,
            final_score, final_violations)
    """
    logger.info(f"Optimizing test case: {test_case.name}")

    round_results: list[RoundResult] = []
    previous_result = None

    for round_num in range(num_iterations):
        logger.info(f"  Round {round_num + 1}/{num_iterations}")

        # Generate outline and draft
        outline, draft, score = run_baseline_func(test_case)

        # Get evaluation and evolutionary strategy
        evaluation = get_evaluation_func(
            test_case=test_case,
            outline=outline,
            draft=draft,
            round_number=round_num + 1,
            previous_result=previous_result,
        )

        # Extract violation counts from evaluation
        slop_data = evaluation.get("slop_violations", {})
        critical = len(slop_data.get("critical", []))
        high = len(slop_data.get("high", []))
        medium = len(slop_data.get("medium", []))
        low = len(slop_data.get("low", []))
        total_violations = critical + high + medium + low

        # Use provided score if available, otherwise fallback
        eval_score = evaluation.get("score", score)

        # Record round result with evaluation
        round_result = RoundResult(
            round_number=round_num + 1,
            test_case_id=test_case.id,
            score=eval_score,
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
        round_file = output_dir / f"round_{test_case.id}_r{round_num + 1:03d}.json"
        with round_file.open("w") as f:
            json.dump(round_result_to_dict(round_result), f, indent=2)

        # Log evolutionary strategy
        strategy = evaluation.get("evolutionary_strategy", {})
        logger.info(f"    Score: {eval_score:.2f}/5.0")
        logger.info(
            f"    Violations: {total_violations} (C:{critical} H:{high} M:{medium} L:{low})"
        )
        logger.info(
            f"    Strategy: {strategy.get('prompt_to_modify', 'N/A')} - {strategy.get('priority', 'N/A')}"
        )

        # Apply evolutionary strategy (mutate prompts)
        if strategy.get("priority") in ["high", "critical"] and total_violations > 0:
            apply_mutations_func(strategy)
            logger.info(f"    Applied {len(strategy.get('specific_changes', []))} prompt mutations")

        # Sleep between rounds to avoid pummeling the LLM
        if round_num < num_iterations - 1:  # Don't sleep after last round
            logger.info(f"    Sleeping {sleep_between_rounds}s before next round...")
            time.sleep(sleep_between_rounds)

    # Calculate baseline vs final
    baseline_score = round_results[0].score
    baseline_violations = round_results[0].slop_violations
    final_score = round_results[-1].score
    final_violations = round_results[-1].slop_violations

    return (
        round_results,
        baseline_score,
        baseline_violations,
        final_score,
        final_violations,
    )
