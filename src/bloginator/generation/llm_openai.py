"""OpenAI LLM client implementation."""

import os
from typing import TYPE_CHECKING

from bloginator.generation.llm_base import (
    LLMClient,
    LLMResponse,
    print_llm_request,
    print_llm_response,
)
from bloginator.timeout_config import timeout_config


if TYPE_CHECKING:
    from openai.types.chat import ChatCompletionMessageParam


class OpenAIClient(LLMClient):
    """Client for OpenAI API.

    Supports GPT-4, GPT-4-turbo, GPT-3.5-turbo and other OpenAI models.

    Attributes:
        model: Model name (e.g., "gpt-4o")
        api_key: OpenAI API key
        timeout: Request timeout in seconds
        verbose: Whether to print requests/responses
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        timeout: int | None = None,
        verbose: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialize OpenAI client.

        Args:
            model: OpenAI model name
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            timeout: Request timeout in seconds (uses TimeoutConfig default if None)
            verbose: Show LLM request/response interactions
            **kwargs: Ignored (for compatibility)
        """
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            ) from e

        self.model = model
        self.timeout = timeout if timeout is not None else timeout_config.LLM_REQUEST_TIMEOUT
        self.verbose = verbose

        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key, timeout=timeout)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text using OpenAI.

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
            print_llm_request(f"OpenAI - {self.model}", full_prompt)

        try:
            # Build messages with proper typing for OpenAI API
            messages: list[ChatCompletionMessageParam] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Call API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            # Extract content
            content = response.choices[0].message.content or ""

            # Get token counts
            prompt_tokens = response.usage.prompt_tokens if response.usage else 0
            completion_tokens = response.usage.completion_tokens if response.usage else 0

            # Display response if verbose
            if self.verbose:
                print_llm_response(content)

            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=response.choices[0].finish_reason or "stop",
            )

        except Exception as e:
            raise ValueError(f"OpenAI generation failed: {e}") from e

    def is_available(self) -> bool:
        """Check if OpenAI API is available.

        Returns:
            True if API key is configured
        """
        return bool(self.api_key)
