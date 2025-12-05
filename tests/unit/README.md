# Unit Tests

Fast, isolated tests for individual components with full mocking of dependencies.

## Directory Structure

```text
unit/
├── cli/           # CLI command tests
├── corpus/        # Corpus configuration tests
├── export/        # Export format tests
├── extraction/    # Document extraction tests
├── generation/    # LLM generation tests
├── indexing/      # Vector indexing tests
├── models/        # Data model tests
├── monitoring/    # Logging and metrics tests
├── prompts/       # Prompt loader tests
├── quality/       # Slop detection tests
├── safety/        # Blocklist tests
├── search/        # Search functionality tests
├── services/      # Service layer tests
├── ui/            # UI component tests
├── utils/         # Utility function tests
└── web/           # Web API tests
```

## Running Unit Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific module
pytest tests/unit/generation/ -v

# Single file
pytest tests/unit/models/test_document.py -v

# Pattern matching
pytest tests/unit/ -k "test_extract" -v
```

## Coverage Target

Unit tests should achieve 90%+ coverage for core modules.

## Test Patterns

All unit tests follow these patterns:

1. **Arrange-Act-Assert** structure
2. **Mock all external dependencies**
3. **Use pytest fixtures for setup**
4. **Parametrize similar test cases**
5. **Descriptive test names and docstrings**

## Example

```python
class TestDocumentModel:
    """Tests for Document model."""

    def test_creation_with_valid_data(self):
        """Valid data should create document successfully."""
        doc = Document(content="test", source_path=Path("test.md"))
        assert doc.content == "test"

    @pytest.mark.parametrize("content", ["", None])
    def test_creation_rejects_empty_content(self, content):
        """Empty content should raise validation error."""
        with pytest.raises(ValueError):
            Document(content=content, source_path=Path("test.md"))
```
