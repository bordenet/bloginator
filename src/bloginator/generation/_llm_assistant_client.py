"""LLM client that uses the AI assistant (Claude) via file-based communication."""

import json
import logging
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from bloginator.generation.llm_base import LLMClient, LLMResponse


console = Console()
logger = logging.getLogger(__name__)


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
        **kwargs: object,
    ) -> None:
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
            console.print(
                f"\n[bold blue]📤 Request {request_id} written to {request_file}[/bold blue]"
            )

        # Wait for response file
        response_file = self.response_dir / f"response_{request_id:04d}.json"

        console.print(
            f"\n[bold yellow]⏳ Waiting for AI assistant response {request_id}...[/bold yellow]"
        )
        console.print(f"[dim]Request file: {request_file}[/dim]")
        console.print(f"[dim]Expecting response: {response_file}[/dim]")
        console.print(f"[dim]Timeout: {self.timeout}s[/dim]")

        start_time = time.time()
        last_status_time = start_time
        warning_shown = False

        while not response_file.exists():
            elapsed = time.time() - start_time
            remaining = self.timeout - elapsed

            # Show status every 30 seconds
            if time.time() - last_status_time >= 30:
                last_status_time = time.time()
                console.print(
                    f"[dim]Still waiting... {int(remaining)}s remaining "
                    f"(request {request_id})[/dim]"
                )

            # Show warning when 60 seconds remain
            if remaining <= 60 and not warning_shown:
                warning_shown = True
                console.print(
                    f"\n[bold red]⚠️  WARNING: Only {int(remaining)}s remaining! "
                    f"Response needed soon.[/bold red]"
                )
                console.print(f"[bold red]   Response file: {response_file}[/bold red]")
                logger.warning(
                    f"Timeout approaching for request {request_id}: " f"{int(remaining)}s remaining"
                )

            if elapsed > self.timeout:
                error_msg = (
                    f"Timeout waiting for response {request_id} after {self.timeout}s.\n"
                    f"Expected response file: {response_file}\n"
                    f"Request file: {request_file}\n\n"
                    f"To resolve:\n"
                    f"1. Read the request file and generate a response\n"
                    f"2. Write response to: {response_file}\n"
                    f"3. Re-run the command\n\n"
                    f"Or increase timeout with BLOGINATOR_ASSISTANT_LLM_RESPONSE_TIMEOUT env var"
                )
                console.print(f"\n[bold red]❌ TIMEOUT: {error_msg}[/bold red]")
                logger.error(f"Assistant LLM timeout: {error_msg}")
                raise TimeoutError(error_msg)

            time.sleep(1)

        # Read response
        with response_file.open() as f:
            response_data = json.load(f)

        content = response_data["content"]

        if self.verbose:
            console.print(f"\n[bold green]📥 Response {request_id} received![/bold green]")
            console.print(
                Panel(
                    content[:500] + "..." if len(content) > 500 else content,
                    border_style="green",
                )
            )

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
