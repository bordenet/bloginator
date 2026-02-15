# Repository Cleanliness

> **When to load:** When organizing files or cleaning up

## Temporary Files Policy

- ALL temporary/experimental scripts → `tmp/` (git-ignored)
- ALL blog generation outputs → `blogs/` (git-ignored)
- ALL prompt experiments → `prompts/experimentation/` (git-ignored)
- ALL context handoff prompts → `prompts/` (e.g., `prompts/finish-refactoring.md`)
- NEVER create shell scripts or markdown files in repository root
- Exception: Only permanent, maintained scripts/docs belong in root

## Markdown Documentation Policy

- Keep all working markdown files in `docs/` updated
- Create index files referencing other docs
- Write comprehensive prompts to `prompts/` for context handoffs
- Reference prompt files instead of pasting huge inline content
- Each prompt should be 200-400 lines max, focused on execution

## Clean Up Commands

```bash
rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/   # Cache dirs
rm -rf build/ dist/ *.egg-info/                    # Build artifacts
rm -rf htmlcov/ .coverage                          # Test outputs
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

## Verify Cleanliness

```bash
./scripts/check-root-cleanliness.sh
./scripts/validate-monorepo.sh
./scripts/validate-cross-references.sh
```

