"""Single-source extraction (legacy mode)."""

import os
import uuid
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from bloginator.cli.error_reporting import ErrorTracker
from bloginator.cli.extract_utils import (
    get_supported_extensions,
    is_temp_file,
    load_existing_extractions,
    should_skip_file,
    wait_for_file_availability,
)
from bloginator.extraction import (
    count_words,
    extract_file_metadata,
    extract_text_from_file,
    extract_yaml_frontmatter,
)
from bloginator.models import Document, QualityRating
from bloginator.utils.checksum import calculate_content_checksum
from bloginator.utils.parallel import parallel_map_with_progress


def extract_single_source(
    source: Path,
    output: Path,
    quality: str,
    tag_list: list[str],
    console: Console,
    force: bool = False,
    workers: int | None = None,
    verbose: bool = False,
) -> None:
    """Extract from single source (legacy mode).

    Args:
        source: Source file or directory
        output: Output directory for extracted documents
        quality: Quality rating for documents
        tag_list: List of tags to apply
        console: Rich console for output
        force: If True, re-extract all files
        workers: Number of parallel workers (None = auto-detect)
        verbose: If True, show detailed progress information
    """
    # Initialize error tracker
    error_tracker = ErrorTracker()

    # Load existing extractions for skip logic
    existing_docs = load_existing_extractions(output)

    # Get list of files to extract
    files = _collect_files(source)

    if not files:
        console.print("[yellow]No supported files found.[/yellow]")
        return

    console.print(f"[cyan]Found {len(files)} file(s)...[/cyan]")

    # Process files
    extracted_count, skipped_count, failed_count = _process_files(
        files=files,
        output=output,
        quality=quality,
        tag_list=tag_list,
        existing_docs=existing_docs,
        force=force,
        error_tracker=error_tracker,
        console=console,
        workers=workers,
    )

    # Print summary
    console.print(f"\n[green]✓ Successfully extracted {extracted_count} document(s)[/green]")
    if skipped_count > 0:
        console.print(f"[cyan]↻ Skipped {skipped_count} document(s) (already extracted)[/cyan]")
    if failed_count > 0:
        console.print(f"[yellow]✗ Failed to extract {failed_count} document(s)[/yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")

    # Print error summary if there were failures
    if failed_count > 0:
        error_tracker.print_summary(console)


def _collect_files(source: Path) -> list[Path]:
    """Collect all supported files from source.

    Args:
        source: Source file or directory

    Returns:
        List of file paths to extract
    """
    if source.is_file():
        return [source]

    files = []
    supported_extensions = get_supported_extensions()

    # Walk directory tree, following symlinks
    for root, dirs, filenames in os.walk(source, followlinks=True):
        root_path = Path(root)

        # Skip directories containing .bloginator-ignore marker file
        if (root_path / ".bloginator-ignore").exists():
            dirs.clear()  # Prevent descending into subdirectories
            continue

        for filename in filenames:
            # Skip temp files
            if is_temp_file(filename):
                continue

            file_path = root_path / filename
            if file_path.suffix.lower() in supported_extensions:
                files.append(file_path)

    return files


def _process_files(
    files: list[Path],
    output: Path,
    quality: str,
    tag_list: list[str],
    existing_docs: dict[str, tuple[str, datetime]],
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
    workers: int | None = None,
) -> tuple[int, int, int]:
    """Process list of files for extraction (with optional parallel processing).

    Args:
        files: List of files to process
        output: Output directory
        quality: Quality rating
        tag_list: Tags to apply
        existing_docs: Dictionary of existing extractions
        force: Force re-extraction flag
        error_tracker: Error tracker instance
        console: Rich console
        workers: Number of parallel workers (None = auto, 1 = sequential)

    Returns:
        Tuple of (extracted_count, skipped_count, failed_count)
    """
    # Use sequential processing for single file or if workers=1
    if len(files) == 1 or workers == 1:
        return _process_files_sequential(
            files, output, quality, tag_list, existing_docs, force, error_tracker, console
        )

    # Parallel processing
    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    # Progress tracking
    with Progress() as progress:
        task = progress.add_task("[green]Processing...", total=len(files))

        def progress_callback(completed: int) -> None:
            progress.update(task, completed=completed)

        # Create worker function that processes a single file
        def process_file(file_path: Path) -> tuple[str, str | None, Exception | None]:
            """Process single file, return (status, doc_id, error)."""
            try:
                # Check if we should skip this file
                skip, doc_id = should_skip_file(file_path, existing_docs, force)

                if skip:
                    return ("skipped", doc_id, None)

                # Extract and save document
                _extract_and_save_document(
                    file_path=file_path,
                    output=output,
                    quality=quality,
                    tag_list=tag_list,
                )

                return ("extracted", None, None)

            except Exception as e:
                return ("failed", None, e)

        # Process files in parallel
        results = parallel_map_with_progress(
            process_file, files, max_workers=workers, progress_callback=progress_callback
        )

    # Aggregate results
    for file_path, (status, _doc_id, error) in zip(files, results, strict=True):
        if status == "extracted":
            extracted_count += 1
        elif status == "skipped":
            skipped_count += 1
        elif status == "failed":
            # Categorize and track error
            if error is not None:
                category = error_tracker.categorize_exception(error, file_path)
                error_tracker.record_error(category, file_path.name, error)
                console.print(f"[red]✗ {file_path.name}: {type(error).__name__}[/red]")
            failed_count += 1

    return extracted_count, skipped_count, failed_count


def _process_files_sequential(
    files: list[Path],
    output: Path,
    quality: str,
    tag_list: list[str],
    existing_docs: dict[str, tuple[str, datetime]],
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
) -> tuple[int, int, int]:
    """Process files sequentially with progress display."""
    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    with Progress() as progress:
        task = progress.add_task("[green]Processing...", total=len(files))

        for file_path in files:
            try:
                # Check if we should skip this file
                skip, doc_id = should_skip_file(file_path, existing_docs, force)

                if skip:
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Extract and save document
                _extract_and_save_document(
                    file_path=file_path,
                    output=output,
                    quality=quality,
                    tag_list=tag_list,
                )

                extracted_count += 1

            except Exception as e:
                # Categorize and track error
                category = error_tracker.categorize_exception(e, file_path)
                error_tracker.record_error(category, file_path.name, e)
                console.print(f"[red]✗ {file_path.name}: {type(e).__name__}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    return extracted_count, skipped_count, failed_count


def _extract_and_save_document(
    file_path: Path,
    output: Path,
    quality: str,
    tag_list: list[str],
) -> None:
    """Extract text from file and save document with metadata."""
    # Wait for file availability (critical for OneDrive/iCloud files)
    # Uses copy-based hydration for cloud-only files
    is_available, reason, alt_path = wait_for_file_availability(
        file_path,
        timeout_seconds=120.0,
        attempt_hydration_flag=True,
        use_copy_hydration=True,
    )
    if not is_available:
        if reason == "cloud_only":
            raise FileNotFoundError(
                f"File is a cloud-only placeholder (OneDrive/iCloud not downloaded). "
                f"Copy-based hydration failed: {file_path}"
            )
        raise FileNotFoundError(f"File not available ({reason}): {file_path}")

    # Use alternate path if file was copied to temp
    extract_from = alt_path if alt_path else file_path

    # Check file size before extraction
    file_size = extract_from.stat().st_size
    if file_size == 0:
        raise ValueError(
            f"File is empty (0 bytes - likely OneDrive placeholder not downloaded): {file_path}"
        )

    # Extract text from available path (original or temp copy)
    text = extract_text_from_file(extract_from)

    # Check for empty content after extraction
    if not text or not text.strip():
        raise ValueError(
            f"File has no extractable text ({file_size} bytes but empty content): {file_path}"
        )

    # Get file metadata from original path (for correct dates/paths)
    file_meta = extract_file_metadata(file_path)

    # Try to extract frontmatter if Markdown
    frontmatter = {}
    if file_path.suffix.lower() in [".md", ".markdown"]:
        content = extract_from.read_text(encoding="utf-8")
        frontmatter = extract_yaml_frontmatter(content)

    # Calculate content checksum for incremental indexing
    content_checksum = calculate_content_checksum(text)

    # Create document
    doc = Document(
        id=str(uuid.uuid4()),
        filename=file_path.name,
        source_path=file_path.absolute(),
        format=file_path.suffix.lstrip(".").lower(),
        created_date=file_meta.get("created_date"),
        modified_date=file_meta.get("modified_date"),
        quality_rating=QualityRating(quality),
        tags=frontmatter.get("tags", tag_list) if frontmatter else tag_list,
        word_count=count_words(text),
        content_checksum=content_checksum,
        source_name=None,
        voice_notes=None,
    )

    # Save extracted text
    text_file = output / f"{doc.id}.txt"
    text_file.write_text(text, encoding="utf-8")

    # Save metadata
    meta_file = output / f"{doc.id}.json"
    meta_file.write_text(doc.model_dump_json(indent=2), encoding="utf-8")
