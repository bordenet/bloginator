"""Helper functions for config-based extraction."""

import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from bloginator.cli._extract_files_engine import extract_source_files
from bloginator.cli._smb_resolver import resolve_smb_path
from bloginator.cli.error_reporting import ErrorTracker, SkipCategory, create_error_panel
from bloginator.cli.extract_utils import is_temp_file
from bloginator.corpus_config import CorpusConfig, CorpusSource


def load_config(config_path: Path, error_tracker: ErrorTracker, console: Console) -> CorpusConfig:
    """Load corpus configuration with error handling.

    Args:
        config_path: Path to config file
        error_tracker: Error tracker instance
        console: Rich console

    Returns:
        Loaded CorpusConfig

    Raises:
        Exception if config cannot be loaded
    """
    try:
        return CorpusConfig.load_from_file(config_path)
    except Exception as e:
        category = error_tracker.categorize_exception(e)
        advice = error_tracker.get_actionable_advice(category)
        panel = create_error_panel(
            "Configuration Error",
            f"Failed to load {config_path}: {e}",
            advice,
        )
        console.print(panel)
        raise


def display_sources_table(enabled_sources: list[CorpusSource], console: Console) -> None:
    """Display table of enabled sources.

    Args:
        enabled_sources: List of enabled source configurations
        console: Rich console
    """
    table = Table(title="Corpus Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Quality", style="yellow")
    table.add_column("Tags", style="blue")

    for source_cfg in enabled_sources:
        tags_str = ", ".join(source_cfg.tags[:3])
        if len(source_cfg.tags) > 3:
            tags_str += f" +{len(source_cfg.tags) - 3}"
        table.add_row(
            source_cfg.name,
            str(source_cfg.path)[:50],
            source_cfg.quality.value,
            tags_str or "-",
        )

    console.print(table)
    console.print()


def process_all_sources(
    enabled_sources: list[CorpusSource],
    config_dir: Path,
    output: Path,
    corpus_config: CorpusConfig,
    existing_docs: dict[str, tuple[str, datetime]],
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Process all enabled sources.

    Args:
        enabled_sources: List of enabled source configurations
        config_dir: Directory containing config file
        output: Output directory
        corpus_config: Corpus configuration
        existing_docs: Dictionary of existing extractions
        force: Force re-extraction flag
        error_tracker: Error tracker instance
        console: Rich console
        verbose: If True, show detailed progress information

    Returns:
        Tuple of (total_extracted, total_skipped, total_failed)
    """
    total_extracted = 0
    total_skipped = 0
    total_failed = 0

    for source_cfg in enabled_sources:
        # Resolve and validate path
        resolved_path = resolve_source_path(source_cfg, config_dir, error_tracker, console)
        if not resolved_path:
            continue

        # Process this source
        extracted, skipped, failed = process_source(
            source_cfg=source_cfg,
            resolved_path=resolved_path,
            output=output,
            corpus_config=corpus_config,
            existing_docs=existing_docs,
            force=force,
            error_tracker=error_tracker,
            console=console,
            verbose=verbose,
        )

        total_extracted += extracted
        total_skipped += skipped
        total_failed += failed

    return total_extracted, total_skipped, total_failed


def resolve_source_path(
    source_cfg: CorpusSource, config_dir: Path, error_tracker: ErrorTracker, console: Console
) -> Path | str | None:
    """Resolve and validate source path.

    Args:
        source_cfg: Source configuration
        config_dir: Directory containing config file
        error_tracker: Error tracker instance
        console: Rich console

    Returns:
        Resolved Path (local) or str (URL like smb://) or None if resolution failed
    """
    try:
        resolved_path = source_cfg.resolve_path(config_dir)
    except Exception as e:
        category = error_tracker.categorize_exception(e)
        error_tracker.record_error(category, f"source '{source_cfg.name}'", e)
        console.print(f"[red]✗ Failed to resolve '{source_cfg.name}': {type(e).__name__}[/red]")
        return None

    # Handle URLs (like smb://) - accept without existence check
    if isinstance(resolved_path, str):
        console.print(f"[cyan]→ Using network path '{source_cfg.name}': {resolved_path}[/cyan]")
        return resolved_path

    # Handle local paths - check existence
    if not resolved_path.exists():
        error_tracker.record_skip(
            SkipCategory.PATH_NOT_FOUND, f"{source_cfg.name}: {resolved_path}"
        )
        console.print(
            f"[yellow]⊘ Skipping '{source_cfg.name}' "
            f"(path does not exist: {resolved_path})[/yellow]"
        )
        return None

    return resolved_path


def process_source(
    source_cfg: CorpusSource,
    resolved_path: Path | str,
    output: Path,
    corpus_config: CorpusConfig,
    existing_docs: dict[str, tuple[str, datetime]],
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Process a single source.

    Args:
        source_cfg: Source configuration
        resolved_path: Resolved source path (local Path or network URL string)
        output: Output directory
        corpus_config: Corpus configuration
        existing_docs: Dictionary of existing extractions
        force: Force re-extraction flag
        error_tracker: Error tracker instance
        console: Rich console
        verbose: If True, show detailed progress information

    Returns:
        Tuple of (extracted_count, skipped_count, failed_count)
    """
    console.print(f"[cyan]Processing '{source_cfg.name}' from {resolved_path}...[/cyan]")

    # Get files from this source
    files = collect_source_files(resolved_path, corpus_config, error_tracker)

    if not files:
        console.print(f"  [dim]No files found in '{source_cfg.name}'[/dim]")
        return 0, 0, 0

    console.print(f"  [dim]Found {len(files)} file(s)[/dim]")

    # Extract files
    extracted_count, skipped_count, failed_count = extract_source_files(
        files=files,
        source_cfg=source_cfg,
        output=output,
        existing_docs=existing_docs,
        force=force,
        error_tracker=error_tracker,
        console=console,
        verbose=verbose,
    )

    # Print source summary
    console.print(f"  [green]✓ {extracted_count} extracted[/green]")
    if skipped_count > 0:
        console.print(f"  [cyan]↻ {skipped_count} skipped[/cyan]")
    if failed_count > 0:
        console.print(f"  [yellow]✗ {failed_count} failed[/yellow]")

    return extracted_count, skipped_count, failed_count


def collect_source_files(
    resolved_path: Path | str, corpus_config: CorpusConfig, error_tracker: ErrorTracker
) -> list[Path]:
    """Collect files from a source path.

    Args:
        resolved_path: Resolved source path (local Path or SMB URL string)
        corpus_config: Corpus configuration
        error_tracker: Error tracker for skip reporting

    Returns:
        List of file paths to extract
    """
    files: list[Path] = []

    # Convert SMB URLs to mounted local paths
    if isinstance(resolved_path, str) and resolved_path.startswith("smb://"):
        smb_resolved = resolve_smb_path(resolved_path, error_tracker)
        if not smb_resolved:
            return files
        resolved_path = smb_resolved

    # Type guard: resolved_path must be Path at this point
    if not isinstance(resolved_path, Path):
        return files

    if resolved_path.is_file():
        # Skip temp files even for single files
        if is_temp_file(resolved_path.name):
            error_tracker.record_skip(SkipCategory.TEMP_FILE, resolved_path.name)
        else:
            files = [resolved_path]
    else:
        supported_extensions = set(corpus_config.extraction.include_extensions)
        ignore_patterns = corpus_config.extraction.ignore_patterns

        for root, dirs, filenames in os.walk(
            resolved_path,
            followlinks=corpus_config.extraction.follow_symlinks,
        ):
            root_path = Path(root)

            # Skip directories containing .bloginator-ignore marker file
            if (root_path / ".bloginator-ignore").exists():
                dirs.clear()  # Prevent descending into subdirectories
                continue

            for filename in filenames:
                # Skip temp files
                if is_temp_file(filename):
                    error_tracker.record_skip(SkipCategory.TEMP_FILE, filename)
                    continue

                # Check ignore patterns
                if any(filename.startswith(p.rstrip("*")) for p in ignore_patterns):
                    error_tracker.record_skip(SkipCategory.IGNORE_PATTERN, filename)
                    continue

                file_path = root_path / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)
                else:
                    error_tracker.record_skip(
                        SkipCategory.UNSUPPORTED_EXTENSION, f"{filename} ({file_path.suffix})"
                    )

    return files
