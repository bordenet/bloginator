"""Batch response collection logic for assistant LLM client."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from rich.console import Console

from bloginator.generation.llm_base import LLMResponse


console = Console()
logger = logging.getLogger(__name__)


def format_elapsed(seconds: float) -> str:
    """Format elapsed time as mm:ss or hh:mm:ss.

    Args:
        seconds: Elapsed time in seconds

    Returns:
        Formatted time string
    """
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def validate_response(
    response_file: Path, request_id: int, request_dir: Path | None = None
) -> dict[str, Any]:
    """Validate response JSON schema, required fields, and timestamp.

    Schema:
      REQUIRED: content (str) - the synthesized content
      OPTIONAL: request_id (int), tokens_used (int), error (str),
                prompt_tokens (int), completion_tokens (int), finish_reason (str)

    Args:
        response_file: Path to response JSON file
        request_id: Expected request ID
        request_dir: Optional path to request directory for timestamp validation

    Returns:
        Validated response data dict

    Raises:
        ValueError: If response is invalid (missing required fields, bad types, or stale)
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

    # Validate timestamp: response must be newer than request
    if request_dir is not None:
        request_file = request_dir / f"request_{request_id:04d}.json"
        if request_file.exists():
            request_mtime = request_file.stat().st_mtime
            response_mtime = response_file.stat().st_mtime
            if response_mtime < request_mtime:
                raise ValueError(
                    f"Stale response: {response_file.name} is older than {request_file.name}. "
                    f"Delete stale responses and regenerate."
                )

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


def collect_batch_responses(
    pending_requests: list[int],
    response_dir: Path,
    model: str,
    timeout: int,
    min_response_threshold: float,
    allow_partial: bool = True,
    request_dir: Path | None = None,
) -> dict[int, LLMResponse]:
    """Wait for batch responses with graceful degradation.

    Blocks until all response files are available, timeout, or minimum threshold met.
    Returns placeholder content for missing/failed responses if allow_partial=True.

    Args:
        pending_requests: List of request IDs to wait for
        response_dir: Directory containing response files
        model: Model name for LLMResponse objects
        timeout: Maximum seconds to wait
        min_response_threshold: Minimum percentage of responses required (0.0-1.0)
        allow_partial: If True, return placeholders for missing responses if threshold met
        request_dir: Optional path to request directory for timestamp validation

    Returns:
        Dictionary mapping request_id to LLMResponse (including placeholders)

    Raises:
        TimeoutError: If threshold not met and allow_partial=False
    """
    if not pending_requests:
        return {}

    total = len(pending_requests)
    timeout_mins = timeout // 60
    min_required = int(total * min_response_threshold)
    response_mtimes: dict[int, float] = {}

    console.print(
        f"\n[bold yellow]⏳ Claude thinking... (5-10min typical for {total} sections)"
        f"[/bold yellow]"
    )
    console.print(f"[dim]Timeout: {timeout_mins}m | Min required: {min_required}/{total}[/dim]")
    console.print(f"[dim]Response directory: {response_dir}[/dim]")

    start_time = time.time()
    last_status_time = start_time
    responses: dict[int, LLMResponse] = {}
    remaining_ids = set(pending_requests)
    errors: dict[int, str] = {}

    while remaining_ids:
        elapsed = time.time() - start_time
        time_remaining = timeout - elapsed

        # Check for new/updated response files
        for request_id in list(remaining_ids):
            response_file = response_dir / f"response_{request_id:04d}.json"
            if response_file.exists():
                # Check for duplicate/updated responses
                is_update = _check_duplicate_response(request_id, response_file, response_mtimes)
                if is_update and request_id in responses:
                    console.print(
                        f"[bold cyan]↻ Response {request_id} updated (overwrite)[/bold cyan]"
                    )

                try:
                    response_data = validate_response(response_file, request_id, request_dir)
                    content = response_data["content"]
                    responses[request_id] = LLMResponse(
                        content=content,
                        model=model,
                        prompt_tokens=response_data.get("prompt_tokens", 0),
                        completion_tokens=response_data.get("completion_tokens", len(content) // 4),
                        finish_reason=response_data.get("finish_reason", "stop"),
                    )
                    remaining_ids.remove(request_id)
                    elapsed_str = format_elapsed(elapsed)
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
            elapsed_str = format_elapsed(elapsed)
            remaining_str = format_elapsed(time_remaining)
            console.print(
                f"[dim]⏳ Waiting for {len(remaining_ids)}/{total} responses... "
                f"[{elapsed_str} elapsed, {remaining_str} remaining][/dim]"
            )

        # Check timeout
        if elapsed > timeout:
            break

        if remaining_ids:
            time.sleep(1)

    # Handle timeout/partial completion
    elapsed_str = format_elapsed(time.time() - start_time)
    received_count = len(responses)
    missing_ids = sorted(remaining_ids)

    # Determine if we have enough responses
    if missing_ids or errors:
        if received_count >= min_required and allow_partial:
            _add_placeholders_for_missing(responses, missing_ids, errors, model)
            console.print(
                f"\n[bold yellow]⚠️  Partial batch: {received_count}/{total} responses "
                f"(≥{int(min_response_threshold * 100)}% threshold met)[/bold yellow]"
            )
        else:
            _raise_insufficient_responses_error(
                elapsed_str, received_count, total, min_required, missing_ids, errors
            )
    else:
        console.print(
            f"\n[bold green]✅ All {received_count} batch responses received! "
            f"[{elapsed_str}][/bold green]"
        )

    return responses


def _check_duplicate_response(
    request_id: int, response_file: Path, response_mtimes: dict[int, float]
) -> bool:
    """Check if response file was updated (overwritten).

    Args:
        request_id: Request ID to check
        response_file: Path to response file
        response_mtimes: Dictionary tracking modification times

    Returns:
        True if this is an update to existing response
    """
    try:
        current_mtime = response_file.stat().st_mtime
    except OSError:
        return False

    if request_id in response_mtimes:
        previous_mtime = response_mtimes[request_id]
        if current_mtime > previous_mtime:
            response_mtimes[request_id] = current_mtime
            return True  # File was overwritten

    response_mtimes[request_id] = current_mtime
    return False


def _add_placeholders_for_missing(
    responses: dict[int, LLMResponse],
    missing_ids: list[int],
    errors: dict[int, str],
    model: str,
) -> None:
    """Add placeholder responses for missing/errored requests.

    Args:
        responses: Dictionary to update with placeholders
        missing_ids: Request IDs that never received responses
        errors: Dictionary of request_id -> error message
        model: Model name for LLMResponse
    """
    for request_id in missing_ids:
        placeholder = (
            f"⚠️ **[SECTION {request_id}]** Response missing - add content manually.\n\n"
            f"_Check `.bloginator/llm_requests/request_{request_id:04d}.json` "
            f"for the original prompt._"
        )
        responses[request_id] = LLMResponse(
            content=placeholder,
            model=model,
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
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            finish_reason="error",
        )


def _raise_insufficient_responses_error(
    elapsed_str: str,
    received_count: int,
    total: int,
    min_required: int,
    missing_ids: list[int],
    errors: dict[int, str],
) -> None:
    """Raise TimeoutError with detailed diagnostic message.

    Args:
        elapsed_str: Formatted elapsed time
        received_count: Number of responses received
        total: Total responses expected
        min_required: Minimum required for success
        missing_ids: Request IDs that never received responses
        errors: Dictionary of request_id -> error message

    Raises:
        TimeoutError: Always raises with diagnostic message
    """
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
