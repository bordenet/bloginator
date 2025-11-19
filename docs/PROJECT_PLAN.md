# Bloginator - Project Plan

**Purpose:** Track implementation roadmap and feature completion for Bloginator.

---

## Current Status

**Core Features (Complete):**
- Streamlit UI (7 pages)
- Classification/Audience in outline & draft generation
- Multi-source corpus configuration
- Blocklist management (CLI + UI)
- Multi-format export (Markdown, PDF, DOCX, HTML, TXT)
- Generation history tracking
- Custom prompt templates (Jinja2-based)
- Parallel extraction
- Incremental indexing with checksums
- E2E validation with mock LLM

**Quality Metrics:**
- Test suite: 355 passing, 0 failing, 6 skipped (optional dependencies)
- Core business logic coverage: 85-100%
- Code quality: Zero linting errors (black, ruff, isort, mypy)
- All files comply with 400-line maximum

**Pending Work:**
- Increase UI/CLI test coverage to >80%
- Advanced search features (date range, source filtering)
- Batch operations
- API documentation generation

---

## Implementation Phases

### Phase 1: Foundation & Quality (Complete)

**Code Quality:**
- All files comply with 400-line maximum
- Zero linting errors (black, ruff, isort)
- Test suite: 355 passing, 0 failing

**Test Infrastructure:**
- Comprehensive pytest fixtures
- Sample engineering leadership corpus (7 documents)
- Mock LLM provider for testing
- Factory functions for common objects

### Phase 2: Core Feature Completion (Complete)

**Features Implemented:**
- Classification/Audience in draft generation
- Blocklist management system (CLI + UI)
- Multi-format export (PDF, DOCX, HTML, TXT)
- Generation history tracking (CLI + UI)
- Custom prompt templates (Jinja2)

**Blocklist Categories:**
- PII, credentials, project codenames, custom

**Export Formats:**
- Markdown, PDF (ReportLab), DOCX (python-docx), HTML (embedded CSS), Plain Text

**History Storage:**
- JSON files in `~/.bloginator/history/`
- Queryable by type, classification, audience
- Re-export capability

### Phase 3: Advanced Features (Complete)

**Performance Optimization:**
- Parallel document extraction (ThreadPoolExecutor)
- Incremental indexing with checksums
- Quality-filtered search (CLI + UI)

**Analytics Enhancements:**
- Source quality distribution
- Document format breakdown
- Tags cloud visualization
- Timeline view by creation date

### Phase 4: Advanced Workflows (Planned)

**Pending Features:**
- Batch operations (CSV input, bulk export)
- Advanced search (date range, source filtering, saved queries)
- Additional template library (marketing, academic, blog-post)

### Phase 5: Testing & Coverage (Ongoing)

**Current Coverage:**
- Unit tests: 355 passing (models, generation, search, indexing, extraction, safety)
- Integration tests: Extract/index/search pipeline
- E2E tests: Full workflow with mock LLM
- Performance benchmarks: Extraction, indexing, search latency

**Coverage Targets:**
- Core business logic: 85-100% (achieved)
- UI/CLI layers: 60-80% (in progress)

---

## Testing Strategy

**Test Organization:**
```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Test data
│   └── sample_corpus/       # 7 engineering leadership documents
├── unit/                    # Unit tests (355 tests)
│   ├── models/
│   ├── extraction/
│   ├── indexing/
│   ├── search/
│   ├── generation/
│   ├── export/
│   ├── blocklist/
│   └── safety/
├── integration/             # Integration tests
├── functional/              # CLI functional tests
├── e2e/                     # End-to-end tests
└── performance/             # Benchmarks
```

**LLM Mocking:**
- Mock LLM provider for deterministic testing
- Realistic canned responses for outlines and drafts
- No external dependencies (Ollama/OpenAI) required

**Fixtures:**
- Sample corpus (7 engineering leadership blog posts)
- Test ChromaDB instances
- Factory functions for models
- Mock LLM clients

---

## Quality Gates

**Pre-Commit:**
- Black formatting
- Ruff linting
- isort import sorting
- Trailing whitespace removal
- YAML validation

**Pre-Push:**
- All tests pass
- Coverage >80% (core logic)
- No critical security issues (bandit)
- All files <400 lines

**Pre-Release:**
- All E2E tests pass
- Documentation up-to-date
- CHANGELOG updated
- Version bumped

---

## Success Metrics

**Functionality:**
- All CLI commands work as documented
- All Streamlit pages functional
- All export formats produce valid output
- Blocklist prevents sensitive content

**Quality:**
- 0 failing tests
- Core logic >85% coverage
- 0 critical security issues
- 0 linting errors

**Performance:**
- Extract 1000 docs in <5 minutes
- Index 1000 docs in <3 minutes
- Search query latency <200ms (p99)
- Outline generation <30 seconds
- Draft generation <2 minutes

**Documentation:**
- User guide complete with examples
- All commands have help text
- Troubleshooting guide available

---

## Risk Mitigation

**Technical Risks:**
- ChromaDB compatibility: Version pinning, comprehensive integration tests
- LLM API rate limits: Mock LLM for testing, local Ollama for development
- Export format compatibility: Test on multiple platforms, fallback to plain text
- Large corpus performance: Benchmarks, optimization, documented limits

**Schedule Risks:**
- Scope creep: Strict prioritization, MVP mindset
- Testing overhead: Parallel test writing, automated fixtures

**Quality Risks:**
- Insufficient coverage: 80% minimum gate, test-first development
- Poor documentation: Write docs alongside features, peer review

---

## Implementation Order

**CRITICAL (Complete):**
1. Fix failing tests
2. Test infrastructure
3. Classification/Audience in drafts

**HIGH (Complete):**
4. Blocklist management
5. Multi-format export
6. Generation history

**MEDIUM (Complete):**
7. Quality-filtered search
8. Analytics enhancements
9. Performance optimization

**LOW (Planned):**
10. Batch operations
11. Advanced search features
12. Additional templates

---

## Notes

- Commit after each feature or every 2-3 hours
- Run linters after every file edit
- Write tests alongside code (TDD where possible)
- Update docs in same commit as feature
- Profile before optimizing, measure after
- Assume user perspective, test end-to-end

This is a living document. Update as implementation progresses.
