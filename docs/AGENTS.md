# AGENTS.md - Standardized Commands for Claude

This document defines the standard commands and workflows that Claude agents should use when working on the bloginator repository.

---

## Mandatory Workflows

### Before Starting Work

Always load the appropriate skills using the skill tool:

```bash
# For major features or refactoring
skill:using-git-worktrees
skill:brainstorming
skill:writing-plans

# For implementation
skill:test-driven-development
skill:systematic-debugging
skill:executing-plans

# Before committing
skill:enforce-style-guide
skill:verification-before-completion
skill:requesting-code-review
```

### Pre-Flight Checklist

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

## Code Quality Commands

### Quick Quality Check (Before Commits)

```bash
./scripts/run-fast-quality-gate.sh
```

This runs:
- Black formatting check
- Ruff linting
- MyPy type checking (key modules)
- isort import sorting
- Fast unit tests

### Full Quality Check (Before PRs)

```bash
# Format code
black --line-length=100 src/ tests/

# Fix linting issues
ruff check --fix src/ tests/

# Sort imports
isort --profile=black --line-length=100 src/ tests/

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

## Testing Commands

### Run All Tests

```bash
# Full test suite with coverage report
pytest tests/ -v --cov=src/bloginator --cov-report=term-missing

# Specific test file
pytest tests/unit/models/test_document.py -v

# Specific test class
pytest tests/unit/models/test_document.py::TestDocument -v

# Specific test
pytest tests/unit/models/test_document.py::TestDocument::test_constructor -v

# Fast tests only (skip slow/integration)
pytest tests/ -m "not slow" -q

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### Coverage Analysis

```bash
# Generate coverage report
pytest tests/ --cov=src/bloginator --cov-report=html

# View coverage report (opens in browser)
open htmlcov/index.html

# Coverage summary
pytest tests/ --cov=src/bloginator --cov-report=term-missing | tail -20
```

---

## Development Commands

### Setup Development Environment

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

### Linting and Formatting

```bash
# Format all code (auto-fix)
black --line-length=100 src/ tests/

# Lint and fix
ruff check --fix src/ tests/

# Sort imports (auto-fix)
isort --profile=black --line-length=100 src/ tests/

# Check only (no auto-fix)
black --check src/ tests/
ruff check src/ tests/
isort --check-only src/ tests/
```

### Type Checking

```bash
# Strict type checking (high-value modules)
mypy src/bloginator/models \
      src/bloginator/extraction \
      src/bloginator/search

# Full mypy output with detailed errors
mypy src/bloginator/models --show-traceback

# Check specific file
mypy src/bloginator/models/document.py
```

---

## Git Workflow Commands

### Feature Branch Workflow

```bash
# Start new feature
git checkout -b feature/my-feature-name
# or using git-worktrees skill:
skill:using-git-worktrees

# Check status
git status

# Stage changes
git add src/

# Commit with conventional message
git commit -m "feat(module): description of change"
# or
git commit -m "fix(module): description of bug fix"
# or
git commit -m "docs(module): documentation update"

# Push for review
git push origin feature/my-feature-name

# Create pull request (on GitHub)
# Add description, link issues, request reviewers
```

### Commit Message Format

**Always use Conventional Commits:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: feat, fix, docs, style, refactor, test, chore, perf, ci
**Scope**: module name (e.g., `generation`, `search`, `cli`)
**Subject**: Imperative, no capitals, no period

**Examples**:
```bash
git commit -m "feat(generation): add voice matching score"
git commit -m "fix(search): handle empty corpus gracefully"
git commit -m "test(extraction): add docx corruption tests"
git commit -m "docs(readme): update installation instructions"
```

---

## Debugging Commands

### Enable Verbose Logging

```bash
# Set debug logging
export BLOGINATOR_DEBUG=1

# Or in code:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect CLI Commands

```bash
# Show help for any command
bloginator --help
bloginator extract --help
bloginator index --help
bloginator search --help
bloginator outline --help
bloginator draft --help

# Run with verbose output
bloginator search --index .bloginator/chroma "test query" -v

# Dry run (no side effects)
bloginator extract ~/writing --dry-run
```

### Check Configuration

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

## Performance & Profiling

### Measure Command Performance

```bash
# Time a command
time bloginator search .bloginator/chroma "test query"

# Profile Python code (requires snakeviz)
python -m cProfile -o /tmp/profile.stats script.py
snakeviz /tmp/profile.stats
```

### Check System Resources

```bash
# Monitor resource usage during command
top -p $(pgrep -f "bloginator")

# Or use system monitor
ps aux | grep bloginator
```

---

## Documentation Commands

### Build & View Documentation

```bash
# Check markdown formatting
markdownlint docs/*.md

# View documentation locally
open docs/README.md
cat docs/INSTALLATION.md

# Find documentation for feature
grep -r "feature name" docs/
```

---

## Repository Maintenance

### Clean Up

```bash
# Remove cache directories
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf .ruff_cache/

# Remove build artifacts
rm -rf build/ dist/ *.egg-info/

# Remove test outputs
rm -rf htmlcov/ .coverage

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

### Verify Repository Health

```bash
# Check root directory cleanliness
./scripts/check-root-cleanliness.sh

# Validate monorepo structure
./scripts/validate-monorepo.sh

# Check cross-references in docs
./scripts/validate-cross-references.sh
```

---

## Blog Generation Workflow (Assistant Mode)

### Generate a Blog Post

```bash
# Step 1: Clear old requests
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*

# Step 2: Generate outline (in background)
BLOGINATOR_LLM_MOCK=assistant bloginator outline \
  --index .bloginator/chroma \
  --title "Your Topic Title" \
  --keywords "keyword1,keyword2,keyword3" \
  --audience "engineering-leaders" \
  -o blogs/my-blog-outline.json \
  --batch --batch-timeout 60 2>&1 &

# Step 3: Wait for requests, then act as LLM
sleep 3
# Read .bloginator/llm_requests/*.json
# Write responses to .bloginator/llm_responses/*.json
# Use corpus-synthesis-llm.md prompt for synthesizing

# Step 4: Generate draft (in background)
rm -rf .bloginator/llm_requests/* .bloginator/llm_responses/*
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
  --index .bloginator/chroma \
  --outline blogs/my-blog-outline.json \
  -o blogs/my-blog.md \
  --batch --batch-timeout 180 2>&1 &

# Step 5: Wait and provide responses again
sleep 5

# Step 6: Verify output
ls -la blogs/my-blog.md
wc -w blogs/my-blog.md
grep -c "^|" blogs/my-blog.md  # Count tables
```

---

## Common Issues & Troubleshooting

### Tests Fail with Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]" --force-reinstall

# Clear cache
rm -rf .pytest_cache/ __pycache__/

# Run tests again
pytest tests/ -x
```

### Type Checking Fails

```bash
# Check specific module
mypy src/bloginator/models --show-traceback

# Ignore specific error (temporary, document why)
# Add to file: # type: ignore[error-code]

# Fix the issue instead:
# Don't add type: ignore, fix the underlying type issue
```

### Pre-commit Hook Fails

```bash
# Check what pre-commit is doing
pre-commit run --all-files --verbose

# Fix issues
black src/ tests/
ruff check --fix src/ tests/
isort src/ tests/

# Commit again
git commit -m "fix: formatting"
```

### Terminal Capture Returns Empty

This happens after 60+ terminal sessions. Workaround:

```bash
# Redirect output to file
command > /tmp/output.txt 2>&1

# Read the file instead
cat /tmp/output.txt
```

---

## Code Review Checklist

Before requesting review or reviewing PRs:

- [ ] All tests pass: `pytest tests/ --cov=src/bloginator`
- [ ] Linting passes: `./scripts/run-fast-quality-gate.sh`
- [ ] Type checking passes: `mypy src/bloginator/models ...`
- [ ] Coverage ≥85%: Check coverage report
- [ ] Docstrings added: All public functions documented
- [ ] No `type: ignore` without justification
- [ ] No untested code paths
- [ ] No hardcoded values (use config)
- [ ] Commit message follows Conventional Commits

---

## When Stuck: Perplexity Workflow

If debugging reaches a dead-end:

```bash
# 1. Generate a detailed diagnostic
echo "
Environment:
$(python --version)
$(pip list | grep -E 'bloginator|pytest|black|mypy')

Recent error:
[paste error message]

What I've tried:
[list attempts and results]

Specific question:
[what are you trying to solve?]
" > /tmp/perplexity_prompt.txt

# 2. Ask user to run on Perplexity
# 3. Return with Perplexity response
# 4. Continue debugging
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Setup** | `python3.11 -m venv venv && source venv/bin/activate && pip install -e ".[dev]"` |
| **Quick check** | `./scripts/run-fast-quality-gate.sh` |
| **Full check** | `pytest tests/ --cov=src/bloginator && mypy src/bloginator/models ...` |
| **Format** | `black --line-length=100 src/ tests/` |
| **Lint** | `ruff check --fix src/ tests/` |
| **Tests** | `pytest tests/ -v --cov=src/bloginator` |
| **Type check** | `mypy src/bloginator/models src/bloginator/extraction ...` |
| **Run command** | `bloginator extract/index/search/outline/draft` |
| **Help** | `bloginator --help` |
| **Cleanup** | `rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/` |

---

## Related Documentation

- **Code Quality**: `CLAUDE.md` (comprehensive guidelines)
- **Style Guide**: `docs/PYTHON_STYLE_GUIDE.md`
- **Development**: `docs/DEVELOPER_GUIDE.md`
- **User Guide**: `docs/USER_GUIDE.md`
- **Repository Health**: `REPO_HOLES.md` (gaps and improvements)
