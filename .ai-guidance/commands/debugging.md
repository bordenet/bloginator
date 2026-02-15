# Debugging

> **When to load:** When debugging issues or checking configuration

## Enable Verbose Logging

```bash
export BLOGINATOR_DEBUG=1
```

## Check Configuration

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

## Cleanup Cache Files

```bash
rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/
```

## Quick Reference

| Task | Command |
|------|---------|
| **Debug mode** | `export BLOGINATOR_DEBUG=1` |
| **Check env** | `env \| grep BLOGINATOR` |
| **Test index** | `bloginator search .bloginator/chroma "query" -n 5` |
| **Cleanup** | `rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/` |

