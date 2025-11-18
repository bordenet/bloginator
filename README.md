# Bloginator: Content Generation from Personal Writing Corpus

**Version**: 1.0.0
**Python**: 3.10+
**License**: MIT

---

## Overview

Bloginator indexes your historical writing (blog posts, documents, notes) to generate new content that maintains your voice and style. Uses RAG (Retrieval-Augmented Generation) with local or cloud LLMs.

### What It Does

1. **Extracts** text from PDFs, DOCX, Markdown, TXT, and ZIP archives
2. **Indexes** content using ChromaDB vector database with semantic embeddings
3. **Searches** your corpus semantically (meaning-based, not keyword matching)
4. **Generates** outlines and drafts based on your historical writing
5. **Refines** content iteratively with natural language feedback
6. **Protects** proprietary content with blocklist validation
7. **Preserves** your authentic voice through RAG-based generation

### What It Does NOT Do

- **Does NOT** work offline without an LLM (requires Ollama or API access)
- **Does NOT** support all document formats (no PowerPoint, spreadsheets, etc.)
- **Does NOT** guarantee perfect voice matching (LLM quality dependent)
- **Does NOT** include cloud LLM providers out-of-box (Ollama only; OpenAI/Anthropic require API keys)
- **Does NOT** have batch processing or automated workflows
- **Does NOT** include advanced analytics or corpus insights
- **Does NOT** support collaborative editing or multi-user workflows

---

## Core Features

### Document Processing
- **Input Formats**: PDF, DOCX, Markdown, TXT, ZIP archives
- **Output Formats**: Markdown, DOCX, HTML, Plain Text
- **Extraction**: Text extraction with metadata (dates, quality ratings)
- **Indexing**: Vector embeddings using sentence-transformers (all-MiniLM-L6-v2)

### Content Generation
- **Outline Generation**: Create structured outlines from keywords/themes
- **Draft Generation**: Generate full drafts from outlines using RAG
- **Refinement**: Iterative improvement with natural language feedback
- **Version Management**: Track changes, compare versions, revert
- **Voice Scoring**: Similarity metrics to ensure consistency

### Safety & Privacy
- **Blocklist System**: Prevent leakage of company names, secrets, PII
- **Pattern Matching**: Exact match, case-insensitive, regex support
- **Local-First**: Can run entirely offline with Ollama (no cloud required)
- **Validation**: Pre-generation checks for blocklisted terms

### LLM Support
- **Ollama** (default): Local LLM inference (llama3, mistral, mixtral, etc.)
- **Custom Endpoints**: Any OpenAI-compatible API (LM Studio, vLLM, text-generation-webui)
- **Cloud LLMs**: OpenAI and Anthropic support (requires API keys, not included)

### User Interfaces
- **CLI**: 12 commands for all workflows (extract, index, search, outline, draft, refine, etc.)
- **Streamlit UI**: 7-page web interface for corpus management and generation
- **FastAPI Web UI**: REST API with HTML templates (experimental)

### Template Library
- 12 pre-built document templates:
  - Blog posts, technical designs, architecture docs
  - Job descriptions, career ladders, performance reviews
  - Project proposals, team charters, incident postmortems
  - Engineering playbooks, onboarding guides, and more

---

## Installation

```bash
# Clone repository
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional, for contributors)
pre-commit install

# Verify installation
bloginator --version
```

### LLM Setup

**Option 1: Local (Ollama - Recommended)**
```bash
# Install Ollama: https://ollama.ai
# Pull a model
ollama pull llama3

# Bloginator will auto-detect Ollama at http://localhost:11434
```

**Option 2: Custom Endpoint**
```bash
# Copy environment template
cp .env.example .env

# Edit .env
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_BASE_URL=http://localhost:1234/v1  # LM Studio example
BLOGINATOR_LLM_MODEL=local-model
```

**Option 3: Cloud LLM (OpenAI/Anthropic)**
```bash
# Edit .env
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1
BLOGINATOR_LLM_API_KEY=sk-...
BLOGINATOR_LLM_MODEL=gpt-4
```

See [CUSTOM_LLM_GUIDE.md](docs/CUSTOM_LLM_GUIDE.md) for detailed configuration.

---

## Quick Start

### CLI Workflow

```bash
# 1. Extract and index your corpus
bloginator extract ~/my-writing -o output/extracted --quality preferred
bloginator index output/extracted -o output/index

# 2. Search your corpus
bloginator search output/index "agile transformation" -n 10

# 3. Manage blocklist
bloginator blocklist add "Acme Corp" --category company_name --notes "Former employer NDA"
bloginator blocklist list

# 4. Generate content
bloginator outline --index output/index --keywords "career,ladder,senior,engineer"
bloginator draft --index output/index --outline outline.json -o draft.md

# 5. Refine and iterate
bloginator refine -i output/index -d draft.json -f "Make tone more optimistic"
bloginator diff my-draft -v1 1 -v2 2
bloginator revert my-draft 1 -o draft.json
```

### Web UI Workflow

```bash
# Start Streamlit UI
bloginator serve --port 8000

# Open browser to http://localhost:8000
# Use the intuitive web interface for all workflows
```

---

## Project Structure

```
bloginator/
├── src/bloginator/          # Source code
│   ├── cli/                 # CLI commands (12 commands)
│   ├── extraction/          # Document extraction (PDF, DOCX, etc.)
│   ├── indexing/            # Vector indexing with ChromaDB
│   ├── search/              # Semantic search and retrieval
│   ├── generation/          # LLM clients and content generators
│   ├── voice/               # Voice preservation system
│   ├── safety/              # Blocklist and validation
│   ├── ui/                  # Streamlit UI (7 pages)
│   ├── web/                 # FastAPI web UI (experimental)
│   ├── templates/           # Document templates library
│   └── models/              # Pydantic data models
├── tests/                   # Test suite (355 tests)
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── docs/                    # Documentation
├── pyproject.toml           # Project configuration
└── .pre-commit-config.yaml  # Pre-commit hooks
```

---

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run pre-commit checks manually
pre-commit run --all-files
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/bloginator --cov-report=html

# Run specific test categories
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests only
pytest -m "not slow" -v         # Skip slow tests
```

### Code Quality

```bash
# Formatting
black src/ tests/
isort src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/

# All checks (recommended before commit)
pre-commit run --all-files
```

### Quality Standards

- **Black**: Line length 100, Python 3.10+ target
- **Ruff**: All errors must be fixed
- **isort**: Black-compatible import sorting
- **MyPy**: Strict mode (disabled for tests)
- **Coverage**: Target >80% (not currently enforced)
- **File Size**: Target <400 lines per file (2 files currently violate)

---

## Implementation Status

### Implemented Features

**Phase 1: Foundation**
- ✅ Document extraction (PDF, DOCX, MD, TXT, ZIP)
- ✅ Vector indexing with ChromaDB
- ✅ Semantic search with quality/recency weighting

**Phase 2: Core Generation**
- ✅ Outline generation from keywords
- ✅ Draft generation from outlines
- ✅ Iterative refinement with feedback
- ✅ Version management (diff, revert)

**Phase 3: Safety & UI**
- ✅ Blocklist system (exact, case-insensitive, regex)
- ✅ Streamlit UI (7 pages)
- ✅ FastAPI web UI (experimental)

**Phase 4: Enhancement**
- ✅ Template library (12 templates)
- ✅ Generation history tracking
- ✅ Parallel extraction
- ✅ Incremental indexing

**Phase 5: Testing**
- ✅ 355 tests passing (100% of runnable tests)
- ✅ 6 tests skipped (optional FastAPI dependency)
- ⚠️ Test coverage % unknown (measurement not implemented)

### Known Limitations

**Current Gaps**:
- No multi-format export (claimed in docs, not verified in code)
- No batch processing or automation workflows
- No advanced corpus analytics (basic analytics only)
- No collaborative features or multi-user support
- No plugin/extension system
- No API documentation (code only)
- Test coverage measurement not configured
- 2 files exceed 400-line guideline (417, 415 lines)

**Future Work**:
See [FUTURE_WORK.md](docs/FUTURE_WORK.md) for extensibility plans and roadmap.

---

## Technology Stack

**Core**:
- Python 3.10+
- ChromaDB (vector store)
- sentence-transformers (embeddings: all-MiniLM-L6-v2)
- Ollama (default local LLM)
- Pydantic v2 (data validation)
- Click (CLI framework)
- Rich (terminal UI)

**Web**:
- Streamlit (primary UI)
- FastAPI (experimental API)
- Uvicorn (ASGI server)
- Jinja2 (templates)

**Documents**:
- PyMuPDF (PDF)
- python-docx (DOCX)
- Markdown (native)

**Quality**:
- pytest (testing)
- black (formatting)
- ruff (linting)
- mypy (type checking)
- pre-commit (git hooks)

---

## Documentation

### User Documentation
- [Installation Guide](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Custom LLM Guide](docs/CUSTOM_LLM_GUIDE.md)
- [Migration Guide](docs/MIGRATION-GUIDE.md)

### Developer Documentation
- [PRD: Core System](docs/PRD-BLOGINATOR-001-Core-System.md)
- [Design Spec](docs/DESIGN-SPEC-001-Implementation-Plan.md)
- [Testing Spec](docs/TESTING-SPEC-003-Quality-Assurance.md)
- [Architecture](docs/ARCHITECTURE-002-Deployment-Modes.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Claude Guidelines](docs/CLAUDE_GUIDELINES.md)
- [Claude AI Notes](docs/CLAUDE.md)

---

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests: `pytest tests/ -v`
5. Run linters: `pre-commit run --all-files`
6. Commit your changes
7. Push to branch
8. Open a Pull Request

### Code Review Criteria

- All tests pass
- All linters pass (black, ruff, isort, mypy)
- No proprietary content in examples or tests
- Documentation updated (if applicable)
- Changes maintain backward compatibility (if possible)

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Contact

**Repository**: https://github.com/bordenet/bloginator
**Issues**: https://github.com/bordenet/bloginator/issues
**Author**: Matt Bordenet

---

## Acknowledgments

- Ollama project for local LLM inference
- ChromaDB for vector database
- sentence-transformers for embeddings
- Local LLM community (LM Studio, vLLM, text-generation-webui)
