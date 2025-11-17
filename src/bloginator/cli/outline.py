"""CLI command for generating outlines."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from bloginator.generation import OutlineGenerator, create_llm_client
from bloginator.search import CorpusSearcher


@click.command()
@click.option(
    "--index",
    "index_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to index directory",
)
@click.option(
    "--title",
    required=True,
    help="Document title",
)
@click.option(
    "--keywords",
    required=True,
    help="Comma-separated keywords/themes",
)
@click.option(
    "--thesis",
    default="",
    help="Optional thesis statement",
)
@click.option(
    "--sections",
    "num_sections",
    type=int,
    default=5,
    help="Target number of main sections (default: 5)",
)
@click.option(
    "--temperature",
    type=float,
    default=0.7,
    help="LLM sampling temperature 0.0-1.0 (default: 0.7)",
)
@click.option(
    "--model",
    default="llama3",
    help="LLM model to use (default: llama3)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    help="Save outline to file (JSON or markdown)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "markdown", "both"]),
    default="both",
    help="Output format (default: both)",
)
@click.option(
    "--min-coverage",
    type=int,
    default=3,
    help="Minimum sources for good coverage (default: 3)",
)
def outline(
    index_dir: Path,
    title: str,
    keywords: str,
    thesis: str,
    num_sections: int,
    temperature: float,
    model: str,
    output_file: Path | None,
    output_format: str,
    min_coverage: int,
) -> None:
    """Generate document outline from keywords and thesis.

    Uses RAG to analyze corpus coverage for each section and
    creates a structured outline with coverage statistics.

    Examples:
      Generate outline:
        bloginator outline --index output/index \\
          --title "Senior Engineer Career Ladder" \\
          --keywords "senior engineer,career ladder,IC track" \\
          --thesis "Senior engineers grow through technical mastery AND impact"

      Save to file:
        bloginator outline --index output/index \\
          --title "Agile Transformation" \\
          --keywords "agile,transformation,culture" \\
          -o outline.json

      Use different model:
        bloginator outline --index output/index \\
          --title "Test Document" \\
          --keywords "testing,quality" \\
          --model llama3.1
    """
    console = Console()

    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

    if not keyword_list:
        console.print("[red]✗[/red] No keywords provided")
        return

    # Initialize components
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load searcher
        task = progress.add_task("Loading corpus index...", total=None)
        try:
            searcher = CorpusSearcher(index_dir=index_dir)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load index: {e}")
            return
        progress.update(task, completed=True)

        # Initialize LLM client
        task = progress.add_task("Connecting to LLM...", total=None)
        try:
            llm_client = create_llm_client(model=model)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to LLM: {e}")
            console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
            return
        progress.update(task, completed=True)

        # Initialize generator
        generator = OutlineGenerator(
            llm_client=llm_client,
            searcher=searcher,
            min_coverage_sources=min_coverage,
        )

        # Generate outline
        task = progress.add_task("Generating outline structure...", total=None)
        try:
            outline_obj = generator.generate(
                title=title,
                keywords=keyword_list,
                thesis=thesis,
                num_sections=num_sections,
                temperature=temperature,
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to generate outline: {e}")
            return
        progress.update(task, completed=True)

    # Display results
    console.print()
    console.print(f"[bold cyan]Outline: {outline_obj.title}[/bold cyan]")
    if outline_obj.thesis:
        console.print(f"[dim]Thesis: {outline_obj.thesis}[/dim]")
    console.print()

    # Statistics table
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row("Total Sections:", str(len(outline_obj.get_all_sections())))
    stats_table.add_row("Avg Coverage:", f"{outline_obj.avg_coverage:.0f}%")
    stats_table.add_row("Low Coverage Sections:", str(outline_obj.low_coverage_sections))
    console.print(stats_table)
    console.print()

    # Coverage analysis
    console.print("[bold]Coverage Analysis:[/bold]")
    _display_section_coverage(console, outline_obj.sections, level=0)
    console.print()

    # Save to file if requested
    if output_file:
        try:
            if output_format in ["json", "both"]:
                json_path = (
                    output_file.with_suffix(".json")
                    if output_format == "both"
                    else output_file
                )
                json_path.write_text(outline_obj.model_dump_json(indent=2))
                console.print(f"[green]✓[/green] Saved JSON to {json_path}")

            if output_format in ["markdown", "both"]:
                md_path = (
                    output_file.with_suffix(".md")
                    if output_format == "both"
                    else output_file
                )
                md_path.write_text(outline_obj.to_markdown())
                console.print(f"[green]✓[/green] Saved markdown to {md_path}")

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to save outline: {e}")
            return
    else:
        # Display markdown preview
        console.print("[bold]Markdown Preview:[/bold]")
        console.print(outline_obj.to_markdown())

    # Warnings
    if outline_obj.low_coverage_sections > 0:
        console.print()
        console.print(
            f"[yellow]⚠️[/yellow] {outline_obj.low_coverage_sections} section(s) have low corpus coverage"
        )
        console.print(
            "[dim]Consider revising these sections or adding more source material[/dim]"
        )


def _display_section_coverage(console: Console, sections: list, level: int = 0) -> None:
    """Display section coverage recursively."""
    indent = "  " * level
    for section in sections:
        # Coverage color coding
        if section.coverage_pct >= 75:
            coverage_color = "green"
            icon = "✓"
        elif section.coverage_pct >= 50:
            coverage_color = "yellow"
            icon = "○"
        else:
            coverage_color = "red"
            icon = "⚠"

        # Display section
        console.print(
            f"{indent}[{coverage_color}]{icon}[/{coverage_color}] {section.title} "
            f"[dim]({section.coverage_pct:.0f}% coverage, {section.source_count} sources)[/dim]"
        )

        if section.notes:
            console.print(f"{indent}  [dim]{section.notes}[/dim]")

        # Recursively display subsections
        if section.subsections:
            _display_section_coverage(console, section.subsections, level + 1)
