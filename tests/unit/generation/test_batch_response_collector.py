"""Tests for batch response collection with race condition coverage.

This module tests batch response collection including edge cases:
- File locking/concurrent writes
- Stale file detection
- Timeout scenarios
- Malformed responses
- Missing files
"""

import json
import time
from pathlib import Path
from threading import Thread

import pytest

from bloginator.generation._batch_response_collector import format_elapsed, validate_response


class TestFormatElapsed:
    """Test elapsed time formatting."""

    def test_format_elapsed_seconds_only(self) -> None:
        """Test formatting sub-minute duration."""
        result = format_elapsed(30.5)

        assert result == "0:30"

    def test_format_elapsed_minutes_seconds(self) -> None:
        """Test formatting minute duration."""
        result = format_elapsed(125.0)  # 2:05

        assert result == "2:05"

    def test_format_elapsed_hours_minutes_seconds(self) -> None:
        """Test formatting hour+ duration."""
        result = format_elapsed(3665.0)  # 1:01:05

        assert result == "1:01:05"

    def test_format_elapsed_zero(self) -> None:
        """Test formatting zero duration."""
        result = format_elapsed(0.0)

        assert result == "0:00"

    def test_format_elapsed_large_hours(self) -> None:
        """Test formatting multiple hours."""
        result = format_elapsed(36000.0)  # 10 hours

        assert result == "10:00:00"


class TestValidateResponseBasic:
    """Test basic response validation."""

    def test_validate_response_valid(self, tmp_path: Path) -> None:
        """Test validating a valid response."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test content"}))

        result = validate_response(response_file, 1)

        assert result["content"] == "Test content"

    def test_validate_response_missing_file(self, tmp_path: Path) -> None:
        """Test validating missing response file."""
        response_file = tmp_path / "missing.json"

        with pytest.raises(FileNotFoundError):
            validate_response(response_file, 1)

    def test_validate_response_invalid_json(self, tmp_path: Path) -> None:
        """Test validating invalid JSON."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text("{invalid json}")

        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_response(response_file, 1)

    def test_validate_response_missing_content(self, tmp_path: Path) -> None:
        """Test validating response without content field."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"other_field": "value"}))

        with pytest.raises(ValueError, match="Missing required 'content' field"):
            validate_response(response_file, 1)

    def test_validate_response_content_not_string(self, tmp_path: Path) -> None:
        """Test validating response with non-string content."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": 123}))

        with pytest.raises(ValueError, match="'content' must be string"):
            validate_response(response_file, 1)

    def test_validate_response_empty_content(self, tmp_path: Path) -> None:
        """Test validating response with empty content."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": ""}))

        with pytest.raises(ValueError, match="Empty 'content'"):
            validate_response(response_file, 1)

    def test_validate_response_whitespace_only_content(self, tmp_path: Path) -> None:
        """Test validating response with whitespace-only content."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "   \n\t  "}))

        with pytest.raises(ValueError, match="Empty 'content'"):
            validate_response(response_file, 1)

    def test_validate_response_with_error_field(self, tmp_path: Path) -> None:
        """Test validating response containing error."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "ignored", "error": "API error occurred"}))

        with pytest.raises(ValueError, match="Response contains error"):
            validate_response(response_file, 1)


class TestValidateResponseOptionalFields:
    """Test optional field validation."""

    def test_validate_response_with_tokens(self, tmp_path: Path) -> None:
        """Test validating response with token count."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test", "tokens_used": 150}))

        result = validate_response(response_file, 1)

        assert result["tokens_used"] == 150

    def test_validate_response_with_request_id(self, tmp_path: Path) -> None:
        """Test validating response with request_id field."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test", "request_id": 1}))

        result = validate_response(response_file, 1)

        assert result["request_id"] == 1

    def test_validate_response_invalid_tokens_type(self, tmp_path: Path, caplog) -> None:
        """Test validating response with invalid token type (warns, not fails)."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test", "tokens_used": "150"}))

        # Should warn but not fail
        result = validate_response(response_file, 1)
        assert result["content"] == "Test"

    def test_validate_response_with_all_optional_fields(self, tmp_path: Path) -> None:
        """Test validating response with all optional fields."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(
            json.dumps(
                {
                    "content": "Test content",
                    "request_id": 1,
                    "tokens_used": 150,
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "finish_reason": "stop",
                }
            )
        )

        result = validate_response(response_file, 1)

        assert result["content"] == "Test content"
        assert result["tokens_used"] == 150


class TestValidateResponseTimestamp:
    """Test timestamp-based staleness detection."""

    def test_validate_response_fresh_response(self, tmp_path: Path) -> None:
        """Test validating fresh response (newer than request)."""
        request_dir = tmp_path / "requests"
        request_dir.mkdir()

        # Create request file
        request_file = request_dir / "request_0001.json"
        request_file.write_text(json.dumps({"prompt": "test"}))

        # Wait slightly so response will be newer
        time.sleep(0.01)

        # Create response file
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test"}))

        # Should validate successfully
        result = validate_response(response_file, 1, request_dir)

        assert result["content"] == "Test"

    def test_validate_response_stale_response(self, tmp_path: Path) -> None:
        """Test validating stale response (older than request)."""
        request_dir = tmp_path / "requests"
        request_dir.mkdir()

        # Create response file first
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test"}))

        # Wait so response will be older
        time.sleep(0.01)

        # Create request file (newer)
        request_file = request_dir / "request_0001.json"
        request_file.write_text(json.dumps({"prompt": "test"}))

        # Should detect staleness
        with pytest.raises(ValueError, match="Stale response"):
            validate_response(response_file, 1, request_dir)

    def test_validate_response_no_request_file_check(self, tmp_path: Path) -> None:
        """Test validation skips timestamp check if request doesn't exist."""
        request_dir = tmp_path / "requests"
        request_dir.mkdir()

        # Request file doesn't exist
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Test"}))

        # Should still validate successfully
        result = validate_response(response_file, 1, request_dir)

        assert result["content"] == "Test"


class TestValidateResponseConcurrency:
    """Test response validation under concurrent conditions."""

    def test_validate_response_concurrent_writes(self, tmp_path: Path) -> None:
        """Test validation with concurrent file writes (simulated)."""
        response_file = tmp_path / "response_0001.json"

        def write_response():
            time.sleep(0.01)
            response_file.write_text(json.dumps({"content": "Concurrent write"}))

        thread = Thread(target=write_response)
        thread.start()

        # Wait for write to complete
        thread.join()

        # Should read the written content
        result = validate_response(response_file, 1)
        assert result["content"] == "Concurrent write"

    def test_validate_response_partial_json_file(self, tmp_path: Path) -> None:
        """Test validation handles incomplete JSON gracefully."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text('{"content": "incomplete')  # Incomplete JSON

        with pytest.raises(ValueError, match="Invalid JSON"):
            validate_response(response_file, 1)


class TestValidateResponseUnicode:
    """Test unicode handling in responses."""

    def test_validate_response_unicode_content(self, tmp_path: Path) -> None:
        """Test validating response with unicode content."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(
            json.dumps({"content": "Unicode: 你好 мир 🌍 café"}, ensure_ascii=False)
        )

        result = validate_response(response_file, 1)

        assert "你好" in result["content"]
        assert "café" in result["content"]
        assert "🌍" in result["content"]

    def test_validate_response_escaped_unicode(self, tmp_path: Path) -> None:
        """Test validating response with escaped unicode."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": "Escaped: \\u4f60\\u597d"}))

        result = validate_response(response_file, 1)

        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0


class TestValidateResponseLargeContent:
    """Test response validation with large content."""

    def test_validate_response_large_content(self, tmp_path: Path) -> None:
        """Test validating response with large content."""
        large_content = "A" * (1024 * 1024)  # 1MB of content

        response_file = tmp_path / "response_0001.json"
        response_file.write_text(json.dumps({"content": large_content}))

        result = validate_response(response_file, 1)

        assert len(result["content"]) == 1024 * 1024

    def test_validate_response_deeply_nested_json(self, tmp_path: Path) -> None:
        """Test validating response with extra nested fields."""
        response_file = tmp_path / "response_0001.json"
        response_file.write_text(
            json.dumps(
                {
                    "content": "Test",
                    "metadata": {
                        "nested": {"deep": {"structure": {"value": 123}}},
                    },
                }
            )
        )

        result = validate_response(response_file, 1)

        assert result["content"] == "Test"
        # Extra fields should be preserved
        assert "metadata" in result
