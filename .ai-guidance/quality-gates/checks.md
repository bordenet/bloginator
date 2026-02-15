# Quality Checks

> **When to load:** When running quality checks or preparing commits

## Quick Check (Before Commits)

```bash
./scripts/run-fast-quality-gate.sh
```

Runs: Black, Ruff, MyPy, fast tests.

## Full Check (Before PRs)

```bash
black --line-length=100 src/ tests/           # Format
ruff check --fix src/ tests/                  # Lint
mypy src/bloginator/models src/bloginator/extraction src/bloginator/search \
     src/bloginator/safety src/bloginator/export src/bloginator/services \
     src/bloginator/indexing/indexer.py src/bloginator/generation \
     src/bloginator/utils/parallel.py         # Type check
pydocstyle src/bloginator/                    # Docstrings
bandit -r src/bloginator/ --skip B101,B601    # Security
pytest tests/ --cov=src/bloginator --cov-fail-under=85 -v  # Tests
```

## CI Mandatory Checks

```bash
ruff check src/bloginator tests && black --check src/bloginator tests
isort --check-only src/bloginator tests && mypy src/bloginator/models ...
pydocstyle src/bloginator && pytest --cov=src/bloginator --cov-fail-under=85
```

