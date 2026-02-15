# CLI Commands

> **When to load:** When running bloginator CLI commands

## Show Help

```bash
bloginator --help
bloginator extract --help
bloginator index --help
bloginator search --help
bloginator outline --help
bloginator draft --help
```

## Run with Verbose Output

```bash
bloginator search --index .bloginator/chroma "test query" -v
```

## Dry Run (no side effects)

```bash
bloginator extract ~/writing --dry-run
```

## Quick Reference

| Task | Command |
|------|---------|
| **Run command** | `bloginator extract/index/search/outline/draft` |
| **Help** | `bloginator --help` |
| **Verbose** | `bloginator <cmd> -v` |
| **Dry run** | `bloginator <cmd> --dry-run` |

