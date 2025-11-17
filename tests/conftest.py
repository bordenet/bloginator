"""Pytest configuration and shared fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def tmp_path(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests.

    Args:
        tmp_path: pytest built-in tmp_path fixture

    Returns:
        Path to temporary directory
    """
    return tmp_path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory.

    Returns:
        Path to tests/fixtures directory
    """
    return Path(__file__).parent / "fixtures"
