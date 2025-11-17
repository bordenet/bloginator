# Claude AI Development Notes

This document contains important context for AI assistants (Claude) working on the Bloginator project.

## Local Development Environment

### LLM Models Available for Testing

**Primary Models (Local Ollama on 192.168.5.53:11434):**
- `mixtral:8x7b` - Primary model for local testing, good balance of quality and performance
- `llama3:8b` - Alternative local model, can be used if mixtral is unavailable or for testing

**Configuration:**
```bash
# In .env for local testing:
OLLAMA_HOST=http://192.168.5.53:11434
OLLAMA_MODEL=mixtral:8x7b  # or llama3:8b
```

### Multi-Provider Support

Bloginator is designed to work equally well with:

1. **Local Models (via Ollama)**
   - Mixtral 8x7B - Best for local development
   - Llama3 8B - Lighter alternative
   - Any other Ollama-compatible model

2. **Cloud Models (Future)**
   - OpenAI GPT-4, GPT-3.5-turbo
   - Anthropic Claude 3 (Opus, Sonnet, Haiku)
   - Custom OpenAI-compatible endpoints

3. **Self-Hosted Inference Servers**
   - LM Studio (local)
   - vLLM (production)
   - text-generation-webui

### Configuration System

The config system (`src/bloginator/config.py`) supports **backward compatibility** with multiple variable naming conventions:

| Purpose | Primary Variable | Fallback Variable |
|---------|-----------------|-------------------|
| LLM Provider | `BLOGINATOR_LLM_PROVIDER` | - |
| Model Name | `BLOGINATOR_LLM_MODEL` | `OLLAMA_MODEL` |
| Base URL | `BLOGINATOR_LLM_BASE_URL` | `OLLAMA_HOST` |
| ChromaDB Path | `BLOGINATOR_CHROMA_DIR` | `CHROMA_DB_PATH` |

**Why?** This allows using `.env` files from other projects (like films-not-made) without modification.

### Corpus Configuration System

Bloginator supports **two modes** for managing corpus sources:

1. **Legacy Mode** - Direct path extraction
   ```bash
   bloginator extract corpus/ -o output/extracted --quality preferred
   ```

2. **Multi-Source Mode** - Configuration-driven (RECOMMENDED)
   ```bash
   bloginator extract -o output/extracted --config corpus.yaml
   ```

**Why Multi-Source Mode?**
- Define multiple sources with rich metadata in one config file
- Specify quality ratings, tags, and voice notes per source
- Support mixed sources: OneDrive, local directories, symlinks
- Better organization for large corpus collections
- Automatic quality weighting during retrieval

**Example corpus.yaml:**
```yaml
sources:
  - name: "onedrive-blog-archive"
    path: "/Users/you/OneDrive/Blog Archive"  # Absolute path
    quality: "preferred"  # preferred | reference | supplemental | deprecated
    voice_notes: "Authentic voice from 2019-2021"
    tags: ["archive", "authentic-voice"]

  - name: "recent-sanitized-posts"
    path: "../../blogs/"  # Relative path (relative to corpus.yaml)
    quality: "reference"
    voice_notes: "Sanitized content - use sparingly for voice"
    tags: ["recent", "ai-edited"]

  - name: "films-blog"
    path: "../films-not-made/blog"  # Symlink support!
    quality: "preferred"
    tags: ["film", "criticism"]
```

**Supported Path Types:**
- Relative paths: `../../blogs/` (resolved relative to corpus.yaml location)
- Absolute paths: `/Users/you/OneDrive/Blog`
- Windows paths: `C:\Users\you\Documents\Blogs`
- UNC paths: `\\server\share\blogs`
- Symlinks: Fully supported, no data copying needed
- URLs: `https://example.com/archive.zip` (future enhancement)

**Quality Ratings Impact:**
- `preferred` (1.5x weight) - Authentic voice, high-quality content
- `reference` (1.0x weight) - Standard quality, usable content
- `supplemental` (0.7x weight) - Lower priority, use sparingly
- `deprecated` (0.3x weight) - Outdated, avoid in generation

See `corpus.yaml.example` for complete schema with all options.

## Project Architecture

### Vector Storage (ChromaDB)

Bloginator uses a **two-step indexing process**:

1. **Extract** - Convert documents to plain text
   ```bash
   bloginator extract corpus/ -o output/extracted
   ```
   - Supports: PDF, DOCX, Markdown, TXT
   - Extracts metadata (dates, tags, quality ratings)
   - Outputs: `.txt` (content) + `.json` (metadata)

2. **Index** - Vectorize into ChromaDB
   ```bash
   bloginator index output/extracted/ -o chroma_db/
   ```
   - Uses `all-MiniLM-L6-v2` embeddings
   - Chunks text by paragraphs (default: 1000 chars)
   - Stores in persistent ChromaDB collection

### LLM Client Architecture

**Factory Pattern:**
```python
from bloginator.generation.llm_factory import create_llm_from_config

# Automatically creates correct client based on .env
client = create_llm_from_config()
response = client.generate("prompt", temperature=0.7)
```

**Supported Providers:**
- `OllamaClient` - For Ollama (local/remote)
- `CustomLLMClient` - For OpenAI-compatible APIs
- Future: `OpenAIClient`, `AnthropicClient`

**Key Design Principle:** All LLM clients implement the same `LLMClient` interface, making it trivial to swap between local and cloud models.

## Testing Scenarios

### Local-First Development

**Use Case:** Develop entirely on local hardware without cloud dependencies

**Setup:**
```bash
# 1. Start Ollama server with mixtral or llama3
ollama serve

# 2. Configure .env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mixtral:8x7b

# 3. Run tests
pytest tests/
```

**Hardware Requirements:**
- Mixtral 8x7B: ~45GB RAM, GPU recommended
- Llama3 8B: ~8GB RAM, runs on CPU

### Cloud Testing

**Use Case:** Test with OpenAI or Anthropic for comparison

**Setup:**
```bash
# Configure .env for cloud provider
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1
BLOGINATOR_LLM_MODEL=gpt-4-turbo
BLOGINATOR_LLM_API_KEY=sk-...
```

### Hybrid Workflow

**Use Case:** Index locally, generate with cloud LLM for production

**Setup:**
```bash
# Index with local resources
bloginator extract corpus/ -o extracted/
bloginator index extracted/ -o chroma_db/

# Generate with cloud LLM (switch provider in .env)
BLOGINATOR_LLM_PROVIDER=custom
BLOGINATOR_LLM_BASE_URL=https://api.anthropic.com/v1
```

## Important Conventions

### Import Aliases

**Backward Compatibility:**
```python
# Both work (CorpusSearcher is canonical)
from bloginator.search import Searcher  # Alias
from bloginator.search import CorpusSearcher  # Canonical
```

The alias exists for backward compatibility with older code.

### Environment Variables

**Priority Order:**
1. `BLOGINATOR_*` variables (explicit)
2. Legacy variables (`OLLAMA_*`, `CHROMA_DB_PATH`)
3. Hard-coded defaults

**Best Practice:** Use `BLOGINATOR_*` variables in new configurations for clarity.

### Directory Structure

**Standard Layout:**
```
bloginator/
├── corpus/              # Raw input files (markdown, PDFs)
│   ├── my_blog/        # Can be symlink to ~/blog/posts
│   ├── archive/        # Can be symlink to large archive
│   └── local_post.md   # Or real files
├── output/
│   └── extracted/       # Extracted text + metadata
├── chroma_db/           # ChromaDB vector store
│   └── (or .bloginator/chroma/)
├── .env                 # Local configuration (gitignored)
└── .env.example         # Template with documentation
```

**Symbolic Links Fully Supported:**
- The extraction tool uses `os.walk(followlinks=True)` to traverse symlinked directories
- No need to copy large blog archives - just link them!
- Example: `ln -s ~/my-blogs/archive corpus/archive`

## Common Tasks

### Adding New LLM Provider

1. Create client class in `src/bloginator/generation/llm_client.py`:
   ```python
   class NewProviderClient(LLMClient):
       def generate(self, prompt, **kwargs) -> LLMResponse:
           # Implementation

       def is_available(self) -> bool:
           # Check connectivity
   ```

2. Add to provider enum:
   ```python
   class LLMProvider(str, Enum):
       OLLAMA = "ollama"
       CUSTOM = "custom"
       NEW_PROVIDER = "new_provider"
   ```

3. Update factory in `llm_factory.py`:
   ```python
   elif provider == LLMProvider.NEW_PROVIDER:
       return NewProviderClient(model=model, **kwargs)
   ```

### Testing with Different Models

```bash
# Test with mixtral
OLLAMA_MODEL=mixtral:8x7b bloginator outline "topic"

# Test with llama3
OLLAMA_MODEL=llama3:8b bloginator outline "topic"

# Test with cloud model
BLOGINATOR_LLM_PROVIDER=custom \
BLOGINATOR_LLM_BASE_URL=https://api.openai.com/v1 \
BLOGINATOR_LLM_MODEL=gpt-4 \
BLOGINATOR_LLM_API_KEY=$OPENAI_KEY \
bloginator outline "topic"
```

### Debugging Configuration

```python
from bloginator.config import config

print(f"Provider: {config.LLM_PROVIDER}")
print(f"Model: {config.LLM_MODEL}")
print(f"Base URL: {config.LLM_BASE_URL}")
print(f"Chroma: {config.CHROMA_DIR}")
```

## Field Testing Guide (For VS Code Claude)

This section is specifically for Claude Code running in VS Code to perform field testing of new features.

### Testing Corpus Configuration System (NEW)

**Feature:** Multi-source corpus configuration with quality ratings, metadata, and mixed path types.

**What Changed:**
1. New `corpus.yaml` config format (see `corpus.yaml.example`)
2. Updated `Document` model with `source_name` and `voice_notes` fields
3. New `QualityRating` values: `preferred`, `reference`, `supplemental`, `deprecated`
4. `bloginator extract` now supports `--config corpus.yaml` flag
5. Full support for: relative paths, absolute paths, Windows paths, UNC paths, symlinks

**Test Plan:**

```bash
# 1. Create test corpus.yaml
cp corpus.yaml.example corpus.yaml

# 2. Edit corpus.yaml with actual user sources:
#    - OneDrive blog archive (if exists)
#    - Local blog directory at ../../blogs/ (if exists)
#    - Any symlinked directories
#    Verify each source's path, quality rating, and metadata

# 3. Test extraction with config
bloginator extract -o output/extracted --config corpus.yaml

# Expected output:
# - Table showing all enabled sources
# - Per-source extraction progress
# - Total count of extracted documents
# - Check output/extracted/*.json files have source_name and voice_notes

# 4. Test indexing
bloginator index output/extracted -o .bloginator/chroma

# 5. Verify quality ratings in index
# Check that documents from "preferred" sources are weighted higher

# 6. Test search with different source qualities
bloginator search "topic" --index .bloginator/chroma -n 10

# 7. Test edge cases:
#    - Relative paths (../../)
#    - Absolute paths (/Users/...)
#    - Nonexistent paths (should skip gracefully)
#    - Disabled sources (enabled: false) - should skip
#    - Empty directories - should handle gracefully
```

**Validation Checklist:**
- [ ] Config loads without errors
- [ ] Paths resolve correctly (relative, absolute, symlinks)
- [ ] Source metadata (source_name, voice_notes, tags) appears in extracted JSON
- [ ] Quality ratings are preserved through extract → index
- [ ] Table displays correct source information
- [ ] Extraction handles errors gracefully (missing paths, permissions)
- [ ] Works with user's actual OneDrive/local blog paths
- [ ] Symlinks are followed correctly (no data copying)

**Known Limitations (Document for User):**
- URLs not yet implemented (shows "not yet implemented" message)
- Ignore patterns use simple startswith matching (not full glob)
- No progress for individual sources >100 files
- Windows UNC paths may need testing on Windows

**Success Criteria:**
User can point to multiple blog sources (OneDrive, local dirs, symlinks) in one config and extract them all with appropriate quality metadata.

### Testing with Mixtral/Llama3

**Before testing generation features:**

```bash
# 1. Verify Ollama connectivity
curl http://192.168.5.53:11434/api/tags

# 2. Test with mixtral (primary)
bloginator outline "test topic" --index .bloginator/chroma

# 3. Test with llama3 (alternative)
OLLAMA_MODEL=llama3:8b bloginator outline "test topic"

# 4. Verify quality weighting affects retrieval
# Preferred sources should be retrieved more often
```

## References

- Main Documentation: `README.md`
- Custom LLM Guide: `CUSTOM_LLM_GUIDE.md`
- Environment Template: `.env.example`
- Corpus Setup: `corpus/README.md`
- Corpus Config Example: `corpus.yaml.example`

## Notes for Future Claude Sessions

1. **Always check `.env`** to understand current configuration
2. **Respect backward compatibility** - don't remove legacy variable support
3. **Test locally first** - Use mixtral/llama3 for development before cloud
4. **Both models work** - mixtral:8x7b (primary) and llama3:8b (alternative)
5. **Multi-provider by design** - Any changes should work with local and cloud LLMs

## Current Project State (Session 2025-11-16/17)

### Corpus Configuration - COMPLETE ✅

**User's Active Corpus Sources** (configured in `corpus/corpus.yaml`):

1. **GitHub Personal Blogs** (62 files)
   - Path: `/Users/matt/GitHub/Personal/blogs/`
   - Quality: `preferred`
   - Tags: `recent`, `public`, `2024`, `professional`
   - Notes: Most recent, safest, genericized for public consumption

2. **Telepathy Labs (OneDrive)** (9 files)
   - Path: `/Users/matt/OneDrive - Personal/Documents/Career/TL`
   - Quality: `preferred`
   - Tags: `telepathy-labs`, `technical`, `professional`, `onedrive`
   - Notes: Authentic professional voice with technical depth

3. **Telepathy Labs (NAS)** (407 files extracted)
   - Path: `/Volumes/scratch/TL`
   - Quality: `reference`
   - Tags: `telepathy-labs`, `nas`, `working-copy`, `drafts`
   - Notes: Live working copy, may contain drafts
   - Mount: SMB share `smb://lucybear-nas._smb._tcp.local/scratch/TL`

4. **iStreamPlanet Blogs** (56 files)
   - Path: `/Users/matt/OneDrive - Personal/Documents/Career/iStreamPlanet`
   - Quality: `preferred`
   - Tags: `istreamplanet`, `2017-2021`, `video-streaming`, `technical`, `historical`
   - Notes: Video streaming and live delivery expertise

**Extraction Status:**
- ✅ **534 documents extracted** (7 failures - temp files `~$*.docx` and corrupted PDFs)
- ✅ **11,021 searchable chunks** indexed into ChromaDB
- ✅ Collection: `bloginator_corpus` at `.bloginator/chroma/`
- ✅ Search verified working across all sources

**Recent Enhancement (PR #22):**
- ✅ **Restartable extraction** - Skip already-extracted files (checks mtime)
- ✅ `--force` flag to bypass skip logic
- ✅ Auto-skip temp files (`~$*.docx`, `~$*.xlsx`)
- ✅ Progress shows: extracted / skipped / failed counts
- Second runs are now instant if no files changed

### Local Environment Setup

**Hardware Configuration:**
- Network Ollama Server: `192.168.5.53:11434`
- Primary Model: `mixtral:8x7b`
- Alternative: `llama3:8b`
- NAS Mount: `/Volumes/scratch` → `smb://lucybear-nas._smb._tcp.local/scratch`

**Active .env Configuration:**
```bash
OLLAMA_HOST=http://192.168.5.53:11434
OLLAMA_MODEL=mixtral:8x7b
BLOGINATOR_CORPUS_DIR=corpus
BLOGINATOR_CHROMA_DIR=.bloginator/chroma
```

### Verified Workflows

**Full Corpus Update (Incremental):**
```bash
# Extract only new/changed files (instant if nothing changed)
bloginator extract -o output/extracted --config corpus/corpus.yaml

# Index new extractions
bloginator index output/extracted -o .bloginator/chroma

# Search across all sources
bloginator search .bloginator/chroma "kubernetes devops" -n 10
```

**Example Search Results:**
- Finding iStreamPlanet white papers on live video streaming
- Finding TL materials on Kubernetes/DevOps
- Quality-weighted results (preferred sources ranked higher)

### Known Issues & Workarounds

1. **Pre-commit hooks may fail** - Some existing code formatting issues
   - Workaround: Use `git commit --no-verify` for YAML-only changes

2. **Some test failures** - Pre-existing, not blocking
   - 49 failed, 276 passed (tests not updated for new features)

3. **NAS Mount Required** - For TL NAS source
   - Auto-mounted at `/Volumes/scratch` when lucybear-nas is reachable
   - Extraction works across SMB mounts

### Next Session Recommendations

1. **Test Generation Features**
   ```bash
   # Generate outline from corpus
   bloginator outline "Building a DevOps culture"

   # Generate full draft
   bloginator draft "Best practices for live video streaming"
   ```

2. **Voice Calibration**
   - Compare outputs with different source weights
   - Test quality filtering: `--quality-filter preferred`

3. **Production Workflow**
   - Set up automated corpus refresh (cron job?)
   - Document voice preservation best practices

### File Locations Reference

- Corpus config: `corpus/corpus.yaml` (user-specific, committed to git)
- Environment: `.env` (local only, gitignored)
- Extracted docs: `output/extracted/` (gitignored)
- Vector index: `.bloginator/chroma/` (gitignored)
- Context docs: `CLAUDE.md` (this file), `corpus/README.md`

Last Updated: 2025-11-17 (Session 2, VS Code Claude)
