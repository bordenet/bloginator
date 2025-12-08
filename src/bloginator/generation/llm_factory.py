"""Factory for creating LLM clients from configuration.

This module provides a convenient way to create LLM clients using
environment variables from the config module.
"""

from typing import Any

from bloginator.config import config
from bloginator.generation.llm_client import (
    AnthropicClient,
    CustomLLMClient,
    InteractiveLLMClient,
    LLMClient,
    LLMProvider,
    MockLLMClient,
    OllamaClient,
    create_llm_client,
)
from bloginator.timeout_config import timeout_config


# Optional OpenAI client (requires openai package)
try:
    from bloginator.generation.llm_openai import OpenAIClient

    OPENAI_AVAILABLE = True
except ImportError:
    OpenAIClient = None  # type: ignore[misc, assignment]
    OPENAI_AVAILABLE = False


def create_llm_from_config(
    verbose: bool = False, batch_mode: bool = False, batch_timeout: int = 1800
) -> LLMClient:
    """Create LLM client from environment configuration.

    Reads configuration from environment variables (via config module)
    and creates the appropriate LLM client.

    Args:
        verbose: Show LLM request/response interactions

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
    import os

    # Check for mock/interactive/assistant mode first (overrides provider)
    mock_mode = os.getenv("BLOGINATOR_LLM_MOCK", "").lower()
    if mock_mode in ("true", "interactive", "assistant"):
        # Use create_llm_client which handles these modes
        # In batch mode, use the batch_timeout; otherwise use config timeout
        if batch_mode:
            timeout = batch_timeout
        elif mock_mode == "assistant":
            timeout = timeout_config.ASSISTANT_LLM_RESPONSE_TIMEOUT
        else:
            timeout = timeout_config.LLM_REQUEST_TIMEOUT
        return create_llm_client(
            provider=LLMProvider.MOCK,
            model=config.LLM_MODEL,
            batch_mode=batch_mode,
            timeout=timeout,
            verbose=verbose,
        )

    provider_str = config.LLM_PROVIDER.lower()

    try:
        provider = LLMProvider(provider_str)
    except ValueError as e:
        raise ValueError(
            f"Invalid LLM provider: {provider_str}. "
            f"Supported: {', '.join([p.value for p in LLMProvider])}"
        ) from e

    # Common parameters
    kwargs: dict[str, Any] = {
        "model": config.LLM_MODEL,
        "timeout": timeout_config.LLM_REQUEST_TIMEOUT,
        "verbose": verbose,
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

    elif provider == LLMProvider.ANTHROPIC:
        if config.LLM_API_KEY:
            kwargs["api_key"] = config.LLM_API_KEY
        return AnthropicClient(**kwargs)

    elif provider == LLMProvider.OPENAI:
        if not OPENAI_AVAILABLE or OpenAIClient is None:
            raise ImportError(
                "OpenAI provider requires openai package. "
                "Install with: pip install bloginator[cloud]"
            )
        if config.LLM_API_KEY:
            kwargs["api_key"] = config.LLM_API_KEY
        return OpenAIClient(**kwargs)

    elif provider == LLMProvider.MOCK:
        # Mock provider for testing - no additional config needed
        # Check if interactive mode is requested via environment variable
        import os

        mock_mode = os.getenv("BLOGINATOR_LLM_MOCK", "").lower()
        if mock_mode == "interactive":
            return InteractiveLLMClient(**kwargs)
        else:
            return MockLLMClient(**kwargs)

    else:
        # Use generic factory (will add more providers in future)
        return create_llm_client(provider, **kwargs)


def get_default_generation_params() -> dict[str, Any]:
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
