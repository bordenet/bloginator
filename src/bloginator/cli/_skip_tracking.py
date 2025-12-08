"""Skip tracking functionality for CLI commands.

This module handles tracking and reporting of skipped files during
extraction and indexing operations.
"""

from enum import Enum

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class SkipCategory(str, Enum):
    """Categories of skipped files (not errors, but useful to report)."""

    ALREADY_EXTRACTED = "already_extracted"
    TEMP_FILE = "temp_file"
    IGNORE_PATTERN = "ignore_pattern"
    UNSUPPORTED_EXTENSION = "unsupported_extension"
    EMPTY_CONTENT = "empty_content"
    URL_SOURCE = "url_source"
    PATH_NOT_FOUND = "path_not_found"
    CLOUD_ONLY = "cloud_only"  # OneDrive/iCloud placeholder not downloaded


def print_skip_summary(
    skipped: dict[SkipCategory, list[str]],
    total_skipped: int,
    console: Console,
    max_display_lines: int = 32,
    show_file_path: str | None = None,
) -> None:
    """Print a summary of skipped files with scrollable-height constraint.

    Args:
        skipped: Dictionary mapping SkipCategory to list of skipped items
        total_skipped: Total count of skipped items
        console: Rich console for output
        max_display_lines: Maximum lines to display (default 32)
        show_file_path: If provided, show path to full report file
    """
    if total_skipped == 0:
        return

    console.print()

    # Build summary table
    table = Table(
        title=f"{total_skipped} File(s) Skipped",
        show_header=True,
        expand=False,
    )
    table.add_column("Reason", style="cyan", no_wrap=True)
    table.add_column("Count", style="yellow", justify="right")
    table.add_column("Examples", style="dim")

    for category, skip_list in sorted(skipped.items(), key=lambda x: len(x[1]), reverse=True):
        examples = skip_list[:3]
        example_str = ", ".join(examples)
        if len(skip_list) > 3:
            example_str += f" (+{len(skip_list) - 3} more)"

        table.add_row(
            category.value.replace("_", " ").title(),
            str(len(skip_list)),
            example_str[:60] + "..." if len(example_str) > 60 else example_str,
        )

    # Build detailed list (constrained to max_display_lines)
    detail_lines: list[Text] = []
    lines_used = 0
    truncated = False

    for category, skip_list in sorted(skipped.items(), key=lambda x: len(x[1]), reverse=True):
        if lines_used >= max_display_lines:
            truncated = True
            break

        # Category header
        header = Text(f"\n{category.value.replace('_', ' ').title()}:", style="bold cyan")
        detail_lines.append(header)
        lines_used += 2  # header + blank line before

        for item in skip_list:
            if lines_used >= max_display_lines:
                truncated = True
                break
            detail_lines.append(Text(f"  • {item}", style="dim"))
            lines_used += 1

    # Create scrollable panel content
    content_group = Group(table, *detail_lines)

    if truncated:
        content_group = Group(
            table,
            *detail_lines,
            Text(
                f"\n... (truncated, see full report for all {total_skipped} items)",
                style="italic yellow",
            ),
        )

    if show_file_path:
        content_group = Group(
            content_group,
            Text(f"\nFull report: {show_file_path}", style="dim italic"),
        )

    console.print(Panel(content_group, title="[bold cyan]Skipped Files[/bold cyan]", expand=False))
    console.print()
