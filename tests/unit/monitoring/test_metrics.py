"""Tests for metrics collection."""

import time

import pytest

from bloginator.monitoring.metrics import (
    AggregateMetrics,
    MetricsCollector,
    OperationMetrics,
    get_metrics_collector,
    track_operation,
)


class TestOperationMetrics:
    """Tests for OperationMetrics."""

    def test_create_operation_metrics(self) -> None:
        """Test creating operation metrics."""
        metrics = OperationMetrics(
            operation="test_op",
            start_time=time.time(),
            metadata={"key": "value"},
        )

        assert metrics.operation == "test_op"
        assert metrics.start_time > 0
        assert metrics.end_time is None
        assert metrics.duration_seconds is None
        assert metrics.success is True
        assert metrics.error is None
        assert metrics.metadata == {"key": "value"}

    def test_complete_operation_success(self) -> None:
        """Test completing operation successfully."""
        metrics = OperationMetrics(operation="test_op", start_time=time.time())
        time.sleep(0.01)  # Small delay
        metrics.complete(success=True)

        assert metrics.end_time is not None
        assert metrics.duration_seconds is not None
        assert metrics.duration_seconds > 0
        assert metrics.success is True
        assert metrics.error is None

    def test_complete_operation_failure(self) -> None:
        """Test completing operation with failure."""
        metrics = OperationMetrics(operation="test_op", start_time=time.time())
        metrics.complete(success=False, error="Test error")

        assert metrics.success is False
        assert metrics.error == "Test error"


class TestAggregateMetrics:
    """Tests for AggregateMetrics."""

    def test_create_aggregate_metrics(self) -> None:
        """Test creating aggregate metrics."""
        agg = AggregateMetrics(operation="test_op")

        assert agg.operation == "test_op"
        assert agg.count == 0
        assert agg.success_count == 0
        assert agg.failure_count == 0
        assert agg.total_duration == 0.0
        assert agg.min_duration is None
        assert agg.max_duration is None
        assert agg.avg_duration == 0.0

    def test_add_operation(self) -> None:
        """Test adding operation to aggregates."""
        agg = AggregateMetrics(operation="test_op")

        # Add first operation
        op1 = OperationMetrics(operation="test_op", start_time=time.time())
        op1.complete(success=True)
        agg.add_operation(op1)

        assert agg.count == 1
        assert agg.success_count == 1
        assert agg.failure_count == 0
        assert agg.min_duration == op1.duration_seconds
        assert agg.max_duration == op1.duration_seconds
        assert agg.avg_duration == op1.duration_seconds

        # Add second operation
        op2 = OperationMetrics(operation="test_op", start_time=time.time())
        time.sleep(0.01)
        op2.complete(success=False, error="Test error")
        agg.add_operation(op2)

        assert agg.count == 2
        assert agg.success_count == 1
        assert agg.failure_count == 1
        assert agg.min_duration is not None
        assert agg.max_duration is not None
        assert agg.avg_duration > 0


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_create_collector(self) -> None:
        """Test creating metrics collector."""
        collector = MetricsCollector()

        assert len(collector.operations) == 0
        assert len(collector.aggregates) == 0
        assert collector.start_time is not None

    def test_start_operation(self) -> None:
        """Test starting operation tracking."""
        collector = MetricsCollector()
        metrics = collector.start_operation("test_op", key="value")

        assert metrics.operation == "test_op"
        assert metrics.metadata == {"key": "value"}
        assert len(collector.operations) == 1

    def test_complete_operation(self) -> None:
        """Test completing operation."""
        collector = MetricsCollector()
        metrics = collector.start_operation("test_op")
        time.sleep(0.01)
        collector.complete_operation(metrics, success=True)

        assert metrics.success is True
        assert metrics.duration_seconds is not None
        assert "test_op" in collector.aggregates
        assert collector.aggregates["test_op"].count == 1

    def test_get_system_metrics(self) -> None:
        """Test getting system metrics."""
        collector = MetricsCollector()
        system = collector.get_system_metrics()

        assert "cpu_percent" in system
        assert "memory_mb" in system
        assert "memory_percent" in system
        assert "num_threads" in system
        assert system["memory_mb"] > 0

    def test_get_summary(self) -> None:
        """Test getting metrics summary."""
        collector = MetricsCollector()

        # Add some operations
        metrics1 = collector.start_operation("extract")
        collector.complete_operation(metrics1, success=True)

        metrics2 = collector.start_operation("index")
        collector.complete_operation(metrics2, success=False, error="Test error")

        summary = collector.get_summary()

        assert "start_time" in summary
        assert "uptime_seconds" in summary
        assert "total_operations" in summary
        assert summary["total_operations"] == 2
        assert "operations" in summary
        assert "extract" in summary["operations"]
        assert "index" in summary["operations"]
        assert "system" in summary


class TestTrackOperationDecorator:
    """Tests for track_operation decorator."""

    def test_track_successful_operation(self) -> None:
        """Test tracking successful operation."""
        collector = get_metrics_collector()
        initial_count = len(collector.operations)

        @track_operation("test_function")
        def test_func() -> str:
            return "success"

        result = test_func()

        assert result == "success"
        assert len(collector.operations) > initial_count
        assert collector.operations[-1].operation == "test_function"
        assert collector.operations[-1].success is True

    def test_track_failed_operation(self) -> None:
        """Test tracking failed operation."""
        collector = get_metrics_collector()
        initial_count = len(collector.operations)

        @track_operation("test_function")
        def test_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_func()

        assert len(collector.operations) > initial_count
        assert collector.operations[-1].operation == "test_function"
        assert collector.operations[-1].success is False
        assert collector.operations[-1].error == "Test error"


class TestGetMetricsCollector:
    """Tests for get_metrics_collector."""

    def test_get_global_collector(self) -> None:
        """Test getting global metrics collector."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Should return same instance
        assert collector1 is collector2
