"""Metrics exporters for different output formats."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from rich.console import Console
from rich.table import Table

from bloginator.monitoring.metrics import MetricsCollector


class MetricsExporter(ABC):
    """Base class for metrics exporters."""

    @abstractmethod
    def export(self, collector: MetricsCollector) -> str:
        """Export metrics to string format.

        Args:
            collector: MetricsCollector instance

        Returns:
            Formatted metrics string
        """
        pass

    def export_to_file(self, collector: MetricsCollector, path: Path) -> None:
        """Export metrics to file.

        Args:
            collector: MetricsCollector instance
            path: Output file path
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.export(collector))


class JSONExporter(MetricsExporter):
    """Export metrics as JSON."""

    def __init__(self, indent: int = 2) -> None:
        """Initialize JSON exporter.

        Args:
            indent: JSON indentation level
        """
        self.indent = indent

    def export(self, collector: MetricsCollector) -> str:
        """Export metrics as JSON.

        Args:
            collector: MetricsCollector instance

        Returns:
            JSON-formatted metrics string
        """
        summary = collector.get_summary()
        return json.dumps(summary, indent=self.indent)


class PrometheusExporter(MetricsExporter):
    """Export metrics in Prometheus text format."""

    def export(self, collector: MetricsCollector) -> str:
        """Export metrics in Prometheus format.

        Args:
            collector: MetricsCollector instance

        Returns:
            Prometheus-formatted metrics string
        """
        lines: list[str] = []

        # Add help and type metadata
        lines.append("# HELP bloginator_operations_total Total number of operations")
        lines.append("# TYPE bloginator_operations_total counter")

        lines.append("# HELP bloginator_operations_duration_seconds Operation duration in seconds")
        lines.append("# TYPE bloginator_operations_duration_seconds histogram")

        lines.append("# HELP bloginator_operations_success_total Successful operations")
        lines.append("# TYPE bloginator_operations_success_total counter")

        lines.append("# HELP bloginator_operations_failure_total Failed operations")
        lines.append("# TYPE bloginator_operations_failure_total counter")

        # Export operation metrics
        for op, agg in collector.aggregates.items():
            # Total operations
            lines.append(f'bloginator_operations_total{{operation="{op}"}} {agg.count}')

            # Success/failure counts
            lines.append(
                f'bloginator_operations_success_total{{operation="{op}"}} {agg.success_count}'
            )
            lines.append(
                f'bloginator_operations_failure_total{{operation="{op}"}} {agg.failure_count}'
            )

            # Duration metrics
            if agg.avg_duration is not None:
                lines.append(
                    f'bloginator_operations_duration_seconds{{operation="{op}",quantile="avg"}} '
                    f"{agg.avg_duration:.6f}"
                )
            if agg.min_duration is not None:
                lines.append(
                    f'bloginator_operations_duration_seconds{{operation="{op}",quantile="min"}} '
                    f"{agg.min_duration:.6f}"
                )
            if agg.max_duration is not None:
                lines.append(
                    f'bloginator_operations_duration_seconds{{operation="{op}",quantile="max"}} '
                    f"{agg.max_duration:.6f}"
                )

        # System metrics
        system = collector.get_system_metrics()
        lines.append("# HELP bloginator_cpu_percent CPU usage percentage")
        lines.append("# TYPE bloginator_cpu_percent gauge")
        lines.append(f"bloginator_cpu_percent {system['cpu_percent']:.2f}")

        lines.append("# HELP bloginator_memory_mb Memory usage in MB")
        lines.append("# TYPE bloginator_memory_mb gauge")
        lines.append(f"bloginator_memory_mb {system['memory_mb']:.2f}")

        lines.append("# HELP bloginator_memory_percent Memory usage percentage")
        lines.append("# TYPE bloginator_memory_percent gauge")
        lines.append(f"bloginator_memory_percent {system['memory_percent']:.2f}")

        return "\n".join(lines) + "\n"


class ConsoleExporter(MetricsExporter):
    """Export metrics to Rich console."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize console exporter.

        Args:
            console: Rich Console instance (creates new if None)
        """
        self.console = console or Console()

    def export(self, collector: MetricsCollector) -> str:
        """Export metrics to console (returns empty string).

        Args:
            collector: MetricsCollector instance

        Returns:
            Empty string (output goes to console)
        """
        summary = collector.get_summary()

        # Operations table
        table = Table(title="Operation Metrics", show_header=True)
        table.add_column("Operation", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Success", justify="right", style="green")
        table.add_column("Failure", justify="right", style="red")
        table.add_column("Avg Duration", justify="right")
        table.add_column("Min Duration", justify="right")
        table.add_column("Max Duration", justify="right")

        for op, metrics in summary["operations"].items():
            table.add_row(
                op,
                str(metrics["count"]),
                str(metrics["success_count"]),
                str(metrics["failure_count"]),
                f"{metrics['avg_duration']:.3f}s" if metrics["avg_duration"] else "N/A",
                f"{metrics['min_duration']:.3f}s" if metrics["min_duration"] else "N/A",
                f"{metrics['max_duration']:.3f}s" if metrics["max_duration"] else "N/A",
            )

        self.console.print(table)

        # System metrics
        system_table = Table(title="System Metrics", show_header=True)
        system_table.add_column("Metric", style="cyan")
        system_table.add_column("Value", justify="right")

        system = summary["system"]
        system_table.add_row("CPU Usage", f"{system['cpu_percent']:.1f}%")
        system_table.add_row("Memory Usage", f"{system['memory_mb']:.1f} MB")
        system_table.add_row("Memory %", f"{system['memory_percent']:.1f}%")
        system_table.add_row("Threads", str(system["num_threads"]))

        self.console.print(system_table)

        # Summary info
        self.console.print(f"\n[cyan]Uptime:[/cyan] {summary['uptime_seconds']:.1f}s")
        self.console.print(f"[cyan]Total Operations:[/cyan] {summary['total_operations']}")

        return ""  # Output goes to console
