# Phase 3: Module Refactoring & Edge Case Coverage

**Status**: Planned
**Goal**: Reduce module sizes, improve testability, add edge case tests

## Large Module Analysis

CLAUDE.md specifies max 350 lines per module. Current violations:

### Critical (340+ lines, immediate refactoring)

1. **utils/cloud_files.py** (346 lines)
   - Cloud file resolution for macOS
   - Split: parsing logic → separate module
   - Current status: Untested (requires macOS specific handling)

2. **cli/extract_single.py** (345 lines)
   - Single file extraction CLI
   - Split: extraction logic → core, CLI parsing → CLI layer
   - Estimated effort: 4-6 hours

3. **generation/_batch_response_collector.py** (341 lines)
   - Batch response collection and validation ✅ (tested in Phase 1)
   - Split: Validation → separate, Collection → separate
   - Estimated effort: 3-4 hours

4. **generation/draft_generator.py** (339 lines)
   - Draft generation orchestration
   - Split: Prompt building → helper, Refinement → strategy
   - Estimated effort: 4-5 hours

5. **generation/outline_generator.py** (334 lines)
   - Outline generation orchestration
   - Split: Prompt building → helper, Coverage analysis → strategy
   - Estimated effort: 4-5 hours

6. **cli/_extract_config_helpers.py** (334 lines)
   - Extraction configuration parsing
   - Split: Validation → separate, Merging → strategy
   - Estimated effort: 3-4 hours

7. **generation/refinement_engine.py** (333 lines)
   - Iterative refinement orchestration
   - Split: Quality assessment → helper, Retry logic → strategy
   - Estimated effort: 4-6 hours

8. **services/corpus_directory_scanner.py** (331 lines)
   - Corpus file scanning and monitoring
   - Split: File discovery → helper, Watching → separate
   - Estimated effort: 3-4 hours

### At Limit (328-330 lines)

- search/searcher.py (328 lines) - Close, monitor but OK for now
- optimization/prompt_tuner.py (310 lines) - Experimental, lower priority
- extraction/extractors.py (310 lines) - Core functionality, consider splitting

## Refactoring Strategy

### Priority 1: Generator Modules (40 hours total estimated)

These are on the critical path and would benefit most from splitting:

1. `outline_generator.py` → `_outline_prompt.py` + `_outline_coverage.py`
2. `draft_generator.py` → `_draft_prompt.py` + `_draft_refinement.py`
3. `refinement_engine.py` → `_quality_assessment.py` + `_retry_strategy.py`

### Priority 2: CLI & Config (20 hours total estimated)

These can be split into validation and parsing layers:

1. `extract_single.py` → `_extract_parser.py` + extraction logic
2. `_extract_config_helpers.py` → `_config_validator.py` + merging logic
3. `cli/template.py` → Template CLI layer

### Priority 3: Services (12 hours total estimated)

Lower criticality but good for code health:

1. `corpus_directory_scanner.py` → `_file_discovery.py` + watching
2. `cloud_files.py` → Cloud file helpers (macOS specific)

## Testing Strategy

### New Edge Case Tests Needed

1. **Extraction Edge Cases** (Phase 1 - COMPLETED)
   - ✅ Empty files
   - ✅ Corrupted files
   - ✅ Large files
   - ✅ Unicode edge cases

2. **Generation Edge Cases** (Phase 3 - TODO)
   - Empty corpus search results
   - LLM API failures
   - Timeout scenarios
   - Partial/invalid responses
   - Retry exhaustion

3. **Refinement Edge Cases** (Phase 3 - TODO)
   - Quality threshold not met
   - Token limits exceeded
   - Conflicting feedback
   - Empty refinement suggestions

4. **Service Edge Cases** (Phase 3 - TODO)
   - File permission errors
   - Concurrent directory changes
   - Symlinks and circular references
   - Mount point disconnections (cloud)

### Performance Baseline Tests

Add benchmarks for:
- Outline generation speed (target: <90 seconds)
- Draft generation speed (target: <5 minutes)
- Search latency (target: <1 second)
- Index creation (target: <30 seconds for 100 docs)

## Refactoring Checklist

For each module:
- [ ] Create comprehensive test suite
- [ ] Run full test suite with coverage
- [ ] Identify extraction opportunities
- [ ] Create helper modules
- [ ] Move logic to helpers
- [ ] Update imports
- [ ] Verify tests still pass
- [ ] Verify no coverage regression
- [ ] Commit with clear message
- [ ] Document design decisions

## Success Criteria

- [ ] All modules ≤ 350 lines
- [ ] Edge case coverage >85% for each module
- [ ] No new type: ignore comments
- [ ] All tests pass
- [ ] Coverage maintained ≥80%
- [ ] Refactored code has clear interfaces

## Effort Estimate

- **Phase 3a**: Edge case tests (20-30 hours)
- **Phase 3b**: Module refactoring (60-80 hours)
- **Phase 3c**: Performance benchmarking (10-15 hours)

**Total**: 90-125 hours spread across Q1 2026

## Notes

- Don't rush refactoring - do 1-2 modules per session
- Refactoring should improve testability, not just reduce lines
- New modules should have clear, single responsibility
- Document interfaces between split modules
- Run full test suite after each refactoring
