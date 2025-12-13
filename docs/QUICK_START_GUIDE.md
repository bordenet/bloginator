# Quick Start Guide

Get started with Bloginator in 5 minutes.

## TL;DR - Using Claude (Free, No API Key)

If you have all-you-can-eat Claude access, use **assistant mode**:

```bash
# Set environment variable
export BLOGINATOR_LLM_MOCK=assistant

# Generate outline (writes request files)
bloginator outline --index .bloginator/chroma --title "Your Topic" -o outline.json

# Claude (you) responds to requests in .bloginator/llm_requests/
# → Read request → Write response to .bloginator/llm_responses/

# Generate draft (same request/response pattern)
bloginator draft --outline outline.json -o draft.md
```

**Cost**: $0 (uses your included Claude access)  
**Setup**: 10 seconds  
See [CLAUDE_API_GUIDE.md](CLAUDE_API_GUIDE.md) → "Complete Working Example" section

---

## Prerequisites

- Python 3.10+
- An indexed corpus (see [INSTALLATION.md](INSTALLATION.md))
- An LLM provider configured (Claude assistant mode, Ollama, OpenAI, Anthropic, or custom)

## 5-Minute Workflow

### 1. Extract Your Writing

```bash
bloginator extract ~/my-writing -o ./extracted --quality preferred
```

### 2. Build Index

```bash
bloginator index ./extracted -o ./my-index
```

### 3. Generate Outline

```bash
bloginator outline --index ./my-index \
  --keywords "leadership,engineering,culture" \
  -o outline.json
```

### 4. Generate Draft

```bash
bloginator draft --index ./my-index --outline outline.json -o draft.md
```

### 5. Review & Export

```bash
# View the result
cat draft.md

# Export to DOCX (optional)
bloginator export draft.md --format docx -o final.docx
```

## Web Interface (Recommended for First Time)

```bash
# Start the web server
bloginator serve --port 8000

# Open http://localhost:8000 in your browser
```

The web UI guides you through the full workflow with a visual interface.

## Next Steps

- **Detailed guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Configuration**: [INSTALLATION.md](INSTALLATION.md)
- **Advanced features**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
