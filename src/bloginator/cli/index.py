"""CLI command for indexing extracted documents."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress

from bloginator.cli.error_reporting import ErrorCategory, ErrorTracker, create_error_panel
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
def index(source: Path, output: Path, chunk_size: int) -> None:
    """Build searchable index from extracted documents in SOURCE.

    SOURCE should be the output directory from the 'extract' command,
    containing .txt and .json files for each document.

    Examples:
        bloginator index output/extracted -o output/index
        bloginator index output/extracted -o output/index --chunk-size 500
    """
    console = Console()

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

    with Progress() as progress:
        task = progress.add_task("[green]Indexing...", total=len(meta_files))

        for meta_file in meta_files:
            try:
                # Load document metadata
                doc_data = json.loads(meta_file.read_text())
                document = Document(**doc_data)

                # Check if document needs reindexing (incremental indexing with checksums)
                if not indexer.document_needs_reindexing(document):
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
                    console.print(f"[yellow]⚠ {document.filename}: Missing text file[/yellow]")
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
                console.print(f"[red]✗ {context}: {type(e).__name__}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

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

    # Print error summary if there were failures
    if failed_count > 0:
        error_tracker.print_summary(console)
