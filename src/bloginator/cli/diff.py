"""CLI command for viewing draft version differences."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from bloginator.generation.version_manager import VersionManager
from bloginator.models.version import DraftVersion, VersionHistory


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.argument("draft_id", type=str)
@click.option(
    "--versions-dir",
    type=click.Path(path_type=Path),
    default=Path("output/versions"),
    help="Directory containing version histories",
)
@click.option(
    "--version1",
    "-v1",
    type=int,
    help="First version to compare (default: current - 1)",
)
@click.option(
    "--version2",
    "-v2",
    type=int,
    help="Second version to compare (default: current)",
)
@click.option(
    "--list-versions",
    "-l",
    is_flag=True,
    help="List all available versions instead of showing diff",
)
@click.option(
    "--show-content",
    is_flag=True,
    help="Show full version content instead of diff",
)
@click.option(
    "--context-lines",
    "-c",
    type=int,
    default=3,
    help="Number of context lines in diff (default: 3)",
)
def diff(
    draft_id: str,
    versions_dir: Path,
    version1: int | None,
    version2: int | None,
    list_versions: bool,
    show_content: bool,
    context_lines: int,
) -> None:
    """View version history and differences for a draft.

    This command helps track how a draft evolved over time by:
    - Listing all versions with timestamps and descriptions
    - Computing diffs between any two versions
    - Showing statistics about changes

    Examples:
        # List all versions
        bloginator diff my-draft --list-versions

        # Show diff between current and previous version
        bloginator diff my-draft

        # Compare specific versions
        bloginator diff my-draft -v1 1 -v2 3

        # Show full content of version 2
        bloginator diff my-draft -v2 2 --show-content
    """
    console.print("\n[bold cyan]Draft Version History[/bold cyan]\n")

    try:
        # Load version history
        version_manager = VersionManager(storage_dir=versions_dir)
        history = version_manager.load_history(draft_id)

        if history is None:
            console.print(f"[bold red]Error:[/bold red] No version history found for '{draft_id}'")
            console.print(f"[dim]Searched in: {versions_dir}[/dim]")
            raise click.Abort()

        # List versions if requested
        if list_versions:
            _display_version_list(version_manager, history)
            return

        # Show content if requested
        if show_content:
            v_num = version2 or history.current_version
            version = history.get_version(v_num)

            if not version:
                console.print(f"[bold red]Error:[/bold red] Version {v_num} not found")
                raise click.Abort()

            _display_version_content(version)
            return

        # Determine versions to compare
        if version1 is None and version2 is None:
            # Default: compare current with previous
            version2 = history.current_version
            version1 = version2 - 1 if version2 > 1 else 1
        elif version1 is None:
            # version2 is not None here
            assert version2 is not None
            version1 = version2 - 1 if version2 > 1 else 1
        elif version2 is None:
            version2 = history.current_version

        # Validate versions (both are now guaranteed to be int)
        assert version1 is not None and version2 is not None
        v1 = history.get_version(version1)
        v2 = history.get_version(version2)

        if not v1:
            console.print(f"[bold red]Error:[/bold red] Version {version1} not found")
            raise click.Abort()

        if not v2:
            console.print(f"[bold red]Error:[/bold red] Version {version2} not found")
            raise click.Abort()

        # Display diff
        _display_diff(version_manager, v1, v2, context_lines)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.exception("Diff operation failed")
        raise click.Abort()


def _display_version_list(
    version_manager: VersionManager,
    history: VersionHistory,
) -> None:
    """Display list of all versions.

    Args:
        version_manager: Version manager instance
        history: Version history
    """
    versions = version_manager.list_versions(history)

    table = Table(title=f"Versions for '{history.draft_id}'")

    table.add_column("Version", style="cyan", justify="center")
    table.add_column("Timestamp", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Feedback", style="dim")
    table.add_column("Words", style="magenta", justify="right")
    table.add_column("Voice", style="green", justify="right")

    for v in versions:
        is_current = v["version"] == history.current_version
        version_str = f"[bold]{v['version']}[/bold]" if is_current else str(v["version"])
        if is_current:
            version_str += " ⬅ current"

        table.add_row(
            version_str,
            v["timestamp"][:19],  # Trim microseconds
            v["description"] or "—",
            (v["feedback"][:40] + "...") if len(v["feedback"]) > 40 else (v["feedback"] or "—"),
            str(v["word_count"]),
            f"{v['voice_score']:.2f}" if v["voice_score"] > 0 else "—",
        )

    console.print(table)
    console.print(f"\n[dim]Total versions: {len(versions)}[/dim]")


def _display_diff(
    version_manager: VersionManager,
    v1: DraftVersion,
    v2: DraftVersion,
    context_lines: int,
) -> None:
    """Display diff between two versions.

    Args:
        version_manager: Version manager instance
        v1: First version
        v2: Second version
        context_lines: Number of context lines
    """
    # Display version info
    console.print(f"[bold]Comparing versions {v1.version_number} → {v2.version_number}[/bold]\n")

    # Display metadata
    info_table = Table(show_header=False, box=None)
    info_table.add_column("", style="dim")
    info_table.add_column("", style="cyan")
    info_table.add_column("", style="dim")
    info_table.add_column("", style="green")

    info_table.add_row(
        f"v{v1.version_number}:",
        v1.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        f"v{v2.version_number}:",
        v2.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
    )
    console.print(info_table)

    if v2.refinement_feedback:
        console.print(f"\n[bold]Feedback:[/bold] {v2.refinement_feedback}")

    # Compute and display diff stats
    stats = version_manager.compute_diff_stats(v1, v2)

    stats_table = Table(title="Change Statistics", show_header=False)
    stats_table.add_column("", style="cyan")
    stats_table.add_column("", style="yellow", justify="right")

    stats_table.add_row("Lines added", f"+{stats['additions']}")
    stats_table.add_row("Lines removed", f"-{stats['deletions']}")
    stats_table.add_row("Total changes", str(stats["changes"]))

    console.print()
    console.print(stats_table)

    # Display unified diff
    console.print("\n[bold]Differences:[/bold]\n")

    diff_text = version_manager.compute_diff(v1, v2, context_lines=context_lines)

    if not diff_text:
        console.print("[dim]No differences found[/dim]")
    else:
        # Use syntax highlighting for diff
        syntax = Syntax(
            diff_text,
            "diff",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
        console.print(syntax)


def _display_version_content(version: DraftVersion) -> None:
    """Display full content of a version.

    Args:
        version: The version to display
    """
    console.print(f"[bold]Version {version.version_number}[/bold]")
    console.print(f"[dim]Timestamp: {version.timestamp.isoformat()}[/dim]")
    console.print(f"[dim]Description: {version.change_description}[/dim]\n")

    # Display as markdown
    markdown_content = version.draft.to_markdown()

    syntax = Syntax(
        markdown_content,
        "markdown",
        theme="monokai",
        line_numbers=False,
        word_wrap=True,
    )

    console.print(Panel(syntax, title=version.draft.title, border_style="cyan"))

    # Display stats
    stats_table = Table(show_header=False, box=None)
    stats_table.add_column("", style="dim")
    stats_table.add_column("", style="cyan")

    stats_table.add_row("Word count", str(version.draft.total_words))
    stats_table.add_row("Sections", str(len(version.draft.sections)))
    stats_table.add_row("Citations", str(version.draft.total_citations))
    if version.draft.voice_score > 0:
        stats_table.add_row("Voice score", f"{version.draft.voice_score:.2f}")

    console.print()
    console.print(stats_table)
