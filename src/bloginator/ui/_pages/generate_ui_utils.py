"""Shared utilities for content generation UI components."""

import subprocess
import time
from datetime import datetime
from pathlib import Path

import streamlit as st


# Classification mapping: UI labels → CLI values
CLASSIFICATION_MAP = {
    "Guidance": "guidance",
    "Best Practice": "best-practice",
    "Mandate": "mandate",
    "Principle": "principle",
    "Opinion": "opinion",
}

# Audience mapping: UI labels → CLI values
AUDIENCE_MAP = {
    "All Disciplines (General)": "all-disciplines",
    "IC Engineers": "ic-engineers",
    "Senior Engineers": "senior-engineers",
    "Engineering Leaders": "engineering-leaders",
    "QA Engineers": "qa-engineers",
    "DevOps/SRE": "devops-sre",
    "Product Managers": "product-managers",
    "Technical Leadership": "technical-leadership",
    "Executives": "executives",
    "General (Non-technical)": "general",
}


def check_index_exists() -> bool:
    """Check if ChromaDB index exists.

    Returns:
        True if index directory exists, False otherwise.
    """
    index_dir = Path(".bloginator/chroma")
    return index_dir.exists()


def check_ollama_available() -> tuple[bool, str]:
    """Check if Ollama server is reachable.

    Returns:
        Tuple of (is_available, error_message).
        If available, error_message is empty.
    """
    try:
        import requests

        ollama_host = st.session_state.get("ollama_host", "http://localhost:11434")
        response = requests.get(f"{ollama_host}/api/tags", timeout=2)

        if response.status_code == 200:
            return True, ""
        else:
            return (
                False,
                f"✗ **Ollama server not reachable at {ollama_host}**\n\n"
                "Start Ollama or configure the server address in Settings.",
            )
    except Exception:
        return (
            False,
            "✗ **Ollama server not reachable**\n\n" "Start Ollama with: `ollama serve`",
        )


def create_output_directory() -> Path:
    """Create timestamped output directory for generated content.

    Returns:
        Path to created output directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/generated/{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def run_bloginator_command(cmd: list[str]) -> tuple[bool, str, str]:
    """Run bloginator CLI command with a custom retry schedule.

    Args:
        cmd: Command and arguments as list

    Returns:
        Tuple of (success, stdout, stderr).
    """
    st.info(f"Running command: `{' '.join(cmd)}`")

    # Custom timeout schedule in seconds: [45m, 90m, 6h]
    timeout_schedule = [2700, 5400, 21600]
    max_retries = len(timeout_schedule) - 1

    for attempt_num, attempt_timeout in enumerate(timeout_schedule):
        if attempt_num > 0:
            st.info(f"Retry attempt {attempt_num} (timeout: {attempt_timeout // 60} minutes)...")
        else:
            st.info(f"Initial attempt (timeout: {attempt_timeout // 60} minutes)...")

        try:
            # nosec B603 - subprocess without shell=True is safe, cmd is built from controlled inputs
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=attempt_timeout
            )  # nosec B603

            st.info(f"Command finished with return code: `{result.returncode}`")
            if result.stdout:
                with st.expander("Command stdout"):
                    st.code(result.stdout, language="text")
            if result.stderr:
                with st.expander("Command stderr"):
                    st.code(result.stderr, language="text")

            if result.returncode == 0:
                return True, result.stdout, result.stderr
            else:
                return False, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            if attempt_num < max_retries:
                st.warning(
                    f"⏱️ Attempt {attempt_num + 1} timed out "
                    f"({attempt_timeout // 60} min). Retrying with longer timeout..."
                )
                time.sleep(2)  # Brief delay before retry
                continue
            else:
                # Final timeout after all retries exhausted
                return (
                    False,
                    "",
                    f"Command timed out after {attempt_timeout} seconds (all retries exhausted)",
                )
        except Exception as e:
            return False, "", str(e)

    return False, "", "Unexpected error in command execution"


def display_generation_error(
    success: bool, stderr: str, timeout_seconds: int | None = None
) -> None:
    """Display generation error in Streamlit UI.

    Args:
        success: Whether generation succeeded
        stderr: Standard error output
        timeout_seconds: Optional timeout duration if timed out
    """
    if "timed out" in stderr.lower() or "timeout" in stderr.lower():
        st.error("✗ Generation timed out after all retry attempts")
        st.info(
            """
            Generation took too long even with extended timeouts and retries.
            This can happen with very large corpuses or slow LLM responses.

            Try:
            - Reducing corpus size or filtering documents
            - Using fewer sections/sources per section
            - Increasing available system resources
            """
        )
        if stderr:
            with st.expander("Error Details"):
                st.code(stderr, language="text")
    elif not success:
        st.error("✗ Generation failed")
        if stderr:
            with st.expander("Error Details"):
                st.code(stderr, language="text")
