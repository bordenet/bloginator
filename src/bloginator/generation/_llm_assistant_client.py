"""LLM client that uses the AI assistant (Claude) via file-based communication."""

import json
import logging
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from bloginator.generation._batch_response_collector import collect_batch_responses
from bloginator.generation.llm_base import LLMClient, LLMResponse


console = Console()
logger = logging.getLogger(__name__)


class AssistantLLMClient(LLMClient):
    """LLM client that uses the AI assistant (Claude) via file-based communication.

    This client writes prompts to files and waits for the AI assistant to provide
    responses. This enables the AI assistant to act as the LLM for optimization
    experiments without requiring API keys or external services.

    Workflow (serial mode - default):
    1. Write prompt to .bloginator/llm_requests/request_N.json
    2. Wait for response file .bloginator/llm_responses/response_N.json
    3. Read and return the response

    Workflow (batch mode - with batch_mode=True):
    1. Write ALL prompt files upfront (no waiting)
    2. Call collect_batch_responses() to wait for ALL responses
    3. Map responses back to original requests

    Attributes:
        model: Model name (for display purposes)
        verbose: Whether to print detailed request/response info
        request_dir: Directory for request files
        response_dir: Directory for response files
        request_counter: Counter for request IDs
        timeout: Maximum seconds to wait for response
        batch_mode: If True, generate requests without waiting for responses
        pending_requests: List of request IDs pending responses (batch mode only)
    """

    # Minimum percentage of responses required to proceed (0.0 - 1.0)
    MIN_RESPONSE_THRESHOLD = 0.80

    def __init__(
        self,
        model: str = "assistant-llm",
        verbose: bool = False,
        timeout: int = 1800,  # 30 minutes default for batch mode
        batch_mode: bool = False,
        min_response_threshold: float = 0.80,
        **kwargs: object,
    ) -> None:
        """Initialize assistant LLM client.

        Args:
            model: Model name (for display)
            verbose: Print request/response details
            timeout: Maximum seconds to wait for response (default: 1800 = 30min)
            batch_mode: If True, write all requests upfront without waiting
            min_response_threshold: Min % of responses required (0.0-1.0, default: 0.80)
            **kwargs: Ignored (for compatibility)
        """
        self.model = model
        self.verbose = verbose
        self.timeout = timeout
        self.batch_mode = batch_mode
        self.min_response_threshold = min_response_threshold

        # Setup directories
        self.request_dir = Path(".bloginator/llm_requests")
        self.response_dir = Path(".bloginator/llm_responses")
        self.request_dir.mkdir(parents=True, exist_ok=True)
        self.response_dir.mkdir(parents=True, exist_ok=True)

        # Request counter and pending requests for batch mode
        self.request_counter = 0
        self.pending_requests: list[int] = []

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate response by communicating with AI assistant via files.

        In batch mode, writes request file and returns placeholder immediately.
        In serial mode (default), writes request and waits for response.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            system_prompt: System prompt

        Returns:
            LLMResponse with assistant-provided content (or placeholder in batch mode)
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

        # In batch mode, track request and return placeholder
        if self.batch_mode:
            self.pending_requests.append(request_id)
            console.print(
                f"[bold cyan]📝 Batch request {request_id} queued "
                f"({len(self.pending_requests)} total)[/bold cyan]"
            )
            # Return placeholder - content will be filled by collect_batch_responses
            return LLMResponse(
                content=f"__BATCH_PLACEHOLDER_{request_id}__",
                model=self.model,
                prompt_tokens=len(prompt) // 4,
                completion_tokens=0,
                finish_reason="batch_pending",
            )

        # Serial mode: Wait for response file
        return self._wait_for_serial_response(request_id, request_file, prompt)

    def _wait_for_serial_response(
        self, request_id: int, request_file: Path, prompt: str
    ) -> LLMResponse:
        """Wait for a single response in serial mode.

        Args:
            request_id: The request ID to wait for
            request_file: Path to the request file
            prompt: Original prompt (for token estimation)

        Returns:
            LLMResponse with the response content

        Raises:
            TimeoutError: If response not received within timeout
        """
        response_file = self.response_dir / f"response_{request_id:04d}.json"

        console.print(
            f"\n[bold yellow]⏳ Waiting for AI assistant response {request_id}..." f"[/bold yellow]"
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
                self._raise_timeout_error(request_id, request_file, response_file)

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

    def _raise_timeout_error(
        self, request_id: int, request_file: Path, response_file: Path
    ) -> None:
        """Raise timeout error with helpful message.

        Args:
            request_id: The request ID that timed out
            request_file: Path to the request file
            response_file: Path to the expected response file

        Raises:
            TimeoutError: Always raises
        """
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

    def is_available(self) -> bool:
        """Assistant client is always available.

        Returns:
            Always True
        """
        return True

    def get_batch_responses(self, allow_partial: bool = True) -> dict[int, LLMResponse]:
        """Wait for batch responses with graceful degradation.

        Blocks until all response files are available, timeout, or minimum threshold met.
        Returns placeholder content for missing/failed responses if allow_partial=True.

        Args:
            allow_partial: If True, return placeholders for missing responses if ≥80% received

        Returns:
            Dictionary mapping request_id to LLMResponse (including placeholders)

        Raises:
            TimeoutError: If <80% responses received and allow_partial=False
        """
        responses = collect_batch_responses(
            pending_requests=self.pending_requests,
            response_dir=self.response_dir,
            model=self.model,
            timeout=self.timeout,
            min_response_threshold=self.min_response_threshold,
            allow_partial=allow_partial,
        )

        # Clear pending requests
        self.pending_requests = []
        return responses

    # Backwards compatibility alias
    collect_batch_responses = get_batch_responses
