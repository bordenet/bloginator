"""Tests for metrics exporters."""

import json
from pathlib import Path

import pytest
from rich.console import Console

from bloginator.monitoring.exporters import ConsoleExporter, JSONExporter, PrometheusExporter
from bloginator.monitoring.metrics import MetricsCollector


@pytest.fixture
def sample_collector() -> MetricsCollector:
    """Create a sample metrics collector with data."""
    collector = MetricsCollector()

    # Add some operations
    metrics1 = collector.start_operation("extract", doc_count=10)
    collector.complete_operation(metrics1, success=True)

    metrics2 = collector.start_operation("index", chunk_count=50)
    collector.complete_operation(metrics2, success=True)

    metrics3 = collector.start_operation("search", query="test")
    collector.complete_operation(metrics3, success=False, error="Test error")

    return collector


class TestJSONExporter:
    """Tests for JSONExporter."""

    def test_export_json(self, sample_collector: MetricsCollector) -> None:
        """Test exporting metrics as JSON."""
        exporter = JSONExporter()
        result = exporter.export(sample_collector)

        # Should be valid JSON
        data = json.loads(result)

        assert "start_time" in data
        assert "uptime_seconds" in data
        assert "total_operations" in data
        assert data["total_operations"] == 3
        assert "operations" in data
        assert "extract" in data["operations"]
        assert "index" in data["operations"]
        assert "search" in data["operations"]
        assert "system" in data

    def test_export_to_file(self, sample_collector: MetricsCollector, tmp_path: Path) -> None:
        """Test exporting metrics to JSON file."""
        exporter = JSONExporter()
        output_file = tmp_path / "metrics.json"

        exporter.export_to_file(sample_collector, output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["total_operations"] == 3


class TestPrometheusExporter:
    """Tests for PrometheusExporter."""

    def test_export_prometheus(self, sample_collector: MetricsCollector) -> None:
        """Test exporting metrics in Prometheus format."""
        exporter = PrometheusExporter()
        result = exporter.export(sample_collector)

        # Should contain Prometheus format elements
        assert "# HELP" in result
        assert "# TYPE" in result
        assert "bloginator_operations_total" in result
        assert "bloginator_operations_duration_seconds" in result
        assert "bloginator_cpu_percent" in result
        assert "bloginator_memory_mb" in result

        # Should contain operation labels
        assert 'operation="extract"' in result
        assert 'operation="index"' in result
        assert 'operation="search"' in result

    def test_export_to_file(self, sample_collector: MetricsCollector, tmp_path: Path) -> None:
        """Test exporting metrics to Prometheus file."""
        exporter = PrometheusExporter()
        output_file = tmp_path / "metrics.prom"

        exporter.export_to_file(sample_collector, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "bloginator_operations_total" in content


class TestConsoleExporter:
    """Tests for ConsoleExporter."""

    def test_export_console(self, sample_collector: MetricsCollector) -> None:
        """Test exporting metrics to console."""
        console = Console()
        exporter = ConsoleExporter(console)

        # Should return empty string (output goes to console)
        result = exporter.export(sample_collector)
        assert result == ""

    def test_export_with_no_console(self, sample_collector: MetricsCollector) -> None:
        """Test exporting with default console."""
        exporter = ConsoleExporter()

        # Should not raise error
        result = exporter.export(sample_collector)
        assert result == ""
