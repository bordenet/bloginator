"""Config-based multi-source extraction."""

from pathlib import Path

from rich.console import Console

from bloginator.cli._extract_config_helpers import (
    display_sources_table,
    load_config,
    process_all_sources,
)
from bloginator.cli.extract_utils import load_existing_extractions


def extract_from_config(
    config_path: Path, output: Path, console: Console, force: bool = False
) -> None:
    """Extract from multiple sources using corpus.yaml config.

    Args:
        config_path: Path to corpus.yaml configuration file
        output: Output directory for extracted documents
        console: Rich console for output
        force: If True, re-extract all files
    """
    from bloginator.cli.error_reporting import ErrorTracker

    # Initialize error tracker
    error_tracker = ErrorTracker()

    # Load config
    corpus_config = load_config(config_path, error_tracker, console)

    # Load existing extractions for skip logic
    existing_docs = load_existing_extractions(output)

    # Get enabled sources
    enabled_sources = corpus_config.get_enabled_sources()

    if not enabled_sources:
        console.print("[yellow]No enabled sources in config[/yellow]")
        return

    # Show sources table
    display_sources_table(enabled_sources, console)

    # Process each source
    total_extracted, total_skipped, total_failed = process_all_sources(
        enabled_sources=enabled_sources,
        config_dir=config_path.parent,
        output=output,
        corpus_config=corpus_config,
        existing_docs=existing_docs,
        force=force,
        error_tracker=error_tracker,
        console=console,
    )

    # Save report to file if there were skips or errors
    report_file: Path | None = None
    if error_tracker.total_skipped > 0 or error_tracker.total_errors > 0:
        report_file = error_tracker.save_to_file(output, prefix="extraction")

    # Print summary
    console.print(f"\n[bold green]Total: {total_extracted} document(s) extracted[/bold green]")
    if total_skipped > 0:
        console.print(
            f"[bold cyan]Total: {total_skipped} document(s) skipped (already extracted)[/bold cyan]"
        )
    if total_failed > 0:
        console.print(f"[bold yellow]Total: {total_failed} document(s) failed[/bold yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")

    # Print skip summary if there were skips (with file path reference)
    if error_tracker.total_skipped > 0:
        error_tracker.print_skip_summary(console, show_file_path=report_file)

    # Print error summary if there were failures
    if total_failed > 0:
        error_tracker.print_summary(console)
