"""CLI command for reverting drafts to previous versions."""

import json
import logging
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from bloginator.generation.version_manager import VersionManager


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.argument("draft_id", type=str)
@click.argument("version_number", type=int)
@click.option(
    "--versions-dir",
    type=click.Path(path_type=Path),
    default=Path("output/versions"),
    help="Directory containing version histories",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output path for reverted draft JSON (required)",
    required=True,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt",
)
def revert(
    draft_id: str,
    version_number: int,
    versions_dir: Path,
    output: Path,
    force: bool,
) -> None:
    """Revert a draft to a previous version.

    This command allows you to go back to an earlier version of a draft,
    which is useful for:
    - Undoing unwanted refinements
    - Comparing different refinement strategies
    - Recovering from mistakes

    The revert operation does not delete version history - all versions
    are preserved and you can switch between them at any time.

    Examples:
        # Revert to version 2
        bloginator revert my-draft 2 -o draft.json

        # Revert without confirmation
        bloginator revert my-draft 1 -o draft.json --force

        # View versions before reverting
        bloginator diff my-draft --list-versions
    """
    console.print("\n[bold cyan]Revert Draft Version[/bold cyan]\n")

    try:
        # Load version history
        version_manager = VersionManager(storage_dir=versions_dir)
        history = version_manager.load_history(draft_id)

        if history is None:
            console.print(f"[bold red]Error:[/bold red] No version history found for '{draft_id}'")
            console.print(f"[dim]Searched in: {versions_dir}[/dim]")
            raise click.Abort()

        # Get target version
        target_version = history.get_version(version_number)

        if not target_version:
            console.print(f"[bold red]Error:[/bold red] Version {version_number} not found")
            console.print(f"[dim]Available versions: 1-{len(history.versions)}[/dim]")
            raise click.Abort()

        # Display current and target versions
        current_version = history.get_current()

        _display_revert_info(current_version, target_version)

        # Confirm if not forced
        if not force and not click.confirm(
            f"\nRevert from v{history.current_version} to v{version_number}?",
            default=False,
        ):
            console.print("[yellow]Revert cancelled[/yellow]")
            return

        # Perform revert
        console.print(f"\n[dim]Reverting to version {version_number}...[/dim]")

        success = version_manager.revert(history, version_number)

        if not success:
            console.print("[bold red]Error:[/bold red] Revert failed")
            raise click.Abort()

        # Save reverted draft
        console.print(f"[dim]Saving reverted draft to: {output}[/dim]")

        with output.open("w") as f:
            json.dump(
                target_version.draft.model_dump(mode="json"),
                f,
                indent=2,
                default=str,
            )

        console.print(f"\n[bold green]✓[/bold green] Reverted to version {version_number}")
        console.print(f"[dim]Draft saved to: {output}[/dim]")
        console.print(
            f"[dim]Version history preserved in: {versions_dir / f'{draft_id}_history.json'}[/dim]"
        )

        # Show next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  • View all versions: bloginator diff {draft_id} --list-versions")
        console.print(
            f"  • Compare versions: bloginator diff {draft_id} -v1 {version_number} -v2 {history.current_version}"
        )
        console.print(f"  • Refine this version: bloginator refine -d {output} -f '<feedback>'")

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.exception("Revert operation failed")
        raise click.Abort()


def _display_revert_info(
    current_version: Optional,
    target_version,
) -> None:
    """Display information about the revert operation.

    Args:
        current_version: Current active version
        target_version: Version to revert to
    """
    console.print("[bold]Revert Information[/bold]\n")

    table = Table(show_header=True)

    table.add_column("", style="dim")
    table.add_column("Current Version", style="yellow", justify="center")
    table.add_column("Target Version", style="green", justify="center")

    if current_version:
        table.add_row(
            "Version",
            str(current_version.version_number),
            str(target_version.version_number),
        )

        table.add_row(
            "Timestamp",
            current_version.timestamp.strftime("%Y-%m-%d %H:%M"),
            target_version.timestamp.strftime("%Y-%m-%d %H:%M"),
        )

        table.add_row(
            "Description",
            current_version.change_description or "—",
            target_version.change_description or "—",
        )

        table.add_row(
            "Word Count",
            str(current_version.draft.total_words),
            str(target_version.draft.total_words),
        )

        table.add_row(
            "Sections",
            str(len(current_version.draft.sections)),
            str(len(target_version.draft.sections)),
        )

        if current_version.draft.voice_score > 0 or target_version.draft.voice_score > 0:
            table.add_row(
                "Voice Score",
                (
                    f"{current_version.draft.voice_score:.2f}"
                    if current_version.draft.voice_score > 0
                    else "—"
                ),
                (
                    f"{target_version.draft.voice_score:.2f}"
                    if target_version.draft.voice_score > 0
                    else "—"
                ),
            )

    console.print(table)

    # Show warning if reverting to much older version
    if current_version:
        version_gap = current_version.version_number - target_version.version_number
        if version_gap > 2:
            console.print(
                f"\n[yellow]⚠[/yellow] Reverting {version_gap} versions back. "
                f"All intermediate versions will be preserved."
            )
