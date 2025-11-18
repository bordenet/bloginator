"""CLI commands for generation history management."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.services.history_manager import HistoryManager


@click.group()
def history():
    """Manage generation history."""
    pass


@history.command("list")
@click.option(
    "--type",
    "generation_type",
    type=click.Choice(["outline", "draft"]),
    help="Filter by generation type",
)
@click.option(
    "--classification",
    help="Filter by classification",
)
@click.option(
    "--audience",
    help="Filter by audience",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of entries to show (default: 10)",
)
@click.option(
    "--history-dir",
    type=click.Path(path_type=Path),
    help="History directory (defaults to ~/.bloginator/history/)",
)
def list_history(
    generation_type: str | None,
    classification: str | None,
    audience: str | None,
    limit: int,
    history_dir: Path | None,
):
    """List generation history entries.

    Examples:
      List all recent generations:
        bloginator history list

      List recent outlines:
        bloginator history list --type outline --limit 5

      Filter by classification:
        bloginator history list --classification best-practice

      Filter by audience:
        bloginator history list --audience engineering-leaders
    """
    console = Console()
    manager = HistoryManager(history_dir)

    # Query with filters
    entries = manager.query(
        generation_type=generation_type,
        classification=classification,
        audience=audience,
        limit=limit,
    )

    if not entries:
        console.print("[yellow]No history entries found[/yellow]")
        return

    # Display table
    table = Table(title="Generation History", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Title", style="bold")
    table.add_column("Classification", style="green")
    table.add_column("Audience", style="blue")
    table.add_column("Timestamp", style="dim")

    for entry in entries:
        table.add_row(
            entry.id[:8],  # Short ID
            entry.generation_type,
            entry.title[:50],  # Truncate long titles
            entry.classification,
            entry.audience,
            entry.timestamp.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(entries)} entries[/dim]")


@history.command("show")
@click.argument("entry_id")
@click.option(
    "--history-dir",
    type=click.Path(path_type=Path),
    help="History directory (defaults to ~/.bloginator/history/)",
)
def show_entry(entry_id: str, history_dir: Path | None):
    """Show detailed information for a history entry.

    Examples:
      Show entry details:
        bloginator history show abc12345
    """
    console = Console()
    manager = HistoryManager(history_dir)

    # Load entry
    entry = manager.load_entry(entry_id)
    if not entry:
        console.print(f"[red]✗[/red] Entry not found: {entry_id}")
        return

    # Display details
    console.print()
    console.print(f"[bold cyan]{entry.title}[/bold cyan]")
    console.print(
        f"[dim italic]{entry.classification.replace('-', ' ').title()} • For {entry.audience.replace('-', ' ').title()}[/dim italic]"
    )
    console.print()

    # Details table
    details = Table(show_header=False, box=None, padding=(0, 2))
    details.add_row("ID:", entry.id)
    details.add_row("Type:", entry.generation_type)
    details.add_row("Timestamp:", entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    details.add_row("Output Path:", entry.output_path)
    details.add_row("Output Format:", entry.output_format)
    console.print(details)

    # Input parameters
    if entry.input_params:
        console.print("\n[bold]Input Parameters:[/bold]")
        params = Table(show_header=False, box=None, padding=(0, 2))
        for key, value in entry.input_params.items():
            params.add_row(f"{key}:", str(value))
        console.print(params)

    # Metadata
    if entry.metadata:
        console.print("\n[bold]Metadata:[/bold]")
        meta = Table(show_header=False, box=None, padding=(0, 2))
        for key, value in entry.metadata.items():
            meta.add_row(f"{key}:", str(value))
        console.print(meta)

    console.print()


@history.command("delete")
@click.argument("entry_id")
@click.option(
    "--history-dir",
    type=click.Path(path_type=Path),
    help="History directory (defaults to ~/.bloginator/history/)",
)
@click.confirmation_option(prompt="Are you sure you want to delete this entry?")
def delete_entry(entry_id: str, history_dir: Path | None):
    """Delete a history entry.

    Examples:
      Delete entry:
        bloginator history delete abc12345
    """
    console = Console()
    manager = HistoryManager(history_dir)

    if manager.delete_entry(entry_id):
        console.print(f"[green]✓[/green] Deleted entry: {entry_id}")
    else:
        console.print(f"[red]✗[/red] Entry not found: {entry_id}")


@history.command("clear")
@click.option(
    "--history-dir",
    type=click.Path(path_type=Path),
    help="History directory (defaults to ~/.bloginator/history/)",
)
@click.confirmation_option(prompt="Are you sure you want to clear ALL history?")
def clear_history(history_dir: Path | None):
    """Clear all history entries.

    WARNING: This will delete all generation history.

    Examples:
      Clear all history:
        bloginator history clear
    """
    console = Console()
    manager = HistoryManager(history_dir)

    count = manager.clear_all()
    console.print(f"[green]✓[/green] Cleared {count} history entries")


@history.command("export")
@click.argument("entry_id")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["json", "markdown"]),
    default="json",
    help="Export format (default: json)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    help="Output file path",
)
@click.option(
    "--history-dir",
    type=click.Path(path_type=Path),
    help="History directory (defaults to ~/.bloginator/history/)",
)
def export_entry(
    entry_id: str,
    export_format: str,
    output_file: Path | None,
    history_dir: Path | None,
):
    """Export a history entry.

    Examples:
      Export entry as JSON:
        bloginator history export abc12345 -o entry.json

      Export as markdown:
        bloginator history export abc12345 --format markdown -o entry.md
    """
    console = Console()
    manager = HistoryManager(history_dir)

    # Load entry
    entry = manager.load_entry(entry_id)
    if not entry:
        console.print(f"[red]✗[/red] Entry not found: {entry_id}")
        return

    # Determine output path
    if not output_file:
        ext = "json" if export_format == "json" else "md"
        output_file = Path(f"history_{entry_id[:8]}.{ext}")

    # Export
    try:
        if export_format == "json":
            output_file.write_text(entry.model_dump_json(indent=2))
        else:  # markdown
            # Create markdown representation
            md_lines = [
                f"# {entry.title}",
                "",
                f"**Type:** {entry.generation_type}",
                f"**Classification:** {entry.classification}",
                f"**Audience:** {entry.audience}",
                f"**Timestamp:** {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Input Parameters",
                "",
            ]
            for key, value in entry.input_params.items():
                md_lines.append(f"- **{key}:** {value}")

            md_lines.extend(["", "## Metadata", ""])
            for key, value in entry.metadata.items():
                md_lines.append(f"- **{key}:** {value}")

            md_lines.extend(["", f"**Output:** {entry.output_path}", ""])

            output_file.write_text("\n".join(md_lines))

        console.print(f"[green]✓[/green] Exported to {output_file}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to export: {e}")
