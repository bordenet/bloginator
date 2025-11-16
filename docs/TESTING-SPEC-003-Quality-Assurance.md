# TESTING-SPEC-003: Comprehensive Quality Assurance & Testing Strategy

**Status**: Planning Phase
**Created**: 2025-11-16
**Last Updated**: 2025-11-16
**Related**: PRD-BLOGINATOR-001, DESIGN-SPEC-001, ARCHITECTURE-002

---

## Overview

This document defines the complete testing strategy, quality gates, and validation requirements for Bloginator. Every implementation phase must meet these standards before being considered complete.

**Quality Philosophy**: "If it's not tested, it's broken. If it's not validated, it's not shipped."

---

## Testing Pyramid

```
                    ▲
                   / \
                  /   \
                 / E2E \          10% - Full system workflows
                /_______\
               /         \
              /Integration\       30% - Component interactions
             /_____________\
            /               \
           /   Unit Tests    \    60% - Individual functions/classes
          /_________________  \
```

**Target Distribution**:
- **60% Unit Tests**: Fast, isolated, comprehensive coverage
- **30% Integration Tests**: Component interactions, database operations
- **10% E2E Tests**: Full workflows, user scenarios

---

## Quality Gates (Required for Every Commit)

### Pre-Commit Hooks (Automated)

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  # Security: Detect secrets
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  # Code formatting
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        args: [--line-length=100]

  # Linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]

  # File checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: [--maxkb=5000]
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: detect-private-key

  # Import sorting
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black, --line-length=100]

  # Docstring validation
  - repo: https://github.com/PyCQA/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
        args: [--convention=google]

  # Fast quality gate (runs on all files)
  - repo: local
    hooks:
      - id: fast-quality-gate
        name: Fast Quality Gate
        entry: ./scripts/fast-quality-gate.sh
        language: system
        pass_filenames: false
        always_run: true
```

### Fast Quality Gate Script

**File**: `scripts/fast-quality-gate.sh`
```bash
#!/bin/bash
set -e

echo "🚀 Running Fast Quality Gate..."

# 1. Format check
echo "1/5 Checking code formatting (black)..."
black --check --line-length=100 src/ tests/ || {
    echo "❌ Code not formatted. Run: black --line-length=100 src/ tests/"
    exit 1
}

# 2. Linting
echo "2/5 Linting (ruff)..."
ruff check src/ tests/ || {
    echo "❌ Linting failed. Run: ruff check --fix src/ tests/"
    exit 1
}

# 3. Type checking
echo "3/5 Type checking (mypy)..."
mypy src/ --strict --ignore-missing-imports || {
    echo "❌ Type checking failed"
    exit 1
}

# 4. Import sorting
echo "4/5 Checking import sorting (isort)..."
isort --check-only --profile=black --line-length=100 src/ tests/ || {
    echo "❌ Imports not sorted. Run: isort --profile=black --line-length=100 src/ tests/"
    exit 1
}

# 5. Unit tests (fast subset only)
echo "5/5 Running fast unit tests..."
pytest tests/ -m "not slow" --tb=short -q || {
    echo "❌ Fast tests failed"
    exit 1
}

echo "✅ Fast Quality Gate passed!"
```

### Full Validation Script

**File**: `validate-bloginator.sh`
```bash
#!/bin/bash
set -e

SKIP_SLOW=false
FIX=false
PRE_COMMIT_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-slow)
            SKIP_SLOW=true
            shift
            ;;
        --fix)
            FIX=true
            shift
            ;;
        --pre-commit)
            PRE_COMMIT_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "╔════════════════════════════════════════╗"
echo "║   Bloginator Validation Suite          ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Activate venv if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    else
        echo "⚠️  Virtual environment not found. Run: python3 -m venv venv"
        exit 1
    fi
fi

# 1. Pre-commit hooks
if [[ "$PRE_COMMIT_ONLY" == "true" ]]; then
    echo "Running pre-commit hooks only..."
    pre-commit run --all-files
    exit 0
fi

# 2. Code formatting
echo "═══ 1/8 Code Formatting (black) ═══"
if [[ "$FIX" == "true" ]]; then
    black --line-length=100 src/ tests/
else
    black --check --line-length=100 src/ tests/
fi
echo "✅ Formatting OK"
echo ""

# 3. Linting
echo "═══ 2/8 Linting (ruff) ═══"
if [[ "$FIX" == "true" ]]; then
    ruff check --fix src/ tests/
else
    ruff check src/ tests/
fi
echo "✅ Linting OK"
echo ""

# 4. Type checking
echo "═══ 3/8 Type Checking (mypy) ═══"
mypy src/ --strict --ignore-missing-imports
echo "✅ Type checking OK"
echo ""

# 5. Import sorting
echo "═══ 4/8 Import Sorting (isort) ═══"
if [[ "$FIX" == "true" ]]; then
    isort --profile=black --line-length=100 src/ tests/
else
    isort --check-only --profile=black --line-length=100 src/ tests/
fi
echo "✅ Import sorting OK"
echo ""

# 6. Security scanning
echo "═══ 5/8 Security Scanning (gitleaks) ═══"
if command -v gitleaks &> /dev/null; then
    gitleaks detect --no-git --source . --verbose
    echo "✅ No secrets detected"
else
    echo "⚠️  gitleaks not installed, skipping"
fi
echo ""

# 7. Unit tests
echo "═══ 6/8 Unit Tests (pytest) ═══"
if [[ "$SKIP_SLOW" == "true" ]]; then
    pytest tests/ -m "not slow" -v --cov=src --cov-report=term-missing --cov-report=html
else
    pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
fi
echo "✅ Tests OK"
echo ""

# 8. Coverage check
echo "═══ 7/8 Coverage Check ═══"
coverage report --fail-under=80
echo "✅ Coverage ≥80%"
echo ""

# 9. Documentation check
echo "═══ 8/8 Documentation Check ═══"
# Check that all public functions have docstrings
python -c "
import ast
import sys
from pathlib import Path

def check_docstrings(filepath):
    code = filepath.read_text()
    tree = ast.parse(code)
    errors = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):  # Public
                if not ast.get_docstring(node):
                    errors.append(f'{filepath}:{node.lineno} - {node.name} missing docstring')

    return errors

all_errors = []
for f in Path('src').rglob('*.py'):
    all_errors.extend(check_docstrings(f))

if all_errors:
    print('❌ Missing docstrings:')
    for e in all_errors[:10]:  # Show first 10
        print(f'  {e}')
    sys.exit(1)
"
echo "✅ Documentation OK"
echo ""

echo "╔════════════════════════════════════════╗"
echo "║   ✅ ALL VALIDATION CHECKS PASSED      ║"
echo "╚════════════════════════════════════════╝"
```

**Usage**:
```bash
# Full validation (all tests)
./validate-bloginator.sh

# Skip slow tests (for pre-commit)
./validate-bloginator.sh --skip-slow

# Auto-fix formatting/linting issues
./validate-bloginator.sh --fix

# Only run pre-commit hooks
./validate-bloginator.sh --pre-commit
```

---

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests (60%)
│   ├── extraction/
│   │   ├── test_pdf_extractor.py
│   │   ├── test_docx_extractor.py
│   │   └── test_metadata_extraction.py
│   ├── indexing/
│   │   ├── test_embeddings.py
│   │   ├── test_vector_store.py
│   │   └── test_chunking.py
│   ├── search/
│   │   ├── test_semantic_search.py
│   │   └── test_weighting.py
│   ├── safety/
│   │   ├── test_blocklist.py
│   │   └── test_validation.py
│   ├── llm/
│   │   ├── test_cloud_llm.py       # Cloud mode
│   │   ├── test_local_llm.py       # Local mode
│   │   └── test_llm_factory.py     # Factory pattern
│   ├── generation/
│   │   ├── test_outline.py
│   │   ├── test_draft.py
│   │   ├── test_refinement.py
│   │   └── test_prompts.py
│   └── models/
│       ├── test_document.py
│       ├── test_blocklist.py
│       └── test_chunk.py
├── integration/                   # Integration tests (30%)
│   ├── test_extraction_pipeline.py
│   ├── test_indexing_pipeline.py
│   ├── test_search_pipeline.py
│   ├── test_generation_pipeline_cloud.py  # Cloud mode
│   ├── test_generation_pipeline_local.py  # Local mode
│   └── test_end_to_end.py
├── e2e/                           # End-to-end tests (10%)
│   ├── test_full_workflow_cloud.py
│   ├── test_full_workflow_local.py
│   └── test_cli_commands.py
├── fixtures/                      # Test data
│   ├── documents/
│   │   ├── sample_blog_post.md
│   │   ├── sample_document.pdf
│   │   └── sample_document.docx
│   ├── blocklists/
│   │   └── test_blocklist.json
│   └── expected_outputs/
│       ├── sample_outline.json
│       └── sample_draft.md
└── performance/                   # Performance benchmarks
    ├── test_indexing_speed.py
    ├── test_search_latency.py
    └── test_generation_latency.py
```

---

## Unit Test Standards

### Requirements

1. **Coverage**: 80%+ line coverage for all modules
2. **Speed**: Unit tests must run in <0.1s each
3. **Isolation**: No external dependencies (mock LLMs, databases)
4. **Determinism**: Same input → same output (no flaky tests)
5. **Clarity**: Test name explains what's being tested

### Example: Good Unit Test

```python
# tests/unit/safety/test_blocklist.py
import pytest
from bloginator.models.blocklist import BlocklistEntry, BlocklistPatternType
from bloginator.safety.blocklist import BlocklistManager
from pathlib import Path

class TestBlocklistEntry:
    """Test BlocklistEntry model and matching logic."""

    def test_exact_match_case_sensitive(self):
        """Exact match should be case-sensitive."""
        entry = BlocklistEntry(
            id="1",
            pattern="Acme Corp",
            pattern_type=BlocklistPatternType.EXACT,
        )
        assert entry.matches("I worked at Acme Corp") == ["Acme Corp"]
        assert entry.matches("I worked at acme corp") == []  # Different case

    def test_case_insensitive_match(self):
        """Case-insensitive match should find all variations."""
        entry = BlocklistEntry(
            id="2",
            pattern="Acme",
            pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
        )
        matches = entry.matches("ACME and Acme and acme")
        assert len(matches) == 3

    def test_regex_match(self):
        """Regex pattern should match correctly."""
        entry = BlocklistEntry(
            id="3",
            pattern=r"Project \w+",
            pattern_type=BlocklistPatternType.REGEX,
        )
        assert entry.matches("Project Falcon was secret") == ["Project Falcon"]
        assert entry.matches("No project here") == []

    @pytest.mark.parametrize("pattern,text,expected", [
        ("test", "this is a test", ["test"]),
        ("test", "TEST", []),  # Exact is case-sensitive
        ("", "anything", []),  # Empty pattern matches nothing
    ])
    def test_edge_cases(self, pattern, text, expected):
        """Test edge cases for pattern matching."""
        entry = BlocklistEntry(
            id="4",
            pattern=pattern,
            pattern_type=BlocklistPatternType.EXACT,
        )
        assert entry.matches(text) == expected


class TestBlocklistManager:
    """Test BlocklistManager operations."""

    def test_add_and_save(self, tmp_path):
        """Adding entry should persist to file."""
        blocklist_file = tmp_path / "blocklist.json"
        manager = BlocklistManager(blocklist_file)

        entry = BlocklistEntry(
            id="1",
            pattern="TestCorp",
            pattern_type=BlocklistPatternType.EXACT,
        )
        manager.add_entry(entry)

        # Verify saved
        assert blocklist_file.exists()

        # Load in new manager instance
        manager2 = BlocklistManager(blocklist_file)
        assert len(manager2.entries) == 1
        assert manager2.entries[0].pattern == "TestCorp"

    def test_validate_text_clean(self, tmp_path):
        """Clean text should pass validation."""
        manager = BlocklistManager(tmp_path / "blocklist.json")
        manager.add_entry(BlocklistEntry(
            id="1",
            pattern="BadWord",
            pattern_type=BlocklistPatternType.EXACT,
        ))

        result = manager.validate_text("This is clean text")
        assert result['is_valid'] is True
        assert len(result['violations']) == 0

    def test_validate_text_violation(self, tmp_path):
        """Text with blocklisted term should fail validation."""
        manager = BlocklistManager(tmp_path / "blocklist.json")
        manager.add_entry(BlocklistEntry(
            id="1",
            pattern="SecretProject",
            pattern_type=BlocklistPatternType.EXACT,
        ))

        result = manager.validate_text("I worked on SecretProject")
        assert result['is_valid'] is False
        assert len(result['violations']) == 1
        assert result['violations'][0]['pattern'] == "SecretProject"

    def test_remove_entry(self, tmp_path):
        """Removing entry should work."""
        manager = BlocklistManager(tmp_path / "blocklist.json")
        entry = BlocklistEntry(id="1", pattern="Test", pattern_type=BlocklistPatternType.EXACT)
        manager.add_entry(entry)
        assert len(manager.entries) == 1

        manager.remove_entry("1")
        assert len(manager.entries) == 0
```

**Markers**:
```python
# Mark slow tests
@pytest.mark.slow
def test_large_corpus_indexing():
    # Takes >5 seconds
    pass

# Mark tests requiring external services
@pytest.mark.requires_ollama
def test_local_llm_generation():
    # Requires Ollama running
    pass

@pytest.mark.requires_api_key
def test_cloud_llm_generation():
    # Requires API key
    pass
```

---

## Integration Test Standards

### Requirements

1. **Coverage**: Critical integration points tested
2. **Speed**: <5s per test
3. **Isolation**: Use test databases, mock expensive operations
4. **Cleanup**: Restore state after test

### Example: Integration Test

```python
# tests/integration/test_generation_pipeline_cloud.py
import pytest
import os
from pathlib import Path
from bloginator.llm import create_llm_provider
from bloginator.generation.outline import OutlineGenerator
from bloginator.generation.draft import DraftGenerator
from bloginator.search import CorpusSearcher

@pytest.mark.requires_api_key
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestCloudGenerationPipeline:
    """Test full generation pipeline with Claude API."""

    @pytest.fixture
    def llm_provider(self):
        """Create Claude LLM provider."""
        return create_llm_provider(
            mode="cloud",
            cloud_provider="claude",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-haiku-20240307",  # Use cheaper model for tests
        )

    @pytest.fixture
    def test_index(self, tmp_path):
        """Create test index with sample documents."""
        # Setup test corpus
        # Index documents
        # Return searcher
        pass

    def test_outline_to_draft_workflow(self, llm_provider, test_index):
        """Test complete workflow: outline → draft."""
        # 1. Generate outline
        outline_gen = OutlineGenerator(llm_provider, test_index)
        outline = outline_gen.generate(
            keywords=["agile", "transformation"],
            thesis="Agile transformation requires cultural change"
        )

        assert outline is not None
        assert len(outline['sections']) > 0

        # 2. Generate draft from outline
        draft_gen = DraftGenerator(llm_provider, test_index)
        draft = draft_gen.generate(outline)

        assert draft is not None
        assert len(draft['content']) > 500  # Reasonable length
        assert draft['voice_similarity_score'] > 0.6  # Minimum quality

        # 3. Verify cost tracking
        assert draft['generation_cost'] > 0
        assert draft['generation_cost'] < 1.00  # Should be cheap for test

    def test_cost_limit_enforcement(self, llm_provider, test_index):
        """Test that cost limits are enforced."""
        from bloginator.generation.cost_control import CostController

        cost_controller = CostController(llm_provider, limit_usd=0.01)  # Very low limit

        outline_gen = OutlineGenerator(llm_provider, test_index, cost_controller)

        # First generation should work
        outline1 = outline_gen.generate(
            keywords=["test"],
            thesis="test"
        )
        assert outline1 is not None

        # Second generation should hit limit
        with pytest.raises(CostLimitExceeded):
            outline_gen.generate(
                keywords=["another", "test"],
                thesis="another test"
            )
```

---

## E2E Test Standards

### Requirements

1. **Coverage**: Critical user workflows
2. **Speed**: <30s per test
3. **Realistic**: Use actual tools (CLI, API)
4. **Isolated**: Clean environment per test

### Example: E2E Test

```python
# tests/e2e/test_full_workflow_cloud.py
import pytest
import subprocess
import os
from pathlib import Path

@pytest.mark.e2e
@pytest.mark.requires_api_key
class TestFullCloudWorkflow:
    """Test complete user workflow with cloud mode."""

    @pytest.fixture
    def workspace(self, tmp_path):
        """Create isolated workspace."""
        workspace = tmp_path / "workspace"
        workspace.mkdir()

        # Copy test corpus
        corpus_dir = workspace / "corpus"
        corpus_dir.mkdir()
        # ... copy test files ...

        return workspace

    def test_complete_document_creation(self, workspace):
        """Test: upload corpus → extract → index → search → generate → refine → export."""

        # 1. Extract documents
        result = subprocess.run([
            "bloginator", "extract",
            str(workspace / "corpus"),
            "-o", str(workspace / "extracted"),
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Extracted" in result.stdout

        # 2. Index documents
        result = subprocess.run([
            "bloginator", "index",
            str(workspace / "extracted"),
            "-o", str(workspace / "index"),
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "Indexed" in result.stdout

        # 3. Search
        result = subprocess.run([
            "bloginator", "search",
            str(workspace / "index"),
            "agile transformation",
            "-n", "5",
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert len(result.stdout) > 0

        # 4. Generate outline (cloud mode)
        result = subprocess.run([
            "bloginator", "outline",
            "--mode", "cloud",
            "--cloud-provider", "claude",
            "--index", str(workspace / "index"),
            "--keywords", "agile,culture,transformation",
            "--thesis", "Agile requires cultural change",
            "-o", str(workspace / "outline.json"),
        ], env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")},
        capture_output=True, text=True)
        assert result.returncode == 0
        assert (workspace / "outline.json").exists()

        # 5. Generate draft
        result = subprocess.run([
            "bloginator", "draft",
            "--mode", "cloud",
            "--cloud-provider", "claude",
            str(workspace / "outline.json"),
            "-o", str(workspace / "draft.md"),
        ], env={**os.environ, "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")},
        capture_output=True, text=True)
        assert result.returncode == 0
        assert (workspace / "draft.md").exists()

        draft_content = (workspace / "draft.md").read_text()
        assert len(draft_content) > 1000  # Substantial content

        # 6. Validate against blocklist (should pass)
        result = subprocess.run([
            "bloginator", "blocklist", "validate",
            str(workspace / "draft.md"),
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert "No blocklist violations" in result.stdout

        # 7. Export to DOCX
        result = subprocess.run([
            "bloginator", "export",
            str(workspace / "draft.md"),
            "--format", "docx",
            "-o", str(workspace / "final.docx"),
        ], capture_output=True, text=True)
        assert result.returncode == 0
        assert (workspace / "final.docx").exists()
```

---

## Performance Benchmarks

### Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Extract 100 documents | <60s | Time to completion |
| Index 500 documents | <30min | Time to completion |
| Index throughput | >200 chunks/sec | Chunks indexed per second |
| Semantic search | <3s | Query to results |
| Outline generation (cloud) | <10s | First outline |
| Draft generation (cloud) | <60s | Full draft |
| Draft generation (local) | <120s | Full draft (llama3:8b) |
| Voice similarity scoring | <5s | Per draft |
| Blocklist validation | <1s | Per document |

### Benchmark Tests

```python
# tests/performance/test_indexing_speed.py
import pytest
import time
from pathlib import Path
from bloginator.indexing import CorpusIndexer

@pytest.mark.performance
@pytest.mark.slow
class TestIndexingPerformance:
    """Benchmark indexing performance."""

    def test_index_500_documents(self, large_test_corpus):
        """Index 500 documents within 30 minutes."""
        indexer = CorpusIndexer(Path("test_output"))

        start = time.time()
        indexer.index_corpus(large_test_corpus)
        elapsed = time.time() - start

        assert elapsed < 1800  # 30 minutes
        print(f"\n✓ Indexed 500 documents in {elapsed:.1f}s")

        # Calculate throughput
        total_chunks = indexer.get_total_chunks()
        throughput = total_chunks / elapsed
        assert throughput > 200  # >200 chunks/sec
        print(f"✓ Throughput: {throughput:.0f} chunks/sec")
```

---

## Test Coverage Requirements by Phase

### Phase 0: Project Setup
- ✅ Package installs correctly
- ✅ CLI commands exist and show help
- ✅ Pre-commit hooks install
- ✅ Validation script runs

**Coverage**: N/A (infrastructure)

### Phase 1: Extraction & Indexing
- ✅ All extractors (PDF, DOCX, MD, TXT, ZIP)
- ✅ Metadata extraction
- ✅ Chunking strategies
- ✅ Vector store operations
- ✅ ChromaDB persistence

**Coverage**: 80%+ for extraction, indexing, models

### Phase 2: Search & Retrieval
- ✅ Semantic search
- ✅ Recency weighting
- ✅ Quality weighting
- ✅ Combined scoring
- ✅ Search CLI

**Coverage**: 80%+ for search module

### Phase 3: Blocklist & Safety
- ✅ All pattern types (exact, case-insensitive, regex)
- ✅ BlocklistManager operations
- ✅ Validation logic
- ✅ CLI operations

**Coverage**: 90%+ for safety module (critical path)

### Phase 4: Content Generation
- ✅ Outline generation (both modes)
- ✅ Draft generation (both modes)
- ✅ Voice similarity scoring
- ✅ Cost estimation (cloud mode)
- ✅ Source attribution

**Coverage**: 80%+ for generation module

### Phase 5: Refinement & Iteration
- ✅ Refinement engine
- ✅ Version management
- ✅ Diff computation
- ✅ Revert functionality

**Coverage**: 80%+ for refinement module

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/ci.yml`
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('pyproject.toml') }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run pre-commit hooks
        run: pre-commit run --all-files

      - name: Run fast quality gate
        run: ./scripts/fast-quality-gate.sh

  unit-tests:
    runs-on: ubuntu-latest
    needs: quality-gate
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=src --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,local]"

      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.com/install.sh | sh
          ollama serve &
          sleep 5
          ollama pull llama3:8b

      - name: Run integration tests (local mode)
        run: |
          pytest tests/integration/ -v -m "not requires_api_key"

  cloud-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.ref == 'refs/heads/main'  # Only on main branch

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,cloud]"

      - name: Run cloud integration tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest tests/integration/ -v -m "requires_api_key" --maxfail=3

      - name: Check test costs
        run: |
          # Verify test costs stay under $1
          python scripts/check_test_costs.py

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e ".[dev,local,cloud]"

      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.com/install.sh | sh
          ollama serve &
          sleep 5
          ollama pull llama3:8b

      - name: Run E2E tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest tests/e2e/ -v

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2

      - name: Run Bandit (security linter)
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Upload Bandit report
        uses: actions/upload-artifact@v3
        with:
          name: bandit-report
          path: bandit-report.json
```

---

## Cost Control Tests (Cloud Mode)

```python
# tests/unit/generation/test_cost_control.py
import pytest
from bloginator.generation.cost_control import CostController
from bloginator.llm import create_llm_provider

class TestCostControl:
    """Test cost estimation and limiting."""

    @pytest.fixture
    def mock_llm(self, mocker):
        """Mock LLM provider."""
        llm = mocker.Mock()
        llm.count_tokens.return_value = 1000
        llm.get_model_info.return_value = {
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
        }
        return llm

    def test_cost_estimation(self, mock_llm):
        """Cost estimation should be accurate."""
        controller = CostController(mock_llm, limit_usd=10.0)

        estimate = controller.estimate_cost("test prompt", max_tokens=2000)

        assert estimate['input_tokens'] == 1000
        assert estimate['output_tokens'] == 2000
        assert estimate['estimated_cost_usd'] == pytest.approx(0.003 + 0.030)  # $0.033

    def test_limit_enforcement(self, mock_llm):
        """Should block operations exceeding limit."""
        controller = CostController(mock_llm, limit_usd=0.01)  # $0.01 limit

        # First operation: OK
        assert controller.check_and_track("prompt", max_tokens=100) is True

        # Second operation: Would exceed limit
        assert controller.check_and_track("prompt", max_tokens=10000) is False

    def test_session_tracking(self, mock_llm):
        """Should track cumulative session costs."""
        controller = CostController(mock_llm, limit_usd=1.0)

        controller.check_and_track("prompt1", max_tokens=1000)
        cost1 = controller.session_cost

        controller.check_and_track("prompt2", max_tokens=1000)
        cost2 = controller.session_cost

        assert cost2 > cost1
        assert cost2 == pytest.approx(cost1 * 2)
```

---

## Test Execution Strategy

### Development (Local)
```bash
# Quick feedback loop
pytest tests/unit/ -m "not slow" -x  # Stop on first failure

# Full unit tests
pytest tests/unit/ -v

# Integration tests (local mode only)
pytest tests/integration/ -v -m "not requires_api_key"

# Full validation
./validate-bloginator.sh
```

### Pull Request
- ✅ All pre-commit hooks pass
- ✅ All unit tests pass (all Python versions)
- ✅ Integration tests pass (local mode)
- ✅ Coverage ≥80%
- ✅ No security issues (gitleaks, bandit)

### Main Branch (Post-Merge)
- ✅ All PR checks
- ✅ Cloud integration tests (with API keys)
- ✅ E2E tests (both modes)
- ✅ Performance benchmarks
- ✅ Cost validation (<$1 per test run)

### Release
- ✅ All main branch checks
- ✅ Manual testing of critical workflows
- ✅ Documentation review
- ✅ Version bump and changelog

---

## Quality Metrics Dashboard

Track quality metrics over time:

```
┌─────────────────────────────────────────┐
│   Bloginator Quality Metrics            │
├─────────────────────────────────────────┤
│ Code Coverage:        87%  ████████▋░   │
│ Unit Tests:          312   ✅ All pass  │
│ Integration Tests:    45   ✅ All pass  │
│ E2E Tests:            12   ✅ All pass  │
│ Linting Issues:        0   ✅           │
│ Type Coverage:       95%   ████████▊░   │
│ Security Issues:       0   ✅           │
│ Avg Test Runtime:   12s    ✅ <15s      │
│ Last Cloud Test:  $0.45    ✅ <$1       │
└─────────────────────────────────────────┘
```

---

*End of TESTING-SPEC-003*
