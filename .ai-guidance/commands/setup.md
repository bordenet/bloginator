# Development Setup

> **When to load:** When setting up or verifying environment

## Pre-Flight Checklist

Before ANY work:

```bash
git status && git log --oneline -3           # Branch/status
python --version                              # Should be 3.10+
source venv/bin/activate
pip list | grep -E "black|ruff|mypy|pytest"  # Tools installed
ls -la .bloginator/ tests/                    # Repo health
```

## Initial Setup

```bash
git clone https://github.com/bordenet/bloginator.git && cd bloginator
python3.11 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
./scripts/run-fast-quality-gate.sh
```

## Quick Reference

| Task | Command |
|------|---------|
| **Setup** | `python3.11 -m venv venv && source venv/bin/activate && pip install -e ".[dev]"` |
| **Quick check** | `./scripts/run-fast-quality-gate.sh` |

