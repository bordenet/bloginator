"""Configuration management for Bloginator.

Loads configuration from environment variables with sensible defaults.
Uses python-dotenv to load .env file from project root.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# Load .env file from project root
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


class Config:
    """Application configuration from environment variables.

    Attributes:
        CORPUS_DIR: Directory containing blog corpus files
        CHROMA_DIR: Directory for ChromaDB vector store
        LLM_PROVIDER: LLM provider (ollama, custom, openai, anthropic)
        LLM_MODEL: Model name to use
        LLM_BASE_URL: Base URL for LLM API (for custom/ollama)
        LLM_API_KEY: API key for cloud LLMs
        LLM_TIMEOUT: Request timeout in seconds
        LLM_TEMPERATURE: Default temperature for generation
        LLM_MAX_TOKENS: Default max tokens for generation
    """

    # Corpus and storage
    # Support both BLOGINATOR_* and legacy variable names
    CORPUS_DIR: Path = Path(os.getenv("BLOGINATOR_CORPUS_DIR", "corpus"))
    CHROMA_DIR: Path = Path(
        os.getenv("BLOGINATOR_CHROMA_DIR", os.getenv("CHROMA_DB_PATH", ".bloginator/chroma"))
    )
    OUTPUT_DIR: Path = Path(os.getenv("BLOGINATOR_OUTPUT_DIR", "output"))

    # LLM Configuration
    # Support both BLOGINATOR_* and OLLAMA_* variable names for compatibility
    LLM_PROVIDER: str = os.getenv("BLOGINATOR_LLM_PROVIDER", "ollama")
    LLM_MODEL: str = os.getenv("BLOGINATOR_LLM_MODEL", os.getenv("OLLAMA_MODEL", "llama3"))
    LLM_BASE_URL: str = os.getenv(
        "BLOGINATOR_LLM_BASE_URL", os.getenv("OLLAMA_HOST", "http://localhost:11434")
    )
    LLM_API_KEY: str | None = os.getenv("BLOGINATOR_LLM_API_KEY")
    LLM_TIMEOUT: int = int(os.getenv("BLOGINATOR_LLM_TIMEOUT", "120"))

    # Generation defaults
    LLM_TEMPERATURE: float = float(os.getenv("BLOGINATOR_LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("BLOGINATOR_LLM_MAX_TOKENS", "2000"))

    # Custom LLM headers (for authentication, etc.)
    LLM_CUSTOM_HEADERS: str | None = os.getenv("BLOGINATOR_LLM_CUSTOM_HEADERS")

    # Web UI (if using)
    WEB_HOST: str = os.getenv(
        "BLOGINATOR_WEB_HOST", "0.0.0.0"
    )  # nosec B104 - intentional for web UI
    WEB_PORT: int = int(os.getenv("BLOGINATOR_WEB_PORT", "8000"))

    # Debug
    DEBUG: bool = os.getenv("BLOGINATOR_DEBUG", "false").lower() == "true"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create necessary directories if they don't exist."""
        cls.CORPUS_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_llm_headers(cls) -> dict[str, str]:
        """Parse custom LLM headers from environment.

        Expected format: "Header1:Value1,Header2:Value2"

        Returns:
            Dictionary of headers
        """
        if not cls.LLM_CUSTOM_HEADERS:
            return {}

        headers = {}
        for header_pair in cls.LLM_CUSTOM_HEADERS.split(","):
            if ":" in header_pair:
                key, value = header_pair.split(":", 1)
                headers[key.strip()] = value.strip()

        return headers


# Singleton instance
config = Config()
