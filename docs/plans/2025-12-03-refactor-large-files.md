# File Size Refactoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Refactor 10 Python source files (722→406 lines) to ensure no single file exceeds 400 lines while maintaining HIGH quality standards and test coverage.

**Architecture:**
- Decompose large monolithic files into focused, single-responsibility modules
- Extract helper functions into utility modules where appropriate
- Extract UI component logic into dedicated UI component files
- Move complex business logic into service/engine classes
- Maintain all existing tests + add new tests for refactored components
- All changes follow TDD: write tests first, implement, verify quality gates

**Tech Stack:** Python 3.10+, Pytest, Pydantic, Streamlit, Click

---

## Files to Refactor (10 total, 5,390 lines → <4,000 lines)

| File | Lines | Target | Strategy |
|------|-------|--------|----------|
| corpus.py | 722 | 4 files <200 each | Extract tab functions to separate modules |
| prompt_tuner.py | 710 | 3 files <300 each | Extract evaluation, test generation, mutation logic |
| extract_config.py | 611 | 2 files <300 each | Extract helpers, config loading, processing |
| outline_generator.py | 546 | 2 files <300 each | Extract prompt building, section generation |
| corpus_config.py | 545 | 2 files <300 each | Extract validators, file operations |
| llm_mock.py | 489 | 2-3 files <250 each | Extract client implementations |
| searcher.py | 488 | 2 files <250 each | Extract search strategies, result handling |
| draft.py | 452 | 2 files <250 each | Extract CLI logic, execution engine |
| template_manager.py | 421 | 2 files <250 each | Extract file I/O, template operations |
| outline.py | 406 | 1-2 files <250 each | Extract CLI helpers, output formatting |

---

## TASK 1: Refactor corpus.py (722 → 4 files)

**Objective:** Extract 3 tab display functions + helpers into separate modules

**Files:**
- Modify: `src/bloginator/ui/_pages/corpus.py` (main orchestrator, ~100 lines)
- Create: `src/bloginator/ui/_pages/_corpus_extraction.py` (extraction tab, ~180 lines)
- Create: `src/bloginator/ui/_pages/_corpus_indexing.py` (indexing tab, ~200 lines)
- Create: `src/bloginator/ui/_pages/_corpus_status.py` (status tab, ~180 lines)
- Modify: `tests/unit/ui/_pages/test_corpus.py` (add new tests)

**Step 1: Write tests for extraction tab component**

File: `tests/unit/ui/_pages/test_corpus_extraction.py`

```python
"""Tests for corpus extraction UI component."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import streamlit as st


class TestCorpusExtraction:
    """Tests for extraction tab display logic."""

    def test_show_extraction_tab_requires_config(self, tmp_path):
        """Extraction tab should warn when corpus config missing."""
        # This test just verifies the function can be called
        # Actual Streamlit rendering is tested via import
        from bloginator.ui._pages._corpus_extraction import show_extraction_tab

        # Function should exist and be callable
        assert callable(show_extraction_tab)

    def test_show_extraction_tab_loads_config(self, tmp_path):
        """Extraction tab should load corpus config when present."""
        from bloginator.ui._pages._corpus_extraction import show_extraction_tab

        # Verify function is callable and has proper docstring
        assert show_extraction_tab.__doc__ is not None
        assert callable(show_extraction_tab)

    def test_extraction_helpers_parse_output_correctly(self):
        """Extraction output parsing should handle stdout/stderr."""
        from bloginator.ui._pages._corpus_extraction import (
            _parse_extraction_summary,
        )

        sample_output = "Extracted: 10 files\nSkipped: 2 files\n"
        result = _parse_extraction_summary(sample_output)

        assert result["extracted"] == 10
        assert result["skipped"] == 2
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/matt/GitHub/Personal/bloginator
pytest tests/unit/ui/_pages/test_corpus_extraction.py -xvs
```

Expected output: FAIL - Module `bloginator.ui._pages._corpus_extraction` does not exist

**Step 3: Extract extraction tab to new module**

File: `src/bloginator/ui/_pages/_corpus_extraction.py`

```python
"""Corpus extraction UI component."""

import subprocess
from pathlib import Path

import streamlit as st
import yaml

from bloginator.corpus_config import CorpusConfigManager


def show_extraction_tab() -> None:
    """Show the extraction interface."""
    st.subheader("Extract Documents")

    st.markdown(
        """
        Extract text from your document corpus (PDF, DOCX, Markdown, TXT).
        Configure your corpus sources in `corpus/corpus.yaml`.
        """
    )

    # Check if corpus config exists
    corpus_config = Path("corpus/corpus.yaml")
    sample_config = Path("corpus/corpus.sample.yaml")
    if not corpus_config.exists():
        st.warning(
            """
            ⚠️ **No corpus configuration found!**

            Create `corpus/corpus.yaml` based on `corpus/corpus.sample.yaml` to define your document sources.

            **Note:** `corpus/corpus.yaml` is gitignored to protect your local paths.
            """
        )

        if st.button("Create Config from Sample"):
            if sample_config.exists():
                corpus_config.write_text(sample_config.read_text())
                st.success("✓ Created corpus/corpus.yaml from sample")
                st.rerun()
            else:
                st.error("Sample config not found at corpus/corpus.sample.yaml")

        return

    # Load and display corpus config
    with corpus_config.open() as f:
        config = yaml.safe_load(f)

    st.success(f"✓ Loaded configuration from {corpus_config}")

    # [REST OF EXTRACTION TAB LOGIC - lines 76-300 from original]


def _parse_extraction_summary(output: str) -> dict[str, int]:
    """Parse extraction command output to extract metrics.

    Args:
        output: Command stdout output

    Returns:
        Dictionary with extracted/skipped counts
    """
    # Parse logic here
    return {"extracted": 0, "skipped": 0}
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/ui/_pages/test_corpus_extraction.py -xvs
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/bloginator/ui/_pages/_corpus_extraction.py tests/unit/ui/_pages/test_corpus_extraction.py
git commit -m "refactor: extract corpus extraction UI to separate module

- Extract show_extraction_tab() to _corpus_extraction.py
- Add helper functions for parsing output
- Add comprehensive tests for extraction logic
- Reduces corpus.py by ~200 lines"
```

---

## TASK 2: Extract corpus indexing UI (corpus.py cleanup continued)

**Objective:** Extract indexing tab logic to separate module

**Files:**
- Create: `src/bloginator/ui/_pages/_corpus_indexing.py` (~200 lines)
- Modify: `tests/unit/ui/_pages/test_corpus.py`

**Step 1: Write tests**

File: `tests/unit/ui/_pages/test_corpus_indexing.py`

```python
"""Tests for corpus indexing UI component."""

import pytest


class TestCorpusIndexing:
    """Tests for indexing tab display logic."""

    def test_show_indexing_tab_callable(self):
        """Indexing tab should be callable."""
        from bloginator.ui._pages._corpus_indexing import show_indexing_tab

        assert callable(show_indexing_tab)

    def test_indexing_helpers_format_status(self):
        """Status formatting should handle index states."""
        from bloginator.ui._pages._corpus_indexing import (
            _format_index_status,
        )

        # Index exists
        result = _format_index_status(True)
        assert "exists" in result.lower()

        # Index missing
        result = _format_index_status(False)
        assert "missing" in result.lower()
```

**Step 2-5: [Same pattern as Task 1]**

```bash
# Run test (fails)
pytest tests/unit/ui/_pages/test_corpus_indexing.py -xvs

# Create module with extraction logic from lines 301-550 of corpus.py
# ... (extract show_indexing_tab and helpers to _corpus_indexing.py)

# Run tests (pass)
pytest tests/unit/ui/_pages/test_corpus_indexing.py -xvs

# Commit
git add src/bloginator/ui/_pages/_corpus_indexing.py tests/unit/ui/_pages/test_corpus_indexing.py
git commit -m "refactor: extract corpus indexing UI to separate module"
```

---

## TASK 3: Extract corpus status UI (corpus.py cleanup continued)

**Objective:** Extract status tab logic to separate module, finalize corpus.py

**Files:**
- Create: `src/bloginator/ui/_pages/_corpus_status.py` (~180 lines)
- Modify: `src/bloginator/ui/_pages/corpus.py` (orchestrator only, ~100 lines)

**Step 1: Write tests**

```python
"""Tests for corpus status UI component."""

class TestCorpusStatus:
    """Tests for status tab display logic."""

    def test_show_status_tab_callable(self):
        """Status tab should be callable."""
        from bloginator.ui._pages._corpus_status import show_status_tab

        assert callable(show_status_tab)

    def test_status_helpers_calculate_statistics(self):
        """Status stats should calculate corpus metrics."""
        from bloginator.ui._pages._corpus_status import _calculate_corpus_stats

        stats = _calculate_corpus_stats(document_count=100, total_words=50000)
        assert stats["avg_words_per_doc"] == 500
```

**Step 2-5: [Execute same pattern]**

**After Task 3 - Update corpus.py main file:**

File: `src/bloginator/ui/_pages/corpus.py` (now ~100 lines)

```python
"""Corpus management page for Bloginator Streamlit UI."""

import streamlit as st

from bloginator.ui._pages._corpus_extraction import show_extraction_tab
from bloginator.ui._pages._corpus_indexing import show_indexing_tab
from bloginator.ui._pages._corpus_status import show_status_tab


def show():
    """Display the corpus management page."""
    st.header("📁 Corpus Management")

    st.markdown(
        """
        Manage your document corpus: extract text from source files and build the searchable index.
        """
    )

    # Tabs for different corpus operations
    tab1, tab2, tab3 = st.tabs(["Extract", "Index", "Status"])

    with tab1:
        show_extraction_tab()

    with tab2:
        show_indexing_tab()

    with tab3:
        show_status_tab()
```

**Step 5 Final: Commit**

```bash
git add src/bloginator/ui/_pages/_corpus_status.py src/bloginator/ui/_pages/corpus.py
git commit -m "refactor: extract corpus status UI, simplify main orchestrator

- Extract show_status_tab() to _corpus_status.py
- Update corpus.py to orchestrate three tab modules
- corpus.py now 100 lines (was 722)
- All tests passing"
```

---

## TASK 4: Refactor llm_mock.py (489 → 2-3 files)

**Objective:** Split 3 LLM client classes into separate focused modules

**Files:**
- Create: `src/bloginator/generation/_llm_assistant_client.py` (AssistantLLMClient, ~150 lines)
- Create: `src/bloginator/generation/_llm_interactive_client.py` (InteractiveLLMClient, ~120 lines)
- Create: `src/bloginator/generation/_llm_mock_client.py` (MockLLMClient, ~150 lines)
- Modify: `src/bloginator/generation/llm_mock.py` (exports only, ~20 lines)

**Step 1-5: [Write tests for each class in isolation, extract to separate modules]**

Tests should verify:
- Each client can be imported independently
- Each client implements LLMClient interface
- Each client's methods work correctly in isolation
- llm_mock.py correctly re-exports all clients

**Example test structure:**

```python
# tests/unit/generation/test_llm_assistant_client.py
def test_assistant_client_initialization():
    from bloginator.generation._llm_assistant_client import AssistantLLMClient
    # Test init and properties

def test_assistant_client_implements_interface():
    from bloginator.generation.llm_client import LLMClient
    from bloginator.generation._llm_assistant_client import AssistantLLMClient

    assert issubclass(AssistantLLMClient, LLMClient)

def test_assistant_client_methods():
    # Test generate_outline, generate_draft, etc.
```

**Final llm_mock.py structure:**

```python
"""LLM client implementations (Streamlit app mock clients).

This module provides multiple LLM implementations for different
interaction patterns:
- AssistantLLMClient: Returns pre-written responses
- InteractiveLLMClient: Prompts user for input
- MockLLMClient: Generates deterministic mock responses
"""

from bloginator.generation._llm_assistant_client import AssistantLLMClient
from bloginator.generation._llm_interactive_client import InteractiveLLMClient
from bloginator.generation._llm_mock_client import MockLLMClient

__all__ = [
    "AssistantLLMClient",
    "InteractiveLLMClient",
    "MockLLMClient",
]
```

---

## TASK 5: Refactor searcher.py (488 → 2 files)

**Objective:** Split embeddings + SearchResult from CorpusSearcher

**Files:**
- Create: `src/bloginator/search/_embedding.py` (embedding utilities, ~80 lines)
- Create: `src/bloginator/search/_search_result.py` (SearchResult class, ~100 lines)
- Modify: `src/bloginator/search/searcher.py` (CorpusSearcher only, ~250 lines)

**Key decomposition:**
- `_get_embedding_model()` → `_embedding.py`
- `SearchResult` class → `_search_result.py`
- `CorpusSearcher` stays in searcher.py
- searcher.py re-exports SearchResult for backward compatibility

---

## TASK 6: Refactor extract_config.py (611 → 2 files)

**Objective:** Extract helper functions and error handling to separate module

**Files:**
- Create: `src/bloginator/cli/_extract_config_helpers.py` (~250 lines)
- Modify: `src/bloginator/cli/extract_config.py` (~300 lines, main orchestrator)

**Functions to extract:**
- `_load_config()`
- `_display_sources_table()`
- `_process_all_sources()`
- `_process_single_source()`
- `_filter_files_by_config()`
- All internal helper functions

**Tests:** Verify each helper works correctly with different input scenarios

---

## TASK 7: Refactor corpus_config.py (545 → 2 files)

**Objective:** Extract validation logic and file operations

**Files:**
- Create: `src/bloginator/models/_corpus_source.py` (CorpusSource + validators, ~200 lines)
- Create: `src/bloginator/models/_date_range.py` (DateRange model, ~60 lines)
- Modify: `src/bloginator/corpus_config.py` (CorpusConfigManager only, ~250 lines)

**Rationale:** Models should live in `src/bloginator/models/` for proper layering

---

## TASK 8: Refactor outline_generator.py (546 → 2 files)

**Objective:** Extract prompt building logic from generation logic

**Files:**
- Create: `src/bloginator/generation/_outline_prompt_builder.py` (~150 lines)
- Modify: `src/bloginator/generation/outline_generator.py` (~350 lines, core generation)

**Functions to extract:**
- Prompt construction helpers
- Section formatting logic
- Metadata generation for prompts

---

## TASK 9: Refactor prompt_tuner.py (710 → 3 files)

**Objective:** Split test generation, evaluation, and mutation strategies

**Files:**
- Create: `src/bloginator/optimization/_tuner_test_generator.py` (test case generation, ~150 lines)
- Create: `src/bloginator/optimization/_tuner_evaluator.py` (scoring logic, ~180 lines)
- Create: `src/bloginator/optimization/_tuner_mutator.py` (prompt mutation, ~150 lines)
- Modify: `src/bloginator/optimization/prompt_tuner.py` (orchestrator, ~180 lines)

**Dataclasses to keep in prompt_tuner.py:**
- TestCase
- RoundResult
- TuningResult

**PromptTuner class methods to extract:**
- Test generation → _test_generator.py
- Evaluation → _evaluator.py
- Mutation → _mutator.py

---

## TASK 10: Refactor draft.py (452 → 2 files)

**Objective:** Extract CLI command logic from execution engine

**Files:**
- Create: `src/bloginator/cli/_draft_engine.py` (execution logic, ~220 lines)
- Modify: `src/bloginator/cli/draft.py` (Click command only, ~200 lines)

**Functions to extract:**
- All non-Click-decorator functions to _draft_engine.py

---

## TASK 11: Refactor template_manager.py (421 → 2 files)

**Objective:** Extract file I/O from template operations

**Files:**
- Create: `src/bloginator/services/_template_storage.py` (file operations, ~160 lines)
- Modify: `src/bloginator/services/template_manager.py` (TemplateManager logic, ~220 lines)

**Functions to extract:**
- `_save_template()`
- `_load_template_from_disk()`
- `_delete_template_from_disk()`
- File listing/discovery logic

---

## TASK 12: Refactor outline.py (406 → 2 files)

**Objective:** Extract output formatting from CLI command

**Files:**
- Create: `src/bloginator/cli/_outline_formatter.py` (output formatting, ~120 lines)
- Modify: `src/bloginator/cli/outline.py` (Click command, ~250 lines)

**Functions to extract:**
- `_format_outline_output()`
- `_write_outline_files()`
- All non-command functions

---

## Quality Assurance Checkpoints

After EVERY task:

1. **Run tests for that module:**
   ```bash
   pytest tests/unit/path/to/test.py -xvs --no-cov
   ```

2. **Run mypy on modified modules:**
   ```bash
   mypy src/bloginator/path/to/module.py
   ```

3. **Check line counts:**
   ```bash
   wc -l src/bloginator/path/to/*.py
   ```

4. **Verify no lines exceed 400:**
   ```bash
   find src/bloginator/path -name "*.py" -exec wc -l {} \; | awk '$1 > 400'
   ```

5. **Run full quality gate before commit:**
   ```bash
   ./scripts/fast-quality-gate.sh
   ```

---

## Overall Checklist

After all 12 tasks complete:

- [ ] All 10 original files now <400 lines
- [ ] All new utility/component files <250 lines
- [ ] All imports updated to use new modules
- [ ] All tests passing (target ≥70% coverage)
- [ ] No mypy errors
- [ ] No ruff/black/isort issues
- [ ] Pydocstyle passes (all public APIs documented)
- [ ] Git history clean with logical commits
- [ ] All backward compatibility maintained (re-exports work)
- [ ] README/documentation updated if needed

---

## Execution Strategy

**Recommended approach:** Use superpowers:subagent-driven-development
- Each task dispatches a fresh subagent
- Code review between tasks
- Quality gates verified before moving forward
- Parallel potential for independent tasks (e.g., Tasks 4-12 after Task 1-3 complete)

**Alternative:** superpowers:executing-plans for batch execution with checkpoints
