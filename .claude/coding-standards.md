# Coding Standards for Bloginator

## Code Style

### Formatting
- **Line Length**: 100 characters (enforced by black)
- **Formatting Tool**: Black with `--line-length=100`
- **Import Sorting**: isort with `--profile=black`
- Run before commit: `black --line-length=100 src/ tests/`

### Linting
- **Linter**: Ruff
- **Rules**: E, W, F, I, N, UP, B, C4, SIM, TCH, PTH
- **Auto-fix**: `ruff check --fix src/ tests/`
- **Zero tolerance**: All errors must be fixed before commit

### Type Checking
- **Tool**: MyPy in strict mode
- **Requirements**:
  - All public functions must have type hints
  - No `Any` without justification
  - No `# type: ignore` without comment explaining why
- **Run**: `mypy src/ --strict --ignore-missing-imports`

### Docstrings
- **Style**: Google-style docstrings
- **Required**: All public functions, classes, and modules
- **Example**:
```python
def search_corpus(query: str, n_results: int = 10) -> list[dict]:
    """Search corpus for relevant content.

    Args:
        query: Natural language search query
        n_results: Number of results to return (default: 10)

    Returns:
        List of search results with content, metadata, and scores

    Raises:
        ValueError: If n_results is negative
    """
```

## Testing Standards

### Coverage Requirements
- **Minimum**: 80% line coverage for ALL modules
- **Safety-Critical**: 90%+ coverage (e.g., blocklist module)
- **Check**: `pytest --cov=src --cov-report=term-missing`
- **Fail Build**: `coverage report --fail-under=80`

### Test Organization
- **60% Unit Tests**: Fast (<0.1s each), isolated, comprehensive
- **30% Integration Tests**: Component interactions (<5s each)
- **10% E2E Tests**: Full workflows (<30s each)

### Test Markers
```python
@pytest.mark.slow  # For tests >5 seconds
@pytest.mark.requires_ollama  # Requires Ollama running
@pytest.mark.requires_api_key  # Requires API keys
@pytest.mark.e2e  # End-to-end tests
@pytest.mark.integration  # Integration tests
@pytest.mark.unit  # Unit tests (default)
```

### Test Naming
- File: `test_<module_name>.py`
- Class: `Test<ComponentName>`
- Function: `test_<specific_behavior>`
- Example: `test_blocklist_exact_match_case_sensitive()`

## Code Organization

### Module Structure
```python
"""Module docstring explaining purpose.

This module handles X by doing Y.
"""

# Standard library imports
import json
from pathlib import Path
from typing import Optional

# Third-party imports
import click
from pydantic import BaseModel

# Local imports
from bloginator.models import Document
from bloginator.safety import BlocklistManager


# Constants
DEFAULT_CHUNK_SIZE = 512

# Classes and functions
class MyClass:
    """Class docstring."""
    pass

def my_function() -> None:
    """Function docstring."""
    pass
```

### File Naming
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

## Quality Workflow

### Before Committing
1. **Format**: `black --line-length=100 src/ tests/`
2. **Sort imports**: `isort --profile=black --line-length=100 src/ tests/`
3. **Lint**: `ruff check --fix src/ tests/`
4. **Type check**: `mypy src/ --strict --ignore-missing-imports`
5. **Test**: `pytest tests/ -m "not slow" -v`
6. **Pre-commit**: Runs automatically via git hooks

### Before Pull Request
1. **Full validation**: `./validate-bloginator.sh`
2. **Coverage check**: Ensure ≥80%
3. **All tests pass**: Including slow tests
4. **Documentation**: Update relevant docs

### Auto-fix Command
```bash
# Fix most issues automatically
./validate-bloginator.sh --fix
```

## Anti-Patterns to Avoid

### ❌ DON'T
- Skip tests to "move faster"
- Use `# type: ignore` without explanation
- Commit without running pre-commit hooks
- Create abstractions before they're needed
- Split files without explicit user request
- Use `Any` type without justification
- Skip docstrings on public functions

### ✅ DO
- Write tests first (TDD preferred)
- Keep functions small and focused
- Prefer composition over inheritance
- Make minimal, necessary changes
- Validate changes with tests
- Document all public APIs
- Use type hints on all functions

## Pydantic Models

### Standard Pattern
```python
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QualityRating(str, Enum):
    PREFERRED = "preferred"
    STANDARD = "standard"
    DEPRECATED = "deprecated"


class Document(BaseModel):
    """Document metadata and content.

    Attributes:
        id: Unique document identifier
        filename: Original filename
        quality_rating: Content quality rating
    """

    id: str = Field(..., description="Unique document identifier")
    filename: str
    quality_rating: QualityRating = QualityRating.STANDARD
    created_date: Optional[datetime] = None

    class Config:
        use_enum_values = True
```

## Error Handling

### Pattern
```python
class BloginatorError(Exception):
    """Base exception for Bloginator errors."""
    pass


class BlocklistViolationError(BloginatorError):
    """Raised when generated content violates blocklist."""

    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__(f"Blocklist violations: {', '.join(violations)}")


# Usage
def validate_content(text: str) -> None:
    """Validate content against blocklist.

    Raises:
        BlocklistViolationError: If content contains blocklisted terms
    """
    violations = check_blocklist(text)
    if violations:
        raise BlocklistViolationError(violations)
```

## CLI Patterns

### Click Command Structure
```python
import click
from pathlib import Path


@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output directory")
@click.option("--quality", type=click.Choice(["preferred", "standard", "deprecated"]))
def extract(source: str, output: str, quality: str) -> None:
    """Extract documents from SOURCE to OUTPUT directory.

    SOURCE: Path to documents or directory
    """
    source_path = Path(source)
    output_path = Path(output)

    # Implementation
    click.echo(f"Extracting from {source_path} to {output_path}")
```

## Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Example**:
```
feat: add blocklist validation to draft generation

- Implement BlocklistManager integration
- Add pre-generation validation
- Return detailed violation reports
- Update tests for new validation flow

Closes #42
```

## Performance Guidelines

- Index 500 documents in <30 minutes
- Search results in <3 seconds
- Generate draft in <5 minutes
- Voice similarity scoring in <10 seconds
- Unit tests in <0.1s each

## Security Guidelines

- Never commit API keys or secrets
- Use gitleaks pre-commit hook
- Validate all user inputs
- Sanitize file paths
- No eval() or exec() of user input
- Review blocklist implementation carefully (legal implications)
