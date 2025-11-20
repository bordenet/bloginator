"""Config-based multi-source extraction."""

import os
import uuid
from pathlib import Path

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from bloginator.cli.error_reporting import ErrorTracker, create_error_panel
from bloginator.cli.extract_utils import is_temp_file, load_existing_extractions, should_skip_file
from bloginator.corpus_config import CorpusConfig
from bloginator.extraction import (
    count_words,
    extract_file_metadata,
    extract_text_from_file,
    extract_yaml_frontmatter,
)
from bloginator.models import Document


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
    # Initialize error tracker
    error_tracker = ErrorTracker()

    # Load config
    corpus_config = _load_config(config_path, error_tracker, console)

    # Load existing extractions for skip logic
    existing_docs = load_existing_extractions(output)

    # Get enabled sources
    enabled_sources = corpus_config.get_enabled_sources()

    if not enabled_sources:
        console.print("[yellow]No enabled sources in config[/yellow]")
        return

    # Show sources table
    _display_sources_table(enabled_sources, console)

    # Process each source
    total_extracted, total_skipped, total_failed = _process_all_sources(
        enabled_sources=enabled_sources,
        config_dir=config_path.parent,
        output=output,
        corpus_config=corpus_config,
        existing_docs=existing_docs,
        force=force,
        error_tracker=error_tracker,
        console=console,
    )

    # Print summary
    console.print(f"\n[bold green]Total: {total_extracted} document(s) extracted[/bold green]")
    if total_skipped > 0:
        console.print(
            f"[bold cyan]Total: {total_skipped} document(s) skipped (already extracted)[/bold cyan]"
        )
    if total_failed > 0:
        console.print(f"[bold yellow]Total: {total_failed} document(s) failed[/bold yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")

    # Print error summary if there were failures
    if total_failed > 0:
        error_tracker.print_summary(console)


def _load_config(config_path: Path, error_tracker: ErrorTracker, console: Console) -> CorpusConfig:
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


def _display_sources_table(enabled_sources: list, console: Console) -> None:
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


def _process_all_sources(
    enabled_sources: list,
    config_dir: Path,
    output: Path,
    corpus_config: CorpusConfig,
    existing_docs: dict,
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
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

    Returns:
        Tuple of (total_extracted, total_skipped, total_failed)
    """
    total_extracted = 0
    total_skipped = 0
    total_failed = 0

    for source_cfg in enabled_sources:
        # Skip URL sources (not implemented)
        if source_cfg.is_url():
            console.print(
                f"[yellow]⊘ Skipping URL source '{source_cfg.name}' (not yet implemented)[/yellow]"
            )
            continue

        # Resolve and validate path
        resolved_path = _resolve_source_path(source_cfg, config_dir, error_tracker, console)
        if not resolved_path:
            continue

        # Process this source
        extracted, skipped, failed = _process_source(
            source_cfg=source_cfg,
            resolved_path=resolved_path,
            output=output,
            corpus_config=corpus_config,
            existing_docs=existing_docs,
            force=force,
            error_tracker=error_tracker,
            console=console,
        )

        total_extracted += extracted
        total_skipped += skipped
        total_failed += failed

    return total_extracted, total_skipped, total_failed


def _resolve_source_path(
    source_cfg, config_dir: Path, error_tracker: ErrorTracker, console: Console
) -> Path | None:
    """Resolve and validate source path.

    Args:
        source_cfg: Source configuration
        config_dir: Directory containing config file
        error_tracker: Error tracker instance
        console: Rich console

    Returns:
        Resolved Path or None if resolution failed
    """
    try:
        resolved_path = source_cfg.resolve_path(config_dir)
        if not isinstance(resolved_path, Path):
            console.print(
                f"[yellow]⊘ Skipping '{source_cfg.name}' (path resolution issue)[/yellow]"
            )
            return None
    except Exception as e:
        category = error_tracker.categorize_exception(e)
        error_tracker.record_error(category, f"source '{source_cfg.name}'", e)
        console.print(f"[red]✗ Failed to resolve '{source_cfg.name}': {type(e).__name__}[/red]")
        return None

    if not resolved_path.exists():
        console.print(
            f"[yellow]⊘ Skipping '{source_cfg.name}' (path does not exist: {resolved_path})[/yellow]"
        )
        return None

    return resolved_path


def _process_source(
    source_cfg,
    resolved_path: Path,
    output: Path,
    corpus_config: CorpusConfig,
    existing_docs: dict,
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
) -> tuple[int, int, int]:
    """Process a single source.

    Args:
        source_cfg: Source configuration
        resolved_path: Resolved source path
        output: Output directory
        corpus_config: Corpus configuration
        existing_docs: Dictionary of existing extractions
        force: Force re-extraction flag
        error_tracker: Error tracker instance
        console: Rich console

    Returns:
        Tuple of (extracted_count, skipped_count, failed_count)
    """
    console.print(f"[cyan]Processing '{source_cfg.name}' from {resolved_path}...[/cyan]")

    # Get files from this source
    files = _collect_source_files(resolved_path, corpus_config)

    if not files:
        console.print(f"  [dim]No files found in '{source_cfg.name}'[/dim]")
        return 0, 0, 0

    console.print(f"  [dim]Found {len(files)} file(s)[/dim]")

    # Extract files
    extracted_count, skipped_count, failed_count = _extract_source_files(
        files=files,
        source_cfg=source_cfg,
        output=output,
        existing_docs=existing_docs,
        force=force,
        error_tracker=error_tracker,
        console=console,
    )

    # Print source summary
    console.print(f"  [green]✓ {extracted_count} extracted[/green]")
    if skipped_count > 0:
        console.print(f"  [cyan]↻ {skipped_count} skipped[/cyan]")
    if failed_count > 0:
        console.print(f"  [yellow]✗ {failed_count} failed[/yellow]")

    return extracted_count, skipped_count, failed_count


def _collect_source_files(resolved_path: Path, corpus_config: CorpusConfig) -> list[Path]:
    """Collect files from a source path.

    Args:
        resolved_path: Resolved source path
        corpus_config: Corpus configuration

    Returns:
        List of file paths to extract
    """
    files = []

    if resolved_path.is_file():
        # Skip temp files even for single files
        if not is_temp_file(resolved_path.name):
            files = [resolved_path]
    else:
        supported_extensions = set(corpus_config.extraction.include_extensions)
        ignore_patterns = corpus_config.extraction.ignore_patterns

        for root, _dirs, filenames in os.walk(
            resolved_path,
            followlinks=corpus_config.extraction.follow_symlinks,
        ):
            root_path = Path(root)
            for filename in filenames:
                # Skip temp files
                if is_temp_file(filename):
                    continue

                # Check ignore patterns
                if any(filename.startswith(p.rstrip("*")) for p in ignore_patterns):
                    continue

                file_path = root_path / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)

    return files


def _extract_source_files(
    files: list[Path],
    source_cfg,
    output: Path,
    existing_docs: dict,
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
) -> tuple[int, int, int]:
    """Extract files from a source with progress tracking.

    Returns:
        Tuple of (extracted_count, skipped_count, failed_count)
    """
    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    with Progress() as progress:
        task = progress.add_task(f"[green]Processing {source_cfg.name}...", total=len(files))

        for file_path in files:
            try:
                # Check if we should skip this file
                skip, doc_id = should_skip_file(file_path, existing_docs, force)

                if skip:
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Extract text
                text = extract_text_from_file(file_path)

                # Get file metadata
                file_meta = extract_file_metadata(file_path)

                # Try to extract frontmatter if Markdown
                frontmatter = {}
                if file_path.suffix.lower() in [".md", ".markdown"]:
                    content = file_path.read_text(encoding="utf-8")
                    frontmatter = extract_yaml_frontmatter(content)

                # Merge tags from source config and frontmatter
                doc_tags = list(source_cfg.tags)
                if frontmatter and "tags" in frontmatter:
                    doc_tags.extend(frontmatter["tags"])

                # Create document with source metadata
                doc = Document(
                    id=str(uuid.uuid4()),
                    filename=file_path.name,
                    source_path=file_path.absolute(),
                    format=file_path.suffix.lstrip(".").lower(),
                    created_date=file_meta.get("created_date"),
                    modified_date=file_meta.get("modified_date"),
                    quality_rating=source_cfg.quality,
                    tags=doc_tags,
                    word_count=count_words(text),
                    source_name=source_cfg.name,
                    voice_notes=source_cfg.voice_notes,
                )

                # Save extracted text
                text_file = output / f"{doc.id}.txt"
                text_file.write_text(text, encoding="utf-8")

                # Save metadata
                meta_file = output / f"{doc.id}.json"
                meta_file.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

                extracted_count += 1

            except Exception as e:
                # Categorize and track error
                category = error_tracker.categorize_exception(e, file_path)
                error_tracker.record_error(category, f"{source_cfg.name}/{file_path.name}", e)
                console.print(f"  [red]✗ {file_path.name}: {type(e).__name__}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    return extracted_count, skipped_count, failed_count
