# Quality Gates - Python

> **When to load:** Before commits, PRs, or running quality checks

---

## Mandatory Quality Gates

All code MUST pass these checks before commit or PR:

```bash
# Format check (automatic in CI)
ruff check src/bloginator tests
black --check src/bloginator tests
isort --check-only src/bloginator tests

# Type checking
mypy src/bloginator/models src/bloginator/extraction src/bloginator/search \
     src/bloginator/safety src/bloginator/export src/bloginator/services \
     src/bloginator/indexing/indexer.py src/bloginator/generation \
     src/bloginator/utils/parallel.py

# Docstring checking
pydocstyle src/bloginator

# Tests with coverage
pytest --cov=src/bloginator --cov-fail-under=85
```

---

## Quick Quality Check (Before Commits)

```bash
./scripts/run-fast-quality-gate.sh
```

This runs:
- Black formatting check
- Ruff linting (includes import sorting via I rules)
- MyPy type checking (key modules)
- Fast unit tests

---

## Full Quality Check (Before PRs)

```bash
# Format code
black --line-length=100 src/ tests/

# Fix linting issues
ruff check --fix src/ tests/

# Type checking (all modules with strict enabled)
mypy \
    src/bloginator/models \
    src/bloginator/extraction \
    src/bloginator/search \
    src/bloginator/safety \
    src/bloginator/export \
    src/bloginator/services \
    src/bloginator/indexing/indexer.py \
    src/bloginator/generation \
    src/bloginator/utils/parallel.py

# Docstring checking
pydocstyle src/bloginator/

# Security scanning
bandit -r src/bloginator/ --skip B101,B601

# Full test suite with coverage
pytest tests/ --cov=src/bloginator --cov-fail-under=85 -v
```

---

## CI Workflow Requirements

1. **Lint and type check** - Must pass Ruff, pydocstyle, and mypy
2. **Tests** - Must pass on Python 3.10, 3.11, and 3.12 with ≥85% coverage
3. **Security scanning** - Bandit, pip-audit, and Safety checks run (non-blocking)
4. **Codecov** - Coverage reports uploaded to Codecov

---

## Coverage Requirements

- **Minimum overall**: 85% (enforced in CI)
- **Target for new code**: 90%+
- **Critical paths**: 95%+ recommended

---

## Development Workflow

### Before Every Commit

1. Run quality gate script: `./scripts/run-fast-quality-gate.sh`
2. Verify all tests pass: `pytest tests/unit --no-cov`
3. Fix any linting/type errors before committing

### Before Every Push

1. Run full test suite: `pytest --cov=src/bloginator`
2. Verify coverage meets threshold (≥85%)
3. Ensure CI will pass by running all quality checks locally

---

## Python Style Guide

All Python code MUST comply with `docs/PYTHON_STYLE_GUIDE.md`. Key requirements:

- **Line length**: 100 characters maximum (enforced by Black/Ruff)
- **Type annotations**: Required on all function parameters, return values, and class attributes
- **Docstrings**: Google style, required for all public modules, classes, and functions
- **Function length**: Target ≤50 lines, maximum 100 lines
- **Parameters**: ≤5 per function, use dataclass/dict for more
- **Import order**: stdlib → third-party → local (enforced by isort)
- **Max file length**: 350 lines maximum. Strive for ~250 lines

---

## Prohibited Patterns

1. **No untyped functions** - Every function must have type annotations
2. **No missing docstrings** - Public APIs must be documented
3. **No ignoring mypy errors** - Fix the issue, don't add `# type: ignore`
4. **No tests without assertions** - Every test must verify behavior
5. **No coverage exclusions without justification** - Document why `# pragma: no cover`
