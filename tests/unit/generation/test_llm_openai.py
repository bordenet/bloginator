"""Tests for OpenAI LLM client."""

from unittest.mock import MagicMock, patch

import pytest


# Skip all tests if openai package is not installed
pytest.importorskip("openai", reason="OpenAI package not installed")


class TestOpenAIClient:
    """Tests for OpenAIClient."""

    def test_init_requires_api_key(self) -> None:
        """OpenAI client requires API key."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch.dict("os.environ", {"OPENAI_API_KEY": ""}),
        ):
            from bloginator.generation.llm_openai import OpenAIClient

            with pytest.raises(ValueError, match="API key required"):
                OpenAIClient()

    def test_init_with_env_api_key(self) -> None:
        """OpenAI client uses OPENAI_API_KEY from environment."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"}),
            patch("openai.OpenAI"),
        ):
            from bloginator.generation.llm_openai import OpenAIClient

            client = OpenAIClient()
            assert client.api_key == "sk-test-key"

    def test_init_with_explicit_api_key(self) -> None:
        """OpenAI client accepts explicit API key parameter."""
        with patch("openai.OpenAI"):
            from bloginator.generation.llm_openai import OpenAIClient

            client = OpenAIClient(api_key="sk-explicit-key")
            assert client.api_key == "sk-explicit-key"

    def test_default_model(self) -> None:
        """OpenAI client uses gpt-4o as default model."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}),
            patch("openai.OpenAI"),
        ):
            from bloginator.generation.llm_openai import OpenAIClient

            client = OpenAIClient()
            assert client.model == "gpt-4o"

    def test_custom_model(self) -> None:
        """OpenAI client accepts custom model name."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}),
            patch("openai.OpenAI"),
        ):
            from bloginator.generation.llm_openai import OpenAIClient

            client = OpenAIClient(model="gpt-3.5-turbo")
            assert client.model == "gpt-3.5-turbo"

    def test_generate_returns_llm_response(self) -> None:
        """Generate returns LLMResponse with content."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            mock_openai = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Generated text"))]
            mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
            mock_response.choices[0].finish_reason = "stop"
            mock_openai.return_value.chat.completions.create.return_value = mock_response

            with patch("openai.OpenAI", mock_openai):
                from bloginator.generation.llm_openai import OpenAIClient

                client = OpenAIClient()
                response = client.generate("Hello, world!")

                assert response.content == "Generated text"
                assert response.prompt_tokens == 10
                assert response.completion_tokens == 5
                assert response.finish_reason == "stop"

    def test_generate_with_system_prompt(self) -> None:
        """Generate includes system prompt when provided."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            mock_openai = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"))]
            mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
            mock_response.choices[0].finish_reason = "stop"
            mock_openai.return_value.chat.completions.create.return_value = mock_response

            with patch("openai.OpenAI", mock_openai):
                from bloginator.generation.llm_openai import OpenAIClient

                client = OpenAIClient()
                client.generate("User message", system_prompt="System instruction")

                # Verify system message was included
                call_args = mock_openai.return_value.chat.completions.create.call_args
                messages = call_args.kwargs["messages"]
                assert len(messages) == 2
                assert messages[0]["role"] == "system"
                assert messages[0]["content"] == "System instruction"

    def test_is_available_with_key(self) -> None:
        """is_available returns True when API key is set."""
        with (
            patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}),
            patch("openai.OpenAI"),
        ):
            from bloginator.generation.llm_openai import OpenAIClient

            client = OpenAIClient()
            assert client.is_available() is True

    def test_generate_raises_on_api_error(self) -> None:
        """Generate raises ValueError on API error."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
            mock_openai = MagicMock()
            mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")

            with patch("openai.OpenAI", mock_openai):
                from bloginator.generation.llm_openai import OpenAIClient

                client = OpenAIClient()
                with pytest.raises(ValueError, match="OpenAI generation failed"):
                    client.generate("Hello")
