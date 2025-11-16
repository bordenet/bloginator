"""Content generation module.

This module handles:
- LLM integration (Ollama, future cloud providers)
- Outline generation from keywords and themes with RAG
- Draft generation with RAG (Retrieval-Augmented Generation)
- Source attribution and citations
- Voice similarity scoring
"""

from bloginator.generation.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    OllamaClient,
    create_llm_client,
)

__all__ = [
    "LLMClient",
    "LLMProvider",
    "LLMResponse",
    "OllamaClient",
    "create_llm_client",
]
