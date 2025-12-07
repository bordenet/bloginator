"""CLI command for generating drafts."""

import logging
import re
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bloginator.cli._draft_display import display_results
from bloginator.cli._draft_initialization import initialize_llm, initialize_searcher, load_outline
from bloginator.cli._draft_output import (
    generate_draft_with_progress,
    save_draft_output,
    save_to_history,
)
from bloginator.cli._draft_validators import score_voice as score_draft_voice
from bloginator.cli._draft_validators import (
    validate_safety_post_generation,
    validate_safety_pre_generation,
)
from bloginator.generation import DraftGenerator
from bloginator.generation.llm_base import LLMResponse
from bloginator.models.draft import Draft, DraftSection


def _replace_batch_placeholders(draft: Draft, responses: dict[int, LLMResponse]) -> None:
    """Replace placeholder content in draft sections with actual LLM responses.

    Args:
        draft: Draft object with placeholder content
        responses: Dictionary mapping request_id to LLMResponse
    """
    placeholder_pattern = re.compile(r"__BATCH_PLACEHOLDER_(\d+)__")

    def replace_in_section(section: DraftSection) -> None:
        """Recursively replace placeholders in section and subsections."""
        match = placeholder_pattern.match(section.content)
        if match:
            request_id = int(match.group(1))
            if request_id in responses:
                section.content = responses[request_id].content

        for subsection in section.subsections:
            replace_in_section(subsection)

    for section in draft.sections:
        replace_in_section(section)


@click.command()
@click.option(
    "--index",
    "index_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to index directory",
)
@click.option(
    "--outline",
    "outline_file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to outline JSON file",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file for draft (markdown or JSON)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="Output format (default: markdown)",
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
    "--sources-per-section",
    type=int,
    default=5,
    help="Number of sources to retrieve per section (default: 5)",
)
@click.option(
    "--max-section-words",
    type=int,
    default=300,
    help="Target words per section (default: 300)",
)
@click.option(
    "--validate-safety",
    is_flag=True,
    help="Validate against blocklist (blocks generation if violations found)",
)
@click.option(
    "--score-voice/--no-score-voice",
    default=True,
    help="Calculate voice similarity score (default: enabled)",
)
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory for blocklist (default: .bloginator)",
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
@click.option(
    "--citations",
    is_flag=True,
    help="Include source citations in generated content",
)
@click.option(
    "--similarity",
    type=float,
    default=0.75,
    help="Voice similarity threshold 0.0-1.0 (default: 0.75)",
)
@click.option(
    "--batch",
    is_flag=True,
    envvar="BLOGINATOR_BATCH_MODE",
    help="Batch mode: generate all LLM requests upfront, then wait for all responses",
)
@click.option(
    "--batch-timeout",
    type=int,
    default=1800,
    envvar="BLOGINATOR_BATCH_TIMEOUT",
    help="Batch mode timeout in seconds (default: 1800 = 30 minutes)",
)
def draft(
    index_dir: Path,
    outline_file: Path,
    output_file: Path,
    output_format: str,
    temperature: float,
    model: str,
    sources_per_section: int,
    max_section_words: int,
    validate_safety: bool,
    score_voice: bool,
    config_dir: Path,
    log_file: Path | None,
    verbose: bool,
    citations: bool,
    similarity: float,
    batch: bool,
    batch_timeout: int,
) -> None:
    r"""Generate document draft from outline.

    Uses RAG to synthesize content for each section based on corpus sources.
    Optionally validates against blocklist and scores voice similarity.

    Examples:
      Generate draft:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md

      With safety validation:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md \\
          --validate-safety

      With voice scoring:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md \\
          --score-voice

      Save as JSON:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.json \\
          --format json
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
        logger.info(f"Starting draft generation from outline: {outline_file}")
    else:
        logging.basicConfig(level=logging.WARNING)
        logger = logging.getLogger(__name__)

    console = Console()

    # Load outline
    outline_obj = load_outline(outline_file, logger, console)
    console.print(f"[bold cyan]Generating draft: {outline_obj.title}[/bold cyan]")
    console.print()

    # Initialize components
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load searcher
        searcher = initialize_searcher(index_dir, progress, logger, console)

        # Initialize LLM client (with batch_mode if requested)
        llm_client = initialize_llm(
            progress, verbose, logger, console, batch_mode=batch, batch_timeout=batch_timeout
        )

        # Pre-validate inputs if safety validation enabled
        if validate_safety:
            validate_safety_pre_generation(outline_obj, config_dir, progress, console)

        # Initialize generator
        generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
            sources_per_section=sources_per_section,
        )

        # Generate draft with progress tracking
        draft_obj = generate_draft_with_progress(
            generator,
            outline_obj,
            temperature,
            max_section_words,
            progress,
            logger,
            console,
        )

        # In batch mode, collect responses and replace placeholders
        if batch:
            from bloginator.generation._llm_assistant_client import AssistantLLMClient

            if isinstance(llm_client, AssistantLLMClient):
                task = progress.add_task("Waiting for batch responses...", total=None)
                responses = llm_client.collect_batch_responses()
                progress.update(task, completed=True)

                # Replace placeholder content with actual responses
                _replace_batch_placeholders(draft_obj, responses)
                logger.info(f"Replaced {len(responses)} batch placeholders with responses")

        # Validate safety if requested
        if validate_safety:
            validate_safety_post_generation(draft_obj, config_dir, progress, console)

        # Score voice if requested
        if score_voice:
            score_draft_voice(draft_obj, searcher, progress, console)

    # Save output
    save_draft_output(draft_obj, output_file, output_format, logger, console)

    # Save to history
    save_to_history(
        draft_obj,
        outline_obj,
        outline_file,
        output_file,
        output_format,
        temperature,
        sources_per_section,
        max_section_words,
        validate_safety,
        score_voice,
        logger,
    )

    # Display results and recommendations
    display_results(draft_obj, searcher, score_voice, validate_safety, console)
