"""Tests for configuration management."""

from pathlib import Path

from bloginator.config import Config


class TestConfigPaths:
    """Test path resolution in Config."""

    def test_resolve_path_absolute(self, tmp_path: Path) -> None:
        """Absolute paths should be returned unchanged."""
        config = Config()
        result = config._resolve_path(str(tmp_path), "default")
        assert result == tmp_path

    def test_resolve_path_relative(self) -> None:
        """Relative paths should be resolved under DATA_DIR."""
        config = Config()
        result = config._resolve_path("subdir", "default")
        assert result == Config.DATA_DIR / "subdir"

    def test_corpus_dir_property(self) -> None:
        """corpus_dir property should return resolved path."""
        config = Config()
        result = config.corpus_dir
        assert isinstance(result, Path)

    def test_chroma_dir_property(self) -> None:
        """chroma_dir property should return resolved path."""
        config = Config()
        result = config.chroma_dir
        assert isinstance(result, Path)

    def test_output_dir_property(self) -> None:
        """output_dir property should return resolved path."""
        config = Config()
        result = config.output_dir
        assert isinstance(result, Path)


class TestConfigDirectories:
    """Test directory creation."""

    def test_ensure_directories_creates_dirs(self, tmp_path: Path, monkeypatch) -> None:
        """ensure_directories should create all required directories."""
        # Set DATA_DIR to temp path
        monkeypatch.setattr(Config, "DATA_DIR", tmp_path / "bloginator")
        monkeypatch.setattr(Config, "_corpus_dir_env", "corpus")
        monkeypatch.setattr(Config, "_chroma_dir_env", "chroma")
        monkeypatch.setattr(Config, "_output_dir_env", "output")

        Config.ensure_directories()

        assert (tmp_path / "bloginator").exists()
        assert (tmp_path / "bloginator" / "corpus").exists()
        assert (tmp_path / "bloginator" / "chroma").exists()
        assert (tmp_path / "bloginator" / "output").exists()


class TestConfigLLMHeaders:
    """Test LLM header parsing."""

    def test_get_llm_headers_empty(self, monkeypatch) -> None:
        """Empty headers should return empty dict."""
        monkeypatch.setattr(Config, "LLM_CUSTOM_HEADERS", None)
        result = Config.get_llm_headers()
        assert result == {}

    def test_get_llm_headers_single(self, monkeypatch) -> None:
        """Single header should be parsed correctly."""
        monkeypatch.setattr(Config, "LLM_CUSTOM_HEADERS", "Authorization:Bearer token123")
        result = Config.get_llm_headers()
        assert result == {"Authorization": "Bearer token123"}

    def test_get_llm_headers_multiple(self, monkeypatch) -> None:
        """Multiple headers should be parsed correctly."""
        monkeypatch.setattr(
            Config, "LLM_CUSTOM_HEADERS", "Authorization:Bearer token,X-Custom:value"
        )
        result = Config.get_llm_headers()
        assert result == {"Authorization": "Bearer token", "X-Custom": "value"}

    def test_get_llm_headers_with_spaces(self, monkeypatch) -> None:
        """Headers with spaces should be trimmed."""
        monkeypatch.setattr(Config, "LLM_CUSTOM_HEADERS", " Key : Value ")
        result = Config.get_llm_headers()
        assert result == {"Key": "Value"}

    def test_get_llm_headers_invalid_format(self, monkeypatch) -> None:
        """Invalid header format should be skipped."""
        monkeypatch.setattr(Config, "LLM_CUSTOM_HEADERS", "InvalidNoColon,Valid:Value")
        result = Config.get_llm_headers()
        assert result == {"Valid": "Value"}


class TestConfigDefaults:
    """Test configuration defaults."""

    def test_llm_provider_default(self) -> None:
        """LLM_PROVIDER should have a default value."""
        assert Config.LLM_PROVIDER is not None

    def test_llm_model_default(self) -> None:
        """LLM_MODEL should have a default value."""
        assert Config.LLM_MODEL is not None

    def test_llm_timeout_is_int(self) -> None:
        """LLM_TIMEOUT should be an integer."""
        assert isinstance(Config.LLM_TIMEOUT, int)

    def test_llm_temperature_is_float(self) -> None:
        """LLM_TEMPERATURE should be a float."""
        assert isinstance(Config.LLM_TEMPERATURE, float)

    def test_llm_max_tokens_is_int(self) -> None:
        """LLM_MAX_TOKENS should be an integer."""
        assert isinstance(Config.LLM_MAX_TOKENS, int)

    def test_debug_is_bool(self) -> None:
        """DEBUG should be a boolean."""
        assert isinstance(Config.DEBUG, bool)
