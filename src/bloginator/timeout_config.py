"""Timeout configuration management for Bloginator.

Centralizes all timeout values used throughout the application.
Loads defaults from code but allows override via environment variables.
All timeouts are validated to be integers between 1 second and 1 day (86400s).
"""

import os

# Load .env file from project root
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


# Constants for validation
MIN_TIMEOUT_SECONDS: Final[int] = 1
MAX_TIMEOUT_SECONDS: Final[int] = 86400  # 1 day


def _validate_timeout(value: int, name: str) -> int:
    """Validate timeout value is within acceptable range.

    Args:
        value: Timeout value in seconds
        name: Name of the timeout for error messages

    Returns:
        Validated timeout value

    Raises:
        ValueError: If timeout is invalid
    """
    if not isinstance(value, int):
        raise ValueError(f"{name} must be an integer (got {type(value).__name__})")
    if value < MIN_TIMEOUT_SECONDS:
        raise ValueError(f"{name} must be >= {MIN_TIMEOUT_SECONDS} second (got {value})")
    if value > MAX_TIMEOUT_SECONDS:
        raise ValueError(f"{name} must be <= {MAX_TIMEOUT_SECONDS} seconds / 1 day (got {value})")
    return value


def _get_timeout_from_env(env_var: str, default: int, name: str) -> int:
    """Load and validate timeout from environment or use default.

    Args:
        env_var: Environment variable name
        default: Default value if env var not set
        name: Name of the timeout for error messages

    Returns:
        Validated timeout value in seconds

    Raises:
        ValueError: If env var is set but invalid
    """
    value_str = os.getenv(env_var)

    if value_str is None:
        return _validate_timeout(default, name)

    try:
        value = int(value_str)
    except ValueError:
        raise ValueError(
            f"{env_var} must be an integer (got '{value_str}'). "
            f"Valid range: {MIN_TIMEOUT_SECONDS}-{MAX_TIMEOUT_SECONDS} seconds."
        ) from None

    return _validate_timeout(value, f"{env_var}")


class TimeoutConfig:
    """Application timeout configuration from environment variables.

    All timeouts are in seconds. Valid range: 1 second to 1 day (86400 seconds).

    Attributes:
        LLM_REQUEST_TIMEOUT: Main LLM API request timeout (default 120s)
        ASSISTANT_LLM_RESPONSE_TIMEOUT: Max wait for assistant LLM response file
            (default 300s)
        SUBPROCESS_OUTLINE_TIMEOUT: Initial subprocess timeout for outline generation
            (default 2700s = 45 minutes)
        SUBPROCESS_OUTLINE_RETRY_TIMEOUT: Extended retry timeout for outline generation
            (default 5400s = 90 minutes)
        SUBPROCESS_OUTLINE_FINAL_TIMEOUT: Final retry timeout for outline generation
            (default 21600s = 6 hours)
        SUBPROCESS_DRAFT_TIMEOUT: Initial subprocess timeout for draft generation
            (default 4500s = 75 minutes, will be adjusted by generation UI)
        SUBPROCESS_DRAFT_RETRY_TIMEOUT: Extended retry timeout for draft generation
            (default 7200s = 120 minutes, will be adjusted by generation UI)
        SUBPROCESS_DRAFT_FINAL_TIMEOUT: Final retry timeout for draft generation
            (default 28800s = 8 hours, will be adjusted by generation UI)
        MODEL_AVAILABILITY_TIMEOUT: Timeout for checking if LLM model is available
            (default 5s)
        OLLAMA_TAG_CHECK_TIMEOUT: Timeout for checking Ollama available models
            (default 5s)
        SEARCH_SUBPROCESS_TIMEOUT: Timeout for corpus search subprocess (default 30s)
        ANALYSIS_SUBPROCESS_TIMEOUT: Timeout for coverage analysis subprocess
            (default 30s)
        FILE_AVAILABILITY_TIMEOUT: Timeout for waiting for file to become available
            (default 10s)
        SMB_MOUNT_TIMEOUT: Timeout for SMB mount operations (default 15s)
    """

    # LLM API request timeouts
    LLM_REQUEST_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_LLM_TIMEOUT",
        120,
        "LLM_REQUEST_TIMEOUT",
    )

    ASSISTANT_LLM_RESPONSE_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_ASSISTANT_LLM_RESPONSE_TIMEOUT",
        300,
        "ASSISTANT_LLM_RESPONSE_TIMEOUT",
    )

    # Subprocess generation timeouts (in seconds)
    SUBPROCESS_OUTLINE_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_OUTLINE_TIMEOUT",
        2700,
        "SUBPROCESS_OUTLINE_TIMEOUT",
    )
    SUBPROCESS_OUTLINE_RETRY_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_OUTLINE_RETRY_TIMEOUT",
        5400,
        "SUBPROCESS_OUTLINE_RETRY_TIMEOUT",
    )
    SUBPROCESS_OUTLINE_FINAL_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_OUTLINE_FINAL_TIMEOUT",
        21600,
        "SUBPROCESS_OUTLINE_FINAL_TIMEOUT",
    )

    SUBPROCESS_DRAFT_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_DRAFT_TIMEOUT",
        4500,
        "SUBPROCESS_DRAFT_TIMEOUT",
    )
    SUBPROCESS_DRAFT_RETRY_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_DRAFT_RETRY_TIMEOUT",
        7200,
        "SUBPROCESS_DRAFT_RETRY_TIMEOUT",
    )
    SUBPROCESS_DRAFT_FINAL_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SUBPROCESS_DRAFT_FINAL_TIMEOUT",
        28800,
        "SUBPROCESS_DRAFT_FINAL_TIMEOUT",
    )

    # Model/service availability check timeouts
    MODEL_AVAILABILITY_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_MODEL_AVAILABILITY_TIMEOUT",
        5,
        "MODEL_AVAILABILITY_TIMEOUT",
    )

    OLLAMA_TAG_CHECK_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_OLLAMA_TAG_CHECK_TIMEOUT",
        5,
        "OLLAMA_TAG_CHECK_TIMEOUT",
    )

    # Subprocess utility operation timeouts
    SEARCH_SUBPROCESS_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SEARCH_SUBPROCESS_TIMEOUT",
        30,
        "SEARCH_SUBPROCESS_TIMEOUT",
    )

    ANALYSIS_SUBPROCESS_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_ANALYSIS_SUBPROCESS_TIMEOUT",
        30,
        "ANALYSIS_SUBPROCESS_TIMEOUT",
    )

    # File and system operation timeouts
    FILE_AVAILABILITY_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_FILE_AVAILABILITY_TIMEOUT",
        10,
        "FILE_AVAILABILITY_TIMEOUT",
    )

    SMB_MOUNT_TIMEOUT: int = _get_timeout_from_env(
        "BLOGINATOR_SMB_MOUNT_TIMEOUT",
        15,
        "SMB_MOUNT_TIMEOUT",
    )

    @classmethod
    def get_outline_schedule(cls) -> list[int]:
        """Get timeout schedule for outline generation retries.

        Returns:
            List of timeouts in seconds for [initial, retry, final] attempts.
        """
        return [
            cls.SUBPROCESS_OUTLINE_TIMEOUT,
            cls.SUBPROCESS_OUTLINE_RETRY_TIMEOUT,
            cls.SUBPROCESS_OUTLINE_FINAL_TIMEOUT,
        ]

    @classmethod
    def get_draft_schedule(cls) -> list[int]:
        """Get timeout schedule for draft generation retries.

        Returns:
            List of timeouts in seconds for [initial, retry, final] attempts.
        """
        return [
            cls.SUBPROCESS_DRAFT_TIMEOUT,
            cls.SUBPROCESS_DRAFT_RETRY_TIMEOUT,
            cls.SUBPROCESS_DRAFT_FINAL_TIMEOUT,
        ]


# Singleton instance
timeout_config = TimeoutConfig()
