# Integration Tests

Multi-component integration tests that verify Bloginator components work correctly together.

## Contents

| File | Purpose |
|------|---------|
| `test_chromadb_integration.py` | ChromaDB vector store integration |
| `test_corpus_directory_integration.py` | Corpus directory scanning and indexing |
| `test_extract_and_index.py` | Document extraction to indexing pipeline |
| `test_sample_corpus_pipeline.py` | Sample corpus end-to-end validation |
| `test_search_and_generation.py` | Search to content generation flow |
| `test_topic_alignment.py` | Topic alignment validation |

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with verbose output and coverage
pytest tests/integration/ -v --cov=src/bloginator

# Skip slow tests (not recommended for integration)
pytest tests/integration/ -m "not slow" -v
```

## Markers

All integration tests should use:

```python
@pytest.mark.integration
@pytest.mark.slow  # If test loads embedding models or takes >5s
```

## Test Patterns

Integration tests verify:

1. **Component boundaries** - Data flows correctly between modules
2. **Real dependencies** - ChromaDB, file system, embedding models
3. **Error propagation** - Errors surface appropriately across layers
4. **State management** - Index persistence and reloading

## Notes

- Tests may download embedding models on first run (~80MB)
- ChromaDB creates temporary directories (cleaned up automatically)
- Use `tmp_path` fixture for isolated file operations
