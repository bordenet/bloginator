"""Custom/OpenAI-compatible LLM client implementation."""

import json

import requests

from bloginator.generation.llm_base import (
    LLMClient,
    LLMResponse,
    print_llm_request,
    print_llm_response,
)
from bloginator.timeout_config import timeout_config


class CustomLLMClient(LLMClient):
    """Client for custom LLM endpoints (OpenAI-compatible API).

    Supports any LLM endpoint that follows OpenAI's chat completion API format.
    This includes LM Studio, vLLM, text-generation-webui, and custom endpoints.

    Attributes:
        base_url: API base URL (e.g., "http://localhost:1234/v1")
        model: Model name to use
        api_key: Optional API key for authentication
        headers: Custom headers for requests
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:1234/v1",
        api_key: str | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
        verbose: bool = False,
    ):
        """Initialize custom LLM client.

        Args:
            model: Model name
            base_url: API base URL (should end with /v1 for OpenAI compatibility)
            api_key: Optional API key (will be added to Authorization header)
            headers: Additional custom headers
            timeout: Request timeout in seconds (uses TimeoutConfig default if None)
            verbose: Show LLM request/response interactions
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout if timeout is not None else timeout_config.LLM_REQUEST_TIMEOUT
        self.verbose = verbose

        # Build headers
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        if headers:
            self.headers.update(headers)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text using custom endpoint.

        Uses OpenAI-compatible chat completion API format.

        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content

        Raises:
            ConnectionError: If unable to connect to endpoint
            ValueError: If generation fails
        """
        url = f"{self.base_url}/chat/completions"

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build full prompt for display
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Display request if verbose
        if self.verbose:
            print_llm_request(f"Custom - {self.model}", full_prompt)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extract content from OpenAI-compatible response
            content = data["choices"][0]["message"]["content"]

            # Extract token usage if available
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            # Display response if verbose
            if self.verbose:
                print_llm_response(content)

            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
            )

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Unable to connect to custom LLM at {self.base_url}. Is the service running?"
            ) from e
        except requests.exceptions.Timeout as e:
            raise ConnectionError(f"Request to custom LLM timed out after {self.timeout}s") from e
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Custom LLM generation failed: {e}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid response from custom LLM: {e}") from e

    def is_available(self) -> bool:
        """Check if custom endpoint is available.

        Returns:
            True if endpoint is reachable
        """
        try:
            # Try to hit the models endpoint
            url = f"{self.base_url}/models"
            response = requests.get(
                url, headers=self.headers, timeout=timeout_config.MODEL_AVAILABILITY_TIMEOUT
            )
            return bool(response.status_code == 200)
        except requests.exceptions.RequestException:
            return False
