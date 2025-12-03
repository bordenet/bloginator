"""CLI command for searching the corpus."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.search import CorpusSearcher


@click.command()
@click.argument("index_dir", type=click.Path(exists=True, path_type=Path))
@click.argument("query", required=False)
@click.option(
    "-n",
    "--num-results",
    default=10,
    type=int,
    help="Number of results to return (default: 10)",
)
@click.option(
    "--recency-weight",
    default=0.2,
    type=float,
    help="Weight for recency scoring 0.0-1.0 (default: 0.2)",
)
@click.option(
    "--quality-weight",
    default=0.1,
    type=float,
    help="Weight for quality scoring 0.0-1.0 (default: 0.1)",
)
@click.option(
    "--quality-filter",
    type=click.Choice(["preferred", "standard", "deprecated"]),
    help="Filter by quality rating",
)
@click.option(
    "--format-filter",
    type=click.Choice(["pdf", "docx", "markdown", "txt"]),
    help="Filter by document format",
)
@click.option(
    "--tags",
    help="Filter by tags (comma-separated, any match)",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Interactive search mode (multiple queries)",
)
@click.option(
    "--show-scores",
    is_flag=True,
    help="Show detailed scoring breakdown",
)
def search(
    index_dir: Path,
    query: str | None,
    num_results: int,
    recency_weight: float,
    quality_weight: float,
    quality_filter: str | None,
    format_filter: str | None,
    tags: str | None,
    interactive: bool,
    show_scores: bool,
) -> None:
    """Search the corpus for relevant content.

    INDEX_DIR: Directory containing the ChromaDB index
    QUERY: Search query (optional in interactive mode)

    Examples:
      # Basic search
      bloginator search output/index "agile transformation"

      # Search with filters
      bloginator search output/index "hiring" --quality-filter preferred

      # Weighted search
      bloginator search output/index "culture" --recency-weight 0.5 --quality-weight 0.2

      # Interactive mode
      bloginator search output/index --interactive

      # Show scoring details
      bloginator search output/index "leadership" --show-scores
    """
    console = Console()

    try:
        searcher = CorpusSearcher(index_dir=index_dir)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]", err=True)
        console.print("[dim]Run 'bloginator index' to create an index first.[/dim]", err=True)
        sys.exit(1)

    # Parse tags
    tags_filter = [t.strip() for t in tags.split(",")] if tags else None

    # Interactive mode
    if interactive:
        console.print("[cyan]Interactive Search Mode[/cyan]")
        console.print("[dim]Type your query (or 'quit' to exit)[/dim]\n")

        while True:
            query_input = click.prompt("Search", default="", show_default=False)

            # Ensure query_input is a string (click.prompt with default should return str)
            if not query_input or query_input.lower() in ["quit", "exit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                break

            if not query_input.strip():
                continue

            _display_results(
                console,
                searcher,
                query_input,
                num_results,
                recency_weight,
                quality_weight,
                quality_filter,
                format_filter,
                tags_filter,
                show_scores,
            )
            console.print()  # Blank line between searches

    else:
        # Single query mode
        if not query:
            raise click.UsageError("Query required in non-interactive mode")

        _display_results(
            console,
            searcher,
            query,
            num_results,
            recency_weight,
            quality_weight,
            quality_filter,
            format_filter,
            tags_filter,
            show_scores,
        )


def _display_results(
    console: Console,
    searcher: CorpusSearcher,
    query: str,
    n: int,
    recency_w: float,
    quality_w: float,
    quality_filter: str | None,
    format_filter: str | None,
    tags_filter: list[str] | None,
    show_scores: bool,
) -> None:
    """Display search results in a formatted table.

    Args:
        console: Rich console for output
        searcher: CorpusSearcher instance
        query: Search query
        n: Number of results
        recency_w: Recency weight
        quality_w: Quality weight
        quality_filter: Quality filter
        format_filter: Format filter
        tags_filter: Tags filter
        show_scores: Whether to show detailed scores
    """
    # Perform search with weights
    results = searcher.search_with_weights(
        query=query,
        n_results=n,
        recency_weight=recency_w,
        quality_weight=quality_w,
        quality_filter=quality_filter,
        format_filter=format_filter,
        tags_filter=tags_filter,
    )

    if not results:
        console.print(f"[yellow]No results found for: '{query}'[/yellow]")
        return

    # Create results table
    title = f"Search Results: '{query}' ({len(results)} results)"
    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("Score", justify="right", style="green", width=6)

    if show_scores:
        table.add_column("Sim", justify="right", width=5)
        table.add_column("Rec", justify="right", width=5)
        table.add_column("Qual", justify="right", width=5)

    table.add_column("Content", overflow="fold", max_width=60)
    table.add_column("Source", style="dim", width=20)
    table.add_column("Date", style="dim", width=10)
    table.add_column("Quality", width=10)

    for result in results:
        # Format content preview
        content_preview = result.content[:150]
        if len(result.content) > 150:
            content_preview += "..."

        # Extract metadata
        filename = result.metadata.get("filename", "Unknown")
        date_str = result.metadata.get("created_date", "")
        date_display = date_str[:10] if date_str else "Unknown"  # Just YYYY-MM-DD
        quality = result.metadata.get("quality_rating", "standard")

        # Format quality with color
        quality_colors = {
            "preferred": "green",
            "standard": "yellow",
            "deprecated": "red",
        }
        quality_color = quality_colors.get(quality, "white")
        quality_display = f"[{quality_color}]{quality}[/{quality_color}]"

        # Build row
        row = [f"{result.combined_score:.3f}"]

        if show_scores:
            row.extend(
                [
                    f"{result.similarity_score:.2f}",
                    f"{result.recency_score:.2f}",
                    f"{result.quality_score:.2f}",
                ]
            )

        row.extend(
            [
                content_preview,
                filename,
                date_display,
                quality_display,
            ]
        )

        table.add_row(*row)

    console.print(table)

    # Show weighting info
    if show_scores:
        sim_weight = 1.0 - recency_w - quality_w
        console.print(
            f"\n[dim]Weights: Similarity={sim_weight:.1f}, "
            f"Recency={recency_w:.1f}, Quality={quality_w:.1f}[/dim]"
        )
