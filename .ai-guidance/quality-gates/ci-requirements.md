# CI Requirements

> **When to load:** When understanding CI pipeline or coverage requirements

## CI Workflow Requirements

1. **Lint and type check** - Must pass Ruff, pydocstyle, and mypy
2. **Tests** - Must pass on Python 3.10, 3.11, and 3.12 with ≥85% coverage
3. **Security scanning** - Bandit, pip-audit, Safety checks (non-blocking)
4. **Codecov** - Coverage reports uploaded to Codecov

## Coverage Requirements

| Category | Minimum |
|----------|---------|
| **Overall** | 85% (enforced in CI) |
| **New code** | 90%+ target |
| **Critical paths** | 95%+ recommended |

## Development Workflow

### Before Every Commit

1. Run: `./scripts/run-fast-quality-gate.sh`
2. Verify tests pass: `pytest tests/unit --no-cov`
3. Fix any linting/type errors

### Before Every Push

1. Run full suite: `pytest --cov=src/bloginator`
2. Verify coverage ≥85%
3. Run all quality checks locally

