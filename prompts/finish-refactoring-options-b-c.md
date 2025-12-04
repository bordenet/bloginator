# Execute Refactoring Options B and C - Full Execution Prompt

## Quick Start

You are continuing the Bloginator refactoring project from a previous context. **All prior work is merged to main.** Your task is to complete the remaining refactoring work and fix the final disabled test suite.

**Choose your path:**
- **Option B:** Complete all remaining refactorings + fix all disabled tests (3-4 hours, 100% complete)
- **Option C:** Complete outline_generator refactoring only + defer corpus_config (3-4 hours, 90% complete)

---

## Current State (Verified)

### Completed (Merged to main)
- ✅ 8 of 10 files successfully refactored and passing quality gates
- ✅ test_outline_cli.py: 8 tests fixed and passing
- ✅ test_search_cli.py: 10 tests fixed and passing
- ✅ test_routes.py: Clarified as working-by-design (optional dependency skip)

### Remaining
- ⚠️ outline_generator.py: 516 lines (target <300) - needs coverage + parser extraction
- ⚠️ corpus_config.py: 427 lines (target <300) - needs settings extraction
- ⚠️ test_retry_orchestrator.py: ~10 tests - needs ChromaDB mock setup

---

## Option B: Complete Everything (Recommended for Thoroughness)

### Phase 1: Extract outline_generator.py (1-2 hours)

**File:** `src/bloginator/generation/outline_generator.py` (516 lines)

**Read the file first to understand structure:**
```bash
# Then examine these specific sections:
# Lines 1-100: Imports and class definition
# Lines 255-362: _parse_outline_response and _build_outline_from_corpus
# Lines 411-474: _analyze_section_coverage and filtering methods
```

**Task 1.1: Create `src/bloginator/generation/_outline_coverage.py`**
- Extract: `_analyze_section_coverage()`, `_filter_sections_by_coverage()`, `_filter_by_keyword_match()`
- Also extract: any helper methods these functions call
- Target size: 80-100 lines
- Imports: Keep self-contained, import OutlineSection and related types from parent module

**Task 1.2: Create `src/bloginator/generation/_outline_parser.py`**
- Extract: `_parse_outline_response()`, `_build_outline_from_corpus()`
- Also extract: Outline model construction helpers
- Target size: 100-120 lines
- Imports: Keep self-contained, import types from parent

**Task 1.3: Refactor main `outline_generator.py`**
- Remove extracted methods
- Import from new helper modules at top
- Update orchestration logic to call helpers
- Target final size: 250-300 lines
- Verify: All public APIs unchanged, backward compatible

**Verification:**
```bash
wc -l src/bloginator/generation/outline_generator.py
wc -l src/bloginator/generation/_outline_coverage.py
wc -l src/bloginator/generation/_outline_parser.py
# Should be < 300, < 100, < 120 respectively
```

**Quality Check:**
```bash
./scripts/fast-quality-gate.sh
pytest tests/unit/generation/test_outline_generator.py -v
```

**Commit:** `refactor: Extract outline_generator coverage and parser logic`

---

### Phase 2: Extract corpus_config.py (45 min - 1 hour)

**File:** `src/bloginator/corpus_config.py` (427 lines)

**Read the file to understand structure:**
```bash
# Identify:
# - ExtractionSettings class
# - IndexingSettings class
# - Any dataclass definitions (~100-150 lines total)
```

**Task 2.1: Create `src/bloginator/_corpus_settings.py`**
- Extract: ExtractionSettings, IndexingSettings (any settings-related dataclasses)
- Move imports they need (just dataclass, field, etc.)
- Target size: 80-100 lines
- Keep private (underscore prefix)

**Task 2.2: Refactor main `corpus_config.py`**
- Remove extracted classes
- Add: `from bloginator._corpus_settings import ExtractionSettings, IndexingSettings`
- Keep re-exports if needed for backward compatibility
- Target final size: 300-320 lines
- Verify: All public APIs unchanged

**Verification:**
```bash
wc -l src/bloginator/corpus_config.py
wc -l src/bloginator/_corpus_settings.py
# Should be < 320 and < 100 respectively
```

**Quality Check:**
```bash
./scripts/fast-quality-gate.sh
pytest tests/unit/ -k corpus_config -v
```

**Commit:** `refactor: Extract corpus_config settings into _corpus_settings.py`

---

### Phase 3: Fix test_retry_orchestrator.py (1-2 hours)

**File:** `tests/quality/test_retry_orchestrator.py`

**Current Issue:** Skipped - requires proper ChromaDB mock setup

**Task 3.1: Investigate the test file**
```bash
# Read the test file
# Look for:
# - What ChromaDB functionality is being tested?
# - What methods are called on ChromaDB?
# - What errors occur when you run it?
```

**Task 3.2: Choose mock strategy**
Option A: In-memory ChromaDB instance for tests
```python
import chromadb
@pytest.fixture
def mock_chromadb():
    client = chromadb.Client()
    # Return configured instance
    return client
```

Option B: Full monkeypatch of ChromaDB
```python
from unittest.mock import MagicMock
@pytest.fixture
def mock_chromadb(monkeypatch):
    # Patch chromadb.Client to return mock
    pass
```

**Task 3.3: Implement chosen strategy**
- Remove pytestmark skip line
- Add proper fixture with ChromaDB setup
- Update test methods to use fixture
- Ensure mocks return realistic data structures

**Task 3.4: Run and fix failures**
```bash
pytest tests/quality/test_retry_orchestrator.py -v
# Fix assertion/mock issues as they appear
```

**Quality Check:**
```bash
./scripts/fast-quality-gate.sh
pytest tests/quality/test_retry_orchestrator.py -v
```

**Commit:** `test: Fix test_retry_orchestrator ChromaDB setup`

---

### Phase 4: Full Test Suite & Merge

**Run comprehensive tests:**
```bash
pytest tests/unit tests/integration tests/quality --no-cov -v
pytest --cov=src/bloginator --cov-fail-under=70
```

**Final verification:**
```bash
./scripts/fast-quality-gate.sh
```

**Commit all changes:**
```bash
git add -A
git commit -m "refactor: Complete file size refactoring - all 10 files <400 lines, all tests passing"
```

**Push to main:**
```bash
git push origin main
```

**Result:** 100% refactoring complete, zero disabled tests

---

## Option C: Finish outline_generator Only (Faster Path)

### Phase 1: Extract outline_generator.py (Same as Option B Phase 1)

Follow Option B Phase 1 exactly.

**Commit:** `refactor: Extract outline_generator coverage and parser logic`

---

### Phase 2: Fix test_outline_cli and test_search_cli

**Status Check:**
```bash
pytest tests/unit/cli/test_outline_cli.py tests/unit/cli/test_search_cli.py -v
```

These should already be passing from previous context. If not, review the fixes in commit f925601.

---

### Phase 3: Create Deferred Issues

**Create GitHub issues for:**

1. "Refactor corpus_config.py to <400 lines"
   - Description: Extract ExtractionSettings, IndexingSettings to _corpus_settings.py
   - Labels: refactoring, deferred
   - Reference: docs/REFACTORING_STATUS_SUMMARY.md

2. "Fix test_retry_orchestrator.py ChromaDB mocking"
   - Description: Set up proper ChromaDB test fixtures
   - Labels: testing, deferred
   - Reference: docs/DISABLED_TESTS_ANALYSIS.md

**Commit:**
```bash
git commit -m "docs: Create GitHub issues for corpus_config and test_retry_orchestrator refactoring"
```

**Result:** 90% refactoring complete, most critical work done

---

## Critical References

**Must read before starting:**
- `docs/REFACTORING_STATUS_SUMMARY.md` - Detailed breakdowns with line numbers
- `docs/DISABLED_TESTS_ANALYSIS.md` - Test remediation guidance
- `docs/PYTHON_STYLE_GUIDE.md` - Code standards
- `CLAUDE.md` - Quality gate requirements

**Key commands:**
```bash
# Quick validation
./scripts/fast-quality-gate.sh

# Full test run
pytest tests/unit tests/integration tests/quality --no-cov -v

# Coverage check
pytest --cov=src/bloginator --cov-fail-under=70
```

---

## Success Criteria

### Option B (Complete)
- [ ] outline_generator.py < 300 lines
- [ ] corpus_config.py < 300 lines
- [ ] _outline_coverage.py created (< 100 lines)
- [ ] _outline_parser.py created (< 120 lines)
- [ ] _corpus_settings.py created (< 100 lines)
- [ ] All 18 CLI tests passing (outline + search)
- [ ] test_retry_orchestrator.py passing
- [ ] `./scripts/fast-quality-gate.sh` passes
- [ ] Coverage ≥ 70%

### Option C (Streamlined)
- [ ] outline_generator.py < 300 lines
- [ ] _outline_coverage.py created (< 100 lines)
- [ ] _outline_parser.py created (< 120 lines)
- [ ] All 18 CLI tests passing
- [ ] `./scripts/fast-quality-gate.sh` passes
- [ ] GitHub issues created for deferred work
- [ ] Coverage ≥ 70%

---

## Important Notes

1. **Keep documentation updated** - Any significant changes should update relevant .md files
2. **Pre-commit hooks will enforce** - Black, Ruff, MyPy, type checking all automatic
3. **Test before push** - Run full test suite locally before pushing
4. **Backward compatibility** - All re-exports must be maintained
5. **Line length** - All code must be < 100 characters (Black enforced)

---

## Estimated Time

- **Option B:** 3-4 hours (complete + thorough)
- **Option C:** 2-3 hours (outline only + quick)

Both are high-quality outcomes. Choose based on available time and priority.

Good luck! The previous context completed the heavy lifting. This is the final push to 100% (B) or 90% (C) completion.
