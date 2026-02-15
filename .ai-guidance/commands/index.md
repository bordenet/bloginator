# Commands Reference Index

> **When to load:** Overview of all command documentation

## Sub-Modules

| Module | Description | Load when... |
|--------|-------------|--------------|
| [cli.md](cli.md) | CLI commands | Running bloginator commands |
| [testing.md](testing.md) | Test commands | Running tests or coverage |
| [setup.md](setup.md) | Environment setup | Setting up dev environment |
| [linting.md](linting.md) | Code formatting | Formatting or fixing lint |
| [debugging.md](debugging.md) | Debug tools | Troubleshooting issues |
| [git.md](git.md) | Git workflow | Committing or branching |

## Quick Reference Table

| Task | Command |
|------|---------|
| **Setup** | `python3.11 -m venv venv && source venv/bin/activate && pip install -e ".[dev]"` |
| **Quick check** | `./scripts/run-fast-quality-gate.sh` |
| **Full check** | `pytest tests/ --cov=src/bloginator && mypy src/bloginator/models ...` |
| **Format** | `black --line-length=100 src/ tests/` |
| **Lint** | `ruff check --fix src/ tests/` |
| **Tests** | `pytest tests/ -v --cov=src/bloginator` |
| **Run command** | `bloginator extract/index/search/outline/draft` |
| **Help** | `bloginator --help` |
| **Cleanup** | `rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/` |

