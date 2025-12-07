# Phase 2 Test Cleanup Execution Plan

**Date**: 2025-12-07
**Baseline**: 758 passed, 1 skipped, 11 xfailed
**Target**: Improve test quality while maintaining all passing tests

---

## Scope & Approach

Given the identified anti-patterns in ~100-120 tests, this document prioritizes fixes by:
1. **Impact** - Which fixes prevent the most test failures
2. **Effort** - Which fixes take least time
3. **Safety** - Which fixes have lowest risk of breaking tests

**Goal**: Maximum quality improvement with zero test breakage

---

## Priority 1: Critical Fixes (Highest Impact)

### 1.1 Fix xfail Tests (11 tests)

**File**: `tests/unit/generation/test_llm_factory.py`
**Current**: All tests marked `@pytest.mark.xfail` with reason "Environment config overrides mock config"
**Impact**: 11 disabled tests that should work

**Root Cause**: Environment variables (`OLLAMA_MODEL`, `OLLAMA_BASE_URL`) override test mocks

**Fix Strategy**:
1. Set up proper test isolation (no env variables during these tests)
2. Use `monkeypatch` fixture to mock environment
3. Remove `@pytest.mark.xfail` decorators
4. Verify tests pass

**Example**:
```python
def test_create_ollama_client(self, monkeypatch):
    # BAD: @pytest.mark.xfail
    # GOOD: Use monkeypatch
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    # Test proceeds normally without xfail
```

**Effort**: LOW (monkeypatch is straightforward)
**Risk**: LOW (isolated changes to one test file)
**Result**: 11 more passing tests

---

### 1.2 Replace Timing Tests with Condition-Based Waiting

**Files** (4 files, ~15 tests):
- `tests/unit/monitoring/test_metrics.py` - Lines 38, 90, 126
- `tests/unit/utils/test_parallel.py` - Line 38
- `tests/unit/services/test_corpus_directory_scanner.py` - Lines 155-160
- `tests/unit/cli/test_extract.py` - Lines 429, 443

**Current Problem**:
```python
time.sleep(0.01)  # ❌ Can fail under system load
assert elapsed > timedelta(milliseconds=10)
```

**Better Pattern**:
```python
# Use pytest's condition-based waiting or polling
condition.wait(timeout=1.0)  # Wait for condition, not time
assert actual_state == expected_state  # Verify state, not time
```

**Effort**: MEDIUM (requires pattern analysis for each test)
**Risk**: LOW-MEDIUM (timing tests don't have side effects)
**Result**: Eliminate ~15 flaky tests

---

## Priority 2: Important Fixes (Medium Impact)

### 2.1 Add Missing Assertions to Incomplete Tests

**Files** (3 files, ~20 tests):
- `tests/unit/ui/test_corpus_extraction_progress.py` - Lines 26-92
- `tests/unit/ui/test_corpus_skip_parsing.py` - Lines 125-148
- `tests/unit/cli/test_extract.py` - Lines 57-143 (partial)

**Current**: Tests set up scenarios but don't verify outcomes

**Fix**: Add specific assertions for:
- Return values
- Exit codes
- Output content
- File creation
- State changes

**Example**:
```python
# BEFORE
def test_extract_requires_output(self):
    result = runner.invoke(extract_cli, ["input.txt"])
    # Missing assertions

# AFTER
def test_extract_requires_output(self):
    result = runner.invoke(extract_cli, ["input.txt"])
    assert result.exit_code != 0  # Should fail
    assert "output" in result.output.lower()  # Error message
```

**Effort**: MEDIUM (need to review each test's intent)
**Risk**: LOW (only adding assertions, not changing logic)
**Result**: ~20 tests with complete coverage

---

## Priority 3: Quality Improvements (Lower Impact)

### 3.1 Review Mock Usage in Generation Tests

**Files** (4 files, ~70 tests):
- `tests/unit/generation/test_llm_client.py`
- `tests/unit/generation/test_draft_generator.py`
- `tests/unit/generation/test_outline_generator.py`
- `tests/unit/generation/test_refinement_engine.py`

**Current Problem**: Tests verify mocks were called instead of testing behavior

**Fix Strategy** (3 approaches):
1. **For isolated unit tests**: Mock external dependencies (HTTP, file I/O) but verify actual code logic
2. **For integration tests**: Create real dependency instances and verify end-to-end behavior
3. **For factories**: Test that correct types are returned, not mock setup

**Pattern**:
```python
# BEFORE - Tests mock
def test_generate(self):
    mock_post.return_value = mock_response
    client.generate(...)
    mock_post.assert_called_once()  # ❌ Tests mock

# AFTER - Tests behavior
def test_generate(self):
    result = client.generate(...)
    assert result.content == "expected"  # ✅ Tests code
```

**Effort**: HIGH (significant refactoring)
**Risk**: MEDIUM (changing many tests, but low-level mocks should still work)
**Result**: Tests become more reliable

---

## Execution Order

**Week 1 (or this session):**
1. [ ] Fix xfail tests in `test_llm_factory.py` (1-2 hours)
2. [ ] Replace timing tests with condition-based waiting (2-3 hours)
3. [ ] Add missing assertions to incomplete tests (2-3 hours)

**Total**: ~6-8 hours of work, should be done in this session

**Week 2+:**
4. [ ] Review and improve mock usage in generation tests (ongoing)

---

## Success Criteria

### For Phase 2A (This Session)
- [ ] All xfail tests converted to regular tests and passing
- [ ] No timing-dependent tests (all use polling/conditions)
- [ ] All test functions have explicit assertions
- [ ] Test suite still passes: `pytest --cov=src/bloginator`
- [ ] Coverage ≥70%

### For Phase 2B (Full Completion)
- [ ] Mock anti-patterns eliminated
- [ ] Tests verify behavior, not mock calls
- [ ] Test suite is flaky-test free
- [ ] CI pipeline is reliable

---

## Testing Strategy

After each fix, verify:
1. Tests still pass: `pytest tests/unit -x`
2. Coverage maintained: `pytest --cov=src/bloginator`
3. No new warnings or errors
4. Run tests multiple times to detect timing issues

---

## Files to Update

### High Priority (This Session)
1. `tests/unit/generation/test_llm_factory.py` - Remove xfail decorators
2. `tests/unit/monitoring/test_metrics.py` - Replace sleep() calls
3. `tests/unit/utils/test_parallel.py` - Replace sleep() calls
4. `tests/unit/services/test_corpus_directory_scanner.py` - Replace timing assertions
5. `tests/unit/cli/test_extract.py` - Add missing assertions + remove sleep()
6. `tests/unit/ui/test_corpus_extraction_progress.py` - Add assertions
7. `tests/unit/ui/test_corpus_skip_parsing.py` - Add assertions

### Medium Priority (Next Session)
8. `tests/unit/generation/test_llm_client.py` - Improve mock usage
9. `tests/unit/generation/test_draft_generator.py` - Improve mock usage
10. `tests/unit/generation/test_outline_generator.py` - Improve mock usage
11. `tests/unit/generation/test_refinement_engine.py` - Improve mock usage

---

## Notes

- This plan focuses on test quality improvement, not new features
- All changes should maintain or improve test reliability
- No changes to production code (Phase 1 is done)
- Each fix will be committed separately with clear messages
- Tests serve as documentation of expected behavior
