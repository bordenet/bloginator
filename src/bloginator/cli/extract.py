"""CLI command for document extraction."""

import json
import uuid
from datetime import datetime
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


def _load_existing_extractions(output_dir: Path) -> dict[str, tuple[str, datetime]]:
    """Load existing extractions from output directory.

    Scans all *.json metadata files and builds a mapping of:
        source_path → (doc_id, modified_date)

    This allows us to skip files that have already been extracted
    and haven't changed since extraction.

    Args:
        output_dir: Directory containing extracted *.json metadata files

    Returns:
        Dictionary mapping source file paths to (doc_id, modified_date) tuples
    """
    existing = {}

    if not output_dir.exists():
        return existing

    # Scan all .json metadata files
    for json_file in output_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            source_path = metadata.get("source_path")
            doc_id = metadata.get("id")
            modified_date_str = metadata.get("modified_date")

            if source_path and doc_id and modified_date_str:
                # Parse the modified date
                modified_date = datetime.fromisoformat(modified_date_str.replace("Z", "+00:00"))
                existing[str(source_path)] = (doc_id, modified_date)
        except (json.JSONDecodeError, ValueError, KeyError):
            # Skip invalid metadata files
            continue

    return existing


def _should_skip_file(file_path: Path, existing_docs: dict[str, tuple[str, datetime]], force: bool = False) -> tuple[bool, str | None]:
    """Determine if a file should be skipped during extraction.

    Args:
        file_path: Path to the file being considered
        existing_docs: Dictionary from _load_existing_extractions()
        force: If True, never skip (re-extract everything)

    Returns:
        Tuple of (should_skip, reason_or_doc_id)
        - If should_skip is True, reason_or_doc_id contains the doc_id to reuse
        - If should_skip is False, reason_or_doc_id is None
    """
    # Skip temp files (Office/Word temp files starting with ~$)
    if file_path.name.startswith("~$"):
        return True, None

    # Never skip if --force is enabled
    if force:
        return False, None

    # Check if file was already extracted
    source_path_str = str(file_path.absolute())
    if source_path_str not in existing_docs:
        return False, None

    doc_id, extracted_mtime = existing_docs[source_path_str]

    # Get current file modification time
    try:
        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

        # Skip if file hasn't been modified since extraction
        # Use a small tolerance (1 second) to handle filesystem timestamp precision
        if current_mtime <= extracted_mtime:
            return True, doc_id
    except (OSError, ValueError):
        # If we can't stat the file, don't skip it
        return False, None

    # File was modified after extraction, needs re-extraction
    return False, None


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
@click.option(
    "--force",
    is_flag=True,
    help="Force re-extraction of all files, even if already extracted",
)
def extract(
    source: Path | None, output: Path, config: Path | None, quality: str, tags: str | None, force: bool
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
        _extract_from_config(config, output, console, force)
    elif source:
        # MODE 1: Legacy single-source extraction
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        _extract_single_source(source, output, quality, tag_list, console, force)
    else:
        console.print("[red]Error: Must provide either SOURCE or --config[/red]")
        raise click.UsageError("Must provide either SOURCE argument or --config option")


def _extract_single_source(
    source: Path,
    output: Path,
    quality: str,
    tag_list: list[str],
    console: Console,
    force: bool = False,
) -> None:
    """Extract from single source (legacy mode)."""
    import os

    # Load existing extractions for skip logic
    existing_docs = _load_existing_extractions(output)

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
                # Skip temp files
                if filename.startswith("~$"):
                    continue

                file_path = root_path / filename
                if file_path.suffix.lower() in supported_extensions:
                    files.append(file_path)

    if not files:
        console.print("[yellow]No supported files found.[/yellow]")
        return

    console.print(f"[cyan]Found {len(files)} file(s)...[/cyan]")

    extracted_count = 0
    skipped_count = 0
    failed_count = 0

    with Progress() as progress:
        task = progress.add_task("[green]Processing...", total=len(files))

        for file_path in files:
            try:
                # Check if we should skip this file
                should_skip, doc_id = _should_skip_file(file_path, existing_docs, force)

                if should_skip:
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
    if skipped_count > 0:
        console.print(f"[cyan]↻ Skipped {skipped_count} document(s) (already extracted)[/cyan]")
    if failed_count > 0:
        console.print(f"[yellow]✗ Failed to extract {failed_count} document(s)[/yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")


def _extract_from_config(config_path: Path, output: Path, console: Console, force: bool = False) -> None:
    """Extract from multiple sources using corpus.yaml config."""
    import os

    # Load config
    try:
        corpus_config = CorpusConfig.load_from_file(config_path)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise

    # Load existing extractions for skip logic
    existing_docs = _load_existing_extractions(output)

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
    total_skipped = 0
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
            # Skip temp files even for single files
            if not resolved_path.name.startswith("~$"):
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
                    # Skip temp files
                    if filename.startswith("~$"):
                        continue

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
        skipped_count = 0
        failed_count = 0

        # Extract files from this source
        with Progress() as progress:
            task = progress.add_task(f"[green]Processing {source_cfg.name}...", total=len(files))

            for file_path in files:
                try:
                    # Check if we should skip this file
                    should_skip, doc_id = _should_skip_file(file_path, existing_docs, force)

                    if should_skip:
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
                    console.print(f"  [red]✗ Failed: {file_path.name}: {e}[/red]")
                    failed_count += 1

                progress.update(task, advance=1)

        console.print(f"  [green]✓ {extracted_count} extracted[/green]")
        if skipped_count > 0:
            console.print(f"  [cyan]↻ {skipped_count} skipped[/cyan]")
        if failed_count > 0:
            console.print(f"  [yellow]✗ {failed_count} failed[/yellow]")

        total_extracted += extracted_count
        total_skipped += skipped_count
        total_failed += failed_count

    # Summary
    console.print(f"\n[bold green]Total: {total_extracted} document(s) extracted[/bold green]")
    if total_skipped > 0:
        console.print(f"[bold cyan]Total: {total_skipped} document(s) skipped (already extracted)[/bold cyan]")
    if total_failed > 0:
        console.print(f"[bold yellow]Total: {total_failed} document(s) failed[/bold yellow]")
    console.print(f"[cyan]Output directory: {output}[/cyan]")
