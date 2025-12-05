# Test Fixtures

Sample documents and test data used across the test suite.

## Contents

| File/Directory | Purpose |
|----------------|---------|
| `sample_doc1.md` | Markdown document for extraction tests |
| `sample_doc2.md` | Second markdown sample for integration |
| `sample_doc3.txt` | Plain text document sample |
| `sample_corpus/` | Multi-file corpus for workflow tests |

## Usage

Access fixtures via pytest fixture:

```python
@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"

def test_extraction(fixtures_dir):
    sample_doc = fixtures_dir / "sample_doc1.md"
    result = extract_text_from_file(sample_doc)
    assert "Engineering Leadership" in result
```

## Sample Document Contents

### sample_doc1.md
Engineering leadership principles and practices.

### sample_doc2.md
Team culture and collaboration guidance.

### sample_doc3.txt
Code review best practices in plain text format.

### sample_corpus/
Directory structure simulating a user's corpus with multiple documents organized by topic.

## Guidelines

- Keep fixture files small and focused
- Use representative content for realistic testing
- Do not include proprietary or sensitive content
- Update this README when adding new fixtures
