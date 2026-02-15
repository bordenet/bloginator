# Quality Gates Index

> **When to load:** Overview of quality gate modules

## Sub-Modules

| Module | Description |
|--------|-------------|
| [checks.md](checks.md) | Quality check commands |
| [ci-requirements.md](ci-requirements.md) | CI pipeline & coverage |
| [style-guide.md](style-guide.md) | Python style requirements |

## Quick Reference

| Task | Command |
|------|---------|
| **Quick check** | `./scripts/run-fast-quality-gate.sh` |
| **Format** | `black --line-length=100 src/ tests/` |
| **Lint** | `ruff check --fix src/ tests/` |
| **Type check** | `mypy src/bloginator/models ...` |
| **Tests** | `pytest tests/ --cov=src/bloginator --cov-fail-under=85` |

