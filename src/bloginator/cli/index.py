"""CLI command for indexing extracted documents."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress

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

    # Find all extracted documents (metadata JSON files)
    meta_files = list(source.glob("*.json"))

    if not meta_files:
        console.print("[yellow]No extracted documents found.[/yellow]")
        console.print("[dim]Run 'bloginator extract' first to extract documents.[/dim]")
        return

    console.print(f"[cyan]Indexing {len(meta_files)} document(s)...[/cyan]")

    # Initialize indexer
    indexer = CorpusIndexer(output_dir=output)

    indexed_count = 0
    failed_count = 0

    with Progress() as progress:
        task = progress.add_task("[green]Indexing...", total=len(meta_files))

        for meta_file in meta_files:
            try:
                # Load document metadata
                doc_data = json.loads(meta_file.read_text())
                document = Document(**doc_data)

                # Load extracted text
                text_file = source / f"{document.id}.txt"
                if not text_file.exists():
                    console.print(f"[yellow]⚠ Missing text file for {document.filename}[/yellow]")
                    failed_count += 1
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
                console.print(f"[red]✗ Failed to index {meta_file.name}: {e}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    # Show statistics
    info = indexer.get_collection_info()

    console.print(f"\n[green]✓ Successfully indexed {indexed_count} document(s)[/green]")
    if failed_count > 0:
        console.print(f"[yellow]✗ Failed to index {failed_count} document(s)[/yellow]")

    console.print("\n[cyan]Index Statistics:[/cyan]")
    console.print(f"  Total chunks: {info['total_chunks']}")
    console.print(f"  Collection: {info['collection_name']}")
    console.print(f"  Output directory: {info['output_dir']}")
