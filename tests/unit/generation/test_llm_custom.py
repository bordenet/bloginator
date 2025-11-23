"""Tests for CustomLLMClient."""

from unittest.mock import Mock, patch

import pytest
import requests

from bloginator.generation.llm_custom import CustomLLMClient


class TestCustomLLMClient:
    """Tests for CustomLLMClient."""

    def test_initialization(self):
        """Test client initialization."""
        client = CustomLLMClient(
            model="gpt-4",
            base_url="https://api.openai.com/v1",
            api_key="test-key",
            timeout=60,
        )

        assert client.model == "gpt-4"
        assert client.base_url == "https://api.openai.com/v1"
        assert client.api_key == "test-key"
        assert client.timeout == 60
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-key"

    def test_initialization_strips_trailing_slash(self):
        """Test that trailing slash is removed from base_url."""
        client = CustomLLMClient(model="test", base_url="http://localhost:1234/v1/")

        assert client.base_url == "http://localhost:1234/v1"

    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        client = CustomLLMClient(model="local-model", base_url="http://localhost:1234/v1")

        assert client.api_key is None
        assert "Authorization" not in client.headers
        assert "Content-Type" in client.headers

    def test_initialization_with_custom_headers(self):
        """Test initialization with custom headers."""
        custom_headers = {"X-Custom": "value"}
        client = CustomLLMClient(model="test", headers=custom_headers)

        assert "X-Custom" in client.headers
        assert client.headers["X-Custom"] == "value"
        assert "Content-Type" in client.headers

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        """Test successful generation."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = CustomLLMClient(model="gpt-4")
        response = client.generate(prompt="Test prompt")

        assert response.content == "Generated text"
        assert response.model == "gpt-4"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
        assert response.total_tokens == 30
        assert response.finish_reason == "stop"

    @patch("requests.post")
    def test_generate_with_system_prompt(self, mock_post):
        """Test generation with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = CustomLLMClient(model="gpt-4")
        client.generate(prompt="User prompt", system_prompt="System instructions")

        call_kwargs = mock_post.call_args.kwargs
        messages = call_kwargs["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System instructions"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User prompt"

    @patch("requests.post")
    def test_generate_connection_error(self, mock_post):
        """Test handling of connection errors."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        client = CustomLLMClient(model="gpt-4")

        with pytest.raises(ConnectionError, match="Unable to connect to custom LLM"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_timeout(self, mock_post):
        """Test handling of timeout errors."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        client = CustomLLMClient(model="gpt-4", timeout=30)

        with pytest.raises(ConnectionError, match="timed out after 30s"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_post.return_value = mock_response

        client = CustomLLMClient(model="gpt-4")

        with pytest.raises(ValueError, match="Custom LLM generation failed"):
            client.generate(prompt="Test")

    @patch("requests.post")
    def test_generate_invalid_response(self, mock_post):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "structure"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = CustomLLMClient(model="gpt-4")

        with pytest.raises(ValueError, match="Invalid response from custom LLM"):
            client.generate(prompt="Test")

    @patch("requests.get")
    def test_is_available_success(self, mock_get):
        """Test is_available when endpoint is reachable."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = CustomLLMClient(model="gpt-4")
        assert client.is_available() is True

    @patch("requests.get")
    def test_is_available_failure(self, mock_get):
        """Test is_available when endpoint is not reachable."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        client = CustomLLMClient(model="gpt-4")
        assert client.is_available() is False
