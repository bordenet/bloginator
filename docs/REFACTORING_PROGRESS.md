# File Size Refactoring - Progress Checkpoint

**Status:** IN PROGRESS
**Last Updated:** 2025-12-03
**Base Commit:** 9973a26 (retry logic for Streamlit generation)

## Overview

Refactoring 10 Python files (5,390 lines → target <4,000 lines) to ensure no single file exceeds 400 lines. This document is **RESUMABLE** - any agent can pick up from here.

## Completed Tasks

### ✅ TASK 1: Refactor corpus.py (722 → 4 files)

**Status:** PARTIALLY COMPLETE - Need further decomposition

**Files Created:**
- `src/bloginator/ui/_pages/corpus.py` (30 lines) ✓
- `src/bloginator/ui/_pages/_corpus_indexing.py` (288 lines) ✓
- `src/bloginator/ui/_pages/_corpus_status.py` (82 lines) ✓
- `src/bloginator/ui/_pages/_corpus_extraction.py` (375 lines) ⚠️ **TOO LARGE**

**Issue:** `_corpus_extraction.py` is 375 lines (should be <200)

**Resolution Needed:**
1. Extract `_run_extraction()` function + helpers to separate `_corpus_extraction_engine.py` (~150 lines)
2. Keep display logic in `_corpus_extraction.py` (~180 lines)
3. Reduces both files to target range

**Next Steps:**
```bash
# Verify current work compiles
python -m py_compile src/bloginator/ui/_pages/_corpus_extraction.py
wc -l src/bloginator/ui/_pages/_corpus_extraction.py

# After further decomposition:
wc -l src/bloginator/ui/_pages/_corpus_extraction.py  # Should be <200
wc -l src/bloginator/ui/_pages/_corpus_extraction_engine.py  # New file ~150

# Update corpus.py imports
# Test imports work
pytest tests/unit/ui/_pages/ -xvs

# Commit when complete
git add src/bloginator/ui/_pages/_corpus_*.py
git commit -m "refactor: split corpus extraction UI into display + engine modules"
```

---

## Remaining Tasks

### 📋 TASK 2-3: Corpus Extraction Engine Decomposition

After TASK 1 split, proceed with:
- Extract `_run_extraction()` to `_corpus_extraction_engine.py` (150 lines)
- Extract source management UI to `_corpus_extraction_sources.py` (180 lines)
- Clean up `_corpus_extraction.py` to 100 lines (orchestrator)

### 📋 TASK 4: Refactor llm_mock.py (489 → 2-3 files)

**Target:** Split 3 client classes into separate modules
- `src/bloginator/generation/_llm_assistant_client.py` (~150 lines)
- `src/bloginator/generation/_llm_interactive_client.py` (~120 lines)
- `src/bloginator/generation/_llm_mock_client.py` (~150 lines)
- `src/bloginator/generation/llm_mock.py` (export stub, ~20 lines)

**Notes:** Classes to extract: `AssistantLLMClient`, `InteractiveLLMClient`, `MockLLMClient`

### 📋 TASK 5: Refactor searcher.py (488 → 2 files)

**Target:** Split embeddings + SearchResult from CorpusSearcher
- `src/bloginator/search/_embedding.py` (~80 lines)
- `src/bloginator/search/_search_result.py` (~100 lines)
- `src/bloginator/search/searcher.py` (CorpusSearcher only, ~250 lines)

### 📋 TASK 6: Refactor extract_config.py (611 → 2 files)

**Target:** Extract helper functions from main orchestrator
- `src/bloginator/cli/_extract_config_helpers.py` (~250 lines)
- `src/bloginator/cli/extract_config.py` (~300 lines)

**Functions to Extract:**
- `_load_config()`
- `_display_sources_table()`
- `_process_all_sources()`
- `_process_single_source()`
- File filtering helpers

### 📋 TASK 7: Refactor corpus_config.py (545 → 2 files)

**Target:** Move models to proper location + keep manager
- Create `src/bloginator/models/_corpus_source.py` (CorpusSource, DateRange, ~200 lines)
- Keep `src/bloginator/corpus_config.py` (CorpusConfigManager, ~250 lines)

### 📋 TASK 8: Refactor outline_generator.py (546 → 2 files)

**Target:** Extract prompt building from generation
- `src/bloginator/generation/_outline_prompt_builder.py` (~150 lines)
- `src/bloginator/generation/outline_generator.py` (~350 lines)

**Functions to Extract:**
- Prompt construction helpers
- Section formatting
- Metadata generation

### 📋 TASK 9: Refactor prompt_tuner.py (710 → 3 files)

**Target:** Split test gen / evaluation / mutation
- `src/bloginator/optimization/_tuner_test_generator.py` (~150 lines)
- `src/bloginator/optimization/_tuner_evaluator.py` (~180 lines)
- `src/bloginator/optimization/_tuner_mutator.py` (~150 lines)
- `src/bloginator/optimization/prompt_tuner.py` (orchestrator, ~180 lines)

**Dataclasses Remain:** TestCase, RoundResult, TuningResult

### 📋 TASK 10: Refactor draft.py (452 → 2 files)

**Target:** Extract execution engine from Click command
- `src/bloginator/cli/_draft_engine.py` (~220 lines)
- `src/bloginator/cli/draft.py` (Click command only, ~200 lines)

### 📋 TASK 11: Refactor template_manager.py (421 → 2 files)

**Target:** Extract file I/O from template operations
- `src/bloginator/services/_template_storage.py` (~160 lines)
- `src/bloginator/services/template_manager.py` (TemplateManager logic, ~220 lines)

**Functions to Extract:**
- `_save_template()`
- `_load_template_from_disk()`
- `_delete_template_from_disk()`
- File discovery/listing

### 📋 TASK 12: Refactor outline.py (406 → 2 files)

**Target:** Extract output formatting from CLI
- `src/bloginator/cli/_outline_formatter.py` (~120 lines)
- `src/bloginator/cli/outline.py` (Click command, ~250 lines)

**Functions to Extract:**
- `_format_outline_output()`
- `_write_outline_files()`
- All non-command functions

---

## Quality Checkpoints (Per Task)

After each task, verify:

```bash
# 1. Syntax check
python -m py_compile src/bloginator/path/to/*.py

# 2. Line count verification
wc -l src/bloginator/path/to/*.py | grep -E "^[[:space:]]*[4-9][0-9][0-9]|^[[:space:]]*[1-9][0-9]{3}"

# 3. Type checking
mypy src/bloginator/path/to/module.py

# 4. Tests
pytest tests/unit/path/to/test_*.py -xvs --no-cov

# 5. Full quality gate (must pass before commit)
./scripts/fast-quality-gate.sh
```

---

## Obsolete Files to Purge

After refactoring complete:
- [ ] PLAN_SKIP_TRACKING_UX.md (obsolete planning doc)
- [ ] RETROSPECTIVE_2025-12-03.md (if obsolete)
- [ ] TEST_BUGS_REVEALED.md (if obsolete)
- [ ] TEST_PLAN.md (if obsolete)
- [ ] VALIDATION_WARNINGS.md (if obsolete)

These will be cleaned up after all refactoring tasks complete.

---

## Key Constraints

1. **Line Limit:** All files MUST be ≤400 lines (target <250 for components)
2. **Quality Bar:**
   - 70%+ test coverage maintained
   - All mypy checks pass
   - All pydocstyle checks pass
   - Fast-quality-gate.sh must pass
3. **Backward Compatibility:**
   - Re-exports in parent modules for moved classes
   - All existing imports should still work
4. **Architecture:**
   - Single responsibility per module
   - Helper modules named with leading underscore `_`
   - Clear orchestrator vs. implementation split

---

## Resumption Instructions (For Next Agent)

If continuing from this checkpoint:

1. **Read this file** to understand progress
2. **Check git status** - work may be staged or committed
3. **Resume from marked section** - start with incomplete task
4. **Update this document** as you complete tasks
5. **Commit with references:** `git commit -m "refactor: complete TASK N (ref: REFACTORING_PROGRESS.md)"`

**Current State:**
- TASK 1: 75% complete (extraction module needs further split)
- All other tasks: Not started
- No commits yet on this work (in progress)

---

## Success Criteria (End of Effort)

- [ ] All 10 files now <400 lines
- [ ] All new utility modules <250 lines
- [ ] 0 files >400 lines: `find src -name "*.py" -exec wc -l {} \; | awk '$1 > 400'` returns nothing
- [ ] All tests passing: `pytest tests/unit --no-cov` ≥70% coverage
- [ ] Mypy clean: `mypy src/bloginator/...`
- [ ] Quality gates pass: `./scripts/fast-quality-gate.sh`
- [ ] Git history clean with logical commits per task
- [ ] All backward-compatible imports maintained
- [ ] Documentation updated (README if needed)
