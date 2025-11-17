"""CLI command for document extraction."""

import uuid
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress

from bloginator.extraction import (
    count_words,
    extract_file_metadata,
    extract_text_from_file,
    extract_yaml_frontmatter,
)
from bloginator.models import Document, QualityRating


@click.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory for extracted documents",
)
@click.option(
    "--quality",
    type=click.Choice(["preferred", "standard", "deprecated"]),
    default="standard",
    help="Quality rating for documents (default: standard)",
)
@click.option(
    "--tags",
    help="Comma-separated tags for documents",
)
def extract(source: Path, output: Path, quality: str, tags: str | None) -> None:
    """Extract documents from SOURCE to OUTPUT directory.

    SOURCE can be a single file or directory. Supported formats:
    - PDF (.pdf)
    - Microsoft Word (.docx)
    - Markdown (.md, .markdown)
    - Plain text (.txt)

    Examples:
        bloginator extract ~/documents -o output/extracted
        bloginator extract blog.md -o output/extracted --quality preferred
        bloginator extract corpus/ -o output/extracted --tags "blog,agile"
    """
    console = Console()
    output.mkdir(parents=True, exist_ok=True)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Get list of files to extract
    if source.is_file():
        files = [source]
    else:
        # Find all supported files in directory
        files = []
        for pattern in ["*.pdf", "*.docx", "*.md", "*.markdown", "*.txt"]:
            files.extend(source.rglob(pattern))

    if not files:
        console.print("[yellow]No supported files found.[/yellow]")
        return

    console.print(f"[cyan]Extracting {len(files)} file(s)...[/cyan]")

    extracted_count = 0
    failed_count = 0

    with Progress() as progress:
        task = progress.add_task("[green]Extracting...", total=len(files))

        for file_path in files:
            try:
                # Extract text
                text = extract_text_from_file(file_path)

                # Get file metadata
                file_meta = extract_file_metadata(file_path)

                # Try to extract frontmatter if Markdown
                frontmatter = {}
                if file_path.suffix.lower() in [".md", ".markdown"]:
                    content = file_path.read_text(encoding="utf-8")
                    frontmatter = extract_yaml_frontmatter(content)

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
                )

                # Save extracted text
                text_file = output / f"{doc.id}.txt"
                text_file.write_text(text, encoding="utf-8")

                # Save metadata
                meta_file = output / f"{doc.id}.json"
                meta_file.write_text(doc.model_dump_json(indent=2), encoding="utf-8")

                extracted_count += 1

            except Exception as e:
                console.print(f"[red]✗ Failed to extract {file_path.name}: {e}[/red]")
                failed_count += 1

            progress.update(task, advance=1)

    console.print(f"\n[green]✓ Successfully extracted {extracted_count} document(s)[/green]")
    if failed_count > 0:
        console.print(f"[yellow]✗ Failed to extract {failed_count} document(s)[/yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")
