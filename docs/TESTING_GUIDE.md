# Testing Guide

This guide covers testing strategies, mock LLM usage, and quality assurance practices for Bloginator.

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Mock LLM Testing](#mock-llm-testing)
5. [Writing Tests](#writing-tests)
6. [Coverage Requirements](#coverage-requirements)
7. [VS Code Integration](#vs-code-integration)
8. [CI/CD Testing](#cicd-testing)

---

## Testing Philosophy

Bloginator follows a comprehensive testing strategy:

- **Unit Tests**: Fast, isolated tests for individual components (>90% of tests)
- **Integration Tests**: Multi-component interaction tests
- **End-to-End Tests**: Full workflow validation
- **Performance Tests**: Benchmark critical operations

**Coverage Target**: 85% minimum (CI enforced), 90%+ aspirational

---

## Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── cli/                # CLI command tests
│   ├── export/             # Export functionality tests
│   ├── extraction/         # Document extraction tests
│   ├── generation/         # LLM generation tests
│   ├── indexing/           # Vector indexing tests
│   ├── models/             # Data model tests
│   ├── safety/             # Blocklist and safety tests
│   ├── search/             # Search functionality tests
│   ├── services/           # Service layer tests
│   └── web/                # Web API tests
├── integration/            # Integration tests
│   ├── test_extract_and_index.py
│   └── test_search_and_generation.py
├── e2e/                    # End-to-end tests
│   ├── test_complete_workflows.py
│   └── test_full_workflow.sh
├── benchmarks/             # Performance tests
│   └── test_performance.py
├── fixtures/               # Test data and fixtures
│   └── sample_corpus/
└── conftest.py            # Shared pytest configuration
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src/bloginator --cov-report=term-missing

# Run with branch coverage
pytest tests/ --cov=src/bloginator --cov-branch --cov-report=term
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Performance benchmarks
pytest tests/benchmarks/ -v
```

### Run Tests by Marker

```bash
# Skip slow tests
pytest -m "not slow" -v

# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run only e2e tests
pytest -m e2e -v
```

### Run Specific Test Files or Functions

```bash
# Run specific file
pytest tests/unit/models/test_document.py -v

# Run specific test function
pytest tests/unit/models/test_document.py::test_document_creation -v

# Run tests matching pattern
pytest tests/ -k "test_extract" -v
```

---

## Mock LLM Testing

### Overview

Bloginator supports **mock LLM mode** for testing without external API dependencies. This enables:

- ✅ Deterministic, reproducible tests
- ✅ Fast test execution (no network calls)
- ✅ CI/CD without API keys
- ✅ Privacy-safe testing (no data sent externally)
- ✅ Controllable error injection

### Enabling Mock Mode

**Environment Variable**:
```bash
export BLOGINATOR_LLM_MOCK=true
```

**In Tests**:
```python
import os
os.environ["BLOGINATOR_LLM_MOCK"] = "true"

# Or use pytest fixture
def test_with_mock_llm(mock_llm_env):
    # Test code here - will use MockLLMClient
    pass
```

**In conftest.py**:
```python
@pytest.fixture
def mock_llm_env(monkeypatch):
    """Enable mock LLM mode for test."""
    monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")
    yield
```

### Mock LLM Behavior

The `MockLLMClient` provides realistic responses based on request type:

**Outline Requests** (detected by keywords: "outline", "section", "structure"):
- Returns structured markdown outline
- Includes introduction, sections, subsections, conclusion
- Realistic content based on prompt

**Draft Requests** (detected by keywords: "write", "draft", "paragraph"):
- Returns multi-paragraph content
- Professional writing style
- Contextual to section title if provided

**Generic Requests**:
- Returns fallback response explaining mock mode

### Mock LLM Configuration

```python
from bloginator.generation.llm_mock import MockLLMClient

# Create mock client
client = MockLLMClient(
    model="mock-model",
    verbose=True  # Print requests/responses for debugging
)

# Generate response
response = client.generate(
    prompt="Create an outline for engineering best practices",
    temperature=0.7,  # Ignored in mock
    max_tokens=2000   # Ignored in mock
)

print(response.content)  # Structured outline
print(response.model)    # "mock-model"
print(response.prompt_tokens)  # Estimated token count
```

### Testing with Mock LLM

**Example Test**:
```python
def test_outline_generation_with_mock(mock_llm_env, tmp_path):
    """Test outline generation using mock LLM."""
    # Setup
    index_path = tmp_path / "index"
    # ... create test index ...

    # Generate outline (will use mock LLM)
    from bloginator.generation.outline_generator import OutlineGenerator
    generator = OutlineGenerator(index_path)
    outline = generator.generate(
        keywords=["testing", "quality"],
        title="Testing Best Practices"
    )

    # Verify
    assert outline.title == "Testing Best Practices"
    assert len(outline.sections) > 0
    assert "Introduction" in [s.title for s in outline.sections]
```

### Error Injection (Future Enhancement)

Mock LLM will support error injection for failure testing:

```python
# Future API
client = MockLLMClient(
    error_mode="timeout",  # Simulate timeout
    error_rate=0.5         # 50% of requests fail
)
```

---

## Writing Tests

### Test Structure

Follow the **Arrange-Act-Assert** pattern:

```python
def test_document_extraction():
    # Arrange: Setup test data and dependencies
    test_file = Path("tests/fixtures/sample_doc.md")

    # Act: Execute the code under test
    document = extract_text_from_file(test_file)

    # Assert: Verify expected outcomes
    assert document.content != ""
    assert document.source_path == test_file
    assert len(document.chunks) > 0
```

### Test Naming

Use descriptive names that explain what is being tested:

```python
# Good
def test_extract_pdf_with_images_returns_text_only():
    pass

def test_search_with_empty_query_raises_value_error():
    pass

def test_blocklist_validation_rejects_exact_match():
    pass

# Bad
def test_extract():
    pass

def test_search_1():
    pass

def test_blocklist():
    pass
```

### Test Fixtures

Use pytest fixtures for reusable test data:

```python
@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        content="Sample content",
        source_path=Path("test.md"),
        source_name="test.md",
        chunks=[],
        voice_notes="Test voice"
    )

def test_document_serialization(sample_document):
    # Use fixture
    json_data = sample_document.model_dump_json()
    assert "Sample content" in json_data
```

### Parametrized Tests

Test multiple scenarios with parametrize:

```python
@pytest.mark.parametrize("quality,expected_weight", [
    (QualityRating.PREFERRED, 1.5),
    (QualityRating.REFERENCE, 1.0),
    (QualityRating.SUPPLEMENTAL, 0.7),
])
def test_quality_weighting(quality, expected_weight):
    weight = calculate_quality_weight(quality)
    assert weight == expected_weight
```

---

## Coverage Requirements

### Minimum Coverage Targets

| Component | Line Coverage | Branch Coverage |
|-----------|--------------|-----------------|
| Models | 95%+ | 90%+ |
| Core Logic | 90%+ | 85%+ |
| CLI Commands | 85%+ | 80%+ |
| API Endpoints | 85%+ | 80%+ |
| UI Components | 80%+ | 75%+ |
| **Overall** | **85%** | **85%** |

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=src/bloginator --cov-report=term-missing

# Generate HTML report
pytest --cov=src/bloginator --cov-report=html
open htmlcov/index.html

# Generate JSON report (for CI)
pytest --cov=src/bloginator --cov-report=json

# Check branch coverage
pytest --cov=src/bloginator --cov-branch --cov-report=term
```

### Coverage Configuration

See `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 70.0
```

---

## VS Code Integration

### Launch Configurations

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current Test File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    },
    {
      "name": "Python: All Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Tests with Coverage",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "--cov=src/bloginator",
        "--cov-report=term-missing"
      ],
      "console": "integratedTerminal"
    },
    {
      "name": "Bloginator CLI (Mock LLM)",
      "type": "python",
      "request": "launch",
      "module": "bloginator.cli.main",
      "args": ["outline", "--help"],
      "env": {
        "BLOGINATOR_LLM_MOCK": "true"
      },
      "console": "integratedTerminal"
    }
  ]
}
```

### Test Explorer

Enable pytest in VS Code settings (`.vscode/settings.json`):

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["tests"],
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

---

## CI/CD Testing

### GitHub Actions Workflow

Tests run automatically on every push and PR:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov=src/bloginator \
                 --cov-branch \
                 --cov-report=term \
                 --cov-fail-under=85
```

### Coverage Enforcement

CI fails if coverage drops below 85%:

```bash
pytest --cov=src/bloginator --cov-fail-under=85
```

---

## Best Practices

1. **Write tests first** (TDD) when possible
2. **Test edge cases** and error conditions
3. **Use mock LLM** for all LLM-dependent tests
4. **Keep tests fast** - unit tests should run in milliseconds
5. **Isolate tests** - no shared state between tests
6. **Use fixtures** for reusable test data
7. **Parametrize** similar test cases
8. **Document** complex test scenarios
9. **Run tests locally** before pushing
10. **Monitor coverage** and improve continuously

---

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Check Python version (CI uses 3.10, 3.11, 3.12)
- Verify dependencies: `pip install -e ".[dev]"`
- Clear pytest cache: `rm -rf .pytest_cache`
- Check for environment-specific issues

### Coverage Lower Than Expected

- Run with `--cov-report=html` to see uncovered lines
- Check for untested error paths
- Verify test markers are correct
- Ensure all test files are discovered

### Mock LLM Not Working

- Verify `BLOGINATOR_LLM_MOCK=true` is set
- Check LLM factory uses environment variable
- Ensure MockLLMClient is imported correctly
- Check for typos in environment variable name

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
