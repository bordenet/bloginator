# LLM Backend Index

> **When to load:** Overview of LLM backend modules

## Sub-Modules

| Module | Description |
|--------|-------------|
| [critical.md](critical.md) | ⚠️ CRITICAL - You are the LLM |
| [modes.md](modes.md) | LLM mode configuration |

## Quick Start

```bash
# Set assistant mode in .env
BLOGINATOR_LLM_MOCK=assistant

# Run a bloginator command
bloginator outline --index .bloginator/chroma --title "Topic" -o outline.json

# Monitor for requests and respond
ls .bloginator/llm_requests/
# Read request, synthesize from sources, write response
```

