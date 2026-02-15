# Troubleshooting Index

> **When to load:** Overview of troubleshooting modules

## Sub-Modules

| Module | Description |
|--------|-------------|
| [terminal-issues.md](terminal-issues.md) | Terminal capture problems |
| [efficiency.md](efficiency.md) | Avoiding debugging loops |
| [common-issues.md](common-issues.md) | Common fixes |

## Quick Reference

| Issue | Solution |
|-------|----------|
| Terminal returns empty | Use file redirection |
| Going in circles | STOP, ask Perplexity |
| Import errors | `pip install -e ".[dev]" --force-reinstall` |
| Type errors | `mypy src/module --show-traceback` |
| Pre-commit fails | `pre-commit run --all-files --verbose` |

