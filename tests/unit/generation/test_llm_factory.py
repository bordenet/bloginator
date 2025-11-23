"""Tests for LLM factory."""

from unittest.mock import patch

import pytest

from bloginator.generation.llm_client import CustomLLMClient, MockLLMClient, OllamaClient
from bloginator.generation.llm_factory import create_llm_from_config, get_default_generation_params


class TestCreateLLMFromConfig:
    """Tests for create_llm_from_config function."""

    def test_create_ollama_client_from_config(self):
        """Test creating Ollama client from config."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "ollama"
            mock_config.LLM_MODEL = "llama3"
            mock_config.LLM_BASE_URL = "http://localhost:11434"
            mock_config.LLM_TIMEOUT = 60
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config(verbose=False)

            assert isinstance(client, OllamaClient)
            assert client.model == "llama3"
            assert client.base_url == "http://localhost:11434"
            assert client.timeout == 60
            assert client.verbose is False

    def test_create_ollama_client_with_verbose(self):
        """Test creating Ollama client with verbose mode."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "ollama"
            mock_config.LLM_MODEL = "llama3"
            mock_config.LLM_BASE_URL = "http://localhost:11434"
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config(verbose=True)

            assert isinstance(client, OllamaClient)
            assert client.verbose is True

    def test_create_mock_client_from_config(self):
        """Test creating Mock client from config."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "mock"
            mock_config.LLM_MODEL = "mock-model"
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config()

            assert isinstance(client, MockLLMClient)
            assert client.model == "mock-model"

    def test_create_custom_client_from_config(self):
        """Test creating Custom client from config."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "custom"
            mock_config.LLM_MODEL = "gpt-4"
            mock_config.LLM_BASE_URL = "https://api.example.com/v1"
            mock_config.LLM_API_KEY = "test-key-123"
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config()

            assert isinstance(client, CustomLLMClient)
            assert client.model == "gpt-4"
            assert client.base_url == "https://api.example.com/v1"
            assert client.api_key == "test-key-123"
            assert client.timeout == 120

    def test_create_custom_client_without_api_key(self):
        """Test creating Custom client without API key."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "custom"
            mock_config.LLM_MODEL = "local-model"
            mock_config.LLM_BASE_URL = "http://localhost:8000"
            mock_config.LLM_API_KEY = None
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config()

            assert isinstance(client, CustomLLMClient)
            assert client.api_key is None

    def test_create_custom_client_with_headers(self):
        """Test creating Custom client with custom headers."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "custom"
            mock_config.LLM_MODEL = "test-model"
            mock_config.LLM_BASE_URL = "http://localhost:8000"
            mock_config.LLM_API_KEY = None
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {
                "X-Custom-Header": "value",
                "Authorization": "Bearer token",
            }

            client = create_llm_from_config()

            assert isinstance(client, CustomLLMClient)
            # CustomLLMClient adds Content-Type header by default
            assert "X-Custom-Header" in client.headers
            assert client.headers["X-Custom-Header"] == "value"
            assert "Authorization" in client.headers
            assert client.headers["Authorization"] == "Bearer token"

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "invalid-provider"
            mock_config.LLM_MODEL = "test"
            mock_config.LLM_TIMEOUT = 120

            with pytest.raises(ValueError, match="Invalid LLM provider"):
                create_llm_from_config()

    def test_provider_case_insensitive(self):
        """Test that provider name is case-insensitive."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_PROVIDER = "OLLAMA"
            mock_config.LLM_MODEL = "llama3"
            mock_config.LLM_BASE_URL = "http://localhost:11434"
            mock_config.LLM_TIMEOUT = 120
            mock_config.get_llm_headers.return_value = {}

            client = create_llm_from_config()
            assert isinstance(client, OllamaClient)


class TestGetDefaultGenerationParams:
    """Tests for get_default_generation_params function."""

    def test_get_default_params(self):
        """Test getting default generation parameters."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_TEMPERATURE = 0.8
            mock_config.LLM_MAX_TOKENS = 2000

            params = get_default_generation_params()

            assert params == {
                "temperature": 0.8,
                "max_tokens": 2000,
            }

    def test_get_default_params_with_defaults(self):
        """Test getting default parameters with standard defaults."""
        with patch("bloginator.generation.llm_factory.config") as mock_config:
            mock_config.LLM_TEMPERATURE = 0.7
            mock_config.LLM_MAX_TOKENS = 2000

            params = get_default_generation_params()

            assert params == {
                "temperature": 0.7,
                "max_tokens": 2000,
            }
