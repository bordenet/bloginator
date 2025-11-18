"""Ollama LLM client implementation."""

import json

import requests

from bloginator.generation.llm_base import (
    LLMClient,
    LLMResponse,
    print_llm_request,
    print_llm_response,
)


class OllamaClient(LLMClient):
    """Client for Ollama local LLM server.

    Ollama provides local LLM inference with models like llama3, mistral, etc.
    See: https://ollama.ai

    Attributes:
        base_url: Ollama server URL (default: http://localhost:11434)
        model: Model name to use (e.g., "llama3", "mistral")
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        verbose: bool = False,
    ):
        """Initialize Ollama client.

        Args:
            model: Model name (e.g., "llama3", "mistral", "codellama")
            base_url: Ollama server URL
            timeout: Request timeout in seconds
            verbose: Show LLM request/response interactions
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text using Ollama.

        Args:
            prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content

        Raises:
            ConnectionError: If unable to connect to Ollama
            ValueError: If generation fails
        """
        url = f"{self.base_url}/api/generate"

        # Build prompt with system instruction if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Display request if verbose
        if self.verbose:
            print_llm_request(f"Ollama - {self.model}", full_prompt)

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Extract content
            content = data.get("response", "")

            # Ollama doesn't return token counts in non-streaming mode
            # Rough estimate: ~4 chars per token
            prompt_tokens = len(full_prompt) // 4
            completion_tokens = len(content) // 4

            # Display response if verbose
            if self.verbose:
                print_llm_response(content)

            return LLMResponse(
                content=content,
                model=self.model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                finish_reason="stop",
            )

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Unable to connect to Ollama at {self.base_url}. "
                f"Is Ollama running? Start with: ollama serve"
            ) from e
        except requests.exceptions.Timeout as e:
            raise ConnectionError(f"Request to Ollama timed out after {self.timeout}s") from e
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"Ollama generation failed: {e}") from e
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid response from Ollama: {e}") from e

    def is_available(self) -> bool:
        """Check if Ollama is available.

        Returns:
            True if Ollama is running and model is available
        """
        try:
            # Check if server is running
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            # Check if our model is available
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            return self.model in model_names

        except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError):
            return False

    def list_models(self) -> list[str]:
        """List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            return [m.get("name", "") for m in models if m.get("name")]

        except (requests.exceptions.RequestException, json.JSONDecodeError):
            return []
