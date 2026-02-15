# Linting and Formatting

> **When to load:** When formatting code or fixing lint errors

## Format All Code (auto-fix)

```bash
black --line-length=100 src/ tests/
```

## Lint and Fix

```bash
ruff check --fix src/ tests/
```

## Check Only (no auto-fix)

```bash
black --check src/ tests/
ruff check src/ tests/
```

## Quick Reference

| Task | Command |
|------|---------|
| **Format** | `black --line-length=100 src/ tests/` |
| **Lint** | `ruff check --fix src/ tests/` |
| **Check only** | `black --check src/ tests/ && ruff check src/ tests/` |

