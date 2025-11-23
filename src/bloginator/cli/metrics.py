"""CLI command for viewing metrics."""

from pathlib import Path

import click
from rich.console import Console

from bloginator.monitoring import (
    ConsoleExporter,
    JSONExporter,
    PrometheusExporter,
    get_metrics_collector,
)


console = Console()


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["console", "json", "prometheus"]),
    default="console",
    help="Output format (default: console)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout)",
)
def metrics(format: str, output: Path | None) -> None:
    """View collected metrics.

    Display metrics collected during Bloginator operations, including:
    - Operation counts and success/failure rates
    - Performance metrics (duration, throughput)
    - System resource usage (CPU, memory)

    Examples:
      # View metrics in console
      bloginator metrics

      # Export as JSON
      bloginator metrics --format json --output metrics.json

      # Export in Prometheus format
      bloginator metrics --format prometheus --output metrics.prom
    """
    collector = get_metrics_collector()

    # Check if any metrics have been collected
    if not collector.operations:
        console.print("[yellow]No metrics collected yet.[/yellow]")
        console.print("[dim]Run some operations first (extract, index, search, etc.)[/dim]")
        return

    # Select exporter
    if format == "json":
        exporter = JSONExporter()
    elif format == "prometheus":
        exporter = PrometheusExporter()
    else:  # console
        exporter = ConsoleExporter(console)

    # Export metrics
    if output:
        exporter.export_to_file(collector, output)
        console.print(f"[green]✓[/green] Metrics exported to {output}")
    else:
        result = exporter.export(collector)
        if result:  # JSON and Prometheus return strings
            console.print(result)
