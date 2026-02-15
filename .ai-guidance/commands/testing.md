# Testing Commands

> **When to load:** When running tests or checking coverage

## Run All Tests

```bash
# Full test suite with coverage
pytest tests/ -v --cov=src/bloginator --cov-report=term-missing

# Specific test file
pytest tests/unit/models/test_document.py -v

# Specific test class
pytest tests/unit/models/test_document.py::TestDocument -v

# Fast tests only (skip slow/integration)
pytest tests/ -m "not slow" -q

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

## Coverage Analysis

```bash
# Generate HTML coverage report
pytest tests/ --cov=src/bloginator --cov-report=html

# View report (opens browser)
open htmlcov/index.html
```

## Quick Reference

| Task | Command |
|------|---------|
| **All tests** | `pytest tests/ -v --cov=src/bloginator` |
| **Fast tests** | `pytest tests/ -m "not slow" -q` |
| **Coverage HTML** | `pytest tests/ --cov-report=html` |

