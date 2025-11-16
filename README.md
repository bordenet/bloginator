# Bloginator: Authentic Content Generation from Your Own Corpus

**Status**: Planning Phase
**Version**: 0.1.0
**Python**: 3.10+

---

## Overview

Bloginator is an AI-assisted content generation system that helps engineering leaders create authentic, high-quality documents by leveraging their own historical writing corpus. The system indexes years of prior written material to generate new content that reads in the author's authentic voice—avoiding generic "AI slop" while dramatically reducing document creation time from dozens of hours to minutes.

### The Problem

Engineering leaders accumulate years of written material—blog posts, internal documents, presentations, career development guides—but face two painful choices when creating new content:

1. **Start from scratch**: Fast but loses the nuance and voice developed over years
2. **Manual synthesis**: Search through dozens of old documents, copy-paste relevant sections, stitch together coherent narrative—taking 8-40+ hours per document

Generic AI tools can generate content quickly but produce recognizably artificial writing that lacks personal voice, authenticity, and grounding in actual experience.

### The Solution

Bloginator solves this by:

- **Indexing your historical corpus** (PDFs, DOCX, Markdown, etc.)
- **Semantic search** to find relevant content from your past writing
- **Voice-preserving generation** that maintains your authentic style
- **Proprietary content protection** via blocklist validation
- **Iterative refinement** through natural language feedback
- **Local-first privacy** (no mandatory cloud dependencies)

**Result**: Reduce document creation from 8-40 hours to 30-60 minutes while maintaining authenticity and quality.

---

## Key Features

### Voice Preservation
- Generates content in your authentic voice using only your prior writing
- No generic AI "slop"—all content grounded in your actual corpus
- Voice similarity scoring to ensure consistency

### Proprietary Content Protection
- Blocklist system prevents leakage of company names, trade secrets, NDAs
- Pre-generation validation
- Support for exact match, case-insensitive, and regex patterns

### Flexible Deployment
- **Local Mode**: Runs entirely locally with Ollama/LM Studio (complete privacy)
- **Cloud Mode**: Optional cloud LLM support with cost controls and user consent

### Multi-Format Support
- **Input**: PDF, DOCX, Markdown, TXT, ZIP archives
- **Output**: Markdown, DOCX, HTML, Plain Text

### Intelligent Search
- Semantic search (meaning-based, not just keywords)
- Recency weighting (prefer recent, refined thinking)
- Quality weighting (prefer marked "preferred" content)

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/bordenet/bloginator.git
cd bloginator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Verify installation
bloginator --version
```

### Basic Workflow

```bash
# 1. Extract and index your corpus
bloginator extract ~/my-writing-corpus -o output/extracted --quality preferred
bloginator index output/extracted -o output/index

# 2. Search your corpus
bloginator search output/index "agile transformation" -n 10

# 3. Manage proprietary terms blocklist
bloginator blocklist add "Acme Corp" --category company_name --notes "Former employer NDA"
bloginator blocklist list

# 4. Generate content (coming in Phase 4)
bloginator outline --index output/index --keywords "career,ladder,senior,engineer"
bloginator draft outline.json -o draft.md

# 5. Refine and export (coming in Phase 5)
bloginator refine draft.md "Make tone more optimistic"
bloginator export draft.md --format docx -o final.docx
```

---

## Project Structure

```
bloginator/
├── src/bloginator/          # Source code
│   ├── cli/                 # Command-line interface
│   ├── extraction/          # Document extraction (PDF, DOCX, etc.)
│   ├── indexing/            # Vector indexing with ChromaDB
│   ├── search/              # Semantic search and retrieval
│   ├── generation/          # Content generation engine
│   ├── voice/               # Voice preservation system
│   ├── safety/              # Blocklist and validation
│   └── models/              # Pydantic data models
├── tests/                   # Comprehensive test suite
│   ├── unit/                # Unit tests (60%)
│   ├── integration/         # Integration tests (30%)
│   └── e2e/                 # End-to-end tests (10%)
├── docs/                    # Project documentation
│   ├── PRD-BLOGINATOR-001-Core-System.md
│   ├── DESIGN-SPEC-001-Implementation-Plan.md
│   ├── TESTING-SPEC-003-Quality-Assurance.md
│   ├── ARCHITECTURE-002-Deployment-Modes.md
│   └── CLAUDE_GUIDELINES.md
├── scripts/                 # Build and validation scripts
├── pyproject.toml           # Project configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
└── validate-bloginator.sh   # Full validation script
```

---

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run pre-commit checks manually
pre-commit run --all-files
```

### Quality Standards

This project maintains **strict quality gates** to ensure reliability:

#### Pre-Commit Hooks (Automated)
- ✅ **Black** formatting (line-length=100)
- ✅ **Ruff** linting (all errors fixed)
- ✅ **MyPy** type checking (strict mode)
- ✅ **isort** import sorting (black-compatible)
- ✅ **Gitleaks** secret detection
- ✅ **Fast unit tests** (non-slow tests pass)
- ✅ **Docstring validation** (Google-style)

#### Full Validation

```bash
# Run complete validation suite
./validate-bloginator.sh

# Auto-fix formatting issues
./validate-bloginator.sh --fix

# Skip slow tests (for pre-commit)
./validate-bloginator.sh --skip-slow
```

### Testing

```bash
# Fast unit tests (pre-commit)
pytest tests/unit/ -m "not slow" -q

# All unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Full test suite with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Coverage must be ≥80%
coverage report --fail-under=80
```

### Code Quality Requirements

- **Coverage**: 80%+ line coverage for all modules
- **Linting**: Zero Ruff errors
- **Type Safety**: MyPy strict mode, no `# type: ignore` without justification
- **Formatting**: Black (line-length=100)
- **Docstrings**: All public functions (Google-style)

---

## Implementation Roadmap

### Phase 0: Project Setup ✅ (In Progress)
- Repository structure
- Development environment
- Quality gates and pre-commit hooks

### Phase 1: Extraction & Indexing (Week 1)
- Document extraction (PDF, DOCX, MD, TXT, ZIP)
- Metadata extraction (dates, quality ratings)
- ChromaDB vector indexing
- CLI: `extract`, `index`

### Phase 2: Search & Retrieval (Week 2)
- Semantic search
- Recency and quality weighting
- CLI: `search`

### Phase 3: Blocklist & Safety (Week 2)
- Blocklist validation system
- Pattern matching (exact, case-insensitive, regex)
- CLI: `blocklist add/list/remove/validate`

### Phase 4: Content Generation (Week 3)
- Outline generation from keywords/themes
- Draft generation with voice preservation
- Source attribution and citations
- CLI: `outline`, `draft`

### Phase 5: Refinement & Iteration (Week 4)
- Iterative refinement from natural language feedback
- Diff tracking and version management
- CLI: `refine`, `diff`, `revert`

### Phase 6: Web UI (Weeks 5-6)
- Interactive web interface
- All workflows accessible via browser
- Responsive design

### Phase 7: Polish & Production (Weeks 7-8)
- External source support (e.g., reference books)
- Template library (10+ document types)
- Comprehensive documentation
- Performance optimization

---

## Architecture

### Technology Stack

**Core**:
- Python 3.10+
- ChromaDB (vector store)
- sentence-transformers (embeddings: all-MiniLM-L6-v2)
- Ollama (local LLM inference)
- Pydantic (data validation)
- Click (CLI framework)
- Rich (terminal UI)

**Document Processing**:
- PyMuPDF (PDF extraction)
- python-docx (DOCX extraction)
- Markdown (native parsing)

**Quality Tools**:
- pytest (testing)
- black (formatting)
- ruff (linting)
- mypy (type checking)
- pre-commit (git hooks)

### Deployment Modes

1. **Local Mode** (Default):
   - Runs entirely offline
   - Ollama or LM Studio for LLM
   - Complete privacy and data control
   - No API costs

2. **Cloud Mode** (Optional):
   - Cloud LLM support (Claude, GPT-4, etc.)
   - Cost tracking and limits
   - User consent required
   - Hybrid: local indexing, cloud generation

---

## Success Metrics

### Quality
- **Voice Authenticity**: 90%+ of readers can't distinguish generated from manually-written content
- **Factual Accuracy**: 98%+ of statements grounded in prior writing
- **Blocklist Enforcement**: 100% catch rate for exact matches
- **Completeness**: All outlined sections generated with appropriate depth

### Performance
- **Index Building**: <30 minutes for 500+ documents
- **Draft Generation**: <5 minutes from outline
- **Search**: <3 seconds
- **Refinement**: <2 minutes per iteration

### User Satisfaction
- **Time Savings**: 85%+ reduction vs. manual creation
- **Quality Rating**: 80%+ of drafts "good enough to edit"
- **Iteration Count**: <5 refinements to "ready to publish"

---

## Documentation

### User Documentation
- [Installation Guide](docs/INSTALLATION.md) (coming soon)
- [User Guide](docs/USER_GUIDE.md) (coming soon)
- [Tutorials](docs/TUTORIALS.md) (coming soon)
- [FAQ](docs/FAQ.md) (coming soon)

### Developer Documentation
- [PRD: Core System](docs/PRD-BLOGINATOR-001-Core-System.md)
- [Design Spec: Implementation Plan](docs/DESIGN-SPEC-001-Implementation-Plan.md)
- [Testing Spec: Quality Assurance](docs/TESTING-SPEC-003-Quality-Assurance.md)
- [Architecture: Deployment Modes](docs/ARCHITECTURE-002-Deployment-Modes.md)
- [Claude Guidelines](docs/CLAUDE_GUIDELINES.md)

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run validation: `./validate-bloginator.sh`
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Review Criteria

- ✅ All tests pass
- ✅ Coverage ≥80%
- ✅ Pre-commit hooks pass
- ✅ Documentation updated
- ✅ No proprietary content in examples

---

## Philosophy

### Pragmatic Minimalism

Bloginator follows these principles (see [CLAUDE_GUIDELINES.md](docs/CLAUDE_GUIDELINES.md)):

1. **Make minimal, necessary changes only** - No speculative improvements
2. **If it's not tested, it's broken** - 80%+ coverage required
3. **Voice preservation is paramount** - Ground all generation in corpus
4. **Privacy by default** - Local-first, no mandatory cloud calls
5. **Avoid over-engineering** - Start simple, add complexity only when needed

### Anti-Patterns We Avoid

- ❌ Generic AI content without corpus grounding
- ❌ Premature optimization and abstraction
- ❌ Skipping tests to "move faster"
- ❌ Committing without quality validation
- ❌ Adding cloud dependencies without user consent

---

## License

[LICENSE](LICENSE) - See LICENSE file for details

---

## Contact

**Project Owner**: Matt Bordenet
**Repository**: https://github.com/bordenet/bloginator
**Issues**: https://github.com/bordenet/bloginator/issues

---

## Acknowledgments

- Films Not Made project for reusable patterns
- RAG community for best practices
- Local LLM community (Ollama, LM Studio)
- ChromaDB for excellent local vector store

---

**Remember**: Bloginator's value is authentic voice preservation and proprietary content protection. Fast, working code that achieves these goals beats elegant, complex code that doesn't.

**Status**: Currently in Phase 0 (Project Setup). See [DESIGN-SPEC-001](docs/DESIGN-SPEC-001-Implementation-Plan.md) for detailed implementation plan.
