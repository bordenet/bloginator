"""Tests for LLM client."""

from unittest.mock import Mock, patch

import pytest
import requests

from bloginator.generation.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    OllamaClient,
    create_llm_client,
)


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_create_response(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Test response",
            model="llama3",
            prompt_tokens=10,
            completion_tokens=20,
        )

        assert response.content == "Test response"
        assert response.model == "llama3"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30  # Auto-calculated

    def test_response_defaults(self):
        """Test response with default token values."""
        response = LLMResponse(content="Test", model="llama3")

        assert response.content == "Test"
        assert response.model == "llama3"
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0  # Auto-calculated


class TestOllamaClient:
    """Tests for Ollama client."""

    def test_initialization(self):
        """Test client initialization."""
        client = OllamaClient(model="llama3", base_url="http://localhost:11434")

        assert client.model == "llama3"
        assert client.base_url == "http://localhost:11434"

    def test_initialization_defaults(self):
        """Test default initialization."""
        client = OllamaClient()

        assert client.model == "llama3"
        assert client.base_url == "http://localhost:11434"

    @patch("requests.post")
    def test_generate_basic(self, mock_post):
        """Test basic generation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Generated content",
            "prompt_eval_count": 10,
            "eval_count": 20,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.generate(prompt="Test prompt")

        assert response.content == "Generated content"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30

        # Check API call
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["model"] == "llama3"
        assert call_kwargs["json"]["prompt"] == "Test prompt"
        assert call_kwargs["json"]["stream"] is False

    @patch("requests.post")
    def test_generate_with_system_prompt(self, mock_post):
        """Test generation with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Response",
            "prompt_eval_count": 5,
            "eval_count": 10,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()
        client.generate(
            prompt="User prompt",
            system_prompt="System instructions",
        )

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["system"] == "System instructions"

    @patch("requests.post")
    def test_generate_with_options(self, mock_post):
        """Test generation with temperature and max_tokens."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Response",
            "prompt_eval_count": 5,
            "eval_count": 10,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()
        client.generate(
            prompt="Test",
            temperature=0.5,
            max_tokens=100,
        )

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"]["options"]["temperature"] == 0.5
        assert call_kwargs["json"]["options"]["num_predict"] == 100

    @patch("requests.post")
    def test_generate_connection_error(self, mock_post):
        """Test handling of connection errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = OllamaClient()

        with pytest.raises(ConnectionError, match="Failed to connect to Ollama"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        client = OllamaClient()

        with pytest.raises(RuntimeError, match="Ollama API error"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_missing_response_field(self, mock_post):
        """Test handling of malformed response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "prompt_eval_count": 10,
            # Missing 'response' field
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()

        with pytest.raises(RuntimeError, match="Invalid response from Ollama"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_missing_token_counts(self, mock_post):
        """Test handling of missing token counts."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "Content",
            # Missing token counts
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.generate(prompt="Test")

        # Should default to 0
        assert response.content == "Content"
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0


class TestCreateLLMClient:
    """Tests for LLM client factory."""

    def test_create_ollama_client(self):
        """Test creating Ollama client."""
        client = create_llm_client(
            provider=LLMProvider.OLLAMA,
            model="llama3.1",
        )

        assert isinstance(client, OllamaClient)
        assert client.model == "llama3.1"

    def test_create_ollama_with_custom_url(self):
        """Test creating Ollama client with custom URL."""
        client = create_llm_client(
            provider=LLMProvider.OLLAMA,
            base_url="http://custom:8080",
        )

        assert isinstance(client, OllamaClient)
        assert client.base_url == "http://custom:8080"

    def test_create_default_provider(self):
        """Test default provider is Ollama."""
        client = create_llm_client()

        assert isinstance(client, OllamaClient)

    def test_create_unsupported_provider(self):
        """Test handling of unsupported provider."""
        # Note: This would require adding a new provider to the enum
        # For now, all enum values are supported
        pass


class TestLLMClientInterface:
    """Tests for LLM client abstract interface."""

    def test_llm_client_is_abstract(self):
        """Test that LLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMClient()  # type: ignore

    def test_ollama_implements_interface(self):
        """Test that OllamaClient implements LLMClient."""
        client = OllamaClient()
        assert isinstance(client, LLMClient)
