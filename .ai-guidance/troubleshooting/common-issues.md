# Common Issues & Fixes

> **When to load:** When encountering common development issues

## Tests Fail with Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev]" --force-reinstall

# Clear cache
rm -rf .pytest_cache/ __pycache__/

# Run tests again
pytest tests/ -x
```

## Type Checking Fails

```bash
# Check specific module
mypy src/bloginator/models --show-traceback

# Fix the issue instead of ignoring:
# Don't add type: ignore, fix the underlying type issue
```

## Pre-commit Hook Fails

```bash
# Check what pre-commit is doing
pre-commit run --all-files --verbose

# Fix issues
black src/ tests/
ruff check --fix src/ tests/

# Commit again
git commit -m "fix: formatting"
```

