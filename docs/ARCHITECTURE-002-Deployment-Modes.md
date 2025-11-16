# ARCHITECTURE-002: Deployment Modes & Component Separation

**Status**: Planning Phase
**Created**: 2025-11-16
**Last Updated**: 2025-11-16
**Related**: PRD-BLOGINATOR-001, DESIGN-SPEC-001

---

## Overview

Bloginator supports **two distinct deployment modes**:

1. **Cloud Mode** (Phase 1): Uses Claude API or OpenAI API for LLM inference
2. **Local Mode** (Phase 2): Fully offline using Ollama, like Films Not Made

This document defines the component separation, shared infrastructure, and mode-specific implementations.

---

## Deployment Mode Comparison

| Aspect | Cloud Mode | Local Mode |
|--------|-----------|------------|
| **LLM Provider** | Claude API or OpenAI API | Ollama (llama3, mistral, etc.) |
| **Embedding Model** | Local (sentence-transformers) | Local (sentence-transformers) |
| **Vector Store** | Local (ChromaDB) | Local (ChromaDB) |
| **Document Processing** | Local | Local |
| **Internet Required** | Yes (for LLM API calls) | No |
| **Privacy** | Data sent to Anthropic/OpenAI | 100% local processing |
| **Cost** | API usage charges | Hardware + electricity only |
| **Performance** | Fast (cloud GPUs) | Depends on local hardware |
| **Setup Complexity** | Low (API key only) | Medium (install Ollama, download models) |
| **Target Users** | Quick start, occasional use | Privacy-focused, heavy use |

---

## Architectural Layers

### Layer 1: Common Infrastructure (Shared by Both Modes)

These components are **identical** across both deployment modes:

#### Document Extraction & Processing
- **Module**: `src/bloginator/extraction/`
- **Functionality**:
  - PDF extraction (PyMuPDF)
  - DOCX extraction (python-docx)
  - Markdown parsing
  - Text file reading
  - ZIP archive handling
- **Dependencies**: PyMuPDF, python-docx, striprtf
- **Tests**: `tests/extraction/`

#### Metadata Management
- **Module**: `src/bloginator/models/`
- **Functionality**:
  - Document model (Pydantic)
  - Chunk model (Pydantic)
  - Blocklist model (Pydantic)
  - Version model (for draft iterations)
- **Dependencies**: Pydantic
- **Tests**: `tests/models/`

#### Embedding Generation
- **Module**: `src/bloginator/indexing/embeddings.py`
- **Functionality**:
  - sentence-transformers integration
  - Embedding caching
  - Batch embedding generation
- **Dependencies**: sentence-transformers, torch
- **Model**: all-MiniLM-L6-v2 (384-dim, local)
- **Tests**: `tests/indexing/test_embeddings.py`
- **Note**: Same in both modes—always local for privacy

#### Vector Store
- **Module**: `src/bloginator/indexing/vector_store.py`
- **Functionality**:
  - ChromaDB persistent storage
  - Metadata filtering
  - Similarity search
  - Recency/quality weighting
- **Dependencies**: ChromaDB
- **Tests**: `tests/indexing/test_vector_store.py`
- **Note**: Same in both modes—always local

#### Blocklist & Safety
- **Module**: `src/bloginator/safety/`
- **Functionality**:
  - BlocklistManager (CRUD operations)
  - Text validation against blocklist
  - Pattern matching (exact, case-insensitive, regex)
- **Dependencies**: None (stdlib only)
- **Tests**: `tests/safety/`

#### Search & Retrieval
- **Module**: `src/bloginator/search/`
- **Functionality**:
  - Semantic search
  - Recency weighting
  - Quality weighting
  - Combined scoring
- **Dependencies**: None (uses vector store)
- **Tests**: `tests/search/`

#### CLI Framework
- **Module**: `src/bloginator/cli/`
- **Functionality**:
  - Command structure (Click)
  - Common utilities (progress bars, formatting)
  - Configuration loading
- **Dependencies**: Click, Rich
- **Tests**: `tests/cli/`
- **Note**: Mode-specific commands added via subcommands

---

### Layer 2: Mode-Specific Components

These components have **different implementations** per mode:

#### LLM Abstraction Layer
- **Module**: `src/bloginator/llm/`
- **Purpose**: Provide unified interface for LLM operations
- **Implementations**:
  - `src/bloginator/llm/cloud.py` - Claude/OpenAI API
  - `src/bloginator/llm/local.py` - Ollama integration
  - `src/bloginator/llm/base.py` - Abstract base class

**Base Interface**:
```python
# src/bloginator/llm/base.py
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> str:
        """Generate text from prompt."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost/context estimation."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return model name, context window, cost info."""
        pass
```

**Cloud Implementation**:
```python
# src/bloginator/llm/cloud.py
import anthropic
import openai
from typing import Literal

class CloudLLMProvider(LLMProvider):
    def __init__(
        self,
        provider: Literal["claude", "openai"],
        api_key: str,
        model: Optional[str] = None,
    ):
        self.provider = provider
        self.api_key = api_key

        if provider == "claude":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model or "claude-3-5-sonnet-20241022"
        elif provider == "openai":
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model or "gpt-4o"
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        if self.provider == "claude":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

    def count_tokens(self, text: str) -> int:
        # Use tiktoken for OpenAI, anthropic's tokenizer for Claude
        if self.provider == "openai":
            import tiktoken
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        else:
            # Approximate for Claude (no official tokenizer in SDK yet)
            # Use anthropic.count_tokens when available
            return len(text) // 4  # Rough approximation

    def get_model_info(self) -> dict:
        if self.provider == "claude":
            return {
                "provider": "claude",
                "model": self.model,
                "context_window": 200000,
                "cost_per_1k_input": 0.003,  # $3 per million tokens
                "cost_per_1k_output": 0.015,  # $15 per million tokens
            }
        else:  # openai
            return {
                "provider": "openai",
                "model": self.model,
                "context_window": 128000,
                "cost_per_1k_input": 0.0025,  # GPT-4o pricing
                "cost_per_1k_output": 0.010,
            }
```

**Local Implementation**:
```python
# src/bloginator/llm/local.py
import ollama
from typing import Optional

class LocalLLMProvider(LLMProvider):
    def __init__(
        self,
        model: str = "llama3:8b",
        ollama_host: Optional[str] = None,
    ):
        self.model = model
        self.ollama_host = ollama_host or "http://localhost:11434"
        self.client = ollama.Client(host=self.ollama_host)

        # Verify model is available
        try:
            self.client.show(model)
        except ollama.ResponseError:
            raise ValueError(
                f"Model '{model}' not found. "
                f"Download it with: ollama pull {model}"
            )

    def generate(self, prompt: str, max_tokens: int = 2000, **kwargs) -> str:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            options={
                "num_predict": max_tokens,
                "temperature": kwargs.get("temperature", 0.7),
            },
        )
        return response['response']

    def count_tokens(self, text: str) -> int:
        # Approximate (Ollama doesn't expose tokenizer directly)
        # Most models: ~4 chars per token
        return len(text) // 4

    def get_model_info(self) -> dict:
        model_info = self.client.show(self.model)
        return {
            "provider": "ollama",
            "model": self.model,
            "ollama_host": self.ollama_host,
            "context_window": 8192,  # Typical for llama3:8b
            "cost_per_1k_input": 0.0,  # Free (local)
            "cost_per_1k_output": 0.0,
        }
```

**Factory Pattern**:
```python
# src/bloginator/llm/__init__.py
from typing import Optional, Literal
from .base import LLMProvider
from .cloud import CloudLLMProvider
from .local import LocalLLMProvider

def create_llm_provider(
    mode: Literal["cloud", "local"],
    cloud_provider: Optional[Literal["claude", "openai"]] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    ollama_host: Optional[str] = None,
) -> LLMProvider:
    """Factory function to create LLM provider based on mode."""
    if mode == "cloud":
        if not cloud_provider or not api_key:
            raise ValueError("cloud_provider and api_key required for cloud mode")
        return CloudLLMProvider(
            provider=cloud_provider,
            api_key=api_key,
            model=model,
        )
    elif mode == "local":
        return LocalLLMProvider(
            model=model or "llama3:8b",
            ollama_host=ollama_host,
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")
```

#### Generation Engine
- **Module**: `src/bloginator/generation/`
- **Functionality**:
  - Outline generation
  - Draft generation
  - Refinement
  - Voice preservation prompts
- **Mode Differences**:
  - **Cloud Mode**: Optimized prompts for Claude/GPT-4 (concise, structured)
  - **Local Mode**: Optimized prompts for Llama3 (more explicit instructions)
- **Common Code**: RAG context assembly, source attribution, validation
- **Tests**: `tests/generation/` (test both modes)

**Prompt Adaptation Example**:
```python
# src/bloginator/generation/prompts.py
def get_draft_generation_prompt(
    outline: dict,
    context_chunks: list[str],
    mode: str,
) -> str:
    """Get prompt for draft generation, adapted to LLM provider."""

    base_instructions = f"""
You are helping an engineering leader create a document.

**CRITICAL RULES**:
1. Use ONLY the provided source material (do not invent facts)
2. Preserve the author's authentic voice and characteristic phrases
3. Include inline citations [Source: document_name]
4. If source material doesn't cover a topic, say so explicitly

**Outline**:
{format_outline(outline)}

**Source Material**:
{format_chunks(context_chunks)}

**Task**: Write a complete draft following the outline.
"""

    if mode == "cloud":
        # Claude/GPT-4 can handle more nuanced instructions
        base_instructions += """
Synthesize the source material naturally while maintaining voice consistency.
Be concise and professional. Use markdown formatting.
"""
    else:  # local
        # Llama3 benefits from more explicit structure
        base_instructions += """
For each section in the outline:
1. Find relevant source material
2. Synthesize into coherent paragraph(s)
3. Add citation at end: [Source: filename]
4. Use markdown formatting (# headers, **bold**, etc.)

Write the complete draft now:
"""

    return base_instructions
```

---

### Layer 3: Configuration & Mode Selection

#### Configuration Files

**User Configuration** (`~/.bloginator/config.yaml`):
```yaml
# Deployment mode: "cloud" or "local"
mode: cloud

# Cloud mode settings
cloud:
  provider: claude  # or "openai"
  api_key_env: ANTHROPIC_API_KEY  # Environment variable name
  model: claude-3-5-sonnet-20241022
  cost_limit_per_session: 5.00  # USD

# Local mode settings
local:
  ollama_host: http://localhost:11434
  model: llama3:8b

# Common settings
corpus:
  default_index_dir: ~/.bloginator/index
  default_quality_rating: standard

blocklist:
  file: ~/.bloginator/blocklist.json

generation:
  max_tokens: 4000
  temperature: 0.7
  recency_weight: 0.2
  quality_weight: 0.1
```

#### Environment Variables

```bash
# Cloud mode
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...

# Local mode (optional, if remote Ollama server)
export OLLAMA_HOST=http://192.168.1.100:11434

# Cost control
export BLOGINATOR_COST_LIMIT=10.00  # Max spend per session (USD)
```

#### CLI Mode Selection

Users specify mode via CLI flag or config file:

```bash
# Cloud mode (Claude)
bloginator --mode cloud --cloud-provider claude outline "senior engineer career ladder"

# Cloud mode (OpenAI)
bloginator --mode cloud --cloud-provider openai draft outline.json

# Local mode
bloginator --mode local --local-model llama3:8b draft outline.json

# Or use config file default
bloginator draft outline.json  # Uses mode from config.yaml
```

---

## Cost Control Measures (Cloud Mode Only)

### 1. Token Counting & Estimation

**Before Generation**:
```python
# src/bloginator/generation/cost_control.py
from bloginator.llm import LLMProvider

class CostController:
    def __init__(self, llm: LLMProvider, limit_usd: float):
        self.llm = llm
        self.limit_usd = limit_usd
        self.session_cost = 0.0

    def estimate_cost(self, prompt: str, max_tokens: int) -> dict:
        """Estimate cost before generation."""
        model_info = self.llm.get_model_info()

        input_tokens = self.llm.count_tokens(prompt)
        output_tokens = max_tokens  # Worst case

        input_cost = (input_tokens / 1000) * model_info['cost_per_1k_input']
        output_cost = (output_tokens / 1000) * model_info['cost_per_1k_output']
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": total_cost,
            "would_exceed_limit": (self.session_cost + total_cost) > self.limit_usd,
        }

    def check_and_track(self, prompt: str, max_tokens: int) -> bool:
        """Check if generation would exceed limit. Returns True if OK to proceed."""
        estimate = self.estimate_cost(prompt, max_tokens)

        if estimate['would_exceed_limit']:
            print(f"⚠️  Cost limit would be exceeded!")
            print(f"   Session cost so far: ${self.session_cost:.4f}")
            print(f"   This generation: ${estimate['estimated_cost_usd']:.4f}")
            print(f"   Limit: ${self.limit_usd:.2f}")
            return False

        self.session_cost += estimate['estimated_cost_usd']
        return True
```

**Usage in Generation**:
```python
def generate_draft(outline, context, llm, cost_controller):
    prompt = create_prompt(outline, context)

    # Check cost before generation
    if not cost_controller.check_and_track(prompt, max_tokens=4000):
        raise CostLimitExceeded("Operation would exceed cost limit")

    # Proceed with generation
    draft = llm.generate(prompt, max_tokens=4000)
    return draft
```

### 2. Session Cost Tracking

Display running costs to user:
```
$ bloginator draft outline.json --mode cloud --cloud-provider claude

⚙️  Generating draft...
   Estimated cost: $0.12
   Session total: $0.35 / $5.00

✓ Draft generated (1247 tokens, $0.11 actual)
  Session total: $0.34 / $5.00
```

### 3. Cost Limits

**Per-Session Limit**:
- Configurable in `config.yaml` or environment variable
- Default: $5.00 USD
- Hard stop when limit reached

**Per-Operation Warnings**:
- Warn if single operation > $1.00
- Require confirmation for operations > $2.00

### 4. Caching & Optimization

**Avoid Redundant API Calls**:
- Cache outline generation results
- Reuse context assembly across refinements
- Incremental refinement (only regenerate changed sections)

**Context Window Optimization**:
- Truncate context to relevant chunks only
- Use smaller context windows when possible
- Prefer cheaper models for simple tasks (e.g., haiku for outlines)

### 5. Budget Presets

Predefined cost profiles:
```yaml
cost_profiles:
  experimental:
    limit: 1.00
    model: claude-3-haiku-20240307  # Cheaper model

  standard:
    limit: 5.00
    model: claude-3-5-sonnet-20241022

  production:
    limit: 20.00
    model: claude-3-5-sonnet-20241022
    confirmation_threshold: 5.00  # Confirm if op > $5
```

---

## Implementation Phases (Revised)

### Phase 1A: Cloud Mode (Claude) - Week 1-3
- All common infrastructure (extraction, indexing, search, blocklist)
- CloudLLMProvider (Claude implementation)
- Generation engine with Claude-optimized prompts
- Cost control and tracking
- CLI with cloud mode
- **Deliverable**: Working system with Claude API

### Phase 1B: Cloud Mode (OpenAI) - Week 4
- OpenAI implementation in CloudLLMProvider
- Prompt optimization for GPT-4
- Cost control adapted for OpenAI pricing
- Side-by-side testing (Claude vs OpenAI quality)
- **Deliverable**: Both cloud providers supported

### Phase 2: Local Mode - Weeks 5-6
- LocalLLMProvider (Ollama implementation)
- Prompt optimization for Llama3/Mistral
- Local model download and setup automation
- Network Ollama support (remote server)
- Performance benchmarking
- **Deliverable**: Fully offline mode working

### Phase 3: Web UI - Weeks 7-8
- Web interface supporting both modes
- Mode switching in UI
- Cost dashboard (cloud mode)
- Model management (local mode)
- **Deliverable**: Complete web application

---

## Testing Strategy by Mode

### Common Infrastructure Tests
- **Unit tests**: All shared modules (extraction, indexing, search, blocklist)
- **Coverage**: 80%+ for all common code
- **Run**: Every commit via pre-commit hooks

### Cloud Mode Tests
- **Unit tests**: CloudLLMProvider (both Claude and OpenAI)
- **Integration tests**: Full generation workflow with real API calls
- **Cost tests**: Verify cost estimation accuracy
- **Tests use**: Small test corpus, minimal API calls (cost < $0.10 per test run)
- **CI/CD**: Use API keys from secrets, run on main branch only

### Local Mode Tests
- **Unit tests**: LocalLLMProvider
- **Integration tests**: Full generation workflow with Ollama
- **Performance tests**: Latency, throughput, memory usage
- **Tests require**: Ollama running with llama3:8b downloaded
- **CI/CD**: Run on self-hosted runner with Ollama (or skip in GitHub Actions)

### Cross-Mode Tests
- **Compatibility**: Same inputs should work in both modes
- **Quality**: Compare output quality (cloud vs local)
- **Voice preservation**: Voice similarity scores should be similar
- **Validation**: Both modes should enforce blocklist identically

---

## Dependency Management

### Common Dependencies
```toml
[project]
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pydantic>=2.0",
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
    "torch>=2.0",  # For embeddings
    "pymupdf>=1.23.0",
    "python-docx>=1.0.0",
    "striprtf>=0.0.26",
    "pyyaml>=6.0",
]
```

### Cloud Mode Dependencies
```toml
[project.optional-dependencies]
cloud = [
    "anthropic>=0.25.0",
    "openai>=1.0.0",
    "tiktoken>=0.5.0",  # For OpenAI token counting
]
```

### Local Mode Dependencies
```toml
[project.optional-dependencies]
local = [
    "ollama>=0.1.0",
]
```

### Installation
```bash
# Cloud mode (Claude)
pip install -e ".[cloud]"

# Cloud mode (OpenAI)
pip install -e ".[cloud]"

# Local mode
pip install -e ".[local]"

# Both modes
pip install -e ".[cloud,local]"

# Development (all modes + dev tools)
pip install -e ".[cloud,local,dev]"
```

---

## Mode Selection Decision Tree

```
User wants to use Bloginator
    │
    ├─> Privacy is critical
    │   └─> Local Mode
    │       ├─> Has powerful machine → Ollama local
    │       └─> Has network server → Ollama remote
    │
    ├─> Occasional use, ease of setup
    │   └─> Cloud Mode
    │       ├─> Prefers Claude → Claude API
    │       └─> Prefers OpenAI → OpenAI API
    │
    └─> Heavy use, budget-conscious
        └─> Local Mode (avoid ongoing API costs)
```

---

## Future Extensions

### Hybrid Mode (Future)
- Use cloud LLM for complex tasks (outline generation)
- Use local LLM for simple tasks (refinements)
- Automatically switch based on task complexity and cost

### Multi-Model Support (Future)
- Support multiple cloud providers simultaneously
- A/B test outputs from different models
- Ensemble voting for quality

### Edge Deployment (Future)
- Package as Docker container
- Deploy to edge devices (Mac Mini, NUC)
- Mobile-friendly web UI

---

*End of ARCHITECTURE-002*
