# End-to-End Tests

Complete workflow tests that validate Bloginator from user input to final output.

## Contents

| File | Purpose |
|------|---------|
| `test_cli_workflows.py` | CLI command workflows using CliRunner |
| `test_complete_workflows.py` | Full corpus → search → generate workflows |
| `test_corpus_directory_e2e.py` | Corpus directory feature validation |
| `test_full_workflow.sh` | Shell script for manual E2E testing |
| `test_llm_roundtrip.py` | LLM request/response cycle validation |
| `test_streamlit_pages.py` | Streamlit UI page tests |

## Running E2E Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# With mock LLM (recommended for CI)
BLOGINATOR_LLM_MOCK=true pytest tests/e2e/ -v

# Skip Streamlit tests if not installed
pytest tests/e2e/ -v --ignore=tests/e2e/test_streamlit_pages.py
```

## Markers

All E2E tests should use:

```python
@pytest.mark.e2e
@pytest.mark.slow  # E2E tests are inherently slow
```

## Mock LLM Mode

E2E tests use mock LLM mode for deterministic, fast execution:

```python
@pytest.fixture
def mock_llm_env(monkeypatch):
    monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")
```

## Test Patterns

E2E tests validate:

1. **Complete workflows** - Extract → Index → Search → Generate
2. **CLI behavior** - Command invocation, argument handling, output
3. **Error handling** - User-facing error messages
4. **File I/O** - Output file creation and content

## Notes

- E2E tests create real files; use `tmp_path` for isolation
- Streamlit tests require `pip install "bloginator[web-ui]"`
- LLM tests use mock mode to avoid external API calls
