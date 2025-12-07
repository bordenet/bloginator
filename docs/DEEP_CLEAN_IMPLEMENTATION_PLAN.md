# Deep Clean Implementation Plan

## Overview

Comprehensive refactoring of the bloginator codebase to improve maintainability, clarity, and correctness. This document captures the plan and marks completed work. Execution will be done in three sequential phases with git commits and pushes after each.

**Status**: PLANNING PHASE
**Last Updated**: 2025-12-07

---

## Phase 1: Python Code Deep Clean

### Objectives
- Identify and fix bugs
- Correct or improve comments
- Clarify variable names
- Clarify function names
- Audit design patterns
- Ensure consistency with CLAUDE.md standards

### Scope
- 145 source files in `src/bloginator/`
- All modules organized by category:
  - `cli/` - Click CLI commands
  - `export/` - Document exporters
  - `extraction/` - Document chunking
  - `generation/` - LLM clients
  - `indexing/` - ChromaDB indexing
  - `models/` - Pydantic models
  - `monitoring/` - Logging/metrics
  - `quality/` - Slop detection
  - `safety/` - Blocklisting
  - `search/` - Semantic search
  - `services/` - History/templates
  - `utils/` - Utility modules

### Approach
For each module category:
1. Read complete source files
2. Check against CLAUDE.md standards:
   - Type annotations complete?
   - Docstrings present and correct?
   - Function length ≤100 lines (target ≤50)?
   - Parameters ≤5 per function?
   - Line length ≤100 chars?
   - Import order correct?
3. Identify bugs, unclear names, poor patterns
4. Document findings and fixes
5. Apply fixes
6. Verify quality gates pass

### Deprecation Strategy
- Mark dead code with `@deprecated` decorator with removal timeline
- Create separate `DEPRECATIONS.md` document listing all marked items
- Keep functional for now; can remove later

### Status
- [ ] models/
- [ ] extraction/
- [ ] safety/
- [ ] search/
- [ ] indexing/
- [ ] generation/
- [ ] quality/
- [ ] export/
- [ ] monitoring/
- [ ] services/
- [ ] utils/
- [ ] cli/

**Completion Target**: TBD
**Output**: Updated source files + DEPRECATIONS.md + commit to main

---

## Phase 2: Test Suite Deep Clean

### Objectives
- Audit test coverage (quality over quantity)
- Verify all code paths tested (especially E2E and edge cases)
- Improve test clarity and maintainability
- Fix any flaky or poorly-written tests
- Ensure tests reflect actual requirements

### Scope
- 87 test files in `tests/`
- Structure:
  - `tests/unit/` - Unit tests
  - `tests/integration/` - Integration tests
  - `tests/e2e/` - End-to-end tests
  - `tests/benchmarks/` - Performance tests
  - `tests/fixtures/` - Test fixtures and data

### Approach
1. Run full test suite and document baseline
2. For each test file:
   - Verify tests match the CLAUDE.md testing pattern
   - Check for flaky tests (timing dependencies, randomness)
   - Verify assertions are meaningful (not testing mocks)
   - Check for test-only methods in production code
   - Ensure edge cases are covered
   - Verify E2E paths are adequately tested
3. Identify missing coverage areas
4. Fix or improve tests
5. Add new tests for uncovered edge cases
6. Run full suite and verify coverage ≥70%

### Coverage Focus Areas
- Code path coverage (not just line coverage)
- Edge cases and error conditions
- Integration points between modules
- E2E workflows

### Status
- [ ] Unit tests review and cleanup
- [ ] Integration tests review and cleanup
- [ ] E2E tests review and cleanup
- [ ] Benchmark tests review
- [ ] Test fixtures audit
- [ ] Coverage verification

**Completion Target**: TBD
**Output**: Updated test files + commit to main

---

## Phase 3: Markdown Documentation Deep Clean

### Objectives
- Remove obsolete/completed information
- Correct invalid/outdated information
- Eliminate duplicate content
- Improve clarity and organization
- Verify all links and references are current

### Scope
- 35 markdown files in `docs/`
- 4 markdown files at root (README.md, CONTRIBUTING.md, SECURITY.md, CLAUDE.md)

### Approach
For each markdown file:
1. Read entire file
2. Identify:
   - Obsolete sections (completed tasks, old status)
   - Outdated information (wrong APIs, old examples)
   - Duplicated content across files
   - Broken links or references
   - Unclear or ambiguous statements
3. Document findings
4. Apply fixes
5. Consolidate duplicate information
6. Verify consistency across related docs

### Documentation Categories
**Architectural Docs**
- [ ] System architecture and design

**API Documentation**
- [ ] Model schemas
- [ ] Function signatures
- [ ] CLI command documentation

**Setup & Installation**
- [ ] Development environment setup
- [ ] Installation instructions
- [ ] Configuration guides

**Implementation Guides**
- [ ] Development workflow
- [ ] Code style and patterns
- [ ] Testing strategies

**Process Documentation**
- [ ] Deprecation policy
- [ ] Contribution process
- [ ] Release process

**Quality & Standards**
- [ ] Style guide
- [ ] Quality gates
- [ ] Coverage requirements

### Status
- [ ] Architectural documentation audit
- [ ] API documentation audit
- [ ] Setup documentation audit
- [ ] Implementation guides audit
- [ ] Process documentation audit
- [ ] Quality standards audit
- [ ] Consolidation and cleanup

**Completion Target**: TBD
**Output**: Updated markdown files + commit to main

---

## Known Issues to Address

### Code Quality
- Review all `# type: ignore` comments (should be fixed, not ignored)
- Verify all functions have complete type annotations
- Check for incomplete docstrings
- Audit error messages for clarity

### Testing
- Check for flaky tests (e.g., timing-dependent tests)
- Verify all major code paths have E2E coverage
- Review edge case handling

### Documentation
- Verify setup instructions are current
- Check API examples work as documented
- Consolidate overlapping documentation
- Remove completed task tracking

---

## Success Criteria

### Phase 1 (Code)
- ✅ All source files reviewed
- ✅ Quality gates pass: `ruff check`, `black --check`, `isort --check-only`, `mypy`, `pydocstyle`
- ✅ All tests still pass
- ✅ DEPRECATIONS.md created and documented
- ✅ Commit pushed to main

### Phase 2 (Tests)
- ✅ All test files reviewed
- ✅ Test coverage ≥70%
- ✅ All tests pass consistently (no flakiness)
- ✅ E2E coverage verified for critical paths
- ✅ Commit pushed to main

### Phase 3 (Docs)
- ✅ All markdown files reviewed
- ✅ No obsolete or duplicate content
- ✅ All links and references valid
- ✅ Consistent terminology and style
- ✅ Commit pushed to main

---

## Notes

- This is a "mark and sweep" approach for deprecations
- Focus is on quality and maintainability, not performance optimization
- Each phase should result in a clean, working state
- Questions will be documented and discussed during execution
- Test suite will be run after each significant change to catch regressions
