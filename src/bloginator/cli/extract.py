"""CLI command for document extraction."""

import uuid
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from bloginator.corpus_config import CorpusConfig
from bloginator.extraction import (
    count_words,
    extract_file_metadata,
    extract_text_from_file,
    extract_yaml_frontmatter,
)
from bloginator.models import Document, QualityRating


@click.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path), required=False)
@click.option(
    "-o",
    "--output",
    required=True,
    type=click.Path(path_type=Path),
    help="Output directory for extracted documents",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to corpus.yaml configuration file",
)
@click.option(
    "--quality",
    type=click.Choice(["preferred", "reference", "supplemental", "deprecated"]),
    default="reference",
    help="Quality rating for documents (default: reference)",
)
@click.option(
    "--tags",
    help="Comma-separated tags for documents",
)
def extract(
    source: Path | None, output: Path, config: Path | None, quality: str, tags: str | None
) -> None:
    """Extract documents from SOURCE to OUTPUT directory.

    MODE 1: Single source (legacy)
        bloginator extract ~/documents -o output/extracted
        bloginator extract blog.md -o output/extracted --quality preferred

    MODE 2: Multi-source from corpus.yaml (recommended)
        bloginator extract -o output/extracted --config corpus.yaml

    SOURCE can be a single file or directory. Supported formats:
    - PDF (.pdf)
    - Microsoft Word (.docx)
    - Markdown (.md, .markdown)
    - Plain text (.txt)

    With --config, SOURCE is ignored and all enabled sources from
    corpus.yaml are processed with their configured metadata.

    Examples:
        bloginator extract corpus/ -o output/extracted --tags "blog,agile"
        bloginator extract -o output/extracted --config corpus.yaml
    """
    console = Console()
    output.mkdir(parents=True, exist_ok=True)

    # Determine extraction mode
    if config:
        # MODE 2: Config-based multi-source extraction
        _extract_from_config(config, output, console)
    elif source:
        # MODE 1: Legacy single-source extraction
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        _extract_single_source(source, output, quality, tag_list, console)
    else:
        console.print("[red]Error: Must provide either SOURCE or --config[/red]")
        raise click.UsageError("Must provide either SOURCE argument or --config option")


def _extract_single_source(
    source: Path,
    output: Path,
    quality: str,
    tag_list: list[str],
    console: Console,
) -> None:
    """Extract from single source (legacy mode)."""
    import os

    # Get list of files to extract
    if source.is_file():
        files = [source]
    else:
        files = []
        supported_extensions = {".pdf", ".docx", ".md", ".markdown", ".txt"}

        # Walk directory tree, following symlinks
        for root, dirs, filenames in os.walk(source, followlinks=True):
            root_path = Path(root)
            for filename in filenames:
                file_path = root_path / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)

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


def _extract_from_config(config_path: Path, output: Path, console: Console) -> None:
    """Extract from multiple sources using corpus.yaml config."""
    import os

    # Load config
    try:
        corpus_config = CorpusConfig.load_from_file(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise

    enabled_sources = corpus_config.get_enabled_sources()

    if not enabled_sources:
        console.print("[yellow]No enabled sources in config[/yellow]")
        return

    # Show sources table
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

    total_extracted = 0
    total_failed = 0
    config_dir = config_path.parent

    # Process each source
    for source_cfg in enabled_sources:
        if source_cfg.is_url():
            console.print(f"[yellow]⊘ Skipping URL source '{source_cfg.name}' (not yet implemented)[/yellow]")
            continue

        # Resolve path
        try:
            resolved_path = source_cfg.resolve_path(config_dir)
            if not isinstance(resolved_path, Path):
                console.print(f"[yellow]⊘ Skipping '{source_cfg.name}' (path resolution issue)[/yellow]")
                continue
        except Exception as e:
            console.print(f"[red]✗ Failed to resolve path for '{source_cfg.name}': {e}[/red]")
            continue

        if not resolved_path.exists():
            console.print(f"[yellow]⊘ Skipping '{source_cfg.name}' (path does not exist: {resolved_path})[/yellow]")
            continue

        console.print(f"[cyan]Processing '{source_cfg.name}' from {resolved_path}...[/cyan]")

        # Get files from this source
        files = []
        if resolved_path.is_file():
            files = [resolved_path]
        else:
            supported_extensions = set(corpus_config.extraction.include_extensions)
            ignore_patterns = corpus_config.extraction.ignore_patterns

            for root, dirs, filenames in os.walk(
                resolved_path,
                followlinks=corpus_config.extraction.follow_symlinks,
            ):
                root_path = Path(root)
                for filename in filenames:
                    # Check ignore patterns
                    if any(filename.startswith(p.rstrip("*")) for p in ignore_patterns):
                        continue

                    file_path = root_path / filename
                    if file_path.suffix.lower() in supported_extensions:
                        files.append(file_path)

        if not files:
            console.print(f"  [dim]No files found in '{source_cfg.name}'[/dim]")
            continue

        console.print(f"  [dim]Found {len(files)} file(s)[/dim]")

        extracted_count = 0
        failed_count = 0

        # Extract files from this source
        with Progress() as progress:
            task = progress.add_task(f"[green]Extracting {source_cfg.name}...", total=len(files))

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
                    console.print(f"  [red]✗ Failed: {file_path.name}: {e}[/red]")
                    failed_count += 1

                progress.update(task, advance=1)

        console.print(f"  [green]✓ {extracted_count} extracted[/green]")
        if failed_count > 0:
            console.print(f"  [yellow]✗ {failed_count} failed[/yellow]")

        total_extracted += extracted_count
        total_failed += failed_count

    # Summary
    console.print(f"\n[bold green]Total: {total_extracted} document(s) extracted[/bold green]")
    if total_failed > 0:
        console.print(f"[bold yellow]Total: {total_failed} document(s) failed[/bold yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")
