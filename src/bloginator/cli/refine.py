"""CLI command for refining drafts with natural language feedback."""

import json
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.generation.llm_client import create_llm_client
from bloginator.generation.refinement_engine import RefinementEngine
from bloginator.generation.safety_validator import SafetyValidator
from bloginator.generation.version_manager import VersionManager
from bloginator.generation.voice_scorer import VoiceScorer
from bloginator.models.draft import Draft
from bloginator.search import Searcher


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--index",
    "-i",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to ChromaDB index directory",
)
@click.option(
    "--draft",
    "-d",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to draft JSON file to refine",
)
@click.option(
    "--feedback",
    "-f",
    required=True,
    type=str,
    help="Natural language feedback for refinement (e.g., 'Make introduction more engaging')",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for refined draft (default: overwrite input)",
)
@click.option(
    "--versions-dir",
    type=click.Path(path_type=Path),
    default=Path("output/versions"),
    help="Directory for storing version history",
)
@click.option(
    "--llm-model",
    default=None,
    help="LLM model to use for refinement (default: from BLOGINATOR_LLM_MODEL env var, falls back to ministral-3:14b)",
)
@click.option(
    "--validate-safety/--no-validate-safety",
    default=True,
    help="Validate refined draft against blocklist",
)
@click.option(
    "--score-voice/--no-score-voice",
    default=True,
    help="Score voice similarity of refined draft",
)
@click.option(
    "--blocklist",
    type=click.Path(exists=True, path_type=Path),
    help="Path to blocklist JSON file",
)
@click.option(
    "--show-diff/--no-show-diff",
    default=True,
    help="Show diff between original and refined versions",
)
def refine(
    index: Path,
    draft: Path,
    feedback: str,
    output: Path | None,
    versions_dir: Path,
    llm_model: str,
    validate_safety: bool,
    score_voice: bool,
    blocklist: Path | None,
    show_diff: bool,
) -> None:
    r"""Refine a draft document based on natural language feedback.

    This command iteratively improves drafts by:
    - Parsing natural language feedback to identify changes
    - Regenerating targeted sections while preserving structure
    - Optionally validating safety and scoring voice
    - Tracking version history for rollback

    Examples:
        # Make introduction more engaging
        bloginator refine -i output/index -d draft.json \\
            -f "Make the introduction more compelling and hook the reader"

        # Add more detail to specific section
        bloginator refine -i output/index -d draft.json \\
            -f "Add more technical depth to the Testing section"

        # Change overall tone
        bloginator refine -i output/index -d draft.json \\
            -f "Make the entire document more optimistic and encouraging"
    """
    console.print("\n[bold cyan]Draft Refinement[/bold cyan]\n")

    try:
        # Load draft
        console.print(f"[dim]Loading draft: {draft}[/dim]")
        with draft.open() as f:
            draft_data = json.load(f)

        current_draft = Draft(**draft_data)

        # Determine draft ID for version tracking
        draft_id = draft.stem

        # Initialize components
        console.print("[dim]Initializing searcher and LLM...[/dim]")

        searcher = Searcher(index_dir=index)
        llm_client = create_llm_client(model=llm_model)

        voice_scorer = VoiceScorer(searcher=searcher) if score_voice else None

        safety_validator = None
        if validate_safety and blocklist:
            safety_validator = SafetyValidator(
                blocklist_file=blocklist,
                auto_reject=True,
            )

        # Create refinement engine
        engine = RefinementEngine(
            llm_client=llm_client,
            searcher=searcher,
            voice_scorer=voice_scorer,
            safety_validator=safety_validator,
        )

        # Initialize version manager
        version_manager = VersionManager(storage_dir=versions_dir)

        # Load or create version history
        history = version_manager.load_history(draft_id)
        if history is None:
            console.print("[dim]Creating new version history...[/dim]")
            history = version_manager.create_history(draft_id, current_draft)
        else:
            console.print(f"[dim]Loaded version history: {len(history.versions)} versions[/dim]")

        # Parse feedback
        console.print(f"\n[bold]Analyzing feedback:[/bold] {feedback}\n")
        parsed = engine.parse_feedback(current_draft, feedback)

        console.print(f"[dim]Action: {parsed['action']}[/dim]")
        console.print(
            f"[dim]Target sections: {', '.join(parsed['target_sections']) if parsed['target_sections'] else 'all'}[/dim]"
        )
        console.print(f"[dim]Instructions: {parsed['instructions']}[/dim]\n")

        # Refine the draft
        console.print("[bold]Refining draft...[/bold]")

        refined_draft = engine.refine_draft(
            draft=current_draft,
            feedback=feedback,
            validate_safety=validate_safety,
            score_voice=score_voice,
        )

        # Add new version to history
        version_manager.add_version(
            history=history,
            draft=refined_draft,
            change_description=f"Refinement: {parsed['action']}",
            refinement_feedback=feedback,
        )

        # Display results
        _display_refinement_results(
            original=current_draft,
            refined=refined_draft,
            score_voice=score_voice,
        )

        # Show diff if requested
        if show_diff:
            console.print("\n[bold]Changes:[/bold]\n")
            v1 = history.get_version(history.current_version - 1)
            v2 = history.get_version(history.current_version)
            if v1 and v2:
                diff = version_manager.compute_diff(v1, v2, context_lines=2)
                console.print(diff)

        # Save refined draft
        output_path = output or draft
        console.print(f"\n[dim]Saving refined draft to: {output_path}[/dim]")

        with output_path.open("w") as f:
            json.dump(
                refined_draft.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )

        console.print(
            f"\n[bold green]✓[/bold green] Refinement complete! Version {history.current_version}"
        )
        console.print(f"[dim]Version history: {versions_dir / f'{draft_id}_history.json'}[/dim]")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.exception("Refinement failed")
        raise click.Abort()


def _display_refinement_results(
    original: Draft,
    refined: Draft,
    score_voice: bool,
) -> None:
    """Display refinement results in a table.

    Args:
        original: Original draft
        refined: Refined draft
        score_voice: Whether voice scoring was performed
    """
    table = Table(title="Refinement Results")

    table.add_column("Metric", style="cyan")
    table.add_column("Original", style="yellow")
    table.add_column("Refined", style="green")
    table.add_column("Change", style="magenta")

    # Word count
    original.calculate_stats()
    refined.calculate_stats()

    word_change = refined.total_words - original.total_words
    word_change_str = f"+{word_change}" if word_change >= 0 else str(word_change)

    table.add_row(
        "Word Count",
        str(original.total_words),
        str(refined.total_words),
        word_change_str,
    )

    # Section count
    table.add_row(
        "Sections",
        str(len(original.sections)),
        str(len(refined.sections)),
        "—",
    )

    # Voice score
    if score_voice:
        voice_change = refined.voice_score - original.voice_score
        voice_change_str = f"+{voice_change:.2f}" if voice_change >= 0 else f"{voice_change:.2f}"

        table.add_row(
            "Voice Score",
            f"{original.voice_score:.2f}",
            f"{refined.voice_score:.2f}",
            voice_change_str,
        )

    # Citations
    citation_change = refined.total_citations - original.total_citations
    citation_change_str = f"+{citation_change}" if citation_change >= 0 else str(citation_change)

    table.add_row(
        "Citations",
        str(original.total_citations),
        str(refined.total_citations),
        citation_change_str,
    )

    console.print(table)

    # Safety warnings
    if refined.has_blocklist_violations:
        console.print("\n[bold yellow]⚠[/bold yellow] Refined draft contains blocklist violations")
