# Git Workflow

> **When to load:** When committing or working with branches

## Feature Branch Workflow

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

## Commit Types

| Type | Use for |
|------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation |
| `style` | Formatting (no code change) |
| `refactor` | Code restructuring |
| `test` | Adding tests |
| `chore` | Maintenance |
| `perf` | Performance |
| `ci` | CI/CD changes |

## Scope

Use module name as scope: `generation`, `search`, `cli`, `models`, etc.

**Examples:**
- `feat(search): add semantic similarity scoring`
- `fix(cli): handle missing index gracefully`
- `docs(readme): update installation steps`

