"""Tests for structured logging."""

import json
import logging
from pathlib import Path

from bloginator.monitoring.logger import StructuredFormatter, configure_logging, get_logger


class TestConfigureLogging:
    """Tests for configure_logging."""

    def test_configure_basic_logging(self) -> None:
        """Test basic logging configuration."""
        configure_logging(level="INFO")

        logger = logging.getLogger("test")
        assert logger.level <= logging.INFO

    def test_configure_with_file(self, tmp_path: Path) -> None:
        """Test logging configuration with file output."""
        log_file = tmp_path / "test.log"
        configure_logging(level="DEBUG", log_file=log_file)

        logger = logging.getLogger("test_file")
        logger.info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_configure_with_string_level(self) -> None:
        """Test configuration with string log level."""
        configure_logging(level="WARNING")

        logger = logging.getLogger("test_level")
        assert logger.level <= logging.WARNING

    def test_configure_with_int_level(self) -> None:
        """Test configuration with integer log level."""
        configure_logging(level=logging.ERROR)

        logger = logging.getLogger("test_int_level")
        assert logger.level <= logging.ERROR


class TestGetLogger:
    """Tests for get_logger."""

    def test_get_logger(self) -> None:
        """Test getting logger instance."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_different_names(self) -> None:
        """Test getting loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2


class TestStructuredFormatter:
    """Tests for StructuredFormatter."""

    def test_format_basic_record(self) -> None:
        """Test formatting basic log record."""
        formatter = StructuredFormatter()
        logger = logging.getLogger("test_structured")

        # Create log record
        record = logger.makeRecord(
            name="test_structured",
            level=logging.INFO,
            fn="test.py",
            lno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # Should be valid JSON
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test_structured"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_format_with_exception(self) -> None:
        """Test formatting log record with exception."""
        formatter = StructuredFormatter()
        logger = logging.getLogger("test_exception")

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

            record = logger.makeRecord(
                name="test_exception",
                level=logging.ERROR,
                fn="test.py",
                lno=20,
                msg="Error occurred",
                args=(),
                exc_info=exc_info,
            )

            result = formatter.format(record)
            data = json.loads(result)

            assert data["level"] == "ERROR"
            assert data["message"] == "Error occurred"
            assert "exception" in data
            assert "ValueError" in data["exception"]
            assert "Test error" in data["exception"]
