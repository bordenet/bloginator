"""Metrics collection for monitoring Bloginator operations."""

import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar, cast

import psutil


F = TypeVar("F", bound=Callable[..., Any])


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""

    operation: str
    start_time: float
    end_time: float | None = None
    duration_seconds: float | None = None
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self, success: bool = True, error: str | None = None) -> None:
        """Mark operation as complete.

        Args:
            success: Whether operation succeeded
            error: Error message if failed
        """
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.success = success
        self.error = error


@dataclass
class AggregateMetrics:
    """Aggregate metrics for an operation type."""

    operation: str
    count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration: float = 0.0
    min_duration: float | None = None
    max_duration: float | None = None
    avg_duration: float = 0.0

    def add_operation(self, metrics: OperationMetrics) -> None:
        """Add operation metrics to aggregates.

        Args:
            metrics: Operation metrics to add
        """
        if metrics.duration_seconds is None:
            return

        self.count += 1
        if metrics.success:
            self.success_count += 1
        else:
            self.failure_count += 1

        self.total_duration += metrics.duration_seconds

        if self.min_duration is None or metrics.duration_seconds < self.min_duration:
            self.min_duration = metrics.duration_seconds

        if self.max_duration is None or metrics.duration_seconds > self.max_duration:
            self.max_duration = metrics.duration_seconds

        self.avg_duration = self.total_duration / self.count


class MetricsCollector:
    """Collects and aggregates metrics for Bloginator operations."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self.operations: list[OperationMetrics] = []
        self.aggregates: dict[str, AggregateMetrics] = defaultdict(
            lambda: AggregateMetrics(operation="")
        )
        self.start_time = datetime.now()
        self.process = psutil.Process()

    def start_operation(self, operation: str, **metadata: Any) -> OperationMetrics:
        """Start tracking an operation.

        Args:
            operation: Operation name (e.g., "extract", "index", "search")
            **metadata: Additional metadata to track

        Returns:
            OperationMetrics instance
        """
        metrics = OperationMetrics(
            operation=operation,
            start_time=time.time(),
            metadata=metadata,
        )
        self.operations.append(metrics)
        return metrics

    def complete_operation(
        self,
        metrics: OperationMetrics,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Complete an operation and update aggregates.

        Args:
            metrics: Operation metrics to complete
            success: Whether operation succeeded
            error: Error message if failed
        """
        metrics.complete(success=success, error=error)

        # Update aggregates
        if metrics.operation not in self.aggregates:
            self.aggregates[metrics.operation] = AggregateMetrics(operation=metrics.operation)

        self.aggregates[metrics.operation].add_operation(metrics)

    def get_system_metrics(self) -> dict[str, Any]:
        """Get current system resource usage.

        Returns:
            Dictionary with CPU, memory, and disk metrics
        """
        return {
            "cpu_percent": self.process.cpu_percent(interval=0.1),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "memory_percent": self.process.memory_percent(),
            "num_threads": self.process.num_threads(),
        }

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all collected metrics.

        Returns:
            Dictionary with operation summaries and system metrics
        """
        return {
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_operations": len(self.operations),
            "operations": {
                op: {
                    "count": agg.count,
                    "success_count": agg.success_count,
                    "failure_count": agg.failure_count,
                    "avg_duration": agg.avg_duration,
                    "min_duration": agg.min_duration,
                    "max_duration": agg.max_duration,
                }
                for op, agg in self.aggregates.items()
            },
            "system": self.get_system_metrics(),
        }


# Global metrics collector instance
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create the global metrics collector.

    Returns:
        Global MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_operation(operation: str) -> Callable[[F], F]:
    """Decorator to track operation metrics.

    Args:
        operation: Operation name to track

    Returns:
        Decorated function

    Example:
        >>> @track_operation("extract_document")
        >>> def extract_doc(path: Path) -> str:
        >>>     return extract_text(path)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            collector = get_metrics_collector()
            metrics = collector.start_operation(operation)

            try:
                result = func(*args, **kwargs)
                collector.complete_operation(metrics, success=True)
                return result
            except Exception as e:
                collector.complete_operation(
                    metrics,
                    success=False,
                    error=str(e),
                )
                raise

        return cast("F", wrapper)

    return decorator
