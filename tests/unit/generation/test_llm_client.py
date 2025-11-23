"""Tests for LLM client."""

import os
from unittest.mock import Mock, patch

import pytest
import requests

from bloginator.generation.llm_client import (
    LLMClient,
    LLMProvider,
    LLMResponse,
    MockLLMClient,
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
        # System prompt is concatenated with user prompt
        assert call_kwargs["json"]["prompt"] == "System instructions\n\nUser prompt"

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

        with pytest.raises(ConnectionError, match="Unable to connect to Ollama"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_post.return_value = mock_response

        client = OllamaClient()

        with pytest.raises(ValueError, match="Ollama generation failed"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_missing_response_field(self, mock_post):
        """Test handling of malformed response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "prompt_eval_count": 10,
            # Missing 'response' field - should return empty string
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = OllamaClient()
        response = client.generate(prompt="Test")

        # Missing response field defaults to empty string
        assert response.content == ""
        assert response.prompt_tokens == 10  # From prompt_eval_count
        assert response.completion_tokens == 0  # len("") // 4 = 0

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

        # Should estimate based on text length (len(text) // 4)
        assert response.content == "Content"
        assert response.prompt_tokens == 1  # len("Test") // 4 = 1
        assert response.completion_tokens == 1  # len("Content") // 4 = 1
        assert response.total_tokens == 2


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

    def test_create_mock_client_via_env_var(self):
        """Test creating MockLLMClient via BLOGINATOR_LLM_MOCK environment variable."""
        # Save original env var
        original_value = os.environ.get("BLOGINATOR_LLM_MOCK")

        try:
            # Set environment variable
            os.environ["BLOGINATOR_LLM_MOCK"] = "true"

            # Should return MockLLMClient regardless of provider parameter
            client = create_llm_client(provider=LLMProvider.OLLAMA, model="llama3")

            assert isinstance(client, MockLLMClient)
            assert client.model == "llama3"
        finally:
            # Restore original env var
            if original_value is None:
                os.environ.pop("BLOGINATOR_LLM_MOCK", None)
            else:
                os.environ["BLOGINATOR_LLM_MOCK"] = original_value

    def test_create_mock_client_case_insensitive(self):
        """Test that BLOGINATOR_LLM_MOCK is case-insensitive."""
        original_value = os.environ.get("BLOGINATOR_LLM_MOCK")

        try:
            # Test various case variations
            for value in ["TRUE", "True", "true", "TrUe"]:
                os.environ["BLOGINATOR_LLM_MOCK"] = value
                client = create_llm_client()
                assert isinstance(client, MockLLMClient), f"Failed for value: {value}"
        finally:
            if original_value is None:
                os.environ.pop("BLOGINATOR_LLM_MOCK", None)
            else:
                os.environ["BLOGINATOR_LLM_MOCK"] = original_value

    def test_create_normal_client_when_env_var_false(self):
        """Test that normal client is created when BLOGINATOR_LLM_MOCK is not 'true'."""
        original_value = os.environ.get("BLOGINATOR_LLM_MOCK")

        try:
            # Test various non-true values
            for value in ["false", "False", "0", "", "yes", "1"]:
                os.environ["BLOGINATOR_LLM_MOCK"] = value
                client = create_llm_client(provider=LLMProvider.OLLAMA)
                assert isinstance(client, OllamaClient), f"Failed for value: {value}"
        finally:
            if original_value is None:
                os.environ.pop("BLOGINATOR_LLM_MOCK", None)
            else:
                os.environ["BLOGINATOR_LLM_MOCK"] = original_value

    def test_create_normal_client_when_env_var_unset(self):
        """Test that normal client is created when BLOGINATOR_LLM_MOCK is not set."""
        original_value = os.environ.get("BLOGINATOR_LLM_MOCK")

        try:
            # Ensure env var is not set
            os.environ.pop("BLOGINATOR_LLM_MOCK", None)

            client = create_llm_client(provider=LLMProvider.OLLAMA)
            assert isinstance(client, OllamaClient)
        finally:
            if original_value is not None:
                os.environ["BLOGINATOR_LLM_MOCK"] = original_value


class TestMockLLMClient:
    """Tests for MockLLMClient."""

    def test_initialization(self):
        """Test mock client initialization."""
        client = MockLLMClient(model="test-model", verbose=False)

        assert client.model == "test-model"
        assert client.verbose is False

    def test_initialization_defaults(self):
        """Test default initialization."""
        client = MockLLMClient()

        assert client.model == "mock-model"
        assert client.verbose is False

    def test_is_available(self):
        """Test that mock client is always available."""
        client = MockLLMClient()
        assert client.is_available() is True

    def test_generate_outline_request(self):
        """Test generating mock outline."""
        client = MockLLMClient()
        response = client.generate(
            prompt="Create an outline for a blog post about testing best practices"
        )

        assert response.content
        assert "## Introduction" in response.content
        assert "## Conclusion" in response.content
        assert response.model == "mock-model"
        assert response.prompt_tokens > 0
        assert response.completion_tokens > 0
        assert response.finish_reason == "stop"

    def test_generate_draft_request(self):
        """Test generating mock draft content."""
        client = MockLLMClient()
        response = client.generate(prompt="Write a paragraph about code review practices")

        assert response.content
        assert len(response.content) > 100  # Should be substantial content
        assert response.model == "mock-model"
        assert response.prompt_tokens > 0
        assert response.completion_tokens > 0

    def test_generate_generic_request(self):
        """Test generating generic response."""
        client = MockLLMClient()
        response = client.generate(prompt="Hello, how are you?")

        assert response.content
        assert "mock response" in response.content.lower()
        assert response.model == "mock-model"

    def test_generate_with_temperature(self):
        """Test that temperature parameter is accepted (but ignored)."""
        client = MockLLMClient()
        response = client.generate(prompt="Test", temperature=0.5)

        assert response.content
        # Temperature is ignored in mock, but should not cause errors

    def test_generate_with_max_tokens(self):
        """Test that max_tokens parameter is accepted (but ignored)."""
        client = MockLLMClient()
        response = client.generate(prompt="Test", max_tokens=100)

        assert response.content
        # max_tokens is ignored in mock, but should not cause errors

    def test_generate_with_system_prompt(self):
        """Test that system_prompt parameter is accepted (but ignored)."""
        client = MockLLMClient()
        response = client.generate(
            prompt="Test",
            system_prompt="You are a helpful assistant",
        )

        assert response.content
        # system_prompt is ignored in mock, but should not cause errors

    def test_token_count_estimation(self):
        """Test that token counts are estimated correctly."""
        client = MockLLMClient()
        prompt = "a" * 100  # 100 characters
        response = client.generate(prompt=prompt)

        # Token count should be roughly len(text) // 4
        assert response.prompt_tokens == 100 // 4
        assert response.completion_tokens > 0

    def test_outline_detection_keywords(self):
        """Test outline request detection with various keywords."""
        client = MockLLMClient()

        outline_prompts = [
            "Create an outline for...",
            "Generate a section structure for...",
            "Organize the table of contents...",
        ]

        for prompt in outline_prompts:
            response = client.generate(prompt=prompt)
            assert "## Introduction" in response.content, f"Failed for: {prompt}"

    def test_draft_detection_keywords(self):
        """Test draft request detection with various keywords."""
        client = MockLLMClient()

        draft_prompts = [
            "Write a paragraph about testing",
            "Expand on this topic in detail",
        ]

        for prompt in draft_prompts:
            response = client.generate(prompt=prompt)
            assert len(response.content) > 200, f"Failed for: {prompt}"
            # Draft responses should be paragraphs, not outlines
            assert response.content.count("##") < 3, f"Too many headers for: {prompt}"

    def test_verbose_mode(self, capsys):
        """Test verbose mode prints request/response."""
        client = MockLLMClient(verbose=True)
        client.generate(prompt="Test prompt")

        captured = capsys.readouterr()
        # Verbose mode should print something (exact format may vary)
        assert len(captured.out) > 0 or len(captured.err) > 0


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

    def test_mock_implements_interface(self):
        """Test that MockLLMClient implements LLMClient."""
        client = MockLLMClient()
        assert isinstance(client, LLMClient)
