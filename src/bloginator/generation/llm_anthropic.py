"""Anthropic Claude LLM client implementation."""

import os

from bloginator.generation.llm_base import (
    LLMClient,
    LLMResponse,
    print_llm_request,
    print_llm_response,
)


class AnthropicClient(LLMClient):
    """Client for Anthropic Claude API.

    Supports Claude models via the Anthropic Messages API.

    Attributes:
        model: Model name (e.g., "claude-3-5-sonnet-20241022")
        api_key: Anthropic API key
        timeout: Request timeout in seconds
        verbose: Whether to print requests/responses
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: str | None = None,
        timeout: int = 120,
        verbose: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialize Anthropic client.

        Args:
            model: Claude model name
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            timeout: Request timeout in seconds
            verbose: Show LLM request/response interactions
            **kwargs: Ignored (for compatibility)
        """
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package not installed. " "Install with: pip install anthropic"
            ) from e

        self.model = model
        self.timeout = timeout
        self.verbose = verbose

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text using Claude.

        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content

        Raises:
            ValueError: If generation fails
        """
        # Display request if verbose
        if self.verbose:
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            print_llm_request(f"Anthropic - {self.model}", full_prompt)

        try:
            # Build message
            from typing import Any

            kwargs: dict[str, Any] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            # Call API
            response = self.client.messages.create(**kwargs)

            # Extract content
            content = response.content[0].text

            # Get token counts
            prompt_tokens = response.usage.input_tokens
            completion_tokens = response.usage.output_tokens

            # Display response if verbose
            if self.verbose:
                print_llm_response(content)

            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=response.stop_reason or "stop",
            )

        except Exception as e:
            raise ValueError(f"Anthropic generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if Anthropic API is available.

        Returns:
            True if API key is configured
        """
        return bool(self.api_key)
