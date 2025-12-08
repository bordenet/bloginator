# Action Plan

Current priorities and active work items.

## Test Coverage Enhancement

**Priority**: HIGH
**Current**: ~67% coverage (CI enforces 70% minimum)
**Target**: 70%+

### Missing Coverage
- CLI commands: `draft.py`, `extract_config.py`, `outline.py`, `search.py`
- Edge cases in extraction and indexing
- Web API routes (if FastAPI extras installed)

### Strategy
- Add realistic end-to-end tests for each CLI command
- Focus on error paths, not just happy paths
- Use fixtures to reduce boilerplate

## Content Quality Improvements

**Priority**: MEDIUM

### Current State
- Generated content scores 4.39/5.0 on average
- Specificity is the limiting factor (3.87-4.94 range)
- Voice similarity scoring is functional but improvable

### Improvements Needed
- More concrete examples in generated content
- Quantifiable metrics and data points
- Better corpus-to-output fidelity

## Documentation Maintenance

**Priority**: MEDIUM

- Keep examples synchronized with actual CLI behavior
- Update coverage badge when metrics change materially (±3-5%)
- Remove stale planning documents periodically

## See Also

- **Long-term roadmap**: [FUTURE_WORK.md](FUTURE_WORK.md)
- **Installation**: [INSTALLATION.md](INSTALLATION.md)
- **User guide**: [USER_GUIDE.md](USER_GUIDE.md)
