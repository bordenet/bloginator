# Python Style Guide for bordenet/* Projects

This document defines the Python coding standards for tools development projects
in the bordenet organization. Standards are derived from PEP 8, PEP 257, and the
Google Python Style Guide, with automated enforcement via Black, isort, pylint, and mypy.

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) - Primary baseline
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/) - Documentation standards
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) - Stricter conventions
- [Black Code Formatter](https://black.readthedocs.io/) - Opinionated formatting
- [Ruff](https://docs.astral.sh/ruff/) - Fast Python linter (optional, replacing flake8)

## Automated Tooling

All code must pass these tools before commit:

```bash
# Formatting (automatic)
black --line-length=100 src/
isort --profile black --line-length 100 src/

# Linting (must pass)
ruff check src/bloginator tests

# Type checking (must pass)
mypy src/bloginator --ignore-missing-imports

# Docstring checking (must pass)
pydocstyle src/bloginator --convention=google

# Tests (must pass with >= 70% coverage)
pytest tests/ --cov=src --cov-fail-under=70
```

## Project Structure

```text
src/
  package_name/
    __init__.py          # Package exports, version
    __main__.py          # CLI entry point
    models.py            # Data classes and types
    cli/                 # CLI commands (click/argparse)
    analyzers/           # Analysis logic
    exporters/           # Output formatters
tests/
  __init__.py
  test_*.py              # Test modules
  conftest.py            # Shared fixtures
docs/
  *.md                   # Documentation
```

## Naming Conventions

### Modules and Packages
- **snake_case**: `code_analyzer.py`, `security_rules.py`
- Avoid: `codeAnalyzer.py`, `CodeAnalyzer.py`

### Classes
- **PascalCase**: `CodeAnalyzer`, `SecurityRule`, `ValidationResult`
- Suffix base classes with `Base`: `AnalyzerBase`
- Suffix abstract classes with `ABC`: `ExporterABC`

### Functions and Methods
- **snake_case**: `analyze_code()`, `get_findings()`, `_private_helper()`
- Use verbs: `calculate_`, `generate_`, `validate_`, `parse_`
- Boolean methods: `is_valid()`, `has_errors()`, `can_process()`

### Variables
- **snake_case**: `file_path`, `error_count`, `is_valid`
- **UPPER_SNAKE_CASE** for constants: `MAX_LINE_LENGTH`, `DEFAULT_TIMEOUT`
- Prefix private with underscore: `_internal_state`

### Type Variables
- **PascalCase** with descriptive suffix: `T`, `ItemT`, `ReturnT`

## Function and Method Guidelines

### Length
- Target: **≤50 lines** per function
- Maximum: **100 lines** (refactor if approaching)
- Single responsibility principle

### Parameters
- **≤5 parameters** - use dataclass/dict if more needed
- Use keyword arguments for optional parameters
- Type all parameters and return values

```python
# Good
def analyze_file(
    file_path: Path,
    *,
    include_metrics: bool = True,
    max_depth: int = 10,
) -> AnalysisResult:
    """Analyze a single file."""
    ...

# Bad - too many positional parameters
def analyze_file(path, metrics, depth, lang, encoding, timeout):
    ...
```

### Return Values
- Always type return values
- Prefer returning objects over tuples for complex returns
- Use `Optional[T]` for nullable returns

## Documentation (PEP 257)

### Module Docstrings
```python
"""Analyze code quality and detect issues.

This module provides functionality for static code analysis including:
- Syntax validation
- Style checking
- Security scanning
"""
```

### Function Docstrings
```python
def analyze_file(file_path: Path, *, include_metrics: bool = True) -> AnalysisResult:
    """Analyze a single file for code quality issues.

    Args:
        file_path: Path to the file to analyze.
        include_metrics: Whether to include code metrics. Defaults to True.

    Returns:
        AnalysisResult containing findings and metrics.

    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If file_path is not a valid Python file.
    """
```

### Class Docstrings
```python
class CodeAnalyzer:
    """Analyze Python source code for quality issues.

    This analyzer supports multiple rule sets and can be configured
    to check specific categories of issues.

    Attributes:
        rules: List of rules to apply during analysis.
        findings: Results from the most recent analysis.
    """
```

## Type Annotations

### Always Type
- All function parameters
- All return values (including `-> None`)
- Class attributes
- Module-level variables

```python
# Good
def calculate_score(findings: list[Finding], weight: float = 1.0) -> float:
    """Calculate weighted score from findings."""
    return sum(f.severity * weight for f in findings)

# Bad - no type annotations
def calculate_score(findings, weight=1.0):
    return sum(f.severity * weight for f in findings)
```

### Common Type Patterns
```python
from typing import Optional, Union, Callable, TypeVar

# Optional for nullable
def find_file(name: str) -> Optional[Path]:
    ...

# Union for multiple types (prefer | in Python 3.10+)
def parse(value: Union[str, int]) -> Result:
    ...

# Callable for function parameters
def apply(transform: Callable[[str], str], data: str) -> str:
    ...

# TypeVar for generics
T = TypeVar("T")
def first(items: list[T]) -> Optional[T]:
    return items[0] if items else None
```

## Error Handling

### Exception Hierarchy
```python
# Define custom exceptions in a module
class CodebaseReviewerError(Exception):
    """Base exception for codebase-reviewer."""

class ValidationError(CodebaseReviewerError):
    """Raised when validation fails."""

class ConfigurationError(CodebaseReviewerError):
    """Raised when configuration is invalid."""
```

### Error Messages
```python
# Good - descriptive with context
raise ValueError(f"Invalid file path: {path!r} (must be absolute)")

# Bad - vague
raise ValueError("invalid path")
```

### Exception Chaining
```python
try:
    config = load_config(path)
except yaml.YAMLError as e:
    raise ConfigurationError(f"Failed to parse config at {path}") from e
```

## Testing

### Test Structure
```python
# tests/test_analyzer.py
import pytest
from codebase_reviewer.analyzers import CodeAnalyzer

class TestCodeAnalyzer:
    """Tests for CodeAnalyzer class."""

    def test_analyze_empty_file(self, tmp_path: Path) -> None:
        """Empty files should return no findings."""
        file = tmp_path / "empty.py"
        file.write_text("")

        analyzer = CodeAnalyzer()
        result = analyzer.analyze(file)

        assert result.findings == []

    def test_analyze_syntax_error(self, tmp_path: Path) -> None:
        """Syntax errors should be reported as critical findings."""
        file = tmp_path / "broken.py"
        file.write_text("def broken(")

        analyzer = CodeAnalyzer()
        result = analyzer.analyze(file)

        assert any(f.severity == "critical" for f in result.findings)
```

### Fixtures
```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Create a minimal repository structure."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").touch()
    (tmp_path / "tests").mkdir()
    return tmp_path
```

### Coverage
- Target: **≥70%** overall (enforced in CI)
- Critical modules: **≥80%** coverage
- Use `# pragma: no cover` sparingly and with justification

## File Organization

### File Length
- Target: **~250 lines** per file
- Maximum: **400 lines** (refactor if approaching)

### Import Order (isort)
1. Standard library
2. Third-party packages
3. Local application imports

```python
import os
from pathlib import Path

import click
import yaml
from pydantic import BaseModel

from codebase_reviewer.models import Finding
from codebase_reviewer.analyzers import CodeAnalyzer
```

### Avoid Circular Imports
- Use `TYPE_CHECKING` for type-only imports
- Import at module level, not inside functions (unless necessary)

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codebase_reviewer.orchestrator import Orchestrator
```

## Code Patterns

### Dataclasses for Data
```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Finding:
    """A single code quality finding."""

    rule_id: str
    message: str
    severity: str
    file_path: Path
    line: int
    column: int = 0
    suggestion: Optional[str] = None
    metadata: dict = field(default_factory=dict)
```

### Context Managers for Resources
```python
from contextlib import contextmanager

@contextmanager
def temp_directory() -> Iterator[Path]:
    """Create a temporary directory that's cleaned up on exit."""
    path = Path(tempfile.mkdtemp())
    try:
        yield path
    finally:
        shutil.rmtree(path)
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

def analyze(path: Path) -> Result:
    logger.info("Starting analysis of %s", path)
    try:
        result = _do_analysis(path)
        logger.debug("Analysis complete: %d findings", len(result.findings))
        return result
    except Exception:
        logger.exception("Analysis failed for %s", path)
        raise
```

## Linting Rules Summary

### Ruff
- Line length: **100** (configured in pyproject.toml)
- Enabled rule sets: E, W, F, I, N, UP, B, C4, SIM, TCH, PTH

### mypy
- Strict mode recommended for new projects
- Minimum: `--ignore-missing-imports`

### Black
- Line length: **100** (configured in pyproject.toml)
- No configuration needed - use defaults

### isort
- Profile: **black** (compatible formatting)
- Line length: **100**
