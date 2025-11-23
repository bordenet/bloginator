"""CLI command for generating outlines."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from bloginator.generation import OutlineGenerator
from bloginator.generation.llm_factory import create_llm_from_config
from bloginator.models.history import GenerationHistoryEntry, GenerationType
from bloginator.models.outline import OutlineSection
from bloginator.search import CorpusSearcher
from bloginator.services.history_manager import HistoryManager
from bloginator.services.template_manager import TemplateManager


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
    "--classification",
    type=click.Choice(["guidance", "best-practice", "mandate", "principle", "opinion"]),
    default="guidance",
    help="Content classification: authority level and tone (default: guidance)",
)
@click.option(
    "--audience",
    type=click.Choice(
        [
            "ic-engineers",
            "senior-engineers",
            "engineering-leaders",
            "qa-engineers",
            "devops-sre",
            "product-managers",
            "technical-leadership",
            "all-disciplines",
            "executives",
            "general",
        ]
    ),
    default="all-disciplines",
    help="Target audience for content (default: all-disciplines)",
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
@click.option(
    "--template",
    "template_id",
    help="Template ID for custom prompt style (use 'bloginator template list' to see options)",
)
@click.option(
    "--log-file",
    type=click.Path(path_type=Path),
    help="Path to log file (logs to stdout if not specified)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show LLM request/response interactions",
)
def outline(
    index_dir: Path,
    title: str,
    keywords: str,
    thesis: str,
    classification: str,
    audience: str,
    num_sections: int,
    temperature: float,
    model: str,
    output_file: Path | None,
    output_format: str,
    min_coverage: int,
    template_id: str | None,
    log_file: Path | None,
    verbose: bool,
) -> None:
    r"""Generate document outline from keywords and thesis.

    Uses RAG to analyze corpus coverage for each section and
    creates a structured outline with coverage statistics.

    Examples:
      Generate outline with classification and audience:
        bloginator outline --index output/index \\
          --title "Senior Engineer Career Ladder" \\
          --keywords "senior engineer,career ladder,IC track" \\
          --thesis "Senior engineers grow through technical mastery AND impact" \\
          --classification best-practice \\
          --audience engineering-leaders

      Mandate for IC engineers:
        bloginator outline --index output/index \\
          --title "Code Review Standards" \\
          --keywords "code review,quality,best practices" \\
          --classification mandate \\
          --audience ic-engineers

      Save to file:
        bloginator outline --index output/index \\
          --title "Agile Transformation" \\
          --keywords "agile,transformation,culture" \\
          --classification guidance \\
          -o outline.json

      Use different model:
        bloginator outline --index output/index \\
          --title "Test Document" \\
          --keywords "testing,quality" \\
          --model llama3.1
    """
    # Configure logging
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        logger = logging.getLogger(__name__)
        logger.info(f"Logging to {log_file}")
        logger.info(f"Starting outline generation: {title}")
    else:
        logging.basicConfig(level=logging.WARNING)
        logger = logging.getLogger(__name__)

    console = Console()

    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    logger.info(f"Keywords: {keyword_list}")

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
            logger.info(f"Loading index from {index_dir}")
            searcher = CorpusSearcher(index_dir=index_dir)
            logger.info("Index loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            console.print(f"[red]✗[/red] Failed to load index: {e}")
            return
        progress.update(task, completed=True)

        # Initialize LLM client
        task = progress.add_task("Connecting to LLM...", total=None)
        try:
            logger.info(
                f"Connecting to LLM from config (model param '{model}' is ignored, using .env)"
            )
            llm_client = create_llm_from_config(verbose=verbose)
            logger.info("LLM client connected")
        except Exception as e:
            logger.error(f"Failed to connect to LLM: {e}")
            console.print(f"[red]✗[/red] Failed to connect to LLM: {e}")
            console.print("[dim]Make sure Ollama is running and check .env configuration[/dim]")
            return
        progress.update(task, completed=True)

        # Initialize generator
        logger.info("Initializing outline generator")
        generator = OutlineGenerator(
            llm_client=llm_client,
            searcher=searcher,
            min_coverage_sources=min_coverage,
        )

        # Handle custom template if provided
        custom_prompt = None
        if template_id:
            try:
                template_manager = TemplateManager()
                rendered = template_manager.render_template(
                    template_id,
                    title=title,
                    keywords=", ".join(keyword_list),
                    thesis=thesis,
                    num_sections=str(num_sections),
                )
                custom_prompt = rendered
                logger.info(f"Using template: {template_id}")
            except Exception as e:
                logger.warning(f"Failed to load template {template_id}: {e}")
                console.print(f"[yellow]⚠️[/yellow] Failed to load template, using default: {e}")

        # Generate outline
        task = progress.add_task("Generating outline structure...", total=None)
        try:
            logger.info(
                f"Generating outline with {num_sections} sections, "
                f"classification={classification}, audience={audience}, temperature={temperature}"
            )
            outline_obj = generator.generate(
                title=title,
                keywords=keyword_list,
                thesis=thesis,
                classification=classification,
                audience=audience,
                num_sections=num_sections,
                temperature=temperature,
                custom_prompt_template=custom_prompt,
            )
            logger.info(f"Outline generated: {len(outline_obj.get_all_sections())} total sections")
        except Exception as e:
            logger.error(f"Failed to generate outline: {e}", exc_info=True)
            console.print(f"[red]✗[/red] Failed to generate outline: {e}")
            return
        progress.update(task, completed=True)

    # Display results
    console.print()
    console.print(f"[bold cyan]Outline: {outline_obj.title}[/bold cyan]")

    # Display classification and audience as subtitle
    classification_label = classification.replace("-", " ").title()
    audience_label = audience.replace("-", " ").title()
    console.print(f"[dim italic]{classification_label} • For {audience_label}[/dim italic]")

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
                    output_file.with_suffix(".json") if output_format == "both" else output_file
                )
                json_path.write_text(outline_obj.model_dump_json(indent=2))
                logger.info(f"Saved JSON to {json_path}")
                console.print(f"[green]✓[/green] Saved JSON to {json_path}")

            if output_format in ["markdown", "both"]:
                md_path = output_file.with_suffix(".md") if output_format == "both" else output_file
                md_path.write_text(outline_obj.to_markdown())
                logger.info(f"Saved markdown to {md_path}")
                console.print(f"[green]✓[/green] Saved markdown to {md_path}")

            # Save to history
            try:
                history_manager = HistoryManager()
                history_entry = GenerationHistoryEntry(
                    generation_type=GenerationType.OUTLINE,
                    title=title,
                    classification=classification,
                    audience=audience,
                    input_params={
                        "keywords": keyword_list,
                        "thesis": thesis,
                        "num_sections": num_sections,
                        "temperature": temperature,
                    },
                    output_path=str(output_file),
                    output_format=output_format,
                    metadata={
                        "total_sections": len(outline_obj.get_all_sections()),
                        "avg_coverage": outline_obj.avg_coverage,
                        "low_coverage_sections": outline_obj.low_coverage_sections,
                        "total_sources": outline_obj.total_sources,
                        "min_coverage": min_coverage,
                    },
                )
                history_manager.save_entry(history_entry)
                logger.info(f"Saved to history: {history_entry.id}")
            except Exception as e:
                # Don't fail the command if history save fails
                logger.warning(f"Failed to save to history: {e}")

        except Exception as e:
            logger.error(f"Failed to save outline: {e}")
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
        console.print("[dim]Consider revising these sections or adding more source material[/dim]")


def _display_section_coverage(
    console: Console, sections: list[OutlineSection], level: int = 0
) -> None:
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
