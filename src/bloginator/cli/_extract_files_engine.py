"""File extraction engine for corpus source processing."""

import uuid
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from bloginator.cli.error_reporting import ErrorTracker, SkipCategory
from bloginator.cli.extract_utils import should_skip_file, wait_for_file_availability
from bloginator.corpus_config import CorpusSource
from bloginator.extraction import (
    count_words,
    extract_file_metadata,
    extract_text_from_file,
    extract_yaml_frontmatter,
)
from bloginator.models import Document
from bloginator.utils.checksum import calculate_content_checksum


def extract_source_files(
    files: list[Path],
    source_cfg: CorpusSource,
    output: Path,
    existing_docs: dict[str, tuple[str, datetime]],
    force: bool,
    error_tracker: ErrorTracker,
    console: Console,
    verbose: bool = False,
) -> tuple[int, int, int]:
    """Extract files from a source with ticker-style progress.

    Uses a single-line ticker that shows current file being processed,
    then disappears when complete.

    Args:
        files: List of file paths to extract
        source_cfg: Source configuration
        output: Output directory
        existing_docs: Dictionary of existing extractions
        force: Force re-extraction flag
        error_tracker: Error tracker instance
        console: Rich console
        verbose: If True, show detailed progress information

    Returns:
        Tuple of (extracted_count, skipped_count, failed_count)
    """
    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    # Create progress with spinner and ticker-style current file display
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("• {task.fields[current_file]}"),
        console=console,
        transient=not verbose,  # Keep progress visible if verbose mode
    )

    with progress:
        task = progress.add_task(
            f"[green]{source_cfg.name}",
            total=len(files),
            current_file="starting...",
        )

        for file_path in files:
            # Output current file path for Streamlit UI to parse (always in verbose)
            if verbose:
                progress.console.print(f"Extracting: {file_path}", highlight=False)

            # Update ticker with current file (show full path)
            display_path = str(file_path)
            progress.update(task, current_file=display_path)

            try:
                # Record file for statistics (not extracted yet)
                error_tracker.record_file(file_path, extracted=False)

                # Check if we should skip this file
                skip, doc_id = should_skip_file(file_path, existing_docs, force)

                if skip:
                    error_tracker.record_skip(SkipCategory.ALREADY_EXTRACTED, str(file_path))
                    # Output parseable skip event for Streamlit (verbose only)
                    if verbose:
                        progress.console.print(
                            f"[SKIP] {file_path} (already_extracted)", highlight=False
                        )
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Wait for file availability (critical for OneDrive/iCloud files)
                # Cloud files may appear in directory but are placeholders (st_blocks=0)
                is_available, availability_reason = wait_for_file_availability(
                    file_path, timeout_seconds=30.0, attempt_hydration_flag=True
                )
                if not is_available:
                    # File not available - determine skip category
                    if availability_reason == "cloud_only":
                        error_tracker.record_skip(
                            SkipCategory.CLOUD_ONLY,
                            f"{file_path} (OneDrive/iCloud placeholder - not downloaded)",
                        )
                        if verbose:
                            progress.console.print(
                                f"[SKIP] {file_path} (cloud_only: hydration failed)",
                                highlight=False,
                            )
                    else:
                        error_tracker.record_skip(
                            SkipCategory.PATH_NOT_FOUND,
                            f"{file_path} (not available - {availability_reason})",
                        )
                        if verbose:
                            progress.console.print(
                                f"[SKIP] {file_path} (path_not_found: {availability_reason})",
                                highlight=False,
                            )
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Log successful hydration if verbose
                if verbose and availability_reason == "hydrated":
                    progress.console.print(
                        f"[HYDRATED] {file_path} (cloud file downloaded)",
                        highlight=False,
                    )

                # Check file size before extraction
                file_size = file_path.stat().st_size
                if file_size == 0:
                    error_tracker.record_skip(
                        SkipCategory.EMPTY_CONTENT,
                        f"{file_path} (0 bytes - likely OneDrive placeholder not downloaded)",
                    )
                    if verbose:
                        progress.console.print(
                            f"[SKIP] {file_path} (empty_content: 0 bytes)", highlight=False
                        )
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Extract text
                text = extract_text_from_file(file_path)

                # Check for empty content after extraction
                if not text or not text.strip():
                    error_tracker.record_skip(
                        SkipCategory.EMPTY_CONTENT,
                        f"{file_path} ({file_size} bytes but no extractable text)",
                    )
                    if verbose:
                        progress.console.print(
                            f"[SKIP] {file_path} (empty_content: no text extracted)",
                            highlight=False,
                        )
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

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

                # Calculate content checksum for incremental indexing
                content_checksum = calculate_content_checksum(text)

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
                    content_checksum=content_checksum,
                )

                # Save extracted text
                text_file = output / f"{doc.id}.txt"
                text_file.write_text(text, encoding="utf-8")

                # Save metadata
                meta_file = output / f"{doc.id}.json"
                meta_file.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

                extracted_count += 1
                # Update file stats to mark as extracted
                error_tracker.extracted_by_type[file_path.suffix.lower() or "(no extension)"] += 1
                error_tracker.total_extracted += 1

            except Exception as e:
                # Categorize and track error
                category = error_tracker.categorize_exception(e, file_path)
                error_tracker.record_error(category, f"{source_cfg.name}/{file_path.name}", e)
                # Print error on separate line (progress is transient so this works)
                progress.console.print(f"  [red]✗ {file_path.name}: {type(e).__name__}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    return extracted_count, skipped_count, failed_count
