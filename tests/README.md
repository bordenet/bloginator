# Test Suite

This directory contains all tests for Bloginator, organized by test type and component.

## Directory Structure

```text
tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Multi-component tests
├── e2e/               # End-to-end workflow tests
├── benchmarks/        # Performance benchmarks
├── fixtures/          # Shared test data
├── quality/           # Quality assurance tests
├── conftest.py        # Shared pytest configuration
├── test_cli.py        # CLI smoke tests
└── test_version.py    # Version validation
```

## Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src/bloginator --cov-report=term-missing

# Unit tests only (fast)
pytest tests/unit/ -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

## Test Strategy

| Type | Purpose | Speed | Isolation |
|------|---------|-------|-----------|
| Unit | Single component | Fast (<1s) | Full mocking |
| Integration | Component interaction | Medium | Partial mocking |
| E2E | Full workflows | Slow | Real dependencies |
| Benchmark | Performance metrics | Slow | Varies |

## Coverage Requirements

- **Minimum**: 85% (CI enforced)
- **Models/Core**: 90%+
- **CLI/API**: 80%+

## Test Naming Convention

```python
def test_<component>_<scenario>_<expected_result>():
    """Descriptive docstring explaining the test."""
    pass

# Examples:
def test_extract_pdf_with_images_returns_text_only(): ...
def test_search_empty_query_raises_value_error(): ...
def test_blocklist_exact_match_blocks_content(): ...
```

## Mock LLM Mode

Tests use `BLOGINATOR_LLM_MOCK=true` for deterministic, fast execution:

```python
@pytest.fixture
def mock_llm_env(monkeypatch):
    monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")
    yield
```

## Writing Tests

Follow Arrange-Act-Assert pattern:

```python
def test_document_extraction(tmp_path):
    # Arrange
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test")

    # Act
    result = extract_text(test_file)

    # Assert
    assert result.content == "# Test"
```

See [TESTING_GUIDE.md](../docs/TESTING_GUIDE.md) for detailed guidance.
