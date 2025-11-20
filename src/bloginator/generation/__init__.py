"""Content generation module.

This module handles:
- LLM integration (Ollama, future cloud providers)
- Outline generation from keywords and themes with RAG
- Draft generation with RAG (Retrieval-Augmented Generation)
- Source attribution and citations
- Voice similarity scoring
- Safety validation with blocklist integration
"""

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    OllamaClient,
    create_llm_client,
)
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.generation.safety_validator import SafetyValidator
from bloginator.generation.voice_scorer import VoiceScorer

__all__ = [
    # LLM client
    "LLMClient",
    "LLMProvider",
    "LLMResponse",
    "OllamaClient",
    "create_llm_client",
    # Generators
    "OutlineGenerator",
    "DraftGenerator",
    # Scoring and validation
    "VoiceScorer",
    "SafetyValidator",
]
