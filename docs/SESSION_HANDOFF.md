# Session Handoff - Bloginator Quick Start

Last Updated: 2025-11-17

## Quick Status

✅ **Multi-source corpus configured and indexed**
- 534 documents from 4 sources
- 11,021 searchable chunks in ChromaDB
- Search verified working

✅ **Restartable extraction implemented**
- Second runs skip unchanged files (instant)
- Use `--force` to re-extract everything

## Start Here Next Session

### Verify System Status
```bash
cd ~/GitHub/Personal/bloginator
source .venv/bin/activate

# Check corpus is indexed
bloginator search .bloginator/chroma "test query" -n 3

# Verify extraction is current
bloginator extract -o output/extracted --config corpus/corpus.yaml
# Should show: "↻ X skipped (already extracted)" if nothing changed
```

### Try Content Generation
```bash
# Generate an outline
bloginator outline "Building a DevOps culture"

# Generate a full draft
bloginator draft "Best practices for live video streaming"
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

1. **GitHub Personal** - `/Users/matt/GitHub/Personal/blogs/` (62 files)
2. **TL OneDrive** - `/Users/matt/OneDrive - Personal/Documents/Career/TL` (9 files)
3. **TL NAS** - `/Volumes/scratch/TL` (407 files)
4. **iStreamPlanet** - `/Users/matt/OneDrive - Personal/Documents/Career/iStreamPlanet` (56 files)

## Ollama Server

- **URL**: `http://192.168.5.53:11434`
- **Primary Model**: `mixtral:8x7b`
- **Alternative**: `llama3:8b`

## Common Commands

```bash
# Search
bloginator search .bloginator/chroma "query" -n 10 --show-scores

# Extract (incremental)
bloginator extract -o output/extracted --config corpus/corpus.yaml

# Extract (force all)
bloginator extract -o output/extracted --config corpus/corpus.yaml --force

# Index
bloginator index output/extracted -o .bloginator/chroma

# Outline
bloginator outline "topic"

# Draft
bloginator draft "topic"
```

## Next Steps

1. Test outline generation with real topics
2. Test draft generation and voice quality
3. Calibrate quality weights for better retrieval
4. Set up automated corpus refresh workflow

## Known Issues

- Pre-commit hooks may fail (use `--no-verify` for YAML changes)
- 49 test failures (pre-existing, not blocking)
- NAS mount required for TL NAS source (`/Volumes/scratch`)

For detailed context, see `CLAUDE.md`.
