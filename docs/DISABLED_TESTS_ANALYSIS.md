# Disabled Tests Analysis

## Overview

This document analyzes all currently disabled tests in the bloginator project and provides recommendations for addressing them.

**Total Disabled Tests:** 4 test modules with skip marks

---

## Disabled Test Modules

### 1. `tests/unit/cli/test_outline_cli.py` (8 tests)

**Skip Reason:** `"Mock implementation needs proper OutlineGenerator setup"`

**Status:** Skipped at module level with `pytestmark = pytest.mark.skip(...)`

**Issue Analysis:**
- Tests mock `OutlineGenerator` but return incorrect mock object structures
- After TASK 12 refactoring, outline command now delegates to helper functions in `_outline_formatter.py`
- Mocks need to be updated to match refactored module structure
- Tests patch `bloginator.cli.outline.OutlineGenerator` but should also mock:
  - `CorpusSearcher` (now explicitly used in outline.py)
  - `create_llm_from_config` (explicitly used)
  - Output functions from `_outline_formatter` module

**Test Count:** 8 tests
- `test_outline_requires_index_or_template`
- `test_outline_with_keywords`
- `test_outline_with_template`
- `test_outline_with_thesis`
- `test_outline_combining_keywords_and_template`
- `test_outline_with_invalid_template`
- `test_outline_generation_timeout`
- `test_outline_structure_saved_to_file`

**Recommendation:** FIXABLE - Update mocks to patch new imports and provide proper mock attributes

---

### 2. `tests/unit/cli/test_search_cli.py` (10 tests)

**Skip Reason:** `"Mock implementation needs SearchResult objects, not dicts"`

**Status:** Skipped at module level with `pytestmark = pytest.mark.skip(...)`

**Issue Analysis:**
- Tests provide dictionary mocks for search results: `{"text": "...", "metadata": {...}, "score": ...}`
- `CorpusSearcher.search()` returns `SearchResult` objects (from `bloginator.search._search_result.SearchResult`)
- Mocks need to create actual `SearchResult` instances instead of dicts
- OR: Tests need to accept that mocks can be flexible with object types

**Test Count:** 10 tests
- `test_search_requires_index`
- `test_search_requires_query`
- `test_search_basic`
- `test_search_with_n_results`
- `test_search_with_no_results`
- `test_search_with_special_characters`
- `test_search_with_very_long_query`
- `test_search_with_corrupted_index`
- `test_search_result_ranking_displayed`
- `test_search_with_json_format`

**Recommendation:** FIXABLE - Create SearchResult mock objects or use MagicMock with flexible attribute access

---

### 3. `tests/quality/test_retry_orchestrator.py` (unknown count)

**Skip Reason:** `"Requires proper ChromaDB mock setup"`

**Status:** Skipped at module level with `pytestmark = pytest.mark.skip(...)`

**Issue Analysis:**
- Tests interact with ChromaDB vector database
- ChromaDB is complex to mock (in-memory vs persistent vs mocked)
- Tests likely validate retry logic under ChromaDB failures
- May require proper ChromaDB test fixtures or temp database setup

**Recommendation:** MEDIUM EFFORT - Requires ChromaDB test environment setup

---

### 4. `tests/unit/web/test_routes.py` (6 tests)

**Skip Reason:** `skipif(not FASTAPI_AVAILABLE, ...)`

**Status:** Conditional skip - skipped if FastAPI dependencies not installed

**Issue Analysis:**
- Not truly "disabled" - this is proper conditional skipping for optional dependencies
- Tests will run if `pip install bloginator[web]` extras are installed
- The skip is by design for optional features
- Pre-commit hook fix in TASK 11 made these skip gracefully instead of erroring on import

**Test Count:** 6 tests
- `test_index_page`
- `test_corpus_page`
- `test_create_page`
- `test_search_page`
- `test_health_check`
- `test_api_docs`

**Recommendation:** NOT A PROBLEM - This is proper optional dependency handling. Skip is intentional.

---

## Summary Table

| File | Tests | Type | Effort | Fixable |
|------|-------|------|--------|---------|
| test_outline_cli.py | 8 | Mock mismatch | Low | ✅ Yes |
| test_search_cli.py | 10 | Type mismatch | Low-Medium | ✅ Yes |
| test_retry_orchestrator.py | ? | DB setup | Medium | ✅ Yes |
| test_routes.py | 6 | Optional | N/A | ℹ️ By Design |

---

## Remediation Priority

### Priority 1 (Quick Wins)
1. **test_outline_cli.py** - Update mocks to use new imports after refactoring
   - Effort: 30-45 minutes
   - Complexity: Low - straightforward mock updates

2. **test_search_cli.py** - Convert dict mocks to SearchResult objects
   - Effort: 30-45 minutes
   - Complexity: Low - convert dicts to proper model objects

### Priority 2 (Medium Effort)
3. **test_retry_orchestrator.py** - Setup ChromaDB test fixtures
   - Effort: 1-2 hours
   - Complexity: Medium - requires ChromaDB knowledge

### Priority 3 (Not Needed)
4. **test_routes.py** - Already properly handled with conditional skip

---

## Code Changes Needed

### For test_outline_cli.py

```python
# Remove this line:
pytestmark = pytest.mark.skip(reason="Mock implementation needs proper OutlineGenerator setup")

# Update test mocks to patch:
@patch("bloginator.cli.outline.CorpusSearcher")
@patch("bloginator.cli.outline.create_llm_from_config")
@patch("bloginator.cli.outline.OutlineGenerator")
@patch("bloginator.cli._outline_formatter.display_outline_results")  # After formatter refactoring
@patch("bloginator.cli._outline_formatter.save_outline_files")       # After formatter refactoring
def test_example(mock_save, mock_display, mock_gen, mock_llm, mock_searcher, ...):
    # Setup mocks with proper attributes
    mock_outline = Mock()
    mock_outline.get_all_sections = Mock(return_value=[])
    mock_outline.sections = []
    mock_outline.title = "Test"
    mock_outline.thesis = None
    mock_outline.avg_coverage = 75.0
    mock_outline.low_coverage_sections = 0
    mock_outline.to_markdown = Mock(return_value="# Test")
    mock_outline.model_dump_json = Mock(return_value='{"title": "Test"}')
```

### For test_search_cli.py

```python
# Remove this line:
pytestmark = pytest.mark.skip(reason="Mock implementation needs SearchResult objects, not dicts")

# Import SearchResult:
from bloginator.search import SearchResult

# In test mocks, create proper SearchResult objects:
mock_results = [
    SearchResult(
        text="Sample text about leadership",
        source="doc1.md",
        score=0.95,
        metadata={"source": "doc1.md"}
    )
]
```

### For test_retry_orchestrator.py

```python
# Remove skip mark

# Add proper fixture setup:
@pytest.fixture
def mock_chromadb(tmp_path):
    """Create in-memory ChromaDB for testing."""
    # Could use chromadb.Client(settings=chromadb.config.Settings(...))
    # or monkeypatch to prevent real DB access
    pass
```

---

## Recommendation to User

All disabled tests are **fixable** with moderate effort:

1. **Quick wins** (test_outline_cli.py, test_search_cli.py): 45-60 minutes total
2. **Medium effort** (test_retry_orchestrator.py): 1-2 hours
3. **Already working** (test_routes.py): No action needed

Suggest tackling Priority 1 immediately after refactoring merge, as these are simple mock updates.

---

## Notes

- The refactoring work (TASK 11, TASK 12) may have made some mocks incorrect
- This is expected and fixable with straightforward mock updates
- No fundamental architectural issues preventing tests from passing
- Web tests are properly skipped by design (optional FastAPI dependency)
