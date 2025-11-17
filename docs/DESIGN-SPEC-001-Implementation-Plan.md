# DESIGN-SPEC-001: Bloginator Implementation Plan

**Status**: Phase 4 Complete - Streamlit UI Implemented
**Created**: 2025-11-16
**Last Updated**: 2025-11-17
**Related PRD**: PRD-BLOGINATOR-001-Core-System.md
**Target**: Claude Code / Google Gemini in VS Code implementation

## Implementation Progress

**Current Phase**: Phase 4 (Web UI) ✅ **COMPLETE**

**Completed**:
- ✅ Phase 0: Project Setup
- ✅ Phase 1: Core Extraction & Indexing
- ✅ Phase 2: Search & Retrieval
- ✅ Phase 3: Blocklist & Safety
- ✅ Phase 4: Streamlit Web UI (NEW - 2025-11-17)

**In Progress**:
- 🚧 Phase 5: Content Generation (outline/draft via CLI working, refinement pending)
- 🚧 Phase 6: Refinement & Iteration

**Upcoming**:
- ⏳ Phase 7: External Sources & Polish

---

## Document Purpose

This design specification translates the PRD into specific, testable, shippable implementation phases. Each phase is designed to be executed by AI coding assistants (Claude Code, Google Gemini) with clear acceptance criteria and validation steps.

---

## Implementation Philosophy

### Principles

1. **Incremental Value**: Each phase delivers usable functionality
2. **Test-Driven**: All phases include comprehensive tests
3. **AI-Friendly**: Clear specifications with minimal ambiguity
4. **Reusable Patterns**: Leverage Films Not Made codebase patterns
5. **Local-First**: Privacy-preserving, no mandatory cloud dependencies

### Technology Reuse from Films Not Made

**Patterns to Reuse**:
- Document extraction pipeline (PDF, DOCX, MD, TXT, ZIP)
- ChromaDB vector indexing architecture
- sentence-transformers embedding approach
- CLI structure using Click
- Testing patterns with pytest
- Pre-commit hooks and validation scripts

**Patterns to Adapt**:
- Generation system (adapt for voice preservation vs. creative pitch materials)
- Search interface (add recency/quality weighting)
- Chunking strategy (optimize for blog posts vs. scripts)

**New Patterns Needed**:
- Voice preservation and similarity scoring
- Blocklist validation system
- Iterative refinement with diff tracking
- Multi-version document management

---

## Phase 0: Project Setup (Week 1, Days 1-2)

### Goal

Create project structure, dependencies, and development environment

### Tasks

#### 0.1: Repository Initialization

**Input**: Empty repository
**Output**: Functional Python package structure

**Steps**:
1. Create directory structure:
   ```
   bloginator/
   ├── src/bloginator/
   │   ├── __init__.py
   │   ├── cli/
   │   ├── extraction/
   │   ├── indexing/
   │   ├── search/
   │   ├── generation/
   │   ├── voice/
   │   ├── safety/
   │   └── models/
   ├── tests/
   ├── docs/
   ├── pyproject.toml
   ├── README.md
   ├── .gitignore
   └── .pre-commit-config.yaml
   ```

2. Create `pyproject.toml` with dependencies:
   ```toml
   [project]
   name = "bloginator"
   version = "0.1.0"
   requires-python = ">=3.10"
   dependencies = [
       "click>=8.0",
       "chromadb>=0.4.0",
       "sentence-transformers>=2.2.0",
       "pymupdf>=1.23.0",
       "python-docx>=1.0.0",
       "striprtf>=0.0.26",
       "rich>=13.0.0",
       "pydantic>=2.0.0",
       "ollama>=0.1.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=7.0.0",
       "pytest-cov>=4.0.0",
       "black>=23.0.0",
       "ruff>=0.1.0",
       "mypy>=1.0.0",
       "pre-commit>=3.0.0",
   ]

   [project.scripts]
   bloginator = "bloginator.cli.main:cli"
   ```

3. Copy and adapt validation scripts from Films Not Made:
   - `validate-monorepo.sh` → `validate-bloginator.sh`
   - `.pre-commit-config.yaml`

4. Create initial `README.md` with:
   - Project description
   - Quick start instructions
   - Development setup

**Acceptance Criteria**:
- `pip install -e .` works
- `bloginator --version` returns version
- Pre-commit hooks install successfully
- All tests pass (even if just placeholder)

**Validation**:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
bloginator --version
pre-commit run --all-files
pytest
```

#### 0.2: Import Reusable Components

**Input**: Films Not Made codebase
**Output**: Adapted extraction and indexing modules

**Steps**:
1. Copy extraction modules:
   - `src/fnm/extraction/` → `src/bloginator/extraction/`
   - Adapt for Bloginator file structure and naming

2. Copy indexing modules:
   - `src/fnm/indexing/` → `src/bloginator/indexing/`
   - Adapt ChromaDB collection naming

3. Copy chunking modules:
   - `src/fnm/chunking/` → `src/bloginator/chunking/`
   - Consider adding paragraph-based chunking for blog posts

4. Copy base CLI structure:
   - `src/fnm/cli/main.py` → `src/bloginator/cli/main.py`
   - Define Bloginator-specific commands

5. Copy test utilities:
   - `tests/conftest.py` and fixtures
   - Adapt for Bloginator test data

**Acceptance Criteria**:
- Extraction module handles PDF, DOCX, MD, TXT
- Indexing module creates ChromaDB collection
- Tests pass for all imported modules
- Code passes linting and type checking

**Validation**:
```bash
./validate-bloginator.sh
pytest tests/extraction/ tests/indexing/ -v
```

---

## Phase 1: Core Extraction & Indexing (Week 1, Days 3-5)

### Goal

Extract and index user's historical corpus with metadata tracking

### Tasks

#### 1.1: Document Model & Metadata

**Input**: Files to extract
**Output**: Pydantic models for documents and chunks

**Implementation**:

Create `src/bloginator/models/document.py`:
```python
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

class QualityRating(str, Enum):
    PREFERRED = "preferred"
    STANDARD = "standard"
    DEPRECATED = "deprecated"

class Document(BaseModel):
    id: str = Field(..., description="Unique document identifier")
    filename: str
    source_path: Path
    format: str  # pdf, docx, markdown, txt
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    indexed_date: datetime = Field(default_factory=datetime.now)
    quality_rating: QualityRating = QualityRating.STANDARD
    tags: list[str] = Field(default_factory=list)
    is_external_source: bool = False
    attribution_required: bool = False
    word_count: int = 0
    chunk_ids: list[str] = Field(default_factory=list)

class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int  # Position in document
    section_heading: Optional[str] = None
    char_start: int
    char_end: int
    # embedding stored in vector DB, not here
```

**Acceptance Criteria**:
- Models validate successfully
- Can serialize/deserialize to JSON
- Enums work correctly
- Default values populate

**Validation**:
```python
def test_document_model():
    doc = Document(
        id="test_123",
        filename="blog.md",
        source_path=Path("/corpus/blog.md"),
        format="markdown",
    )
    assert doc.quality_rating == QualityRating.STANDARD
    assert doc.indexed_date is not None
    json_str = doc.model_dump_json()
    doc2 = Document.model_validate_json(json_str)
    assert doc == doc2
```

#### 1.2: Enhanced Extraction with Metadata

**Input**: Source files
**Output**: Documents with extracted metadata

**Implementation**:

Extend extraction to capture metadata:
```python
# src/bloginator/extraction/metadata.py
from pathlib import Path
from datetime import datetime
from typing import Optional

def extract_file_metadata(filepath: Path) -> dict:
    """Extract creation/modification dates from file."""
    stat = filepath.stat()
    return {
        "created_date": datetime.fromtimestamp(stat.st_ctime),
        "modified_date": datetime.fromtimestamp(stat.st_mtime),
        "file_size": stat.st_size,
    }

def extract_frontmatter_metadata(content: str, format: str) -> dict:
    """Extract YAML frontmatter from markdown or metadata from docx."""
    if format == "markdown":
        return extract_yaml_frontmatter(content)
    elif format == "docx":
        return extract_docx_properties(content)
    return {}
```

Create `src/bloginator/cli/extract.py`:
```python
import click
from pathlib import Path
from bloginator.extraction import extract_documents
from bloginator.models import Document

@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Output directory")
@click.option("--quality", type=click.Choice(["preferred", "standard", "deprecated"]))
@click.option("--tags", help="Comma-separated tags")
def extract(source: str, output: str, quality: str, tags: str):
    """Extract documents from SOURCE to OUTPUT directory."""
    source_path = Path(source)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    tag_list = tags.split(",") if tags else []

    documents = extract_documents(
        source_path,
        quality_rating=quality or "standard",
        tags=tag_list,
    )

    # Save documents metadata
    for doc in documents:
        save_document_metadata(doc, output_path)

    click.echo(f"Extracted {len(documents)} documents to {output_path}")
```

**Acceptance Criteria**:
- Extracts file creation/modification dates
- Extracts YAML frontmatter from markdown
- Extracts document properties from DOCX
- Respects quality rating and tags from CLI
- Saves metadata alongside extracted text

**Validation**:
```bash
# Create test corpus
mkdir -p test-corpus
echo "---\ntitle: Test Post\ndate: 2019-07-15\n---\n# Hello" > test-corpus/blog.md

# Run extraction
bloginator extract test-corpus -o output/extracted --quality preferred --tags "blog,agile"

# Verify metadata
python -c "
import json
from pathlib import Path
meta = json.loads(Path('output/extracted/blog.md.json').read_text())
assert meta['quality_rating'] == 'preferred'
assert 'blog' in meta['tags']
assert 'agile' in meta['tags']
print('✓ Metadata extraction works')
"
```

#### 1.3: Indexing with Metadata Filtering

**Input**: Extracted documents with metadata
**Output**: ChromaDB index with metadata

**Implementation**:

Create `src/bloginator/indexing/index_builder.py`:
```python
import chromadb
from sentence_transformers import SentenceTransformer
from bloginator.models import Document, Chunk

class CorpusIndexer:
    def __init__(self, output_dir: Path, collection_name: str = "bloginator_corpus"):
        self.client = chromadb.PersistentClient(path=str(output_dir))
        self.collection = self.client.get_or_create_collection(collection_name)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def index_document(self, document: Document, chunks: list[Chunk]) -> None:
        """Add document chunks to vector store with metadata."""
        embeddings = self.embedding_model.encode([c.content for c in chunks])

        self.collection.add(
            ids=[c.id for c in chunks],
            embeddings=embeddings.tolist(),
            documents=[c.content for c in chunks],
            metadatas=[
                {
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "section_heading": c.section_heading or "",
                    "created_date": document.created_date.isoformat() if document.created_date else "",
                    "quality_rating": document.quality_rating,
                    "is_external_source": document.is_external_source,
                    "tags": ",".join(document.tags),
                }
                for c in chunks
            ]
        )
```

**Acceptance Criteria**:
- ChromaDB collection stores metadata
- Can filter by quality_rating
- Can filter by date range
- Can filter by tags
- Metadata preserved in search results

**Validation**:
```python
def test_indexing_with_metadata():
    indexer = CorpusIndexer(Path("test_output"))
    doc = create_test_document(quality_rating="preferred", tags=["agile"])
    chunks = create_test_chunks(doc)
    indexer.index_document(doc, chunks)

    # Search with metadata filter
    results = indexer.collection.query(
        query_embeddings=[test_embedding],
        where={"quality_rating": "preferred"},
        n_results=10,
    )
    assert len(results['ids'][0]) > 0
    assert all("preferred" in m.get("quality_rating", "") for m in results['metadatas'][0])
```

#### 1.4: CLI Integration

**Input**: User commands
**Output**: Working end-to-end extraction and indexing

**Implementation**:

Create `src/bloginator/cli/index.py`:
```python
@click.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("-o", "--output", required=True, help="Index output directory")
@click.option("--chunk-size", default=512, help="Chunk size in tokens")
@click.option("--chunk-strategy", type=click.Choice(["semantic", "paragraph", "fixed"]))
def index(source: str, output: str, chunk_size: int, chunk_strategy: str):
    """Build searchable index from extracted documents in SOURCE."""
    # Load extracted documents
    # Chunk documents
    # Build index
    # Save index
    pass
```

**Acceptance Criteria**:
- `bloginator extract` works end-to-end
- `bloginator index` works end-to-end
- Progress bars show during processing
- Error handling for corrupted files
- Comprehensive logging

**Validation**:
```bash
# End-to-end test
bloginator extract test-corpus -o output/extracted
bloginator index output/extracted -o output/index
ls output/index/chroma.sqlite3  # Verify index exists
```

### Phase 1 Deliverables

- ✅ Document and Chunk models
- ✅ Metadata extraction (file system + frontmatter)
- ✅ ChromaDB indexing with metadata
- ✅ CLI commands: `extract`, `index`
- ✅ Tests with 80%+ coverage
- ✅ Documentation: README, docstrings

### Phase 1 Validation Checklist

```bash
# 1. Install and setup
pip install -e ".[dev]"
bloginator --help

# 2. Extract test corpus
bloginator extract test-corpus -o output/extracted --tags "test,blog"

# 3. Index extracted corpus
bloginator index output/extracted -o output/index

# 4. Verify index
python -c "
import chromadb
client = chromadb.PersistentClient(path='output/index')
collection = client.get_collection('bloginator_corpus')
print(f'Indexed {collection.count()} chunks')
assert collection.count() > 0
"

# 5. Run tests
pytest tests/extraction/ tests/indexing/ -v --cov

# 6. Validate code quality
./validate-bloginator.sh
```

---

## Phase 2: Search & Retrieval (Week 2, Days 1-3)

### Goal

Implement semantic search with recency/quality weighting

### Tasks

#### 2.1: Basic Semantic Search

**Input**: Query string
**Output**: Ranked relevant chunks

**Implementation**:

Create `src/bloginator/search/searcher.py`:
```python
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from typing import Optional

class CorpusSearcher:
    def __init__(self, index_dir: Path):
        self.client = chromadb.PersistentClient(path=str(index_dir))
        self.collection = self.client.get_collection("bloginator_corpus")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def search(
        self,
        query: str,
        n_results: int = 10,
        quality_filter: Optional[str] = None,
        tags_filter: Optional[list[str]] = None,
    ) -> list[dict]:
        """Search corpus with optional filters."""
        query_embedding = self.embedding_model.encode([query])[0]

        where = {}
        if quality_filter:
            where["quality_rating"] = quality_filter
        if tags_filter:
            # ChromaDB metadata filtering for tags is tricky
            # May need to filter post-query
            pass

        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=where if where else None,
        )

        return self._format_results(results)

    def _format_results(self, raw_results: dict) -> list[dict]:
        """Format ChromaDB results into user-friendly structure."""
        formatted = []
        for i, chunk_id in enumerate(raw_results['ids'][0]):
            formatted.append({
                "chunk_id": chunk_id,
                "content": raw_results['documents'][0][i],
                "metadata": raw_results['metadatas'][0][i],
                "distance": raw_results['distances'][0][i],
            })
        return formatted
```

**Acceptance Criteria**:
- Returns relevant results for test queries
- Respects quality_rating filter
- Results include metadata
- Distance scores are reasonable

**Validation**:
```python
def test_semantic_search():
    searcher = CorpusSearcher(Path("output/index"))
    results = searcher.search("agile transformation", n_results=5)
    assert len(results) <= 5
    assert all("content" in r for r in results)
    assert all("metadata" in r for r in results)
```

#### 2.2: Recency Weighting

**Input**: Search results with dates
**Output**: Re-ranked results favoring recent content

**Implementation**:

Add to `CorpusSearcher`:
```python
from datetime import datetime, timedelta

def search_with_recency_boost(
    self,
    query: str,
    n_results: int = 10,
    recency_weight: float = 0.3,
) -> list[dict]:
    """Search with recency boost (more recent = higher rank)."""
    # Get more results than needed (we'll re-rank)
    results = self.search(query, n_results=n_results * 3)

    # Calculate recency scores
    now = datetime.now()
    for r in results:
        created_date_str = r['metadata'].get('created_date', '')
        if created_date_str:
            created_date = datetime.fromisoformat(created_date_str)
            days_old = (now - created_date).days
            # Decay factor: 1.0 for today, 0.5 for 1 year old, 0.1 for 5 years old
            recency_score = 1.0 / (1.0 + days_old / 365.0)
        else:
            recency_score = 0.5  # Unknown date = medium score

        r['recency_score'] = recency_score

        # Combined score: (1 - recency_weight) * similarity + recency_weight * recency
        similarity_score = 1.0 - r['distance']  # Convert distance to similarity
        r['combined_score'] = (
            (1 - recency_weight) * similarity_score +
            recency_weight * recency_score
        )

    # Sort by combined score
    results.sort(key=lambda r: r['combined_score'], reverse=True)

    return results[:n_results]
```

**Acceptance Criteria**:
- Recent documents rank higher than old ones (all else equal)
- Highly relevant old documents still rank high
- Configurable recency_weight parameter
- Tests verify weighting behavior

**Validation**:
```python
def test_recency_weighting():
    searcher = CorpusSearcher(Path("output/index"))

    # Search with no recency boost
    results_no_boost = searcher.search("agile", n_results=10)

    # Search with strong recency boost
    results_with_boost = searcher.search_with_recency_boost(
        "agile", n_results=10, recency_weight=0.8
    )

    # Recent documents should rank higher in boosted results
    # (Exact assertion depends on test data)
```

#### 2.3: Quality Weighting

**Input**: Search results with quality ratings
**Output**: Re-ranked results favoring "preferred" content

**Implementation**:

Add quality scoring to `CorpusSearcher`:
```python
def search_with_quality_boost(
    self,
    query: str,
    n_results: int = 10,
    quality_weight: float = 0.2,
) -> list[dict]:
    """Search with quality boost (preferred > standard > deprecated)."""
    results = self.search(query, n_results=n_results * 3)

    quality_scores = {
        "preferred": 1.0,
        "standard": 0.5,
        "deprecated": 0.1,
    }

    for r in results:
        quality_rating = r['metadata'].get('quality_rating', 'standard')
        r['quality_score'] = quality_scores.get(quality_rating, 0.5)

        similarity_score = 1.0 - r['distance']
        r['combined_score'] = (
            (1 - quality_weight) * similarity_score +
            quality_weight * r['quality_score']
        )

    results.sort(key=lambda r: r['combined_score'], reverse=True)
    return results[:n_results]
```

#### 2.4: Combined Weighting (Recency + Quality)

**Input**: Query
**Output**: Results ranked by similarity, recency, AND quality

**Implementation**:

```python
def search_with_all_weights(
    self,
    query: str,
    n_results: int = 10,
    recency_weight: float = 0.2,
    quality_weight: float = 0.1,
) -> list[dict]:
    """Search with combined similarity, recency, and quality weighting."""
    results = self.search(query, n_results=n_results * 3)

    now = datetime.now()
    quality_scores = {"preferred": 1.0, "standard": 0.5, "deprecated": 0.1}

    for r in results:
        # Similarity score
        similarity_score = 1.0 - r['distance']

        # Recency score
        created_date_str = r['metadata'].get('created_date', '')
        if created_date_str:
            created_date = datetime.fromisoformat(created_date_str)
            days_old = (now - created_date).days
            recency_score = 1.0 / (1.0 + days_old / 365.0)
        else:
            recency_score = 0.5

        # Quality score
        quality_rating = r['metadata'].get('quality_rating', 'standard')
        quality_score = quality_scores.get(quality_rating, 0.5)

        # Combined: normalize weights to sum to 1.0
        similarity_weight = 1.0 - recency_weight - quality_weight
        r['combined_score'] = (
            similarity_weight * similarity_score +
            recency_weight * recency_score +
            quality_weight * quality_score
        )

        r['similarity_score'] = similarity_score
        r['recency_score'] = recency_score
        r['quality_score'] = quality_score

    results.sort(key=lambda r: r['combined_score'], reverse=True)
    return results[:n_results]
```

#### 2.5: Search CLI

**Input**: User search query
**Output**: Pretty-printed search results

**Implementation**:

Create `src/bloginator/cli/search.py`:
```python
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from bloginator.search import CorpusSearcher

@click.command()
@click.argument("index_dir", type=click.Path(exists=True))
@click.argument("query", required=False)
@click.option("-n", "--num-results", default=10, help="Number of results")
@click.option("--recency-weight", default=0.2, help="Recency weight (0-1)")
@click.option("--quality-weight", default=0.1, help="Quality weight (0-1)")
@click.option("--quality-filter", type=click.Choice(["preferred", "standard", "deprecated"]))
@click.option("--interactive", is_flag=True, help="Interactive search mode")
def search(
    index_dir: str,
    query: str,
    num_results: int,
    recency_weight: float,
    quality_weight: float,
    quality_filter: str,
    interactive: bool,
):
    """Search corpus for QUERY."""
    searcher = CorpusSearcher(Path(index_dir))
    console = Console()

    if interactive:
        while True:
            query = click.prompt("Search query (or 'quit')")
            if query.lower() == 'quit':
                break
            display_results(searcher, query, num_results, recency_weight, quality_weight, console)
    else:
        if not query:
            raise click.UsageError("Query required in non-interactive mode")
        display_results(searcher, query, num_results, recency_weight, quality_weight, console)

def display_results(searcher, query, n, recency_w, quality_w, console):
    results = searcher.search_with_all_weights(
        query,
        n_results=n,
        recency_weight=recency_w,
        quality_weight=quality_w,
    )

    table = Table(title=f"Search Results: '{query}'")
    table.add_column("Score", justify="right")
    table.add_column("Content Preview", overflow="fold")
    table.add_column("Source", overflow="fold")
    table.add_column("Date")
    table.add_column("Quality")

    for r in results:
        preview = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
        date = r['metadata'].get('created_date', 'Unknown')[:10]  # Just date part
        quality = r['metadata'].get('quality_rating', 'standard')

        table.add_row(
            f"{r['combined_score']:.3f}",
            preview,
            r['metadata'].get('filename', 'Unknown'),
            date,
            quality,
        )

    console.print(table)
```

**Acceptance Criteria**:
- Non-interactive mode works with query argument
- Interactive mode allows multiple queries
- Results displayed in readable table format
- Scores, source, date, quality shown
- Colors/formatting enhance readability (rich library)

**Validation**:
```bash
# Non-interactive search
bloginator search output/index "agile transformation" -n 5

# Interactive search
bloginator search output/index --interactive
# > agile
# > engineering culture
# > quit

# With weighting adjustments
bloginator search output/index "hiring" --recency-weight 0.5 --quality-weight 0.2
```

### Phase 2 Deliverables

- ✅ Semantic search implementation
- ✅ Recency weighting
- ✅ Quality weighting
- ✅ Combined weighting
- ✅ Search CLI (interactive + non-interactive)
- ✅ Tests with 80%+ coverage
- ✅ User documentation

### Phase 2 Validation Checklist

```bash
# 1. Basic search
bloginator search output/index "agile transformation"

# 2. Search with filters
bloginator search output/index "hiring" --quality-filter preferred

# 3. Search with weighting
bloginator search output/index "culture" --recency-weight 0.5

# 4. Interactive search
bloginator search output/index --interactive

# 5. Tests
pytest tests/search/ -v --cov

# 6. Validation
./validate-bloginator.sh
```

---

## Phase 3: Blocklist & Safety (Week 2, Days 4-5)

### Goal

Prevent proprietary content leakage with blocklist validation

### Tasks

#### 3.1: Blocklist Data Model

**Input**: Proprietary terms to block
**Output**: Pydantic models and storage

**Implementation**:

Create `src/bloginator/models/blocklist.py`:
```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import re

class BlocklistPatternType(str, Enum):
    EXACT = "exact"
    REGEX = "regex"
    CASE_INSENSITIVE = "case_insensitive"

class BlocklistCategory(str, Enum):
    COMPANY_NAME = "company_name"
    PRODUCT_NAME = "product_name"
    PROJECT_CODENAME = "project"
    METHODOLOGY = "methodology"
    PERSON_NAME = "person"
    OTHER = "other"

class BlocklistEntry(BaseModel):
    id: str = Field(..., description="Unique entry ID")
    pattern: str = Field(..., description="Term or regex pattern to block")
    pattern_type: BlocklistPatternType = BlocklistPatternType.EXACT
    category: BlocklistCategory = BlocklistCategory.OTHER
    added_date: datetime = Field(default_factory=datetime.now)
    notes: str = Field(default="", description="Why this is blocked")

    def matches(self, text: str) -> list[str]:
        """Check if pattern appears in text. Returns list of matches."""
        if self.pattern_type == BlocklistPatternType.EXACT:
            if self.pattern in text:
                return [self.pattern]
        elif self.pattern_type == BlocklistPatternType.CASE_INSENSITIVE:
            pattern_lower = self.pattern.lower()
            if pattern_lower in text.lower():
                # Find actual matches to return
                return [m for m in re.findall(re.escape(self.pattern), text, re.IGNORECASE)]
        elif self.pattern_type == BlocklistPatternType.REGEX:
            matches = re.findall(self.pattern, text)
            return matches if matches else []
        return []
```

**Acceptance Criteria**:
- Exact matching works
- Case-insensitive matching works
- Regex matching works
- Returns actual matched strings (not just True/False)

**Validation**:
```python
def test_blocklist_entry():
    # Exact match
    entry = BlocklistEntry(
        id="1",
        pattern="Acme Corp",
        pattern_type=BlocklistPatternType.EXACT,
        category=BlocklistCategory.COMPANY_NAME,
    )
    assert entry.matches("I worked at Acme Corp") == ["Acme Corp"]
    assert entry.matches("I worked at acme corp") == []  # Exact is case-sensitive

    # Case-insensitive
    entry2 = BlocklistEntry(
        id="2",
        pattern="Acme",
        pattern_type=BlocklistPatternType.CASE_INSENSITIVE,
        category=BlocklistCategory.COMPANY_NAME,
    )
    assert len(entry2.matches("ACME and acme")) == 2

    # Regex
    entry3 = BlocklistEntry(
        id="3",
        pattern=r"Project \w+",
        pattern_type=BlocklistPatternType.REGEX,
        category=BlocklistCategory.PROJECT_CODENAME,
    )
    assert entry3.matches("Project Falcon was secret") == ["Project Falcon"]
```

#### 3.2: Blocklist Manager

**Input**: Blocklist entries
**Output**: Validation service

**Implementation**:

Create `src/bloginator/safety/blocklist.py`:
```python
import json
from pathlib import Path
from typing import Optional
from bloginator.models.blocklist import BlocklistEntry

class BlocklistManager:
    def __init__(self, blocklist_file: Path):
        self.blocklist_file = blocklist_file
        self.entries: list[BlocklistEntry] = []
        self.load()

    def load(self) -> None:
        """Load blocklist from JSON file."""
        if self.blocklist_file.exists():
            data = json.loads(self.blocklist_file.read_text())
            self.entries = [BlocklistEntry(**e) for e in data]
        else:
            self.entries = []

    def save(self) -> None:
        """Save blocklist to JSON file."""
        data = [e.model_dump() for e in self.entries]
        self.blocklist_file.write_text(json.dumps(data, indent=2, default=str))

    def add_entry(self, entry: BlocklistEntry) -> None:
        """Add entry to blocklist."""
        self.entries.append(entry)
        self.save()

    def remove_entry(self, entry_id: str) -> None:
        """Remove entry by ID."""
        self.entries = [e for e in self.entries if e.id != entry_id]
        self.save()

    def validate_text(self, text: str) -> dict:
        """Check text for blocklist violations.

        Returns:
            {
                "violations": [
                    {
                        "entry_id": "...",
                        "pattern": "...",
                        "matches": ["...", ...],
                        "category": "...",
                    },
                    ...
                ],
                "is_valid": True/False,
            }
        """
        violations = []
        for entry in self.entries:
            matches = entry.matches(text)
            if matches:
                violations.append({
                    "entry_id": entry.id,
                    "pattern": entry.pattern,
                    "matches": matches,
                    "category": entry.category,
                    "notes": entry.notes,
                })

        return {
            "violations": violations,
            "is_valid": len(violations) == 0,
        }
```

**Acceptance Criteria**:
- Load/save blocklist from JSON
- Add/remove entries
- Validate text against all entries
- Return detailed violation information
- Handle empty blocklist gracefully

**Validation**:
```python
def test_blocklist_manager(tmp_path):
    blocklist_file = tmp_path / "blocklist.json"
    manager = BlocklistManager(blocklist_file)

    # Add entry
    entry = BlocklistEntry(
        id="1",
        pattern="Acme Corp",
        pattern_type=BlocklistPatternType.EXACT,
        category=BlocklistCategory.COMPANY_NAME,
    )
    manager.add_entry(entry)

    # Validate
    result = manager.validate_text("I worked at Acme Corp for 5 years.")
    assert not result['is_valid']
    assert len(result['violations']) == 1
    assert result['violations'][0]['pattern'] == "Acme Corp"

    # Clean text passes
    result2 = manager.validate_text("I worked at a tech company for 5 years.")
    assert result2['is_valid']
    assert len(result2['violations']) == 0
```

#### 3.3: Blocklist CLI

**Input**: User commands to manage blocklist
**Output**: CRUD operations on blocklist

**Implementation**:

Create `src/bloginator/cli/blocklist.py`:
```python
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from bloginator.safety.blocklist import BlocklistManager
from bloginator.models.blocklist import BlocklistEntry, BlocklistPatternType, BlocklistCategory
import uuid

@click.group()
def blocklist():
    """Manage proprietary term blocklist."""
    pass

@blocklist.command()
@click.option("--config-dir", type=click.Path(), default=".bloginator")
@click.argument("pattern")
@click.option("--type", "pattern_type", type=click.Choice(["exact", "case_insensitive", "regex"]), default="exact")
@click.option("--category", type=click.Choice(["company_name", "product_name", "project", "methodology", "person", "other"]), default="other")
@click.option("--notes", default="", help="Why this is blocked")
def add(config_dir: str, pattern: str, pattern_type: str, category: str, notes: str):
    """Add term to blocklist."""
    config_path = Path(config_dir)
    config_path.mkdir(exist_ok=True)

    manager = BlocklistManager(config_path / "blocklist.json")
    entry = BlocklistEntry(
        id=str(uuid.uuid4()),
        pattern=pattern,
        pattern_type=BlocklistPatternType(pattern_type),
        category=BlocklistCategory(category),
        notes=notes,
    )
    manager.add_entry(entry)
    click.echo(f"✓ Added '{pattern}' to blocklist")

@blocklist.command()
@click.option("--config-dir", type=click.Path(), default=".bloginator")
def list(config_dir: str):
    """List all blocklist entries."""
    manager = BlocklistManager(Path(config_dir) / "blocklist.json")

    console = Console()
    table = Table(title="Blocklist")
    table.add_column("ID")
    table.add_column("Pattern")
    table.add_column("Type")
    table.add_column("Category")
    table.add_column("Notes")

    for entry in manager.entries:
        table.add_row(
            entry.id[:8],  # Short ID
            entry.pattern,
            entry.pattern_type,
            entry.category,
            entry.notes,
        )

    console.print(table)

@blocklist.command()
@click.option("--config-dir", type=click.Path(), default=".bloginator")
@click.argument("entry_id")
def remove(config_dir: str, entry_id: str):
    """Remove entry from blocklist by ID."""
    manager = BlocklistManager(Path(config_dir) / "blocklist.json")
    manager.remove_entry(entry_id)
    click.echo(f"✓ Removed entry {entry_id}")

@blocklist.command()
@click.option("--config-dir", type=click.Path(), default=".bloginator")
@click.argument("text_file", type=click.Path(exists=True))
def validate(config_dir: str, text_file: str):
    """Validate text file against blocklist."""
    manager = BlocklistManager(Path(config_dir) / "blocklist.json")
    text = Path(text_file).read_text()

    result = manager.validate_text(text)

    console = Console()
    if result['is_valid']:
        console.print("✓ No blocklist violations found", style="green")
    else:
        console.print(f"✗ Found {len(result['violations'])} violation(s)", style="red")
        for v in result['violations']:
            console.print(f"  - Pattern '{v['pattern']}' matched: {v['matches']}")
            if v['notes']:
                console.print(f"    Notes: {v['notes']}")
```

**Acceptance Criteria**:
- `bloginator blocklist add` works
- `bloginator blocklist list` displays entries
- `bloginator blocklist remove` works
- `bloginator blocklist validate` checks text files
- User-friendly output with rich formatting

**Validation**:
```bash
# Add entries
bloginator blocklist add "Acme Corp" --category company_name --notes "Former employer"
bloginator blocklist add "Project Falcon" --category project --notes "Confidential project"
bloginator blocklist add "Acme" --type case_insensitive --category company_name

# List entries
bloginator blocklist list

# Validate a file
echo "I worked at Acme Corp on Project Falcon" > test.txt
bloginator blocklist validate test.txt
# Should report violations

# Remove entry
bloginator blocklist remove <entry-id>
```

### Phase 3 Deliverables

- ✅ Blocklist data models
- ✅ BlocklistManager service
- ✅ Blocklist CLI (add, list, remove, validate)
- ✅ Tests with 80%+ coverage
- ✅ Documentation

### Phase 3 Validation Checklist

```bash
# 1. Add blocklist entries
bloginator blocklist add "TestCorp" --category company_name

# 2. List entries
bloginator blocklist list

# 3. Validate text
echo "I worked at TestCorp" > test.txt
bloginator blocklist validate test.txt

# 4. Tests
pytest tests/safety/ -v --cov

# 5. Validation
./validate-bloginator.sh
```

---

## Phase 4: Content Generation (Week 3)

### Goal

RAG-based content generation with voice preservation

*Due to length constraints, providing high-level structure. Full implementation details would follow same pattern as above phases.*

### Tasks

#### 4.1: Outline Generation
- Input: Keywords, themes, thesis
- Output: Structured document outline with coverage analysis
- Implementation: RAG query for each topic, analyze coverage, suggest sections

#### 4.2: Draft Generation
- Input: Approved outline
- Output: Full draft with inline citations
- Implementation: Section-by-section generation, grounding validation, source attribution

#### 4.3: Voice Similarity Scoring
- Input: Generated text, corpus samples
- Output: Voice similarity score (0-1)
- Implementation: Embedding-based similarity, style metrics, characteristic phrase detection

#### 4.4: Blocklist Integration
- Input: Generated draft
- Output: Validated draft (or violations report)
- Implementation: Pre-display validation, violation highlighting, regeneration if needed

#### 4.5: Generation CLI
- Commands: `bloginator outline`, `bloginator draft`
- Features: Progress tracking, coverage warnings, voice scores

### Phase 4 Deliverables
- ✅ Outline generation
- ✅ Draft generation
- ✅ Voice similarity scoring
- ✅ Blocklist pre-validation
- ✅ Generation CLI
- ✅ Tests and documentation

---

## Phase 5: Refinement & Iteration (Week 4)

### Goal

Interactive refinement with diff tracking

### Tasks

#### 5.1: Refinement Engine
- Input: Draft + natural language feedback
- Output: Updated draft with changes
- Implementation: Parse feedback, targeted regeneration, diff computation

#### 5.2: Version Management
- Input: Multiple iterations
- Output: Version history with diffs
- Implementation: Document versioning, diff visualization, revert capability

#### 5.3: Refinement CLI
- Commands: `bloginator refine`, `bloginator diff`, `bloginator revert`

### Phase 5 Deliverables
- ✅ Refinement engine
- ✅ Version management
- ✅ Diff visualization
- ✅ Refinement CLI
- ✅ Tests and documentation

---

## Phase 6: Streamlit Web UI (Week 5) ✅ **COMPLETE**

### Goal

Interactive web interface for all workflows - Implemented 2025-11-17

### Implementation Summary

**Technology Choice**: Streamlit (Python-native, rapid development, excellent for data apps)

**Why Streamlit over Flask/FastAPI**:
- **Faster development**: No separate frontend code (React/Vue) needed
- **Python-native**: Leverage existing Python codebase directly
- **Built-in components**: Data viz, forms, file uploads, progress bars
- **Stateful by default**: Session state management included
- **Local-first**: No deployment complexity for MVP

### Implemented Components

#### 6.1: Main App (`src/bloginator/ui/app.py`)
- ✅ Multi-page navigation with sidebar
- ✅ Session state management
- ✅ Custom CSS styling
- ✅ Corpus status indicators
- ✅ Page routing system

#### 6.2: Home Dashboard (`pages/home.py`)
- ✅ System status overview (index, extracted files, LLM)
- ✅ Quick start guide
- ✅ Workflow visualization
- ✅ Recent activity feed
- ✅ Quick action buttons

#### 6.3: Corpus Management (`pages/corpus.py`)
- ✅ Extract tab: Configure and run extraction with progress
- ✅ Index tab: Build ChromaDB index with stats
- ✅ Status tab: View corpus statistics and metadata
- ✅ Source visualization from corpus.yaml
- ✅ Error handling and validation

#### 6.4: Search Interface (`pages/search.py`)
- ✅ Interactive search with live results
- ✅ Adjustable filters (quality, recency weight, count)
- ✅ Search history
- ✅ Search tips and examples
- ✅ Rich result formatting

#### 6.5: Content Generation (`pages/generate.py`)
- ✅ Outline generation form (title, keywords, thesis, sections)
- ✅ Draft generation from outline
- ✅ Visual parameter controls (temperature, sources, word limits)
- ✅ Inline preview of generated content
- ✅ Download drafts as markdown
- ✅ Progress tracking for long operations

#### 6.6: Analytics Dashboard (`pages/analytics.py`)
- ✅ Corpus statistics (documents, size, chunks)
- ✅ Source distribution visualization
- ✅ Quality rating breakdown
- ✅ Tag cloud and topic coverage
- ✅ Temporal distribution (documents by year)
- ✅ Generated content tracking
- ✅ Coverage analysis tool

#### 6.7: Settings Panel (`pages/settings.py`)
- ✅ LLM configuration (Ollama/Custom)
- ✅ Connection testing
- ✅ Available models display
- ✅ Path configuration (corpus, index, output)
- ✅ Generation defaults
- ✅ System diagnostics
- ✅ About/version information

#### 6.8: Launcher Script (`run-streamlit.sh`)
- ✅ Command-line launcher with options
- ✅ Port configuration
- ✅ Browser auto-open
- ✅ Virtual environment detection
- ✅ Dependency checks

### Phase 6 Deliverables - ALL COMPLETE ✅
- ✅ Streamlit web application (6 pages)
- ✅ All core workflows accessible via UI
- ✅ Responsive design (desktop-optimized, mobile-friendly)
- ✅ Real-time progress indicators
- ✅ Visual analytics and insights
- ✅ LLM configuration UI
- ✅ Launch script with `./run-streamlit.sh`
- ✅ Integration with existing CLI tools (subprocess calls)

---

## Phase 7: Enhanced Features & Polish (Weeks 7-8+)

### Goal

Production readiness and advanced features

### Roadmap Priority Tiers

#### Tier 1: Essential Polish (Next Sprint)
**Goal**: Make current features production-ready

1. **Blocklist Management UI**
   - Add/remove blocklist entries via Settings page
   - Visual blocklist validation for generated content
   - Import/export blocklist configurations
   - **WHY**: Safety is critical, CLI-only blocklist is too buried
   - **Effort**: 2 days
   - **Assigned**: Pending

2. **Multi-Format Export**
   - Export drafts to DOCX, HTML, PDF from UI
   - Citation include/exclude toggle
   - Formatting preservation
   - **WHY**: Users need publication-ready formats, not just markdown
   - **Effort**: 3 days
   - **Assigned**: Pending

3. **Error Handling & Validation**
   - Better error messages in UI
   - Input validation (corpus paths, LLM endpoints)
   - Graceful degradation when services unavailable
   - **WHY**: Current errors are cryptic, users get stuck
   - **Effort**: 2 days
   - **Assigned**: Pending

4. **End-to-End Tests**
   - Automated E2E tests for critical paths
   - UI smoke tests
   - Performance benchmarks
   - **WHY**: Prevent regressions as features grow
   - **Effort**: 3 days
   - **Assigned**: Pending

#### Tier 2: Enhanced Workflows (Future Sprints)

1. **Refinement & Iteration**
   - Natural language refinement prompts
   - Diff viewer for changes
   - Version history with revert
   - **WHY**: Users need to iterate without starting over
   - **Effort**: 5 days
   - **Assigned**: Pending

2. **External Source Support**
   - Upload reference materials (PDFs, books)
   - Attribution tracking (required vs. own voice)
   - Citation formatting (footnotes, bibliography)
   - **WHY**: Users want to incorporate external research safely
   - **Effort**: 4 days
   - **Assigned**: Pending

3. **Template Library**
   - Pre-built templates (blog, job description, career ladder, etc.)
   - Template editor in UI
   - Community template sharing
   - **WHY**: Accelerate common document types
   - **Effort**: 3 days
   - **Assigned**: Pending

4. **Advanced Analytics**
   - Topic clustering and visualization
   - Corpus gap analysis ("You write a lot about X but nothing about Y")
   - Voice evolution over time
   - **WHY**: Help users understand their corpus better
   - **Effort**: 5 days
   - **Assigned**: Pending

#### Tier 3: Power User Features (Nice to Have)

1. **Batch Generation**
   - Generate multiple drafts from template + CSV
   - Scheduled generation (cron integration)
   - Bulk export
   - **WHY**: Users managing many similar documents
   - **Effort**: 4 days

2. **Collaboration Features**
   - Share corpus index (read-only)
   - Team blocklists
   - Shared templates
   - **WHY**: Teams want to leverage collective voice
   - **Effort**: 8+ days

3. **Advanced LLM Integration**
   - Support for Anthropic Claude, OpenAI GPT-4
   - Model comparison (same prompt, different models)
   - Fine-tuning integration
   - **WHY**: Give users more LLM options
   - **Effort**: 5 days

4. **Corpus Versioning**
   - Track corpus changes over time
   - Reindex diff (only changed documents)
   - Corpus branching (experimental vs. production)
   - **WHY**: Large corpuses are expensive to reindex
   - **Effort**: 6 days

### Phase 7 Deliverables (Adjusted Scope)
- ⏳ Tier 1 features (blocklist UI, export, tests, error handling)
- ⏳ Tier 2 features (refinement, external sources, templates, analytics)
- ⏳ Tier 3 features (batch, collaboration, advanced LLM)
- ⏳ Production-ready documentation
- ⏳ Comprehensive testing suite
- ⏳ Performance benchmarks

### Success Metrics for Phase 7
- User can complete full workflow (extract → index → generate → export) in <30 minutes
- 95%+ of errors have actionable error messages
- Test coverage >80% for critical paths
- Blocklist enforcement rate: 100% for exact matches
- Export preserves formatting in DOCX/HTML

---

## Testing Strategy

### Unit Tests
- Every module has unit tests
- 80%+ code coverage minimum
- Fast tests (<1s per test)
- Mock external dependencies (LLM, embedding model)

### Integration Tests
- End-to-end workflows
- Real ChromaDB operations
- Real embedding generation (use small test corpus)
- CLI command testing

### Voice Preservation Tests
- Blind comparison tests (manual)
- Voice similarity score thresholds
- Characteristic phrase detection
- Tone consistency validation

### Blocklist Tests
- Adversarial examples (trying to evade blocklist)
- Regex pattern edge cases
- Performance with large blocklists (1000+ entries)

### Performance Tests
- Index 500 documents in <30 minutes
- Search in <3 seconds
- Generate draft in <5 minutes
- Voice scoring in <10 seconds

---

## Documentation Deliverables

### For Users
1. README.md - Project overview and quick start
2. INSTALLATION.md - Detailed setup instructions
3. USER_GUIDE.md - Complete feature walkthrough
4. TUTORIALS.md - Step-by-step examples
5. FAQ.md - Common questions and troubleshooting

### For Developers
1. DEVELOPER_GUIDE.md - Coding standards (adapted from Films Not Made)
2. ARCHITECTURE.md - System design and components
3. API_REFERENCE.md - CLI and API documentation
4. TESTING.md - Testing guidelines
5. CONTRIBUTING.md - Contribution workflow

### For AI Assistants
1. CLAUDE_GUIDELINES.md - Already created
2. IMPLEMENTATION_CHECKLIST.md - Phase-by-phase validation
3. PROMPT_TEMPLATES.md - Effective prompts for generation

---

## Success Criteria

Each phase is complete when:

1. ✅ All acceptance criteria met
2. ✅ Tests pass with 80%+ coverage
3. ✅ Code passes linting and type checking
4. ✅ Documentation updated
5. ✅ Validation checklist completed
6. ✅ Demo video recorded (for major phases)

Project is complete when:

1. ✅ All 7 phases delivered
2. ✅ End-to-end workflow works smoothly
3. ✅ Voice preservation scores >0.7 on test corpus
4. ✅ Blocklist enforcement at 100% for exact matches
5. ✅ Performance meets or exceeds success metrics
6. ✅ User can complete full document creation workflow in <60 minutes
7. ✅ Comprehensive documentation published
8. ✅ CI/CD pipeline configured (GitHub Actions)

---

## Risk Mitigation

### Technical Risks
- **LLM quality varies**: Test with multiple models (llama3, mistral, etc.)
- **Voice preservation difficult**: Extensive blind testing, iterative improvement
- **Blocklist evasion**: Multiple validation layers, fuzzy matching

### Scope Risks
- **Feature creep**: Stick to phased plan, defer non-essential features
- **Over-engineering**: Follow CLAUDE_GUIDELINES.md principles
- **Timeline slippage**: Each phase has clear deliverables and validation

---

## Appendix: Technology Stack

### Core Dependencies
- **Python**: 3.10+
- **Click**: CLI framework
- **Rich**: Terminal formatting
- **Pydantic**: Data validation
- **ChromaDB**: Vector store
- **sentence-transformers**: Embeddings (all-MiniLM-L6-v2)
- **Ollama**: Local LLM inference
- **PyMuPDF**: PDF extraction
- **python-docx**: DOCX extraction
- **striprtf**: RTF extraction

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

### Optional Dependencies
- **Flask** or **FastAPI**: Web UI
- **SQLite**: Metadata storage (alternative to JSON files)
- **FAISS**: Alternative vector store for massive corpuses

---

*End of DESIGN-SPEC-001*
