# Bloginator: Repository Holes & Gaps

**Last Scanned**: 2025-12-11
**Status**: 80.4% test coverage (899 passing, 12 skipped, 4 xfailed)
**Python Files**: 158 source files, 90 test files

---

## 🔴 Critical Gaps (Coverage <50%)

### 1. Document Extraction (52% coverage)
**File**: `src/bloginator/extraction/_doc_extractors.py` (52.38%)

- **Missing tests**: Word (.docx), RTF, and legacy formats
- **Impact**: Users may encounter untested extraction failures
- **Action**: Add tests for DOC, DOCX, RTF edge cases (empty, corrupted, large files)

### 2. Email & Markup Extraction (5-9% coverage)
**Files**:
- `extraction/_email_extractors.py` (5.26%)
- `extraction/_markup_extractors.py` (9.41%)

- **Status**: Feature incomplete; minimal test coverage
- **Impact**: Email/HTML extraction largely untested
- **Action**: Decide: complete feature or remove/deprecate

### 3. Office Format Extraction (4.5% coverage)
**File**: `extraction/_office_extractors.py` (4.50%)

- **Status**: Requires `python-pptx` optional dependency
- **Impact**: PowerPoint extraction is essentially untested
- **Action**: Add tests or move to optional extras with clear warnings

### 4. Batch Response Collection (55.74% coverage)
**File**: `generation/_batch_response_collector.py` (55.74%)

- **Missing edge cases**: File locking, concurrent writes, timeout scenarios
- **Impact**: Batch mode may fail silently under load
- **Action**: Add tests for race conditions, stale files, incomplete responses

---

## 🟡 High-Risk Gaps (Coverage 60-75%)

### 5. Metadata Extraction (60.27%)
**File**: `extraction/metadata.py`

- **Lines 77-78, 82-99 untested**
- **Impact**: Document metadata may be incorrect or missing
- **Action**: Test edge cases: missing dates, unusual formats, encoding issues

### 6. LLM Factory (67.86%)
**File**: `generation/llm_factory.py`

- **Missing**: Provider fallback logic, invalid config handling
- **Impact**: Configuration errors may not surface clearly
- **Action**: Add error path tests, validation checks

### 7. LLM Ollama Client (58.73%)
**File**: `generation/llm_ollama.py`

- **Missing**: Connection failures, timeout handling, invalid responses
- **Impact**: Local LLM errors may cause cryptic failures
- **Action**: Add tests for network errors, malformed responses

### 8. CLI LLM Client (65.71%)
**File**: `generation/llm_client.py`

- **Lines 74, 80-85 untested**
- **Impact**: Custom LLM providers may not initialize correctly
- **Action**: Test custom endpoint validation and error messages

### 9. Outline Generator (75.17%)
**File**: `generation/outline_generator.py`

- **Missing**: Error handling for empty corpus, LLM failures, timeout scenarios
- **Impact**: May fail ungracefully when corpus is insufficient
- **Action**: Add robustness tests for edge cases

### 10. Checksum Utility (40%)
**File**: `utils/checksum.py`

- **Lines 46-50 untested** (likely fallback/error path)
- **Impact**: Shadow copy system may not detect changes correctly
- **Action**: Test checksum computation edge cases

---

## 🟠 Medium Gaps (Coverage 75-85%)

### 11. Document Models & History (78-82%)
**Files**:
- `models/history.py` (78.43%)
- `models/_corpus_source.py` (75.36%)
- `models/_date_range.py` (42.86%)

- **Issue**: History serialization edge cases, date range boundaries
- **Action**: Test date parsing, history merging, conflict resolution

### 12. Template Storage (81.82%)
**File**: `services/_template_storage.py`

- **Missing**: File permission errors, concurrent writes
- **Action**: Test I/O failure scenarios

### 13. Timeout Config (81.36%)
**File**: `timeout_config.py`

- **Missing**: Invalid config validation, edge cases
- **Action**: Test malformed timeout values, negative numbers

### 14. Monitoring Logger (77.36%)
**File**: `monitoring/logger.py`

- **Missing**: File rotation edge cases, log level validation
- **Action**: Test logger edge cases

### 15. CLI Search (untested depth)
**File**: `cli/search.py` (305 lines)

- **Status**: Large module with uncertain coverage
- **Impact**: Search CLI may have hidden bugs
- **Action**: Verify coverage, add edge case tests

---

## 📋 Structural Issues

### 16. Large Modules (330+ lines)
**Problem**: Code maintainability
```
346 lines: utils/cloud_files.py (cloud file handling)
345 lines: cli/extract_single.py (extraction logic)
341 lines: generation/_batch_response_collector.py (batch collection)
339 lines: generation/draft_generator.py (draft generation)
334 lines: generation/outline_generator.py (outline generation)
```

**Action**: CLAUDE.md specifies max 350 lines. Consider splitting large generators into helpers.

### 17. Missing Tests for Optional Dependencies
- **Streamlit UI** (2 tests skipped)
- **PDF export** (requires reportlab, 2 tests skipped)
- **FastAPI web routes** (5 tests skipped)
- **Extended extractors** (requires python-pptx, 1 test skipped)
- **OpenAI client** (1 test skipped, requires API key)

**Impact**: Features with optional deps may have untested code paths

**Action**: Add CI detection for installed extras, skip tests conditionally or add mock tests

### 18. Integration Test Expectations Not Met
**File**: `tests/integration/test_sample_corpus_pipeline.py`

- **XFAIL**: `test_search_hiring_manager_content` expects hiring content in corpus
- **Issue**: Corpus may not have sufficient topic coverage
- **Impact**: Real-world usage may find topics unsupported by corpus

**Action**: Document corpus requirements, add validation tools

---

## 🧪 Testing Gaps

### 19. No Concurrent/Parallel Testing
- **Issue**: No tests for parallel CLI execution, race conditions
- **Impact**: Batch mode may fail under concurrent load
- **Action**: Add tests using threading/multiprocessing

### 20. No Performance Regression Tests
- **Issue**: No benchmarks tracked over time
- **Impact**: Optimizations can't be verified
- **Action**: Add baseline performance tests

### 21. Limited Edge Case Coverage
- **Empty files**: Not tested
- **Very large files**: Not tested
- **Unicode edge cases**: Minimal testing
- **Corrupted files**: Not tested
- **File encoding**: Limited testing

**Action**: Add parametrized tests for edge cases

### 22. Incomplete Type Annotations
**Exceptions**:
```
bloginator.ui.*           (disabled, 8 modules)
bloginator.cli.serve      (disabled)
bloginator.cli.error_reporting (disabled)
bloginator.cli.search     (disabled)
bloginator.generation.llm_mock (disabled)
bloginator.generation.llm_custom (disabled)
bloginator.generation.llm_ollama (disabled)
bloginator.utils.parallel (disabled)
bloginator.cli.extract_utils (disabled)
```

**Impact**: 10+ modules lack strict type checking
**Action**: Gradually enable strict typing module-by-module

---

## 📚 Documentation Gaps

### 23. ~~AGENTS.md Missing~~ ✅ RESOLVED
- **Issue**: No `AGENTS.md` file documented in CLAUDE.md standards
- **Expected**: Standardized commands for this project
- **Resolution**: Created root `Agents.md` with comprehensive AI guidance and command reference

### 24. No Runbook for Production Issues
- **Issue**: PRODUCTION_READINESS_CHECKLIST exists but no runbook
- **Missing**: Common errors, troubleshooting guide, recovery steps
- **Action**: Create `docs/RUNBOOK.md`

### 25. Sparse Coverage of Experimental Features
- **Optimization module**: Experimental, minimal coverage
- **PDF export**: Optional, untested
- **Cloud file handling**: Optional, untested
- **Interactive LLM**: Minimal coverage

**Action**: Document which features are experimental vs. stable

### 26. No Deployment Topology Guide
- **Issue**: DEPLOYMENT.md exists but limited guidance
- **Missing**: Docker setup, multiple-instance scenarios, clustering
- **Action**: Expand deployment documentation

---

## ⚙️ Configuration & Defaults

### 27. Hardcoded Values in Code
- **Issue**: Some config values may be hardcoded or have weak defaults
- **Example**: Timeout values, retry limits, model names
- **Action**: Audit config loading, document defaults

### 28. Environment Variable Documentation
- **Issue**: `.env.example` exists but may be incomplete
- **Missing**: All configuration options documented
- **Action**: Generate complete `.env` docs from code

---

## 🔍 Known Issues (From Code)

### 29. TODO Comments (2 found)
```python
# src/bloginator/ui/_pages/search.py
# TODO: Parse output into structured format for better display

# src/bloginator/_corpus_settings.py
# default_factory=lambda: [".*", "_*", "draft_*", "TODO.md", "README.md"],
```

- **Impact**: UI search output may not be well-formatted
- **Action**: Complete TODO or document as deferred

### 30. XFAIL Tests (4 found)
```
test_search_hiring_manager_content      - Corpus content gap
test_create_ollama_client               - Environment override
test_create_ollama_with_custom_url      - Environment override
test_create_default_provider            - Environment override
```

- **Impact**: These tests only pass under specific conditions
- **Action**: Refactor or document workarounds

---

## 📊 Summary Table

| Category | Count | Severity | Action |
|----------|-------|----------|--------|
| **Coverage <50%** | 4 modules | 🔴 Critical | Add tests |
| **Coverage 50-75%** | 8 modules | 🟡 High | Improve tests |
| **Coverage 75-90%** | 12 modules | 🟠 Medium | Edge cases |
| **Large modules** | 10 files | 🟡 High | Refactor or document |
| **Skipped tests** | 10 tests | 🟠 Medium | Mock or require deps |
| **XFAIL tests** | 4 tests | 🟠 Medium | Fix or document |
| **TODO comments** | 2 | 🟠 Medium | Complete or defer |
| **Type check exclusions** | 10 modules | 🟡 High | Gradual enablement |

---

## 🎯 Recommended Priority

### Phase 1: Critical (This Sprint)
1. Add tests for document extraction edge cases (52%)
2. Fix batch response collector (55.74%)
3. Address LLM client failures (58-67%)

### Phase 2: High (Next Sprint)
1. Enable strict typing for more modules
2. Reduce large module sizes
3. Add parallel/concurrent tests

### Phase 3: Medium (Q1)
1. Complete optional dependency test coverage
2. Add performance benchmarks
3. Improve edge case coverage

### Phase 4: Documentation
1. ✅ Create Agents.md (consolidated in root)
2. ✅ Create RUNBOOK.md
3. Complete configuration documentation

---

## ✅ What's Working Well

- ✅ Core outline/draft generation (90%+ coverage)
- ✅ Safety/quality assurance (97%+ coverage)
- ✅ Search indexing (95%+ coverage)
- ✅ Version management (100% coverage)
- ✅ CLI commands (functional, E2E tested)
- ✅ Error handling (strong in main paths)
- ✅ Type safety (strict for 90% of code)

---

## 🚀 Next Steps

1. **Immediate**: Fix coverage gaps in extraction (52%)
2. **This week**: Add batch mode race condition tests
3. **This month**: Improve optional dependency coverage
4. **Q1 2026**: Phase in strict typing, reduce module sizes
