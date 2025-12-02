# Claude AI Agent Guidelines for Bloginator

This document defines coding conventions and quality standards that MUST be followed
without exception for all work on this repository.

## CRITICAL: LLM Mode Configuration

**CLAUDE IS ALWAYS THE LLM FOR BLOG GENERATION**

When running Bloginator to generate blogs:
- The `.env` file MUST have `BLOGINATOR_LLM_MOCK=assistant`
- The `.env` file MUST have `BLOGINATOR_LLM_PROVIDER=mock`
- Claude (the AI assistant) acts as the LLM by responding to requests in `.bloginator/llm_responses/`
- Use `auto_respond.py` to automatically generate LLM responses
- NEVER switch to Ollama or other LLMs without explicit user request
- The user wants Claude to BE the LLM, not to USE an external LLM

## Mandatory Coding Standards

### Python Style Guide

All Python code MUST comply with `docs/PYTHON_STYLE_GUIDE.md`. Key requirements:

- **Line length**: 100 characters maximum (enforced by Black/Ruff)
- **Type annotations**: Required on all function parameters, return values, and class attributes
- **Docstrings**: Google style, required for all public modules, classes, and functions
- **Function length**: Target ≤50 lines, maximum 100 lines
- **Parameters**: ≤5 per function, use dataclass/dict for more
- **Import order**: stdlib → third-party → local (enforced by isort)

### Go Style Guide

All Go code MUST comply with `docs/GO_STYLE_GUIDE.md`. Key requirements:

- **Error wrapping**: Use `fmt.Errorf("context: %w", err)` for all error returns
- **Function length**: Target ≤50 lines, maximum 100 lines
- **Parameters**: ≤5 per function, context first, error last
- **Never panic**: Return errors from library code

## Mandatory Quality Gates

All code MUST pass these checks before commit or PR:

```bash
# Format check (automatic in CI)
ruff check src/bloginator tests
black --check src/bloginator tests
isort --check-only src/bloginator tests

# Type checking
mypy src/bloginator/models src/bloginator/extraction src/bloginator/search \
     src/bloginator/safety src/bloginator/export src/bloginator/services \
     src/bloginator/indexing/indexer.py src/bloginator/generation \
     src/bloginator/utils/parallel.py

# Docstring checking
pydocstyle src/bloginator

# Tests with coverage (minimum 70%)
pytest --cov=src/bloginator --cov-fail-under=70
```

### CI Workflow Requirements

1. **Lint and type check** - Must pass Ruff, pydocstyle, and mypy
2. **Tests** - Must pass on Python 3.10, 3.11, and 3.12 with ≥70% coverage
3. **Security scanning** - Bandit, pip-audit, and Safety checks run (non-blocking)
4. **Codecov** - Coverage reports uploaded to Codecov

## Development Workflow

### Before Every Commit

1. Run quality gate script: `./scripts/fast-quality-gate.sh`
2. Verify all tests pass: `pytest tests/unit --no-cov`
3. Fix any linting/type errors before committing

### Before Every Push

1. Run full test suite: `pytest --cov=src/bloginator`
2. Verify coverage meets threshold (≥70%)
3. Ensure CI will pass by running all quality checks locally

## Code Patterns

### Error Handling

```python
# Good - descriptive with context
raise ValueError(f"Invalid file path: {path!r} (must exist)")

# Bad - vague
raise ValueError("invalid path")
```

### Type Annotations

```python
# Required pattern
def process_document(
    file_path: Path,
    *,
    include_metadata: bool = True,
    max_chunks: int = 100,
) -> list[DocumentChunk]:
    """Process a document into chunks."""
    ...
```

### Testing

```python
class TestFeatureName:
    """Tests for FeatureName functionality."""

    def test_specific_behavior(self, tmp_path: Path) -> None:
        """Specific behavior should produce expected result."""
        # Arrange
        ...
        # Act
        ...
        # Assert
        ...
```

## Project Structure

```text
src/bloginator/
  cli/           # Click CLI commands
  export/        # Document exporters (HTML, Markdown, DOCX, PDF)
  extraction/    # Document chunking and metadata extraction
  generation/    # LLM clients and content generation
  indexing/      # ChromaDB vector indexing
  models/        # Pydantic models and dataclasses
  monitoring/    # Logging and metrics
  quality/       # Slop detection and quality assurance
  safety/        # Blocklist and content filtering
  search/        # Semantic search
  services/      # History and template management
tests/
  unit/          # Unit tests (fast, isolated)
  integration/   # Integration tests
  e2e/           # End-to-end workflow tests
  benchmarks/    # Performance tests
docs/
  *.md           # Documentation files
```

## Prohibited Patterns

1. **No untyped functions** - Every function must have type annotations
2. **No missing docstrings** - Public APIs must be documented
3. **No ignoring mypy errors** - Fix the issue, don't add `# type: ignore`
4. **No tests without assertions** - Every test must verify behavior
5. **No coverage exclusions without justification** - Document why `# pragma: no cover`

## Running Quality Checks

```bash
# Quick local check
source venv/bin/activate
ruff check src/bloginator tests
mypy src/bloginator/models src/bloginator/generation
pytest tests/unit -x --no-cov

# Full CI simulation
pytest --cov=src/bloginator --cov-report=term-missing
```

## Coverage Requirements

- **Minimum overall**: 70% (enforced in CI)
- **Target for new code**: 80%+
- **Critical paths**: 90%+ recommended

Current coverage: ~78% (as of 2024-11-25)
