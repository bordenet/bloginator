# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-20

### Added
- Complete CLI interface with 12 commands for document workflows
- Streamlit web UI with 7 pages for interactive corpus management
- FastAPI REST API (experimental)
- Document extraction support for PDF, DOCX, Markdown, TXT, and ZIP files
- ChromaDB-based vector indexing with sentence-transformers
- Semantic search with quality and recency weighting
- RAG-based outline and draft generation
- Iterative refinement with version management
- Blocklist validation (exact, case-insensitive, regex patterns)
- Template system with 12 pre-built document templates
- Support for Ollama (local), OpenAI, Anthropic, and custom LLM providers
- Comprehensive test suite (355 tests: unit, integration, E2E, benchmarks)
- Type hints throughout codebase with MyPy strict mode
- Pre-commit hooks for code quality (Black, Ruff, MyPy, Gitleaks)
- Parallel processing for extraction and indexing
- Voice similarity scoring
- Export functionality (Markdown, DOCX, HTML, PDF, TXT)

### Documentation
- User Guide with complete workflow documentation
- Developer Guide with architecture and contribution guidelines
- Installation Guide for macOS, Linux, and Windows
- Custom LLM Guide for provider configuration
- Architecture documentation for deployment modes
- Testing specification with quality assurance guidelines

### Quality
- 37.58% overall test coverage (85%+ on core modules)
- Black code formatting (100 char line length)
- Ruff linting with comprehensive rule set
- MyPy strict type checking
- Bandit security scanning
- Gitleaks secret detection
- Pre-commit hooks for automated quality gates

## [Unreleased]

### Planned
- Increase test coverage to 85% overall
- GitHub Actions CI/CD pipeline
- Docker containerization
- Additional export formats
- Enhanced voice analysis metrics
- Multi-language support for corpus documents

