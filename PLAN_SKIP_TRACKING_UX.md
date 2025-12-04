# Skip Tracking & UX Improvements Plan

**Created:** 2025-12-03
**Status:** In Progress

## Problem Statement

1. **Stale Index:** The ChromaDB index at `.bloginator/chroma` contains 62 documents with IDs that don't match the 342 documents in `.bloginator/extracted`. The index was built from a previous extraction run.

2. **Silent Skips:** During extraction and indexing, many files are silently skipped (temp files, already extracted, unsupported formats) with no visibility to the user.

3. **UX Issues:** Progress display scrolls the terminal; no clear indication of what file is currently being processed.

---

## Completed Tasks

### 1. ✅ Add SkipCategory Enum
- Added `SkipCategory` enum to `error_reporting.py`
- Categories: `ALREADY_EXTRACTED`, `TEMP_FILE`, `IGNORE_PATTERN`, `UNSUPPORTED_EXTENSION`, `EMPTY_CONTENT`, `URL_SOURCE`, `PATH_NOT_FOUND`

### 2. ✅ Add Skip Tracking to ErrorTracker
- Added `record_skip(category, context)` method
- Added `skipped` dict and `total_skipped` counter

### 3. ✅ Add `save_to_file()` Method
- Writes JSON report with all skips and errors
- Includes timestamp, summary counts, and full lists
- Creates output directory if needed

### 4. ✅ Add Scrollable Pane UX (max 32 lines)
- `print_skip_summary()` now accepts `max_display_lines` parameter
- Truncates detailed list after limit
- Shows "see full report" message when truncated

### 5. ✅ Add Ticker-Style Progress for Extraction
- Single-line progress bar with current file name
- Uses `transient=True` so it disappears when complete
- Truncates long filenames to 40 chars

### 6. ✅ Add Ticker-Style Progress for Indexing
- Same ticker-style progress as extraction
- Shows current document being indexed

### 7. ✅ Wire Up Skip Tracking in extract_config.py
- Track skips for: temp files, ignore patterns, unsupported extensions, already extracted, URL sources, path not found
- Save report file when skips/errors occur
- Pass report file path to `print_skip_summary()`

### 8. ✅ Wire Up Skip Tracking in index.py
- Track skips for unchanged documents
- Save report file when skips/errors occur

### 9. ✅ Write Tests for Error Reporting
- Tests for ErrorTracker init, record_error, record_skip
- Tests for categorization logic
- Tests for save_to_file (structure, directory creation, edge cases)
- Tests for print_skip_summary output

---

## Remaining Tasks

### 10. ✅ Verify Full Test Suite Passes
- Run `pytest tests/` to ensure no regressions - **PASSED (96 passed, 18 skipped)**
- Run type checker (`mypy`) and linter (`ruff`) - **PASSED**
- Fixed unused imports in extract_config.py

### 11. ✅ Purge Stale .bloginator Content and Re-Index Fresh
- ✅ Purged stale content (`.bloginator/extracted/*`, `.bloginator/chroma/*`, `.bloginator/corpus-combined/*`, `.bloginator/index/*`)
- ✅ Ready for fresh re-extraction and re-indexing
- **User can now rebuild via Streamlit UI or CLI**

### 12. ✅ Add Streamlit UI Progress Indicators (BONUS)
- ✅ Added real-time progress to Streamlit extraction tab
- ✅ Added real-time progress to Streamlit indexing tab
- ✅ Streamlit now has CLI parity for progress display
- Shows current file/document being processed in real-time
- Displays scrollable output log (last 20 lines)
- File: `src/bloginator/ui/_pages/corpus.py`

### 13. ✅ Add High-Quality Tests for Streamlit UX
- ✅ Created comprehensive test suite for progress indicators
- ✅ 19 new tests for extraction and indexing progress
- ✅ Tests verify subprocess streaming, output collection, success/failure handling
- ✅ Tests verify Streamlit container behavior (progress, output, status)
- ✅ All 32 tests pass (13 existing + 19 new)
- File: `tests/unit/ui/test_corpus_management.py`

### 14. ✅ Add Skip Summary Display to Streamlit UI
- ✅ Added skip summary parsing and display for extraction tab
- ✅ Added skip summary parsing and display for indexing tab
- ✅ Reads skip report JSON files (extraction_report_*.json, indexing_report_*.json)
- ✅ Displays skip categories with counts and examples
- ✅ Shows first 5 items per category with "... and N more" for larger lists
- ✅ Graceful error handling for corrupted report files
- ✅ Uses markdown formatting for readable display (bold headers, bullet points)
- File: `src/bloginator/ui/_pages/corpus.py`

### 15. ✅ Add Tests for Skip Summary Display
- ✅ Created comprehensive test suite for skip summary functionality
- ✅ 10 new tests covering all skip summary scenarios
- ✅ Tests verify JSON parsing, category display, item limiting, error handling
- ✅ Tests verify markdown formatting and report file selection
- ✅ All 42 tests pass (32 existing + 10 new)
- File: `tests/unit/ui/test_corpus_management.py`

### 16. ✅ Verify PDF Parsing Error Handling
- ✅ Confirmed MuPDF warnings are informational, not errors
- ✅ PyMuPDF continues extracting text despite syntax errors in PDF content streams
- ✅ Error handling properly catches and reports extraction failures
- ✅ All supported file types (PDF, DOCX, MD, TXT) are being parsed correctly
- File: `src/bloginator/extraction/extractors.py`

### 17. ✅ OneDrive File Availability Check
- ✅ Added `wait_for_file_availability()` to extract_utils.py
- ✅ Polls file size every 200ms for up to 10 seconds
- ✅ Triggers OneDrive download by opening 0-byte files
- ✅ Integrated into extract_config.py and extract_single.py
- File: `src/bloginator/cli/extract_utils.py`

### 18. ✅ CLI Force Re-index with Purge
- ✅ Added `--force` flag to `bloginator index` command
- ✅ Purges existing index directory before rebuild
- ✅ Shows clear confirmation messages
- File: `src/bloginator/cli/index.py`

### 19. ✅ Full Path Display in CLI
- ✅ Changed extraction progress to show full file paths
- ✅ Changed indexing progress to show full file paths
- ✅ No more 40-character truncation
- Files: `src/bloginator/cli/extract_config.py`, `src/bloginator/cli/index.py`

### 20. ✅ MuPDF Stderr Warning Suppression
- ✅ Added `suppress_stderr()` context manager
- ✅ Suppresses C-level warnings during PDF extraction
- ✅ Informational warnings no longer clutter output
- File: `src/bloginator/extraction/extractors.py`

---

## NEW REQUIREMENTS - Phase 2: Improved Streamlit UX

### Problem Statement (Revised)

The current Streamlit UX doesn't match user expectations:
1. **Missing Running Skip List**: User wants to see skipped files as they happen in real-time
2. **Unclear Current File**: Single line should continuously update with current file path
3. **Wrong Output Display**: Current "Extraction Output" text area is not what user wanted

### Desired UX (User Requirements)

**For Extraction Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Current File: /Users/matt/Library/CloudStorage/OneDrive... │  ← Single line, updates continuously
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Skipped Files:                                              │
│ • /path/to/file1.md (already_extracted)                     │  ← Scrolling list
│ • /path/to/~$temp.docx (temp_file)                          │     of skipped files
│ • /path/to/file2.pdf (already_extracted)                    │     with reasons
│ • /path/to/.DS_Store (ignore_pattern)                       │     in real-time
│ ...                                                          │
└─────────────────────────────────────────────────────────────┘
```

**For Indexing Tab:**
Same pattern - current document + scrolling skip list

### 21. ✅ Implement Real-Time Skip List Display (Streamlit)
- ✅ Parse stdout line-by-line to detect skip events (`[SKIP]` prefix)
- ✅ Extract file path and skip reason from CLI output
- ✅ Display "Current File/Document" in single-line container (updates continuously)
- ✅ Display "Skipped Files/Documents" in scrolling text area (append-only)
- ✅ Apply to both extraction and indexing tabs
- ✅ Remove old "Extraction Output" text area
- ✅ Remove old skip summary JSON parsing
- File: `src/bloginator/ui/_pages/corpus.py`

### 22. ✅ Modify CLI to Output Skip Events in Parseable Format
- ✅ Add structured output for skip events (e.g., `[SKIP] path/to/file.md (already_extracted)`)
- ✅ Keep human-readable format but make it parseable
- ✅ Update extract_config.py to output skip events (already_extracted, path_not_found)
- ✅ Update index.py to output skip events (already_indexed)
- Files: `src/bloginator/cli/extract_config.py`, `src/bloginator/cli/index.py`

### 23. ✅ Update Tests for New UX
- ✅ Test skip event parsing from stdout
- ✅ Test current file display updates
- ✅ Test scrolling skip list accumulation
- ✅ Verify both extraction and indexing tabs
- ✅ 12 new comprehensive tests for real-time skip event parsing
- ✅ All 54 tests pass (42 existing + 12 new)
- File: `tests/unit/ui/test_corpus_management.py`

### 24. ✅ Verify Full Test Suite Passes
- ✅ Run pytest - all corpus management tests pass (54/54)
- ✅ No regressions in existing tests
- ✅ Coverage maintained at 100% for new code

---

## Phase 3: Code Refactoring (400 Line Limit)

### Files to Refactor (>400 lines)

```
741 src/bloginator/ui/_pages/corpus.py
710 src/bloginator/optimization/prompt_tuner.py
545 src/bloginator/corpus_config.py
489 src/bloginator/generation/llm_mock.py
488 src/bloginator/search/searcher.py
467 src/bloginator/cli/extract_config.py
450 src/bloginator/cli/draft.py
421 src/bloginator/services/template_manager.py
406 src/bloginator/cli/outline.py
```

### 25. ⏳ Refactor corpus.py (741 → <400 lines)
- ⏳ Extract extraction tab to separate function/module
- ⏳ Extract indexing tab to separate function/module
- ⏳ Extract status tab to separate function/module
- ⏳ Keep main orchestration in corpus.py
- ⏳ Ensure all tests still pass

### 26. ⏳ Refactor Other Large Files
- ⏳ prompt_tuner.py (710 lines)
- ⏳ corpus_config.py (545 lines)
- ⏳ llm_mock.py (489 lines)
- ⏳ searcher.py (488 lines)
- ⏳ extract_config.py (467 lines)
- ⏳ draft.py (450 lines)
- ⏳ template_manager.py (421 lines)
- ⏳ outline.py (406 lines)

### 27. ⏳ Final Test Suite Verification
- ⏳ Run full pytest suite
- ⏳ Run mypy type checking
- ⏳ Run ruff linting
- ⏳ Verify coverage ≥70%
- ⏳ Ensure no regressions

---

## Files Modified

- `src/bloginator/cli/error_reporting.py` - Added SkipCategory, skip tracking, save_to_file, improved print_skip_summary
- `src/bloginator/cli/extract_config.py` - Added ticker progress, skip tracking, report saving
- `src/bloginator/cli/index.py` - Added ticker progress, skip tracking, report saving
- `src/bloginator/ui/_pages/corpus.py` - Added real-time progress indicators for extraction and indexing (Streamlit)
- `src/bloginator/cli/search.py` - Added `--format json` output option
- `tests/unit/cli/test_error_reporting.py` - New test file for error reporting
- `tests/unit/ui/test_corpus_management.py` - Added 19 comprehensive tests for Streamlit progress indicators

---

## How to Re-Index Fresh

```bash
# 1. Purge stale content
rm -rf .bloginator/extracted/*
rm -rf .bloginator/chroma/*
rm -rf .bloginator/corpus-combined/*
rm -rf .bloginator/index/*

# 2. Re-extract from corpus.yaml
bloginator extract corpus/corpus.yaml -o .bloginator/extracted

# 3. Re-build index
bloginator index .bloginator/extracted -o .bloginator/chroma
```

---

## Report File Format

Reports are saved to the output directory as `{prefix}_report_{timestamp}.json`:

```json
{
  "timestamp": "2025-12-03T10:30:00.000000",
  "summary": {
    "total_skipped": 15,
    "total_errors": 2
  },
  "skipped": {
    "temp_file": ["~$doc1.docx", "~$doc2.docx"],
    "already_extracted": ["file1.md", "file2.md"],
    "unsupported_extension": ["image.png (.png)"]
  },
  "errors": {
    "corrupted_file": [
      {"context": "broken.pdf", "error": "PDF is corrupted", "type": "ValueError"}
    ]
  }
}
```
