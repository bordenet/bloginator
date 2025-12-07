"""LLM client that uses the AI assistant (Claude) via file-based communication."""

import json
import logging
import time
from pathlib import Path
from typing import Any

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
        self._response_mtimes: dict[int, float] = {}  # Track file modification times

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
                f"[bold cyan]📝 Batch request {request_id} queued ({len(self.pending_requests)} total)[/bold cyan]"
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

    def _validate_response(self, response_file: Path, request_id: int) -> dict[str, Any]:
        """Validate response JSON schema and required fields.

        Schema:
          REQUIRED: content (str) - the synthesized content
          OPTIONAL: request_id (int), tokens_used (int), error (str),
                    prompt_tokens (int), completion_tokens (int), finish_reason (str)

        Args:
            response_file: Path to response JSON file
            request_id: Expected request ID

        Returns:
            Validated response data dict

        Raises:
            ValueError: If response is invalid (missing required fields or bad types)
        """
        try:
            with response_file.open() as f:
                response_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {response_file}: {e}") from e

        # Check for error field first
        if "error" in response_data:
            error_msg = response_data.get("error", "Unknown error")
            raise ValueError(f"Response contains error: {error_msg}")

        # Validate required field: content
        if "content" not in response_data:
            raise ValueError(f"Missing required 'content' field in {response_file}")

        content = response_data["content"]
        if not isinstance(content, str):
            raise ValueError(
                f"'content' must be string in {response_file}, got {type(content).__name__}"
            )

        if len(content.strip()) == 0:
            raise ValueError(f"Empty 'content' in {response_file}")

        # Validate optional fields if present
        if "request_id" in response_data:
            rid = response_data["request_id"]
            if not isinstance(rid, int):
                logger.warning(f"Response {request_id}: request_id should be int, got {type(rid)}")

        if "tokens_used" in response_data:
            tokens = response_data["tokens_used"]
            if not isinstance(tokens, int):
                logger.warning(f"Response {request_id}: tokens_used should be int")

        return dict(response_data)

    def _check_duplicate_response(self, request_id: int, response_file: Path) -> bool:
        """Check if response file was updated (overwritten).

        Args:
            request_id: Request ID to check
            response_file: Path to response file

        Returns:
            True if this is an update to existing response
        """
        try:
            current_mtime = response_file.stat().st_mtime
        except OSError:
            return False

        if request_id in self._response_mtimes:
            previous_mtime = self._response_mtimes[request_id]
            if current_mtime > previous_mtime:
                self._response_mtimes[request_id] = current_mtime
                return True  # File was overwritten

        self._response_mtimes[request_id] = current_mtime
        return False

    def _format_elapsed(self, seconds: float) -> str:
        """Format elapsed time as mm:ss or hh:mm:ss."""
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def collect_batch_responses(self, allow_partial: bool = True) -> dict[int, LLMResponse]:
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
        if not self.pending_requests:
            return {}

        total = len(self.pending_requests)
        timeout_mins = self.timeout // 60
        min_required = int(total * self.min_response_threshold)

        console.print(
            f"\n[bold yellow]⏳ Claude thinking... (5-10min typical for {total} sections)"
            f"[/bold yellow]"
        )
        console.print(f"[dim]Timeout: {timeout_mins}m | Min required: {min_required}/{total}[/dim]")
        console.print(f"[dim]Response directory: {self.response_dir}[/dim]")

        start_time = time.time()
        last_status_time = start_time
        responses: dict[int, LLMResponse] = {}
        remaining_ids = set(self.pending_requests)
        errors: dict[int, str] = {}  # request_id -> error message

        while remaining_ids:
            elapsed = time.time() - start_time
            time_remaining = self.timeout - elapsed

            # Check for new/updated response files
            for request_id in list(remaining_ids):
                response_file = self.response_dir / f"response_{request_id:04d}.json"
                if response_file.exists():
                    # Check for duplicate/updated responses
                    is_update = self._check_duplicate_response(request_id, response_file)
                    if is_update and request_id in responses:
                        console.print(
                            f"[bold cyan]↻ Response {request_id} updated (overwrite)[/bold cyan]"
                        )

                    try:
                        response_data = self._validate_response(response_file, request_id)
                        content = response_data["content"]
                        responses[request_id] = LLMResponse(
                            content=content,
                            model=self.model,
                            prompt_tokens=response_data.get("prompt_tokens", 0),
                            completion_tokens=response_data.get(
                                "completion_tokens", len(content) // 4
                            ),
                            finish_reason=response_data.get("finish_reason", "stop"),
                        )
                        remaining_ids.remove(request_id)
                        elapsed_str = self._format_elapsed(elapsed)
                        console.print(
                            f"[bold green]✓ Response {request_id}/{total} received "
                            f"[{elapsed_str} elapsed][/bold green]"
                        )
                    except ValueError as e:
                        errors[request_id] = str(e)
                        remaining_ids.remove(request_id)
                        console.print(f"[bold red]✗ Response {request_id}: {e}[/bold red]")

            # Show progress every 15 seconds
            if time.time() - last_status_time >= 15:
                last_status_time = time.time()
                elapsed_str = self._format_elapsed(elapsed)
                remaining_str = self._format_elapsed(time_remaining)
                console.print(
                    f"[dim]⏳ Waiting for {len(remaining_ids)}/{total} responses... "
                    f"[{elapsed_str} elapsed, {remaining_str} remaining][/dim]"
                )

            # Check timeout
            if elapsed > self.timeout:
                break

            if remaining_ids:
                time.sleep(1)

        # Handle timeout/partial completion
        elapsed_str = self._format_elapsed(time.time() - start_time)
        received_count = len(responses)
        missing_ids = sorted(remaining_ids)

        # Determine if we have enough responses
        if missing_ids or errors:
            if received_count >= min_required and allow_partial:
                # Graceful degradation: add placeholders for missing responses
                console.print(
                    f"\n[bold yellow]⚠️  Partial batch: {received_count}/{total} responses "
                    f"(≥{int(self.min_response_threshold * 100)}% threshold met)[/bold yellow]"
                )

                for request_id in missing_ids:
                    placeholder = (
                        f"⚠️ **[SECTION {request_id}]** Response missing - add content manually.\n\n"
                        f"_Check `.bloginator/llm_requests/request_{request_id:04d}.json` "
                        f"for the original prompt._"
                    )
                    responses[request_id] = LLMResponse(
                        content=placeholder,
                        model=self.model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        finish_reason="missing",
                    )
                    console.print(f"[yellow]  ⚠️ Section {request_id}: using placeholder[/yellow]")

                for request_id, err in errors.items():
                    placeholder = (
                        f"⚠️ **[SECTION {request_id}]** Response error: {err}\n\n"
                        f"_Fix and re-run, or add content manually._"
                    )
                    responses[request_id] = LLMResponse(
                        content=placeholder,
                        model=self.model,
                        prompt_tokens=0,
                        completion_tokens=0,
                        finish_reason="error",
                    )
            else:
                # Not enough responses - fail
                error_msg = (
                    f"Insufficient responses after {elapsed_str}.\n"
                    f"Received: {received_count}/{total} (need ≥{min_required})\n"
                    f"Missing: {missing_ids}\n"
                )
                if errors:
                    error_msg += f"Errors: {list(errors.keys())}\n"
                error_msg += (
                    "\nTo resolve:\n"
                    "1. Check .bloginator/llm_requests/ for pending requests\n"
                    "2. Write responses to .bloginator/llm_responses/\n"
                    "3. Re-run with --batch-timeout or lower threshold"
                )
                console.print(f"\n[bold red]❌ FAILED: {error_msg}[/bold red]")
                logger.error(f"Batch failed: {error_msg}")
                raise TimeoutError(error_msg)
        else:
            console.print(
                f"\n[bold green]✅ All {received_count} batch responses received! "
                f"[{elapsed_str}][/bold green]"
            )

        # Clear pending requests
        self.pending_requests = []
        self._response_mtimes = {}
        return responses
