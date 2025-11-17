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
├── output/
│   └── extracted/       # Extracted text + metadata
├── chroma_db/           # ChromaDB vector store
│   └── (or .bloginator/chroma/)
├── .env                 # Local configuration (gitignored)
└── .env.example         # Template with documentation
```

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

## References

- Main Documentation: `README.md`
- Custom LLM Guide: `CUSTOM_LLM_GUIDE.md`
- Environment Template: `.env.example`
- Corpus Setup: `corpus/README.md`

## Notes for Future Claude Sessions

1. **Always check `.env`** to understand current configuration
2. **Respect backward compatibility** - don't remove legacy variable support
3. **Test locally first** - Use mixtral/llama3 for development before cloud
4. **Both models work** - mixtral:8x7b (primary) and llama3:8b (alternative)
5. **Multi-provider by design** - Any changes should work with local and cloud LLMs

Last Updated: 2025-11-17
