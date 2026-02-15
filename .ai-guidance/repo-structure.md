# Repository Structure

> **When to load:** When working on project structure, organization, or file locations

---

## Project Structure

```text
src/bloginator/
  cli/           # Click CLI commands
  export/        # Document exporters (HTML, Markdown, DOCX, PDF)
  extraction/    # Document chunking and metadata extraction
  generation/    # LLM clients and content generation
  indexing/      # ChromaDB vector indexing
  models/        # Pydantic models and dataclasses
  monitoring/    # Logging and metrics
  quality/       # Slop detection and quality assurance
  safety/        # Blocklist and content filtering
  search/        # Semantic search
  services/      # History and template management
tests/
  unit/          # Unit tests (fast, isolated)
  integration/   # Integration tests
  e2e/           # End-to-end workflow tests
  benchmarks/    # Performance tests
docs/
  *.md           # Documentation files
```

---

## Repository Cleanliness

### Temporary Files Policy

- ALL temporary/experimental scripts go in `tmp/` directory (git-ignored)
- ALL blog generation outputs go in `blogs/` directory (git-ignored)
- ALL prompt experiments go in `prompts/experimentation/` (git-ignored)
- ALL context handoff prompts go in `prompts/` (e.g., `prompts/finish-refactoring-options-b-c.md`)
- NEVER create shell scripts or markdown files in the repository root
- Exception: Only permanent, maintained scripts/docs belong in root

### Markdown Documentation Policy

- Keep all working markdown files in `docs/` updated as you work
- Create index files (e.g., `docs/IMPLEMENTATION_PLAN_TOPIC_DRIFT_FIX.md`) that reference other docs
- Write comprehensive prompts to `prompts/` for context handoffs
- Reference prompt files instead of pasting huge inline content
- Each prompt should be 200-400 lines max, focused on execution steps

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `src/bloginator/` | Main source code |
| `tests/` | All tests (unit, integration, e2e) |
| `docs/` | Documentation |
| `prompts/` | LLM prompts and context handoffs |
| `corpus/` | User's knowledge base documents |
| `blogs/` | Generated blog outputs (git-ignored) |
| `tmp/` | Temporary experiments (git-ignored) |
| `.bloginator/` | Index and runtime data |

---

## Repository Maintenance

**Clean Up:**

```bash
# Remove cache directories
rm -rf .pytest_cache/
rm -rf .mypy_cache/
rm -rf .ruff_cache/

# Remove build artifacts
rm -rf build/ dist/ *.egg-info/

# Remove test outputs
rm -rf htmlcov/ .coverage

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

**Verify Repository Health:**

```bash
# Check root directory cleanliness
./scripts/check-root-cleanliness.sh

# Validate monorepo structure
./scripts/validate-monorepo.sh

# Check cross-references in docs
./scripts/validate-cross-references.sh
```
