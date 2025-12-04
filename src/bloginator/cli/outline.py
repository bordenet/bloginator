"""CLI command for generating outlines."""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bloginator.cli._outline_formatter import (
    display_markdown_preview,
    display_outline_results,
    save_outline_files,
)
from bloginator.generation import OutlineGenerator
from bloginator.generation.llm_factory import create_llm_from_config
from bloginator.search import CorpusSearcher
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
    default=None,
    help="LLM model to use (default: from BLOGINATOR_LLM_MODEL env var, falls back to ministral-3:14b)",
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
          --model ministral-3:14b
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
        sys.exit(1)

    # Initialize components
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load searcher (this may load embedding model on first run)
        task = progress.add_task(
            "Loading corpus index and embedding model (first run may take 10-60s)...", total=None
        )
        try:
            logger.info(f"Loading index from {index_dir}")
            searcher = CorpusSearcher(index_dir=index_dir)
            logger.info("Index loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            console.print(f"[red]✗[/red] Failed to load index: {e}")
            console.print(
                "[dim]Note: First run downloads embedding model from HuggingFace (may take time)[/dim]"
            )
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
            sys.exit(1)
        progress.update(task, completed=True)

    # Display results
    display_outline_results(console, outline_obj, classification, audience, min_coverage, logger)

    # Save to file if requested
    if output_file:
        save_outline_files(
            outline_obj,
            output_file,
            output_format,
            title,
            classification,
            audience,
            keyword_list,
            thesis,
            num_sections,
            temperature,
            min_coverage,
            logger,
            console,
        )
    else:
        # Display markdown preview
        display_markdown_preview(console, outline_obj)
