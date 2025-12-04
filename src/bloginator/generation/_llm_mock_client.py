"""Mock LLM client that returns canned responses."""

from bloginator.generation._llm_mock_responses import (
    detect_draft_request,
    detect_outline_request,
    generate_generic_response,
    generate_mock_draft,
    generate_mock_outline,
)
from bloginator.generation.llm_base import LLMClient, LLMResponse


class MockLLMClient(LLMClient):
    """Mock LLM client that returns canned responses.

    This client detects the type of request (outline or draft) based on
    the prompt content and returns appropriate realistic responses for testing.

    Attributes:
        model: Mock model name
        verbose: Whether to print requests/responses
    """

    def __init__(
        self,
        model: str = "mock-model",
        verbose: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialize mock LLM client.

        Args:
            model: Model name (always "mock-model")
            verbose: Print request/response details
            **kwargs: Ignored (for compatibility with other clients)
        """
        self.model = model
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate mock response based on prompt content.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature (ignored)
            max_tokens: Maximum tokens (ignored)
            system_prompt: System prompt (ignored)

        Returns:
            LLMResponse with mock content
        """
        # Detect request type from prompt
        if detect_outline_request(prompt):
            content = generate_mock_outline(prompt)
        elif detect_draft_request(prompt):
            content = generate_mock_draft(prompt)
        else:
            content = generate_generic_response()

        # Calculate token counts (rough estimate: 1 token ≈ 4 chars)
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4

        if self.verbose:
            from bloginator.generation.llm_base import print_llm_request, print_llm_response

            print_llm_request(self.model, prompt)
            print_llm_response(content)

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
        )

    def is_available(self) -> bool:
        """Mock client is always available.

        Returns:
            Always True
        """
        return True
