"""Factory for creating LLM clients from configuration.

This module provides a convenient way to create LLM clients using
environment variables from the config module.
"""

from bloginator.config import config
from bloginator.generation.llm_client import (
    CustomLLMClient,
    LLMClient,
    LLMProvider,
    OllamaClient,
    create_llm_client,
)


def create_llm_from_config() -> LLMClient:
    """Create LLM client from environment configuration.

    Reads configuration from environment variables (via config module)
    and creates the appropriate LLM client.

    Returns:
        Configured LLM client instance

    Raises:
        ValueError: If provider is invalid or configuration is incomplete

    Example:
        >>> from bloginator.generation.llm_factory import create_llm_from_config
        >>> client = create_llm_from_config()
        >>> response = client.generate("Write a blog post about Python")
        >>> print(response.content)
    """
    provider_str = config.LLM_PROVIDER.lower()

    try:
        provider = LLMProvider(provider_str)
    except ValueError as e:
        raise ValueError(
            f"Invalid LLM provider: {provider_str}. "
            f"Supported: {', '.join([p.value for p in LLMProvider])}"
        ) from e

    # Common parameters
    kwargs = {
        "model": config.LLM_MODEL,
        "timeout": config.LLM_TIMEOUT,
    }

    # Provider-specific parameters
    if provider == LLMProvider.OLLAMA:
        kwargs["base_url"] = config.LLM_BASE_URL
        return OllamaClient(**kwargs)

    elif provider == LLMProvider.CUSTOM:
        kwargs["base_url"] = config.LLM_BASE_URL
        if config.LLM_API_KEY:
            kwargs["api_key"] = config.LLM_API_KEY

        # Add custom headers if specified
        custom_headers = config.get_llm_headers()
        if custom_headers:
            kwargs["headers"] = custom_headers

        return CustomLLMClient(**kwargs)

    else:
        # Use generic factory (will add more providers in future)
        return create_llm_client(provider, **kwargs)


def get_default_generation_params() -> dict:
    """Get default generation parameters from config.

    Returns:
        Dictionary with temperature and max_tokens

    Example:
        >>> params = get_default_generation_params()
        >>> client.generate("prompt", **params)
    """
    return {
        "temperature": config.LLM_TEMPERATURE,
        "max_tokens": config.LLM_MAX_TOKENS,
    }
