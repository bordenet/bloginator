#!/usr/bin/env python3
"""Analyze prompt optimization results and identify optimal round count."""

import json
import sys
from pathlib import Path
from typing import Any


def load_summary(results_dir: Path) -> dict[str, Any]:
    """Load optimization summary."""
    summary_file = results_dir / "optimization_summary.json"
    if not summary_file.exists():
        raise FileNotFoundError(f"Summary not found: {summary_file}")

    with summary_file.open() as f:
        return json.load(f)


def analyze_convergence(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze when scores converge across rounds.

    Returns:
        Analysis including optimal round count
    """
    analysis = {
        "total_rounds": 0,
        "convergence_threshold": 0.05,  # 5% change threshold
        "test_cases": [],
    }

    for result in results:
        test_case_id = result["test_case_id"]
        rounds = result["rounds"]
        analysis["total_rounds"] = len(rounds)

        # Track score changes between rounds
        score_changes = []
        for i in range(1, len(rounds)):
            prev_score = rounds[i - 1]["score"]
            curr_score = rounds[i]["score"]
            change = abs(curr_score - prev_score)
            score_changes.append(change)

        # Find convergence point (when changes drop below threshold)
        convergence_round = None
        for i, change in enumerate(score_changes):
            if change < analysis["convergence_threshold"]:
                convergence_round = i + 2  # +2 because we start at round 2
                break

        # Calculate statistics
        scores = [r["score"] for r in rounds]
        violations = [r["slop_violations"] for r in rounds]

        test_analysis = {
            "test_case_id": test_case_id,
            "convergence_round": convergence_round or len(rounds),
            "score_range": {
                "min": min(scores),
                "max": max(scores),
                "mean": sum(scores) / len(scores),
                "first": scores[0],
                "last": scores[-1],
            },
            "violation_range": {
                "min": min(violations),
                "max": max(violations),
                "mean": sum(violations) / len(violations),
                "first": violations[0],
                "last": violations[-1],
            },
            "score_changes": score_changes,
        }

        analysis["test_cases"].append(test_analysis)

    # Calculate optimal round count
    convergence_rounds = [tc["convergence_round"] for tc in analysis["test_cases"]]
    analysis["optimal_rounds"] = {
        "min": min(convergence_rounds),
        "max": max(convergence_rounds),
        "mean": sum(convergence_rounds) / len(convergence_rounds),
        "recommended": int(sum(convergence_rounds) / len(convergence_rounds)) + 5,
    }

    return analysis


def print_analysis(analysis: dict[str, Any]) -> None:
    """Print analysis results."""
    print("\n" + "=" * 80)
    print("PROMPT OPTIMIZATION ANALYSIS")
    print("=" * 80)

    print(f"\nTotal Rounds Run: {analysis['total_rounds']}")
    print(f"Convergence Threshold: {analysis['convergence_threshold']} (5% change)")

    print("\n" + "-" * 80)
    print("PER TEST CASE ANALYSIS")
    print("-" * 80)

    for tc in analysis["test_cases"]:
        print(f"\nTest Case: {tc['test_case_id']}")
        print(f"  Convergence Round: {tc['convergence_round']}")
        print(f"  Score: {tc['score_range']['first']:.2f} → {tc['score_range']['last']:.2f}")
        print(f"  Violations: {tc['violation_range']['first']} → {tc['violation_range']['last']}")
        print(f"  Score Range: [{tc['score_range']['min']:.2f}, {tc['score_range']['max']:.2f}]")
        print(f"  Mean Score: {tc['score_range']['mean']:.2f}")

    print("\n" + "-" * 80)
    print("OPTIMAL ROUND COUNT RECOMMENDATION")
    print("-" * 80)

    opt = analysis["optimal_rounds"]
    print("\nConvergence Statistics:")
    print(f"  Minimum rounds to convergence: {opt['min']}")
    print(f"  Maximum rounds to convergence: {opt['max']}")
    print(f"  Average rounds to convergence: {opt['mean']:.1f}")
    print(f"\n✅ RECOMMENDED ROUND COUNT: {opt['recommended']}")
    print("   (Average convergence + 5 round buffer)")

    print("\n" + "=" * 80)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analyze_optimization.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    # Load summary
    summary = load_summary(results_dir)

    # Analyze convergence
    analysis = analyze_convergence(summary["results"])

    # Print results
    print_analysis(analysis)

    # Save analysis
    analysis_file = results_dir / "convergence_analysis.json"
    with analysis_file.open("w") as f:
        json.dump(analysis, f, indent=2)

    print(f"\n📊 Analysis saved to: {analysis_file}")


if __name__ == "__main__":
    main()
