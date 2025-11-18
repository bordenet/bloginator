"""CLI command for document extraction.

This module provides the CLI interface for extracting documents from various sources.
Supports both single-source extraction (legacy mode) and multi-source extraction
from corpus.yaml configuration files.
"""

from pathlib import Path

import click
from rich.console import Console

from bloginator.cli.extract_config import extract_from_config
from bloginator.cli.extract_single import extract_single_source


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
    source: Path | None,
    output: Path,
    config: Path | None,
    quality: str,
    tags: str | None,
    force: bool,
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
        bloginator extract -o output/extracted --config corpus.yaml --force
    """
    console = Console()
    output.mkdir(parents=True, exist_ok=True)

    # Determine extraction mode
    if config:
        # MODE 2: Config-based multi-source extraction
        extract_from_config(config, output, console, force)
    elif source:
        # MODE 1: Legacy single-source extraction
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        extract_single_source(source, output, quality, tag_list, console, force)
    else:
        console.print("[red]Error: Must provide either SOURCE or --config[/red]")
        raise click.UsageError("Must provide either SOURCE argument or --config option")
