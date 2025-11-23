"""Mock LLM client for testing.

This module provides both canned-response and interactive mock LLM clients,
allowing end-to-end testing without requiring a real LLM service.
"""

import json
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from bloginator.generation.llm_base import LLMClient, LLMResponse


console = Console()


class AssistantLLMClient(LLMClient):
    """LLM client that uses the AI assistant (Claude) via file-based communication.

    This client writes prompts to files and waits for the AI assistant to provide
    responses. This enables the AI assistant to act as the LLM for optimization
    experiments without requiring API keys or external services.

    Workflow:
    1. Write prompt to .bloginator/llm_requests/request_N.json
    2. Wait for response file .bloginator/llm_responses/response_N.json
    3. Read and return the response

    Attributes:
        model: Model name (for display purposes)
        verbose: Whether to print detailed request/response info
        request_dir: Directory for request files
        response_dir: Directory for response files
        request_counter: Counter for request IDs
        timeout: Maximum seconds to wait for response
    """

    def __init__(
        self,
        model: str = "assistant-llm",
        verbose: bool = False,
        timeout: int = 300,
        **kwargs,
    ):
        """Initialize assistant LLM client.

        Args:
            model: Model name (for display)
            verbose: Print request/response details
            timeout: Maximum seconds to wait for response
            **kwargs: Ignored (for compatibility)
        """
        self.model = model
        self.verbose = verbose
        self.timeout = timeout

        # Setup directories
        self.request_dir = Path(".bloginator/llm_requests")
        self.response_dir = Path(".bloginator/llm_responses")
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

        # Request counter
        self.request_counter = 0

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate response by communicating with AI assistant via files.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: System prompt

        Returns:
            LLMResponse with assistant-provided content
        """
        self.request_counter += 1
        request_id = self.request_counter

        # Write request to file
        request_file = self.request_dir / f"request_{request_id:04d}.json"
        request_data = {
            "request_id": request_id,
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_prompt": system_prompt,
            "prompt": prompt,
            "timestamp": time.time(),
        }

        with request_file.open("w") as f:
            json.dump(request_data, f, indent=2)

        if self.verbose:
            console.print(f"\n[bold blue]📤 Request {request_id} written to {request_file}[/bold blue]")

        # Wait for response file
        response_file = self.response_dir / f"response_{request_id:04d}.json"

        console.print(f"\n[bold yellow]⏳ Waiting for AI assistant response {request_id}...[/bold yellow]")
        console.print(f"[dim]Request file: {request_file}[/dim]")
        console.print(f"[dim]Expecting response: {response_file}[/dim]")

        start_time = time.time()
        while not response_file.exists():
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                raise TimeoutError(
                    f"Timeout waiting for response {request_id} after {self.timeout}s"
                )
            time.sleep(1)

        # Read response
        with response_file.open() as f:
            response_data = json.load(f)

        content = response_data["content"]

        if self.verbose:
            console.print(f"\n[bold green]📥 Response {request_id} received![/bold green]")
            console.print(Panel(content[:500] + "..." if len(content) > 500 else content, border_style="green"))

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=response_data.get("prompt_tokens", len(prompt) // 4),
            completion_tokens=response_data.get("completion_tokens", len(content) // 4),
            finish_reason=response_data.get("finish_reason", "stop"),
        )

    def is_available(self) -> bool:
        """Assistant client is always available.

        Returns:
            Always True
        """
        return True


class InteractiveLLMClient(LLMClient):
    """Interactive LLM client that prompts the user for responses.

    This client displays the prompt to the user and waits for them to provide
    the LLM response. This allows a human (or AI assistant like Claude) to act
    as the LLM for testing and optimization experiments.

    Attributes:
        model: Model name (for display purposes)
        verbose: Whether to print detailed request/response info
    """

    def __init__(
        self,
        model: str = "interactive-llm",
        verbose: bool = False,
        **kwargs,
    ):
        """Initialize interactive LLM client.

        Args:
            model: Model name (for display)
            verbose: Print request/response details
            **kwargs: Ignored (for compatibility)
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
        """Generate response by prompting the user.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature (displayed to user)
            max_tokens: Maximum tokens (displayed to user)
            system_prompt: System prompt (displayed to user)

        Returns:
            LLMResponse with user-provided content
        """
        # Display the request
        console.print("\n" + "=" * 80, style="bold blue")
        console.print("🤖 INTERACTIVE LLM REQUEST", style="bold blue")
        console.print("=" * 80 + "\n", style="bold blue")

        console.print(f"[bold]Model:[/bold] {self.model}")
        console.print(f"[bold]Temperature:[/bold] {temperature}")
        console.print(f"[bold]Max Tokens:[/bold] {max_tokens}")

        if system_prompt:
            console.print("\n[bold yellow]SYSTEM PROMPT:[/bold yellow]")
            console.print(Panel(system_prompt, border_style="yellow"))

        console.print("\n[bold green]USER PROMPT:[/bold green]")
        console.print(Panel(prompt, border_style="green"))

        # Prompt for response
        console.print("\n" + "=" * 80, style="bold magenta")
        console.print("📝 PLEASE PROVIDE LLM RESPONSE", style="bold magenta")
        console.print("=" * 80, style="bold magenta")
        console.print(
            "[dim]Enter your response below. Type 'END_RESPONSE' on a new line when done:[/dim]\n"
        )

        # Collect multi-line response
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END_RESPONSE":
                    break
                lines.append(line)
            except EOFError:
                break

        content = "\n".join(lines)

        # Calculate token counts
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4

        if self.verbose:
            console.print("\n[bold cyan]RESPONSE RECEIVED:[/bold cyan]")
            console.print(Panel(content, border_style="cyan"))

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
        )

    def is_available(self) -> bool:
        """Interactive client is always available.

        Returns:
            Always True
        """
        return True


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
        **kwargs,
    ):
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
        if self._is_outline_request(prompt):
            content = self._generate_mock_outline(prompt)
        elif self._is_draft_request(prompt):
            content = self._generate_mock_draft(prompt)
        else:
            content = self._generate_generic_response()

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

    def _is_outline_request(self, prompt: str) -> bool:
        """Check if prompt is requesting an outline.

        Args:
            prompt: User prompt

        Returns:
            True if outline request detected
        """
        outline_keywords = [
            "outline",
            "section",
            "structure",
            "organize",
            "table of contents",
        ]
        return any(keyword in prompt.lower() for keyword in outline_keywords)

    def _is_draft_request(self, prompt: str) -> bool:
        """Check if prompt is requesting draft content.

        Args:
            prompt: User prompt

        Returns:
            True if draft request detected
        """
        draft_keywords = [
            "write",
            "draft",
            "paragraph",
            "expand",
            "content for",
        ]
        return any(keyword in prompt.lower() for keyword in draft_keywords)

    def _generate_mock_outline(self, prompt: str) -> str:
        """Generate mock outline response.

        Args:
            prompt: Outline generation prompt

        Returns:
            Markdown outline structure
        """
        # Extract title if present
        title = "Engineering Best Practices"
        if "title:" in prompt.lower():
            lines = prompt.split("\n")
            for line in lines:
                if "title:" in line.lower():
                    title = line.split(":", 1)[1].strip()
                    break

        return f"""## Introduction
Brief overview of {title.lower()} and why this topic matters for engineering teams.

## Background and Context
Historical perspective and industry trends that make this topic relevant today.

### Evolution Over Time
How practices and approaches have changed in recent years.

### Current State
Where the industry stands today on this topic.

## Core Principles
The fundamental concepts and principles that guide effective implementation.

### Key Concept 1
First major principle with practical implications.

### Key Concept 2
Second major principle and how it applies in practice.

## Practical Implementation
Concrete steps and strategies for putting these principles into action.

### Getting Started
Initial steps and foundational approaches.

### Advanced Techniques
More sophisticated methods for experienced practitioners.

## Common Challenges
Obstacles teams typically encounter and how to address them.

## Conclusion
Summary of key takeaways and recommendations for moving forward.
"""

    def _generate_mock_draft(self, prompt: str) -> str:
        """Generate mock draft content.

        Args:
            prompt: Draft generation prompt

        Returns:
            Realistic paragraph content
        """
        # Extract section title if present
        section = "this topic"
        if "section:" in prompt.lower() or "title:" in prompt.lower():
            lines = prompt.split("\n")
            for line in lines:
                if "section:" in line.lower() or "title:" in line.lower():
                    section = line.split(":", 1)[1].strip().lower()
                    break

        # Generate realistic content
        return f"""When considering {section}, it's important to understand both the theoretical
foundations and practical applications. Based on established best practices and real-world
experience, successful teams tend to focus on a few key areas.

First, establishing clear communication channels and expectations helps ensure everyone is
aligned on goals and approach. This includes both synchronous and asynchronous methods,
with documentation serving as a critical reference point.

Second, building iterative processes allows teams to learn and adapt as they progress.
Rather than trying to achieve perfection upfront, successful practitioners embrace
incremental improvement and continuous refinement. This approach reduces risk while
maintaining forward momentum.

Third, measuring outcomes and gathering feedback creates accountability and enables
data-driven decision making. Teams that regularly assess their progress and adjust based
on results tend to achieve better outcomes than those that operate on assumptions alone.

These principles, when applied consistently and thoughtfully, form the foundation for
sustainable success in this domain. The specific implementation details will vary based
on team context, organizational culture, and technical constraints, but the underlying
concepts remain broadly applicable across different environments and scenarios.
"""

    def _generate_generic_response(self) -> str:
        """Generate generic fallback response.

        Returns:
            Generic text content
        """
        return """This is a mock response generated for testing purposes.
In a real scenario, this would be replaced by actual LLM-generated content
based on the specific prompt and context provided. The mock client is designed
to simulate realistic responses without requiring an actual language model service.
"""
