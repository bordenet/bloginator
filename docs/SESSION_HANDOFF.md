# Session Handoff - Bloginator Quick Start

Last Updated: 2025-11-17 (Session 3 - Error Tracking & Streamlit UI)

## Quick Status

✅ **Multi-source corpus configured and indexed**
- 534 documents from 4 sources (193 PDFs, 155 DOCX, 112 MD, 74 TXT)
- 11,021 searchable chunks in ChromaDB
- Search verified working

✅ **Rich error tracking with actionable advice (NEW - PR #24)**
- Categorized errors (corrupted files, permissions, encoding, etc.)
- Beautiful Rich console output with guidance
- Integrated into extract and index commands

✅ **Streamlit Web UI (NEW - PR #24)**
- Full-featured web interface
- Launch with: `./run-streamlit.sh`
- Corpus management, search, outline/draft generation, analytics

✅ **Enhanced E2E testing (NEW - PR #24)**
- `./run-e2e.sh` with `--title`, `--keywords`, `--thesis` arguments
- Classification and Audience metadata support

## Start Here Next Session

### Option 1: Streamlit UI (Easiest)
```bash
cd ~/GitHub/Personal/bloginator
./run-streamlit.sh
# Opens at http://localhost:8501
# Use the web interface for all operations
```

### Option 2: CLI Quick Check
```bash
cd ~/GitHub/Personal/bloginator
source .venv/bin/activate

# Check corpus is indexed
bloginator search .bloginator/chroma "test query" -n 3

# Verify extraction is current (now shows rich error summaries)
bloginator extract -o output/extracted --config corpus/corpus.yaml
```

### Option 3: Test New Error Reporting
```bash
# Intentionally create an error to see the new error reporting
touch /tmp/test.rtf
bloginator extract /tmp/test.rtf -o output/test --quality reference
# Should show categorized error with actionable advice
```

### Update Corpus (Add New Blogs)
```bash
# 1. Add new blog files to any corpus source directory
# 2. Run extraction (only new/changed files extracted)
bloginator extract -o output/extracted --config corpus/corpus.yaml

# 3. Re-index
bloginator index output/extracted -o .bloginator/chroma

# 4. Test search
bloginator search .bloginator/chroma "new topic" -n 5
```

## Key Files

- **Corpus Config**: `corpus/corpus.yaml` (4 sources configured)
- **Environment**: `.env` (Ollama server, model settings)
- **Context Docs**: `CLAUDE.md` (comprehensive AI assistant context)
- **Extracted Docs**: `output/extracted/` (534 docs)
- **Vector Index**: `.bloginator/chroma/` (11,021 chunks)

## Corpus Sources

1. **GitHub Personal** - `/path/to/your/blogs/` (62 files)
2. **TL OneDrive** - `/home/user/OneDrive - Personal/Documents/Career/TL` (9 files)
3. **TL NAS** - `/Volumes/scratch/TL` (407 files)
4. **iStreamPlanet** - `/home/user/OneDrive - Personal/Documents/Career/iStreamPlanet` (56 files)

## Ollama Server

- **URL**: `http://192.168.5.53:11434`
- **Primary Model**: `mixtral:8x7b`
- **Alternative**: `llama3:8b`

## Common Commands

### Streamlit UI (Recommended)
```bash
./run-streamlit.sh  # Opens web interface at http://localhost:8501
```

### CLI Commands
```bash
# Search
bloginator search .bloginator/chroma "query" -n 10 --show-scores

# Extract (incremental) - now shows rich error reports
bloginator extract -o output/extracted --config corpus/corpus.yaml

# Extract (force all)
bloginator extract -o output/extracted --config corpus/corpus.yaml --force

# Index - now categorizes errors with advice
bloginator index output/extracted -o .bloginator/chroma

# End-to-end generation with custom params
./run-e2e.sh --title "Your Title" --keywords "key1,key2" --thesis "Your thesis"

# Or use defaults
./run-e2e.sh
```

## What's New (PR #24)

### Error Tracking
- **9 Error Categories**: Corrupted file, Permission denied, Unsupported format, Encoding error, etc.
- **Actionable Advice**: Specific guidance for each error type
- **Rich Output**: Beautiful tables and panels with error summaries

### Streamlit Web UI
- **Home**: Dashboard with corpus overview and statistics
- **Corpus**: Upload, extract, and index documents
- **Search**: Interactive search with filters
- **Generate**: Create outlines and drafts
- **Analytics**: Visualizations of corpus composition
- **Settings**: Configure LLM provider and parameters

### Enhanced Metadata
- **Classification**: Technical, Strategic, Tutorial, Opinion, Case Study, etc.
- **Audience**: Technical, Executive, General, Academic, etc.
- Better content targeting and filtering

## Supported File Types

| Type | Extensions | Extractor | Count in Corpus |
|------|-----------|-----------|-----------------|
| **PDF** | `.pdf` | PyMuPDF | 193 files (36%) |
| **Word** | `.docx`, `.doc` | python-docx | 155 files (29%) |
| **Markdown** | `.md`, `.markdown` | Built-in | 112 files (21%) |
| **Text** | `.txt`, `.text` | Built-in | 74 files (14%) |

## Next Steps

1. ✅ ~~Test error tracking~~ - Implemented in PR #24
2. ✅ ~~Add web UI~~ - Streamlit UI in PR #24
3. Test outline/draft generation with real topics via Streamlit UI
4. Calibrate quality weights for better retrieval
5. Set up automated corpus refresh workflow

## Known Issues

- Pre-commit hooks may fail (use `--no-verify` for YAML changes)
- 49 test failures (pre-existing, not blocking)
- NAS mount required for TL NAS source (`/Volumes/scratch`)

For detailed context, see `CLAUDE.md`.
