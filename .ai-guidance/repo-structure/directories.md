# Directory Structure

> **When to load:** When understanding project organization

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

