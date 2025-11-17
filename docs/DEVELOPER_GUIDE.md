# Developer Guide

This guide covers everything developers need to know to contribute to Bloginator, including architecture, coding standards, testing strategies, and development workflows.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Architecture Overview](#architecture-overview)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Code Quality Standards](#code-quality-standards)
7. [Adding New Features](#adding-new-features)
8. [Debugging](#debugging)
9. [Performance Optimization](#performance-optimization)
10. [Contributing](#contributing)

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- pip and virtualenv
- Pre-commit hooks
- Ollama (recommended for local testing)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
pytest tests/unit/ -q
```

### Development Tools

Bloginator uses these quality tools:

- **Black**: Code formatting (line-length=100)
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking (strict mode)
- **isort**: Import sorting (black-compatible)
- **pytest**: Testing framework
- **pre-commit**: Git hooks for quality gates
- **Gitleaks**: Secret detection

### Recommended IDE Setup

**VS Code**:
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true
}
```

**PyCharm**:
- Enable Black formatting on save
- Configure Ruff as external tool
- Enable pytest as test runner
- Enable MyPy type checking

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│  (Click commands: extract, index, search, outline, draft)   │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                       Web Layer                             │
│   (FastAPI app, routes, templates, static files)            │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                     Core Services                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Extraction│  │ Indexing │  │  Search  │  │Generation│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Voice   │  │ Blocklist│  │  Export  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                    Data Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ChromaDB  │  │   JSON   │  │ Template │                 │
│  │(Vectors) │  │(Blocklist│  │ Library  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                  External Services                          │
│       Ollama / LM Studio / Cloud LLMs                       │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: CLI, Web, and Core logic are separate layers
2. **Dependency Injection**: Services don't create dependencies, they receive them
3. **Immutable Data**: Use Pydantic models for data validation
4. **Privacy by Default**: Local-first, no mandatory cloud dependencies
5. **Testability**: All core logic is testable without external dependencies

### Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `cli/` | Command-line interface | Click commands |
| `web/` | Web UI and REST API | FastAPI app, routes |
| `extraction/` | Document text extraction | `Extractor` |
| `indexing/` | Vector indexing | `Indexer` |
| `search/` | Semantic search | `Searcher` |
| `generation/` | Content generation | `OutlineGenerator`, `DraftGenerator` |
| `voice/` | Voice preservation | `VoiceAnalyzer` |
| `safety/` | Blocklist validation | `Blocklist`, `Validator` |
| `models/` | Data models | Pydantic models |
| `templates/` | Document templates | Template library |

---

## Code Organization

### Directory Structure

```
src/bloginator/
├── cli/                    # Command-line interface
│   ├── __init__.py
│   ├── main.py            # Main CLI entry point
│   ├── extract.py         # Extract command
│   ├── index.py           # Index command
│   ├── search.py          # Search command
│   ├── outline.py         # Outline generation command
│   ├── draft.py           # Draft generation command
│   ├── refine.py          # Refinement command
│   ├── blocklist.py       # Blocklist management commands
│   ├── serve.py           # Web server command
│   └── utils.py           # CLI utilities
│
├── web/                    # Web UI
│   ├── __init__.py
│   ├── app.py             # FastAPI application factory
│   ├── routes/            # API routes
│   │   ├── main.py        # UI page routes
│   │   ├── corpus.py      # Corpus management API
│   │   └── documents.py   # Document generation API
│   ├── templates/         # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── corpus.html
│   │   ├── create.html
│   │   └── search.html
│   └── static/            # Static assets
│       ├── css/style.css
│       └── js/app.js
│
├── extraction/             # Document extraction
│   ├── __init__.py
│   ├── extractor.py       # Main extractor
│   ├── pdf.py             # PDF extraction
│   ├── docx.py            # DOCX extraction
│   └── markdown.py        # Markdown extraction
│
├── indexing/               # Vector indexing
│   ├── __init__.py
│   ├── indexer.py         # ChromaDB indexer
│   └── chunking.py        # Text chunking
│
├── search/                 # Semantic search
│   ├── __init__.py
│   ├── searcher.py        # Search engine
│   └── ranking.py         # Result ranking
│
├── generation/             # Content generation
│   ├── __init__.py
│   ├── outline.py         # Outline generator
│   ├── draft.py           # Draft generator
│   ├── refine.py          # Refinement engine
│   └── llm.py             # LLM interface
│
├── voice/                  # Voice preservation
│   ├── __init__.py
│   ├── analyzer.py        # Voice analysis
│   └── similarity.py      # Similarity scoring
│
├── safety/                 # Blocklist and validation
│   ├── __init__.py
│   ├── blocklist.py       # Blocklist management
│   └── validator.py       # Content validation
│
├── templates/              # Document templates
│   ├── __init__.py
│   ├── blog_post.json
│   ├── job_description.json
│   └── ... (12 templates)
│
└── models/                 # Data models
    ├── __init__.py
    ├── document.py        # Document models
    ├── outline.py         # Outline models
    └── search.py          # Search models
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`
- **Tests**: `test_feature_name.py`

---

## Development Workflow

### Feature Development

1. **Create branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement feature**:
   - Write code following [Code Quality Standards](#code-quality-standards)
   - Add tests (aim for 80%+ coverage)
   - Update documentation

3. **Run quality checks**:
   ```bash
   # Quick validation (fast tests only)
   ./validate-monorepo.sh --quick

   # Full validation
   ./validate-monorepo.sh

   # Auto-fix formatting
   ./validate-monorepo.sh --fix
   ```

4. **Commit changes**:
   ```bash
   # Pre-commit hooks will run automatically
   git add .
   git commit -m "feat: add feature description"
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Commit Message Convention

Follow conventional commits:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Add or update tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Build/tooling changes

**Examples**:
```
feat: add template library with 12 document types
fix: resolve ChromaDB connection timeout
docs: update installation guide
test: add integration tests for outline generation
refactor: extract LLM interface to separate module
```

---

## Testing Strategy

### Test Organization

```
tests/
├── unit/              # Fast, isolated unit tests (60%)
│   ├── extraction/
│   ├── indexing/
│   ├── search/
│   ├── generation/
│   ├── voice/
│   ├── safety/
│   └── web/
├── integration/       # Integration tests (30%)
│   ├── test_extract_and_index.py
│   ├── test_search_and_generate.py
│   └── test_full_workflow.py
└── e2e/              # End-to-end tests (10%)
    └── test_complete_workflow.py
```

### Writing Tests

**Unit Test Example**:
```python
"""Tests for blocklist validation."""

import pytest
from bloginator.safety.blocklist import Blocklist
from bloginator.safety.validator import Validator


class TestBlocklist:
    """Tests for Blocklist class."""

    @pytest.fixture
    def blocklist(self):
        """Create test blocklist."""
        bl = Blocklist()
        bl.add("Acme Corp", category="company_name")
        bl.add("SecretProject", category="internal_project", case_insensitive=True)
        return bl

    def test_exact_match(self, blocklist):
        """Test exact match detection."""
        validator = Validator(blocklist)
        text = "We worked with Acme Corp on the project."

        violations = validator.validate(text)

        assert len(violations) == 1
        assert violations[0].term == "Acme Corp"
        assert violations[0].category == "company_name"

    def test_case_insensitive_match(self, blocklist):
        """Test case-insensitive matching."""
        validator = Validator(blocklist)
        text = "The secretproject was a success."

        violations = validator.validate(text)

        assert len(violations) == 1
        assert violations[0].term == "SecretProject"
```

**Integration Test Example**:
```python
"""Integration tests for extract-and-index workflow."""

import tempfile
from pathlib import Path

import pytest

from bloginator.extraction.extractor import Extractor
from bloginator.indexing.indexer import Indexer
from bloginator.search.searcher import Searcher


@pytest.mark.integration
def test_extract_index_search_workflow():
    """Test complete extract, index, and search workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract
        extractor = Extractor()
        extracted = extractor.extract("tests/fixtures/sample.pdf")

        # Index
        index_path = Path(tmpdir) / "index"
        indexer = Indexer()
        indexer.create_index([extracted], output_dir=index_path)

        # Search
        searcher = Searcher(persist_directory=str(index_path))
        results = searcher.search("leadership")

        assert len(results) > 0
        assert "leadership" in results[0]["text"].lower()
```

### Running Tests

```bash
# Fast unit tests only (for pre-commit)
pytest tests/unit/ -m "not slow" -q

# All unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Full suite with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Coverage threshold check
coverage report --fail-under=80

# Run specific test
pytest tests/unit/safety/test_blocklist.py::TestBlocklist::test_exact_match -v

# Run with verbose logging
pytest tests/unit/safety/ -v -s
```

### Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow           # Slow tests (>1s)
@pytest.mark.integration    # Integration tests
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.requires_llm  # Requires LLM access
```

---

## Code Quality Standards

### Code Formatting

**Black** (line-length=100):
```bash
# Format all code
black src/ tests/

# Check formatting
black src/ tests/ --check
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

### Linting

**Ruff** (replaces flake8, isort, pyupgrade):
```bash
# Run linter
ruff check src/ tests/

# Auto-fix issues
ruff check src/ tests/ --fix
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line length (handled by Black)
```

### Type Checking

**MyPy** (strict mode):
```bash
# Type check
mypy src/

# Type check specific module
mypy src/bloginator/generation/
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Type Hint Example**:
```python
from typing import List, Optional
from pathlib import Path

def extract_document(
    file_path: Path,
    quality: Optional[str] = None,
) -> List[str]:
    """Extract text from document.

    Args:
        file_path: Path to document file
        quality: Quality marker (preferred, standard, draft)

    Returns:
        List of extracted text chunks

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format not supported
    """
    ...
```

### Docstrings

Use **Google-style** docstrings:

```python
def generate_outline(
    keywords: List[str],
    template_id: Optional[str] = None,
    index_path: Optional[Path] = None,
) -> OutlineModel:
    """Generate document outline from keywords and template.

    Combines keyword-based search with template structure to create
    a comprehensive document outline.

    Args:
        keywords: List of keywords to guide outline generation
        template_id: Optional template identifier (e.g., "blog_post")
        index_path: Path to search index for keyword expansion

    Returns:
        OutlineModel containing title, thesis, sections, and subsections

    Raises:
        ValueError: If both keywords and template_id are None
        FileNotFoundError: If index_path doesn't exist

    Example:
        >>> outline = generate_outline(
        ...     keywords=["leadership", "culture"],
        ...     template_id="team_charter",
        ...     index_path=Path("./my-index")
        ... )
        >>> print(outline.title)
        "Team Charter: Leadership & Culture"
    """
    ...
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]

  - repo: local
    hooks:
      - id: pytest-fast
        name: Fast unit tests
        entry: pytest
        args: [tests/unit/, -m, "not slow", -q]
        language: system
        pass_filenames: false
```

---

## Adding New Features

### Adding a New CLI Command

1. **Create command module** (`src/bloginator/cli/new_command.py`):
```python
"""New command implementation."""

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--option", help="Description")
def new_command(option: str) -> None:
    """Brief description of command."""
    console.print(f"Running new command with {option}")
```

2. **Register in main CLI** (`src/bloginator/cli/main.py`):
```python
from bloginator.cli.new_command import new_command

cli.add_command(new_command)
```

3. **Add tests** (`tests/unit/cli/test_new_command.py`):
```python
from click.testing import CliRunner
from bloginator.cli.new_command import new_command


def test_new_command():
    """Test new command executes successfully."""
    runner = CliRunner()
    result = runner.invoke(new_command, ["--option", "value"])

    assert result.exit_code == 0
    assert "Running new command" in result.output
```

### Adding a New Document Template

1. **Create template JSON** (`src/bloginator/templates/new_template.json`):
```json
{
  "title": "New Template",
  "thesis": "",
  "keywords": ["keyword1", "keyword2"],
  "sections": [
    {
      "title": "Section 1",
      "description": "What this section covers",
      "subsections": []
    }
  ]
}
```

2. **Register in catalog** (`src/bloginator/templates/__init__.py`):
```python
TEMPLATES = {
    # ... existing templates
    "new_template": {
        "name": "New Template",
        "description": "Description of what this template is for",
        "category": "documentation",
        "file": "new_template.json",
    },
}
```

3. **Add tests** (`tests/unit/templates/test_new_template.py`):
```python
from bloginator.templates import get_template


def test_new_template_loads():
    """Test new template loads correctly."""
    template = get_template("new_template")

    assert template is not None
    assert template["title"] == "New Template"
    assert len(template["sections"]) > 0
```

### Adding a New Web Route

1. **Add route** (`src/bloginator/web/routes/new_route.py`):
```python
"""New route implementation."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class NewRequest(BaseModel):
    """Request model."""
    field: str


class NewResponse(BaseModel):
    """Response model."""
    result: str


@router.post("/new")
async def new_endpoint(request: NewRequest) -> NewResponse:
    """New API endpoint."""
    return NewResponse(result=f"Processed {request.field}")
```

2. **Register router** (`src/bloginator/web/app.py`):
```python
from bloginator.web.routes.new_route import router as new_router

app.include_router(new_router, prefix="/api", tags=["new"])
```

3. **Add tests** (`tests/unit/web/test_new_route.py`):
```python
from fastapi.testclient import TestClient
from bloginator.web.app import create_app


def test_new_endpoint():
    """Test new endpoint."""
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/new", json={"field": "test"})

    assert response.status_code == 200
    assert response.json()["result"] == "Processed test"
```

---

## Debugging

### Logging

Bloginator uses Python's built-in logging:

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

**Enable debug logging**:
```bash
# Set log level via environment variable
export BLOGINATOR_LOG_LEVEL=DEBUG
bloginator outline --keywords "test"

# Or use --verbose flag
bloginator outline --keywords "test" --verbose
```

### Debugging Tests

```bash
# Run with pdb on failure
pytest tests/unit/safety/ --pdb

# Print output (disable capture)
pytest tests/unit/safety/ -s

# Verbose output
pytest tests/unit/safety/ -vv

# Stop on first failure
pytest tests/unit/safety/ -x
```

### Using VS Code Debugger

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    },
    {
      "name": "Pytest: Current File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Performance Optimization

### Profiling

```bash
# Profile code with cProfile
python -m cProfile -o output.prof -m bloginator.cli.main outline --keywords "test"

# View profile results
python -m pstats output.prof
```

### Benchmarking

Create benchmarks in `tests/benchmarks/`:

```python
"""Performance benchmarks."""

import pytest


@pytest.mark.benchmark
def test_indexing_performance(benchmark):
    """Benchmark indexing performance."""
    def run_indexing():
        indexer = Indexer()
        indexer.create_index(documents, output_dir="./bench-index")

    result = benchmark(run_indexing)
    assert result is not None
```

Run benchmarks:
```bash
pytest tests/benchmarks/ --benchmark-only
```

---

## Contributing

### Pull Request Process

1. **Fork and clone** repository
2. **Create feature branch** from `main`
3. **Implement changes** with tests
4. **Run validation**: `./validate-monorepo.sh`
5. **Commit** with conventional commit message
6. **Push** to your fork
7. **Create PR** with description

### PR Checklist

- [ ] Tests added/updated (80%+ coverage)
- [ ] All tests pass
- [ ] Pre-commit hooks pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No proprietary content in examples

### Code Review Criteria

Reviewers will check:
- Code quality and readability
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Adherence to coding standards

---

## Additional Resources

- [PRD: Core System](PRD-BLOGINATOR-001-Core-System.md)
- [Design Spec](DESIGN-SPEC-001-Implementation-Plan.md)
- [Testing Spec](TESTING-SPEC-003-Quality-Assurance.md)
- [Architecture Doc](ARCHITECTURE-002-Deployment-Modes.md)
- [Claude Guidelines](CLAUDE_GUIDELINES.md)
- [Style Guide](../STYLE_GUIDE.md)

---

**Questions?** Open an issue or start a discussion on GitHub.
