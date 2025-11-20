"""Base classes and types for LLM clients."""

import sys
from abc import ABC, abstractmethod
from enum import Enum


# ANSI color codes for verbose output (only if stdout is a TTY)
if sys.stdout.isatty():
    COLOR_PROMPT = "\033[37;40m"  # Light gray on black
    COLOR_RESPONSE = "\033[33;44m"  # Yellow on dark blue
    COLOR_RESET = "\033[0m"
else:
    COLOR_PROMPT = ""
    COLOR_RESPONSE = ""
    COLOR_RESET = ""


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OLLAMA = "ollama"
    CUSTOM = "custom"
    MOCK = "mock"  # For testing without real LLM
    # Future: OPENAI = "openai", ANTHROPIC = "anthropic"


class LLMResponse:
    """Response from LLM generation.

    Attributes:
        content: Generated text content
        model: Model name used for generation
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used
        finish_reason: Reason generation stopped (e.g., "stop", "length")
    """

    def __init__(
        self,
        content: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        finish_reason: str = "stop",
    ):
        """Initialize LLM response.

        Args:
            content: Generated text
            model: Model name
            prompt_tokens: Prompt token count
            completion_tokens: Completion token count
            finish_reason: Why generation stopped
        """
        self.content = content
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.finish_reason = finish_reason


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate text from prompt.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system/instruction prompt

        Returns:
            LLMResponse with generated content

        Raises:
            ConnectionError: If unable to connect to LLM service
            ValueError: If generation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if LLM service is available.

        Returns:
            True if service is reachable and ready
        """
        pass


def print_llm_request(model: str, prompt: str) -> None:
    """Print LLM request in formatted style.

    Args:
        model: Model name
        prompt: Full prompt being sent
    """
    print(f"\n{COLOR_PROMPT}{'=' * 80}")
    print(f"LLM REQUEST ({model})")
    print(f"{'=' * 80}")
    print(prompt)
    print(f"{'=' * 80}{COLOR_RESET}\n")


def print_llm_response(content: str) -> None:
    """Print LLM response in formatted style.

    Args:
        content: Response content
    """
    print(f"\n{COLOR_RESPONSE}{'=' * 80}")
    print(f"LLM RESPONSE ({len(content)} chars)")
    print(f"{'=' * 80}")
    print(content)
    print(f"{'=' * 80}{COLOR_RESET}\n")
