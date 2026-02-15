# Command Reference

> **When to load:** When running CLI commands, debugging, or setting up environment

---

## Pre-Flight Checklist

Before ANY work:

```bash
# 1. Check current branch and status
git status
git log --oneline -3

# 2. Verify environment
python --version              # Should be 3.10+
which python3.11 || which python3.12
source venv/bin/activate
pip list | grep -E "black|ruff|mypy|pytest"

# 3. Verify repo health
ls -la .bloginator/           # Index directory exists
ls tests/ | head -5           # Tests present
```

---

## CLI Commands

**Show help for any command:**
```bash
bloginator --help
bloginator extract --help
bloginator index --help
bloginator search --help
bloginator outline --help
bloginator draft --help
```

**Run with verbose output:**
```bash
bloginator search --index .bloginator/chroma "test query" -v
```

**Dry run (no side effects):**
```bash
bloginator extract ~/writing --dry-run
```

---

## Testing Commands

**Run All Tests:**
```bash
# Full test suite with coverage report
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

**Coverage Analysis:**
```bash
# Generate coverage report
pytest tests/ --cov=src/bloginator --cov-report=html

# View coverage report (opens in browser)
open htmlcov/index.html
```

---

## Development Setup

```bash
# Clone and setup
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# Create virtualenv (choose Python 3.11 or 3.12)
python3.11 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
python -c "import bloginator; print(bloginator.__version__)"
./scripts/run-fast-quality-gate.sh
```

---

## Linting and Formatting

```bash
# Format all code (auto-fix)
black --line-length=100 src/ tests/

# Lint and fix
ruff check --fix src/ tests/

# Check only (no auto-fix)
black --check src/ tests/
ruff check src/ tests/
```

---

## Debugging

**Enable Verbose Logging:**
```bash
export BLOGINATOR_DEBUG=1
```

**Check Configuration:**
```bash
# View environment variables
env | grep BLOGINATOR

# Check .env file
cat .env | grep -v "^#" | grep -v "^$"

# Verify index exists
ls -la .bloginator/
ls -la .bloginator/chroma/

# Test search index
bloginator search .bloginator/chroma "engineering" -n 5
```

---

## Git Workflow

**Feature Branch Workflow:**
```bash
# Start new feature
git checkout -b feature/my-feature-name

# Commit with conventional message
git commit -m "feat(module): description of change"
git commit -m "fix(module): description of bug fix"
git commit -m "docs(module): documentation update"

# Push for review
git push origin feature/my-feature-name
```

**Commit Types**: feat, fix, docs, style, refactor, test, chore, perf, ci
**Scope**: module name (e.g., `generation`, `search`, `cli`)

---

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
