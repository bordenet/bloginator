"""CLI command for indexing extracted documents."""

import json
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from bloginator.cli.error_reporting import (
    ErrorCategory,
    ErrorTracker,
    SkipCategory,
    create_error_panel,
)
from bloginator.extraction import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Document


@click.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory for index",
)
@click.option(
    "--chunk-size",
    default=1000,
    type=int,
    help="Maximum chunk size in characters (default: 1000)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force rebuild: purge existing index and rebuild from scratch",
)
def index(source: Path, output: Path, chunk_size: int, force: bool) -> None:
    """Build searchable index from extracted documents in SOURCE.

    SOURCE should be the output directory from the 'extract' command,
    containing .txt and .json files for each document.

    Examples:
        bloginator index output/extracted -o output/index
        bloginator index output/extracted -o output/index --chunk-size 500
    """
    console = Console()

    # If force flag is set, purge existing index
    if force and output.exists():
        console.print(f"[yellow]🗑️  Purging existing index: {output}[/yellow]")
        shutil.rmtree(output)
        console.print("[green]✓ Index purged successfully[/green]\n")

    # Initialize error tracker
    error_tracker = ErrorTracker()

    # Find all extracted documents (metadata JSON files) - recursively
    meta_files = list(source.rglob("*.json"))

    if not meta_files:
        panel = create_error_panel(
            "No Documents Found",
            f"No extracted documents found in {source}",
            "Run 'bloginator extract' first to extract documents from your corpus.",
        )
        console.print(panel)
        return

    console.print(f"[cyan]Indexing {len(meta_files)} document(s)...[/cyan]")

    # Initialize indexer
    try:
        indexer = CorpusIndexer(output_dir=output)
    except Exception as e:
        category = error_tracker.categorize_exception(e)
        advice = error_tracker.get_actionable_advice(category)
        panel = create_error_panel(
            "Indexer Initialization Failed",
            f"Failed to initialize indexer: {e}",
            advice,
        )
        console.print(panel)
        raise

    indexed_count = 0
    skipped_count = 0
    failed_count = 0

    # Create ticker-style progress bar (single line that updates in place)
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("• {task.fields[current_file]}"),
        console=console,
        transient=True,  # Disappears when complete
    )

    with progress:
        task = progress.add_task(
            "[green]Indexing",
            total=len(meta_files),
            current_file="starting...",
        )

        for meta_file in meta_files:
            # Update ticker with current file (show full path)
            display_path = str(meta_file)
            progress.update(task, current_file=display_path)

            try:
                # Load document metadata
                doc_data = json.loads(meta_file.read_text())
                document = Document(**doc_data)

                # Check if document needs reindexing (incremental indexing with checksums)
                if not indexer.document_needs_reindexing(document):
                    source_path = document.source_path or document.filename
                    error_tracker.record_skip(SkipCategory.ALREADY_EXTRACTED, source_path)
                    # Output parseable skip event for Streamlit
                    progress.console.print(
                        f"[SKIP] {source_path} (already_indexed)", highlight=False
                    )
                    skipped_count += 1
                    progress.update(task, advance=1)
                    continue

                # Delete old version if it exists (for reindexing)
                if indexer.get_document_checksum(document.id) is not None:
                    indexer.delete_document(document.id)

                # Load extracted text (look in same directory as JSON file)
                text_file = meta_file.parent / f"{document.id}.txt"
                if not text_file.exists():
                    error = FileNotFoundError(f"Missing text file: {text_file}")
                    category = ErrorCategory.FILE_NOT_FOUND
                    error_tracker.record_error(category, document.filename, error)
                    progress.console.print(
                        f"[yellow]⚠ {document.filename}: Missing text file[/yellow]"
                    )
                    failed_count += 1
                    progress.update(task, advance=1)
                    continue

                text = text_file.read_text(encoding="utf-8")

                # Chunk text
                chunks = chunk_text_by_paragraphs(
                    text=text,
                    document_id=document.id,
                    max_chunk_size=chunk_size,
                )

                # Index document
                indexer.index_document(document, chunks)

                indexed_count += 1

            except Exception as e:
                # Categorize and track error
                category = error_tracker.categorize_exception(e, meta_file)
                context = document.filename if "document" in locals() else meta_file.name
                error_tracker.record_error(category, context, e)
                progress.console.print(f"[red]✗ {context}: {type(e).__name__}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    # Save report to file if there were skips or errors
    report_file: Path | None = None
    if error_tracker.total_skipped > 0 or error_tracker.total_errors > 0:
        report_file = error_tracker.save_to_file(output, prefix="indexing")

    # Show statistics
    info = indexer.get_collection_info()

    console.print(f"\n[green]✓ Successfully indexed {indexed_count} document(s)[/green]")
    if skipped_count > 0:
        console.print(
            f"[cyan]↻ Skipped {skipped_count} document(s) (unchanged since last index)[/cyan]"
        )
    if failed_count > 0:
        console.print(f"[yellow]✗ Failed to index {failed_count} document(s)[/yellow]")

    console.print("\n[cyan]Index Statistics:[/cyan]")
    console.print(f"  Total chunks: {info['total_chunks']}")
    console.print(f"  Collection: {info['collection_name']}")
    console.print(f"  Output directory: {info['output_dir']}")

    # Print skip summary if there were skips (with file path)
    if skipped_count > 0 and error_tracker.total_skipped > 0:
        error_tracker.print_skip_summary(console, show_file_path=report_file)

    # Print error summary if there were failures
    if failed_count > 0:
        error_tracker.print_summary(console)
