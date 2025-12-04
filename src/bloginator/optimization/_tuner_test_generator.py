"""Test case generation for prompt optimization."""

import logging
from pathlib import Path

import yaml

from bloginator.optimization._tuner_models import TestCase


logger = logging.getLogger(__name__)


def load_test_cases_from_file(
    test_cases_file: Path | None = None,
) -> list[TestCase]:
    """Load test cases from YAML configuration file.

    Args:
        test_cases_file: Path to test cases file (defaults to
            prompts/optimization/test_cases.yaml)

    Returns:
        List of loaded test cases

    Raises:
        FileNotFoundError: If test cases file not found
        ValueError: If test cases file is invalid YAML or missing required fields
    """
    if test_cases_file is None:
        # Default location relative to this module
        # __file__ is: .../src/bloginator/optimization/_tuner_test_generator.py
        # Go up 4 levels to repo root
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
        return test_cases

    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse test cases YAML: {e}") from e
    except KeyError as e:
        raise ValueError(f"Invalid test case format: missing required field {e}") from e


def get_test_cases(num_cases: int = 5, test_cases_file: Path | None = None) -> list[TestCase]:
    """Load and return requested number of test cases.

    Args:
        num_cases: Number of test cases to load (0 = all, default: 5)
        test_cases_file: Path to test cases file

    Returns:
        List of test cases (limited to num_cases if specified)

    Raises:
        FileNotFoundError: If test cases file not found
        ValueError: If test cases file is invalid
    """
    test_cases = load_test_cases_from_file(test_cases_file)

    # Return requested number of test cases
    if num_cases <= 0:
        return test_cases
    return test_cases[:num_cases]
