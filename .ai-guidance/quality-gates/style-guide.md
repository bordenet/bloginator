# Python Style Guide

> **When to load:** When writing Python code or fixing style issues

All Python code MUST comply with `docs/PYTHON_STYLE_GUIDE.md`.

## Key Requirements

| Rule | Value |
|------|-------|
| **Line length** | 100 chars max (Black/Ruff enforced) |
| **Type annotations** | Required on all functions |
| **Docstrings** | Google style, required for public APIs |
| **Function length** | Target ≤50 lines, max 100 lines |
| **Parameters** | ≤5 per function |
| **Import order** | stdlib → third-party → local (isort) |
| **Max file length** | 350 lines max, target ~250 |

## Prohibited Patterns

1. **No untyped functions** - Every function must have type annotations
2. **No missing docstrings** - Public APIs must be documented
3. **No ignoring mypy errors** - Fix the issue, don't add `# type: ignore`
4. **No tests without assertions** - Every test must verify behavior
5. **No coverage exclusions without justification** - Document `# pragma: no cover`

