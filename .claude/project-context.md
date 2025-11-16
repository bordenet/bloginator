# Bloginator Project Context

## Overview
Bloginator is an AI-assisted content generation system that helps engineering leaders create authentic, high-quality documents by leveraging their own historical writing corpus.

## Core Value Propositions
1. **Voice Preservation**: Generate content in author's authentic voice (not generic AI slop)
2. **Corpus-Grounded**: All content grounded in actual prior writing
3. **Privacy First**: Local-first architecture, no mandatory cloud dependencies
4. **Proprietary Content Protection**: Blocklist system prevents NDA violations

## Technology Stack
- **Language**: Python 3.10+
- **CLI Framework**: Click
- **Vector Store**: ChromaDB
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (local) with optional cloud support
- **Testing**: pytest with 80%+ coverage requirement
- **Quality Tools**: black, ruff, mypy, isort, pre-commit

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
├── tests/                   # Test suite (60% unit, 30% integration, 10% E2E)
└── docs/                    # Project documentation
```

## Implementation Phases
- **Phase 0** (Current): Project setup, quality gates
- **Phase 1**: Extraction & indexing
- **Phase 2**: Search & retrieval
- **Phase 3**: Blocklist & safety
- **Phase 4**: Content generation
- **Phase 5**: Refinement & iteration
- **Phase 6**: Web UI
- **Phase 7**: Polish & production

## Key Design Principles (from CLAUDE_GUIDELINES.md)
1. **Pragmatic Minimalism**: Make minimal, necessary changes only
2. **Test-Driven**: 80%+ coverage required for all modules
3. **Voice Preservation is Paramount**: Ground all generation in corpus
4. **No Over-Engineering**: Start simple, add complexity only when needed
5. **Privacy by Default**: No mandatory cloud APIs

## Quality Gates (MANDATORY)
Every commit must pass:
- ✅ Black formatting (line-length=100)
- ✅ Ruff linting (all errors fixed)
- ✅ MyPy type checking (strict mode)
- ✅ isort import sorting
- ✅ Gitleaks secret detection
- ✅ Fast unit tests
- ✅ Docstring validation (Google-style)

## Success Metrics
- **Voice Authenticity**: 90%+ indistinguishable from manually-written
- **Factual Accuracy**: 98%+ grounded in corpus
- **Blocklist Enforcement**: 100% catch rate for exact matches
- **Performance**: <30min index 500 docs, <5min generate draft, <3s search
- **Time Savings**: 85%+ reduction vs. manual (8-40hrs → 30-60min)

## Current Status
- Phase 0 (Project Setup): In Progress
- Foundational docs complete
- Quality infrastructure being established
