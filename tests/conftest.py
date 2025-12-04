"""Pytest configuration and shared fixtures."""

from __future__ import annotations

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


@pytest.fixture
def sample_corpus_dir() -> Path | None:
    """Return path to sample corpus directory (Engineering_Culture).

    The sample corpus is downloaded by setup-macos.sh from:
    https://github.com/bordenet/Engineering_Culture

    Returns:
        Path to test-corpus/Engineering_Culture if it exists, None otherwise
    """
    repo_root = Path(__file__).parent.parent
    corpus_dir = repo_root / "test-corpus" / "Engineering_Culture"
    if corpus_dir.exists():
        return corpus_dir
    return None


@pytest.fixture
def sample_corpus_config() -> Path:
    """Return path to sample corpus configuration file.

    Returns:
        Path to corpus/sample.yaml
    """
    repo_root = Path(__file__).parent.parent
    return repo_root / "corpus" / "sample.yaml"
