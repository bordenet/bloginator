# Claude AI Agent Guidelines for Bloginator

This document defines coding conventions and quality standards that MUST be followed
without exception for all work on this repository.

## CRITICAL: Repository Cleanliness

### Temporary Files Policy

- ALL temporary/experimental scripts go in `tmp/` directory (git-ignored)
- ALL blog generation outputs go in `blogs/` directory (git-ignored)
- ALL prompt experiments go in `prompts/experimentation/` (git-ignored)
- ALL context handoff prompts go in `prompts/` (e.g., `prompts/finish-refactoring-options-b-c.md`)
- NEVER create shell scripts or markdown files in the repository root
- Exception: Only permanent, maintained scripts/docs belong in root

### Markdown Documentation Policy

- Keep all working markdown files in `docs/` updated as you work
- Create index files (e.g., `docs/IMPLEMENTATION_PLAN_TOPIC_DRIFT_FIX.md`) that reference other docs
- Write comprehensive prompts to `prompts/` for context handoffs
- Reference prompt files instead of pasting huge inline content
- Each prompt should be 200-400 lines max, focused on execution steps

## CRITICAL: LLM Mode Configuration

### Available LLM Modes

The `BLOGINATOR_LLM_MOCK` environment variable controls LLM behavior:

| Value | Client | Use Case |
|-------|--------|----------|
| `true` | `MockLLMClient` | Unit tests - returns canned responses |
| `interactive` | `InteractiveLLMClient` | Human-in-the-loop via terminal prompts |
| `assistant` | `AssistantLLMClient` | File-based communication for AI agents |
| *(unset)* | Real LLM client | Production use with Ollama/OpenAI/Anthropic |

**Note**: `BLOGINATOR_LLM_MOCK` takes precedence over `BLOGINATOR_LLM_PROVIDER`.

### Assistant Mode (Claude as the LLM)

When `BLOGINATOR_LLM_MOCK=assistant`:
1. Bloginator writes requests to `.bloginator/llm_requests/request_NNNN.json`
2. Bloginator waits for `.bloginator/llm_responses/response_NNNN.json`
3. Claude (or another AI agent) reads requests and writes responses

To act as the LLM backend:
1. Set `BLOGINATOR_LLM_MOCK=assistant` in `.env`
2. Run a bloginator command (e.g., `bloginator outline "Topic"`)
3. Monitor `.bloginator/llm_requests/` for new request files
4. Read the request, generate a response, write to `.bloginator/llm_responses/`

### Demo Script

`scripts/respond-to-llm-requests.py` provides **template-based** responses for demos.
It does NOT use any LLM - just hardcoded content for specific topics.

### No External LLM Required

- The user does NOT have external LLM API keys configured
- For testing, use `BLOGINATOR_LLM_MOCK=true` (canned responses)
- For real generation, Claude can act as the LLM via assistant mode
- NEVER switch to Ollama or other LLMs without explicit user request

## Mandatory Coding Standards

### Python Style Guide

All Python code MUST comply with `docs/PYTHON_STYLE_GUIDE.md`. Key requirements:

- **Line length**: 100 characters maximum (enforced by Black/Ruff)
- **Type annotations**: Required on all function parameters, return values, and class attributes
- **Docstrings**: Google style, required for all public modules, classes, and functions
- **Function length**: Target ≤50 lines, maximum 100 lines
- **Parameters**: ≤5 per function, use dataclass/dict for more
- **Import order**: stdlib → third-party → local (enforced by isort)
- **Max file length**: 400 lines maximum. Strive for ~250 lines

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

1. Run quality gate script: `./scripts/run-fast-quality-gate.sh`
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

Current coverage: ~76% (as of 2025-12-05)
