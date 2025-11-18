# Claude AI Development Notes

Essential guidance for AI assistants working on Bloginator.

---

## Rule #1: Test-First Development

**Fix all broken tests before writing new code.**

### Workflow
1. Run `pytest tests/ -v` before starting work
2. Fix any failures immediately
3. Only then proceed with new features
4. Verify tests still pass after changes

### Current Status
- **355 tests passing** (100% of runnable tests)
- **6 tests skipped** (optional fastapi dependency)
- Last verified: 2025-11-18

Update this section after running tests in new sessions.

---

## Rule #2: Professional Documentation

**Be factual. No celebratory or marketing language.**

### Avoid
- "Production-ready" / "Production-grade" (naive)
- "Amazing" / "Awesome" / "Incredible"
- Excessive checkmarks/emojis
- "All phases complete!"
- Unsubstantiated quality claims

### Use Instead
- "Tests passing: 355/361"
- "Feature implemented"
- "Supports X, Y, Z"
- Clear capability statements
- Honest limitations

---

## Rule #3: Code Quality Standards

### Linting (Must Pass Before Commit)
```bash
black src/ tests/              # Format (line-length=100)
ruff check src/ tests/         # Lint (zero errors)
isort src/ tests/              # Sort imports
mypy src/                      # Type check (strict)
```

### File Size
- **Target**: <400 lines per file
- **Current violations**: 2 files (417, 415 lines - acceptable)
- Refactor when approaching limit

### Type Hints
- Required for all public functions
- Use `| None` not `Optional[]`
- Use `list[str]` not `List[str]`
- Strict mode except tests

---

## Rule #4: Security Requirements

### Never Commit
- .env files
- API keys or credentials
- Private keys
- Personal data

### Dependency Security
```toml
cryptography>=43.0.1  # CVE fixes
setuptools>=78.1.1    # RCE fix
pip>=25.3             # Path traversal fix
```

### Before Public Release
- Run `pip-audit` to scan for CVEs
- Update vulnerable dependencies
- Enable Dependabot on GitHub
- Add SECURITY.md

---

## Rule #5: LLM Provider Support

**Support local and cloud LLMs equally.**

### Supported Providers
1. **Ollama** - Local (default)
   - Models: mixtral:8x7b, llama3:8b
   - URL: http://localhost:11434

2. **Custom/OpenAI-Compatible** - Cloud/self-hosted
   - OpenAI, Anthropic, LM Studio, vLLM

3. **Mock** - Testing only

### Configuration
```bash
# .env
BLOGINATOR_LLM_PROVIDER=ollama
BLOGINATOR_LLM_MODEL=mixtral:8x7b
BLOGINATOR_LLM_BASE_URL=http://localhost:11434
```

Factory pattern (`create_llm_client()`) ensures provider-agnostic code.

---

## Rule #6: Commit Message Standards

### Format
```
<type>: <description>

[optional body]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Restructuring
- `test`: Tests
- `chore`: Maintenance

### Examples
```
feat: Add parallel extraction with --workers flag
style: Fix import sorting with isort across codebase
fix: Update cryptography to 43.0.1 for CVE fixes
docs: Remove celebratory language from README
```

---

## Rule #7: README.md Requirements

### Must Include
- What it does (clear list)
- What it does NOT do (limitations)
- Installation steps
- Quick start examples
- Project structure
- Technology stack

### Must NOT Include
- Celebratory language
- "Production-ready" claims
- Vague features
- Marketing hype

---

## Common Tasks

### Run Tests
```bash
pytest tests/ -v                   # All tests
pytest tests/unit/ -v              # Unit only
pytest -m "not slow" -v            # Fast only
pytest --cov=src --cov-report=html # Coverage
```

### Check Quality
```bash
pre-commit run --all-files         # All checks
black --check src/ tests/          # Check format
ruff check src/ tests/             # Lint
isort --check-only src/ tests/     # Check imports
```

### Security Scan
```bash
pip-audit                          # Check CVEs
safety check                       # Alternative scanner
```

---

## Project Structure

```
bloginator/
├── src/bloginator/
│   ├── cli/                # 12 CLI commands
│   ├── extraction/         # Document extraction
│   ├── indexing/           # ChromaDB integration
│   ├── search/             # Semantic search
│   ├── generation/         # LLM clients
│   ├── safety/             # Blocklist
│   ├── ui/                 # Streamlit (7 pages)
│   └── web/                # FastAPI (experimental)
├── tests/                  # 355 tests
├── docs/                   # Documentation
└── pyproject.toml          # Dependencies
```

---

## Known Limitations

- No multi-format export rendering (claimed but not implemented)
- No batch processing
- No advanced analytics
- No collaborative features
- No plugin system
- Test coverage % not measured
- 2 files exceed 400-line guideline

See FUTURE_WORK.md for planned enhancements.

---

## Dependencies

### Core
- Python 3.10+
- ChromaDB (vector store)
- sentence-transformers (embeddings)
- Ollama (default LLM)
- Pydantic v2
- Click (CLI)

### Security
- cryptography>=43.0.1 (required)
- Latest pip and setuptools

### Optional
- fastapi (web UI)
- streamlit (alternative UI)

---

## Troubleshooting

### Tests Fail
1. Check Python version (3.10-3.13)
2. Install: `pip install -e ".[dev]"`
3. Clear cache: `rm -rf .bloginator/chroma`
4. Re-run tests

### Import Errors
- Install package: `pip install -e .`
- Activate venv
- Check PYTHONPATH

### LLM Errors
- Start Ollama: `ollama serve`
- Check .env configuration
- Test with mock: `BLOGINATOR_LLM_PROVIDER=mock`

---

## Final Notes

This document defines development standards. When in doubt:
1. Check tests first
2. Be professional and factual
3. Support all LLM providers
4. Keep code clean
5. Document honestly

Update as standards evolve.
