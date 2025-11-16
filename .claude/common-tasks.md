# Common Development Tasks

## Initial Setup

### First Time Setup
```bash
# Clone and setup
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify setup
bloginator --version
./validate-bloginator.sh
```

## Daily Development Workflow

### Starting Work
```bash
# Activate virtualenv
source venv/bin/activate

# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Run tests to ensure starting point is clean
pytest tests/ -m "not slow" -v
```

### During Development
```bash
# Auto-fix formatting and linting
black --line-length=100 src/ tests/
ruff check --fix src/ tests/
isort --profile=black --line-length=100 src/ tests/

# Type check
mypy src/ --strict --ignore-missing-imports

# Run fast tests
pytest tests/ -m "not slow" -v

# Run specific test file
pytest tests/unit/test_blocklist.py -v

# Run specific test
pytest tests/unit/test_blocklist.py::test_exact_match -v

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Before Committing
```bash
# Run full validation
./validate-bloginator.sh

# Or auto-fix issues
./validate-bloginator.sh --fix

# Stage changes
git add .

# Commit (pre-commit hooks run automatically)
git commit -m "feat: add amazing feature"

# Push
git push origin feature/my-feature
```

## Testing Tasks

### Run Different Test Suites
```bash
# Fast unit tests only (for quick feedback)
pytest tests/unit/ -m "not slow" -q

# All unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# Tests requiring Ollama
pytest tests/ -m requires_ollama -v

# Everything except slow tests
pytest tests/ -m "not slow" -v

# Everything including slow tests
pytest tests/ -v

# Stop on first failure
pytest tests/ -x

# Run with verbose output and show local variables on failure
pytest tests/ -vv --showlocals
```

### Coverage Tasks
```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View in browser

# Check coverage threshold
coverage report --fail-under=80

# Coverage for specific module
pytest tests/unit/safety/ --cov=src/bloginator/safety --cov-report=term-missing
```

## Code Quality Tasks

### Formatting and Linting
```bash
# Format code
black --line-length=100 src/ tests/

# Check formatting without changing
black --check --line-length=100 src/ tests/

# Lint and auto-fix
ruff check --fix src/ tests/

# Lint without fixing
ruff check src/ tests/

# Sort imports
isort --profile=black --line-length=100 src/ tests/

# Check import sorting
isort --check-only --profile=black --line-length=100 src/ tests/
```

### Type Checking
```bash
# Type check all source
mypy src/ --strict --ignore-missing-imports

# Type check specific file
mypy src/bloginator/safety/blocklist.py --strict --ignore-missing-imports

# Generate type coverage report
mypy src/ --strict --ignore-missing-imports --html-report mypy-report
open mypy-report/index.html
```

### Pre-commit Hooks
```bash
# Run all pre-commit hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run ruff --all-files

# Update pre-commit hook versions
pre-commit autoupdate

# Skip pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "message"
```

## Creating New Components

### New Module
```bash
# 1. Create module file
touch src/bloginator/mymodule/myfile.py

# 2. Add module docstring and implementation
# 3. Create corresponding test file
touch tests/unit/mymodule/test_myfile.py

# 4. Write tests first (TDD)
# 5. Implement functionality
# 6. Run tests
pytest tests/unit/mymodule/test_myfile.py -v

# 7. Validate
./validate-bloginator.sh
```

### New CLI Command
```bash
# 1. Create command file
touch src/bloginator/cli/mycommand.py

# 2. Implement Click command
# 3. Register in src/bloginator/cli/main.py
# 4. Create tests
touch tests/integration/cli/test_mycommand.py

# 5. Test manually
bloginator mycommand --help

# 6. Validate
./validate-bloginator.sh
```

### New Pydantic Model
```bash
# 1. Create model file
touch src/bloginator/models/mymodel.py

# 2. Define model with docstrings
# 3. Create tests
touch tests/unit/models/test_mymodel.py

# 4. Test serialization/deserialization
pytest tests/unit/models/test_mymodel.py -v
```

## Debugging Tasks

### Run Tests with Debugging
```bash
# Run with pytest debugger
pytest tests/ --pdb

# Break on first failure
pytest tests/ -x --pdb

# Show print statements
pytest tests/ -s

# Very verbose output
pytest tests/ -vv
```

### Interactive Python
```bash
# Start Python with project in path
python

# Import and test
>>> from bloginator.models import Document
>>> doc = Document(id="test", filename="test.md", source_path=Path("test.md"), format="markdown")
>>> doc.model_dump_json()
```

### Check Dependencies
```bash
# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Show dependency tree
pip install pipdeptree
pipdeptree
```

## Documentation Tasks

### Generate Documentation
```bash
# Check docstring coverage
pydocstyle src/bloginator/

# Generate API docs (when ready)
# pdoc --html --output-dir docs/api src/bloginator
```

### Update Documentation
```bash
# After major changes, update:
# - README.md
# - docs/ARCHITECTURE-002-Deployment-Modes.md (if architecture changes)
# - .claude/project-context.md (if major changes)
```

## Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes, commit frequently
git add .
git commit -m "feat: implement part 1"

# Push to remote
git push origin feature/my-feature

# Create PR when ready
```

### Updating from Main
```bash
# Fetch latest
git fetch origin

# Rebase on main (if feature branch)
git rebase origin/main

# Or merge (if collaboration branch)
git merge origin/main
```

### Fixing Issues
```bash
# Create bugfix branch
git checkout -b fix/issue-123

# Make fixes
# ... commit ...

# Push and create PR
git push origin fix/issue-123
```

## Performance Profiling

### Profile Tests
```bash
# Profile test execution time
pytest tests/ --durations=10

# Profile code
python -m cProfile -o profile.stats src/bloginator/cli/main.py

# View profile
python -m pstats profile.stats
```

### Benchmark Performance
```bash
# Run performance tests
pytest tests/performance/ -v

# Time specific operations
time bloginator extract test-corpus -o output/extracted
time bloginator index output/extracted -o output/index
time bloginator search output/index "test query"
```

## Troubleshooting

### Common Issues

**Import errors**:
```bash
# Reinstall in editable mode
pip install -e ".[dev]"
```

**Test failures**:
```bash
# Clear pytest cache
rm -rf .pytest_cache

# Clear coverage data
rm -f .coverage
rm -rf htmlcov/
```

**Type checking errors**:
```bash
# Clear mypy cache
rm -rf .mypy_cache
```

**Pre-commit hook failures**:
```bash
# Auto-fix most issues
./validate-bloginator.sh --fix

# Update pre-commit hooks
pre-commit autoupdate
pre-commit install
```

## Cleanup

### Remove Build Artifacts
```bash
# Remove all build/cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
rm -rf build/ dist/ *.egg-info
rm -rf .pytest_cache .mypy_cache .ruff_cache
rm -rf htmlcov/ .coverage
```

### Reset Environment
```bash
# Deactivate and remove virtualenv
deactivate
rm -rf venv/

# Recreate from scratch
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```
