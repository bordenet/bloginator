"""Safety and voice validation for draft generation."""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from bloginator.generation import SafetyValidator, VoiceScorer
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.search import CorpusSearcher


def validate_safety_pre_generation(
    outline: Outline, config_dir: Path, progress: Progress, console: Console
) -> None:
    """Pre-validate inputs against blocklist.

    Args:
        outline: Outline to validate
        config_dir: Configuration directory
        progress: Rich progress bar
        console: Rich console for output

    Raises:
        SystemExit: If validation fails
    """
    import sys

    task = progress.add_task("Pre-validating inputs...", total=None)
    validator = SafetyValidator(config_dir / "blocklist.json")

    validation_result = validator.validate_before_generation(
        title=outline.title,
        keywords=outline.keywords,
        thesis=outline.thesis,
    )

    if not validation_result["is_valid"]:
        progress.update(task, completed=True)
        console.print()
        console.print(
            f"[red]✗[/red] Input validation failed: {len(validation_result['violations'])} violation(s) found"
        )
        for v in validation_result["violations"]:
            console.print(f"  • Pattern '{v['pattern']}' matched: {', '.join(v['matches'])}")

        console.print()
        console.print("[dim]Fix these violations before generating content[/dim]")
        sys.exit(1)

    progress.update(task, completed=True)


def validate_safety_post_generation(
    draft: Draft, config_dir: Path, progress: Progress, console: Console
) -> None:
    """Validate generated draft against blocklist.

    Args:
        draft: Generated draft object
        config_dir: Configuration directory
        progress: Rich progress bar
        console: Rich console for output

    Raises:
        SystemExit: If validation fails
    """
    import sys

    task = progress.add_task("Validating against blocklist...", total=None)
    validator = SafetyValidator(config_dir / "blocklist.json", auto_reject=False)
    try:
        validator.validate_draft(draft)
    except Exception as e:
        console.print(f"[red]✗[/red] Safety validation failed: {e}")
        sys.exit(1)
    progress.update(task, completed=True)


def score_voice(
    draft: Draft, searcher: CorpusSearcher, progress: Progress, console: Console
) -> None:
    """Calculate voice similarity score for draft.

    Args:
        draft: Generated draft object
        searcher: CorpusSearcher instance
        progress: Rich progress bar
        console: Rich console for output
    """
    task = progress.add_task("Calculating voice similarity...", total=None)
    scorer = VoiceScorer(searcher=searcher)
    try:
        scorer.score_draft(draft)
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Voice scoring failed: {e}")
    progress.update(task, completed=True)
