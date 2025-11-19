# Bloginator

Generate content from your historical writing using RAG and local/cloud LLMs.

**Version**: 1.0.0
**Python**: 3.10+
**License**: MIT

---

## What It Does

Bloginator indexes your writing (blog posts, documents, notes) and generates new content that preserves your voice:

1. **Extract** text from PDFs, DOCX, Markdown, TXT
2. **Index** content using ChromaDB with semantic embeddings
3. **Search** your corpus semantically (meaning-based)
4. **Generate** outlines and drafts grounded in your writing
5. **Refine** content with natural language feedback
6. **Validate** against blocklist to prevent leaking proprietary content

---

## Quick Start

```bash
# Install
git clone https://github.com/bordenet/bloginator.git
cd bloginator
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Setup LLM (Ollama recommended)
ollama pull llama3

# Use CLI
bloginator extract ~/writing -o output/extracted
bloginator index output/extracted -o output/index
bloginator search output/index "agile transformation" -n 10
bloginator outline --index output/index --keywords "career,senior,engineer"
bloginator draft --index output/index --outline outline.json

# Or use web UI
bloginator serve --port 8000
```

---

## Features

### Core
- Document extraction (PDF, DOCX, MD, TXT, ZIP)
- Vector indexing with ChromaDB + sentence-transformers
- Semantic search with quality/recency weighting
- RAG-based outline and draft generation
- Iterative refinement with version management
- Blocklist validation (exact, case-insensitive, regex)

### Interfaces
- **CLI**: 12 commands for all workflows
- **Streamlit UI**: 7-page web interface
- **FastAPI**: REST API (experimental, requires `pip install ".[web]"`)

### LLM Support
- **Ollama** (default): Local inference
- **Custom**: Any OpenAI-compatible API
- **Cloud**: OpenAI/Anthropic (requires API keys)

See [CUSTOM_LLM_GUIDE.md](docs/CUSTOM_LLM_GUIDE.md) for configuration.

---

## Documentation

- [Installation](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Architecture](docs/ARCHITECTURE-002-Deployment-Modes.md)

---

## Development

```bash
# Setup
pip install -e ".[dev]"
pre-commit install

# Test
pytest tests/ -v --cov=src/bloginator

# Quality
pre-commit run --all-files  # black, ruff, isort, mypy
```

**Standards**: Black (100 chars), Ruff, MyPy strict, 80% coverage target

---

## Technology Stack

**Core**: Python 3.10+, ChromaDB, sentence-transformers, Pydantic v2
**LLM**: Ollama (default), OpenAI-compatible APIs
**UI**: Streamlit, FastAPI, Jinja2
**Docs**: PyMuPDF, python-docx
**Quality**: pytest, black, ruff, mypy, bandit, pre-commit

---

## Contributing

1. Fork and create feature branch
2. Run tests: `pytest tests/ -v`
3. Run linters: `pre-commit run --all-files`
4. Open pull request

**Requirements**: All tests pass, all linters pass, no proprietary content in examples.

---

## License

MIT - See LICENSE file.

---

## Links

**Repository**: https://github.com/bordenet/bloginator
**Issues**: https://github.com/bordenet/bloginator/issues
**Author**: Matt Bordenet
