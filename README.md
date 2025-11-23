# Bloginator

[![Tests](https://github.com/bordenet/bloginator/actions/workflows/tests.yml/badge.svg)](https://github.com/bordenet/bloginator/actions/workflows/tests.yml)
[![Lint and type check](https://github.com/bordenet/bloginator/actions/workflows/lint.yml/badge.svg)](https://github.com/bordenet/bloginator/actions/workflows/lint.yml)
![Coverage](https://img.shields.io/badge/coverage-50.79%25-blue)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Content generation from your historical writing using RAG and local/cloud LLMs.

**Version**: 1.0.0
**Python**: 3.10+
**License**: MIT

---

## Overview

Bloginator indexes your writing (blog posts, documents, notes) and generates new content based on your existing corpus:

1. **Extract** text from PDFs, DOCX, Markdown, TXT
2. **Index** content using ChromaDB with semantic embeddings
3. **Search** your corpus using semantic similarity
4. **Generate** outlines and drafts based on retrieved content
5. **Refine** content with iterative feedback
6. **Validate** against blocklist to prevent proprietary content leakage

---

## Quick Start

```bash
# Install
git clone https://github.com/bordenet/bloginator.git
cd bloginator
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# First-time setup (recommended)
bloginator init  # Pre-downloads embedding models (~80MB, 10-60s)

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

### Performance Expectations

**First-time setup:**
- `bloginator init`: 10-60 seconds (downloads embedding model)
- Without `init`, first command will download models automatically

**Typical command times:**
- `extract`: 1-10 seconds per document (depends on size/format)
- `index`: 5-30 seconds (depends on corpus size)
- `search`: <1 second (after first run)
- `outline`: 30-90 seconds (depends on LLM speed)
- `draft`: 1-5 minutes (depends on outline complexity and LLM speed)

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

### Quality Assurance

Bloginator includes an iterative, generational quality assurance system:

**Automated Evaluation:**
- Slop detection (em-dashes, corporate jargon, hedging words, vague language)
- Scoring on 0-5 scale with configurable thresholds
- Violation categorization (critical, high, medium, low)

**Retry Logic:**
- Automatic retry with alternate prompts when quality is below threshold
- Escalating prompt variants (default → strict_no_slop → minimal)
- Configurable retry limits (default: 3 attempts)
- Full attempt history tracking

**Prompt Optimization:**
- Evolutionary optimization framework with automated evaluation
- Round-by-round tracking of quality metrics
- Adaptive strategy based on violation patterns
- Detailed JSON output for analysis

This methodology ensures high-quality output by detecting poor results and automatically retrying with improved prompts until satisfactory content is produced.

---

## Documentation

- [Installation](docs/INSTALLATION.md)
- [User Guide](docs/USER_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Custom LLM Guide](docs/CUSTOM_LLM_GUIDE.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

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

## Code Coverage

Bloginator maintains **50.79% test coverage** with ongoing improvements. The coverage visualization below shows detailed coverage by module:

[![Coverage Grid](https://codecov.io/gh/bordenet/bloginator/graphs/tree.svg)](https://codecov.io/gh/bordenet/bloginator)

**What this means:**
- **Green**: Well-tested code (>80% coverage)
- **Yellow**: Moderate coverage (60-80%)
- **Red**: Needs more tests (<60%)
- **Size**: Larger boxes = more lines of code

Click the image to explore detailed coverage reports on Codecov, including line-by-line coverage, branch coverage, and historical trends.

---

## License

MIT - See LICENSE file.

---

## Monitoring

Bloginator includes built-in monitoring and observability:

```bash
# View metrics
bloginator metrics

# Export as JSON or Prometheus format
bloginator metrics --format json --output metrics.json
bloginator metrics --format prometheus --output metrics.prom
```

**Features:**
- Operation counts and success/failure rates
- Performance metrics (duration, throughput)
- System resource usage (CPU, memory)
- Structured logging with JSON support
- Prometheus integration

See [MONITORING.md](docs/MONITORING.md) for details.

---

## Links

- **Repository**: <https://github.com/bordenet/bloginator>
- **Issues**: <https://github.com/bordenet/bloginator/issues>
- **Author**: Matt Bordenet
