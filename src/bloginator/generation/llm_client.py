"""LLM client for content generation.

This module provides a unified interface for LLM clients supporting
local LLM via Ollama and custom OpenAI-compatible endpoints.

Note: This module has been refactored into smaller focused components.
This file serves as a compatibility wrapper, re-exporting all public APIs.
"""

# Re-export base classes and types
from bloginator.generation.llm_base import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    print_llm_request,
    print_llm_response,
)

# Re-export client implementations
from bloginator.generation.llm_custom import CustomLLMClient
from bloginator.generation.llm_mock import MockLLMClient
from bloginator.generation.llm_ollama import OllamaClient


def create_llm_client(
    provider: LLMProvider = LLMProvider.OLLAMA,
    model: str = "llama3",
    **kwargs,
) -> LLMClient:
    """Factory function to create LLM client.

    Args:
        provider: LLM provider to use
        model: Model name
        **kwargs: Additional arguments passed to client constructor

    Returns:
        Configured LLM client instance

    Raises:
        ValueError: If provider is not supported

    Example:
        >>> client = create_llm_client(LLMProvider.OLLAMA, model="llama3")
        >>> response = client.generate("Write a haiku about coding")
        >>> print(response.content)
    """
    if provider == LLMProvider.OLLAMA:
        return OllamaClient(model=model, **kwargs)
    elif provider == LLMProvider.CUSTOM:
        return CustomLLMClient(model=model, **kwargs)
    elif provider == LLMProvider.MOCK:
        return MockLLMClient(model=model, **kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


__all__ = [
    "LLMClient",
    "LLMProvider",
    "LLMResponse",
    "OllamaClient",
    "CustomLLMClient",
    "MockLLMClient",
    "create_llm_client",
    "print_llm_request",
    "print_llm_response",
]
