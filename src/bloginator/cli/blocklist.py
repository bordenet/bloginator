"""CLI command for managing the blocklist."""

import uuid
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.models.blocklist import (
    BlocklistCategory,
    BlocklistEntry,
    BlocklistPatternType,
)
from bloginator.safety import BlocklistManager


@click.group()
def blocklist() -> None:
    """Manage proprietary term blocklist.

    The blocklist prevents sensitive terms (company names, project codenames,
    proprietary methodologies, etc.) from appearing in generated content.

    Examples:
      Add a company name to blocklist:
        bloginator blocklist add "Acme Corp" --category company_name --notes "Former employer"

      List all blocklist entries:
        bloginator blocklist list

      Validate a file against the blocklist:
        bloginator blocklist validate draft.md

      Remove an entry:
        bloginator blocklist remove <entry-id>
    """
    pass


@blocklist.command()
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory (default: .bloginator)",
)
@click.argument("pattern")
@click.option(
    "--type",
    "pattern_type",
    type=click.Choice(["exact", "case_insensitive", "regex"]),
    default="exact",
    help="Pattern matching type (default: exact)",
)
@click.option(
    "--category",
    type=click.Choice(
        ["company_name", "product_name", "project", "methodology", "person", "other"]
    ),
    default="other",
    help="Category for organization (default: other)",
)
@click.option("--notes", default="", help="Explanation of why this is blocked")
def add(
    config_dir: Path, pattern: str, pattern_type: str, category: str, notes: str
) -> None:
    """Add term or pattern to blocklist.

    PATTERN: The term or regex pattern to block

    Examples:
      Add exact match:
        bloginator blocklist add "Acme Corp" --category company_name

      Add case-insensitive:
        bloginator blocklist add "acme" --type case_insensitive --category company_name

      Add regex pattern:
        bloginator blocklist add "Project \\w+" --type regex --category project
    """
    console = Console()

    # Ensure config directory exists
    config_dir.mkdir(parents=True, exist_ok=True)

    # Load manager
    manager = BlocklistManager(config_dir / "blocklist.json")

    # Create entry
    entry = BlocklistEntry(
        id=str(uuid.uuid4()),
        pattern=pattern,
        pattern_type=BlocklistPatternType(pattern_type),
        category=BlocklistCategory(category),
        notes=notes,
    )

    # Add and save
    manager.add_entry(entry)

    console.print(f"[green]✓[/green] Added '{pattern}' to blocklist")
    console.print(f"  ID: {entry.id[:8]}...")
    console.print(f"  Type: {pattern_type}")
    console.print(f"  Category: {category}")
    if notes:
        console.print(f"  Notes: {notes}")


@blocklist.command()
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory (default: .bloginator)",
)
@click.option(
    "--category",
    help="Filter by category",
)
def list(config_dir: Path, category: str | None) -> None:
    """List all blocklist entries.

    Examples:
      List all entries:
        bloginator blocklist list

      List only company names:
        bloginator blocklist list --category company_name
    """
    manager = BlocklistManager(config_dir / "blocklist.json")

    console = Console()

    # Filter by category if specified
    if category:
        entries = manager.get_entries_by_category(category)
    else:
        entries = manager.entries

    if not entries:
        if category:
            console.print(
                f"[yellow]No blocklist entries found for category '{category}'[/yellow]"
            )
        else:
            console.print("[yellow]No blocklist entries found[/yellow]")
        console.print(
            "[dim]Use 'bloginator blocklist add' to create entries[/dim]"
        )
        return

    # Create table
    title = f"Blocklist Entries ({len(entries)} total)"
    if category:
        title = f"Blocklist Entries - Category: {category} ({len(entries)} total)"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim", width=10)
    table.add_column("Pattern", overflow="fold", max_width=30)
    table.add_column("Type", width=15)
    table.add_column("Category", width=15)
    table.add_column("Notes", overflow="fold", max_width=30)

    for entry in entries:
        # Color code by category
        category_colors = {
            "company_name": "red",
            "product_name": "yellow",
            "project": "magenta",
            "methodology": "blue",
            "person": "cyan",
            "other": "white",
        }
        color = category_colors.get(entry.category, "white")

        table.add_row(
            entry.id[:8] + "...",  # Short ID
            f"[{color}]{entry.pattern}[/{color}]",
            entry.pattern_type,
            entry.category,
            entry.notes or "[dim]—[/dim]",
        )

    console.print(table)


@blocklist.command()
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory (default: .bloginator)",
)
@click.argument("entry_id")
def remove(config_dir: Path, entry_id: str) -> None:
    """Remove entry from blocklist by ID.

    ENTRY_ID: ID of the entry to remove (first 8 characters are sufficient)

    Examples:
      Remove an entry:
        bloginator blocklist remove abc12345
    """
    console = Console()
    manager = BlocklistManager(config_dir / "blocklist.json")

    # Find entry by prefix match
    matching_entries = [e for e in manager.entries if e.id.startswith(entry_id)]

    if not matching_entries:
        console.print(f"[red]✗[/red] No entry found with ID starting with '{entry_id}'")
        console.print("[dim]Use 'bloginator blocklist list' to see all entries[/dim]")
        return

    if len(matching_entries) > 1:
        console.print(
            f"[yellow]![/yellow] Multiple entries match '{entry_id}'. Please be more specific:"
        )
        for entry in matching_entries:
            console.print(f"  {entry.id[:16]}... - {entry.pattern}")
        return

    # Remove the entry
    entry = matching_entries[0]
    manager.remove_entry(entry.id)

    console.print(f"[green]✓[/green] Removed entry: {entry.pattern}")
    console.print(f"  ID: {entry.id[:8]}...")


@blocklist.command()
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory (default: .bloginator)",
)
@click.argument("text_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed violation information",
)
def validate(config_dir: Path, text_file: Path, verbose: bool) -> None:
    """Validate text file against blocklist.

    TEXT_FILE: Path to text file to validate

    Examples:
      Validate a file:
        bloginator blocklist validate draft.md

      Validate with detailed output:
        bloginator blocklist validate draft.md --verbose
    """
    console = Console()
    manager = BlocklistManager(config_dir / "blocklist.json")

    # Read text file
    try:
        text = text_file.read_text()
    except Exception as e:
        console.print(f"[red]✗[/red] Error reading file: {e}")
        return

    # Validate
    result = manager.validate_text(text)

    if result["is_valid"]:
        console.print(
            f"[green]✓[/green] No blocklist violations found in {text_file.name}"
        )
        return

    # Report violations
    console.print(
        f"[red]✗[/red] Found {len(result['violations'])} blocklist violation(s) in {text_file.name}"
    )
    console.print()

    if verbose:
        # Detailed table view
        table = Table(title="Violations", show_header=True, header_style="bold red")
        table.add_column("Pattern")
        table.add_column("Matches")
        table.add_column("Category")
        table.add_column("Notes")

        for violation in result["violations"]:
            matches_str = ", ".join(violation["matches"])
            table.add_row(
                violation["pattern"],
                matches_str,
                violation["category"],
                violation["notes"] or "—",
            )

        console.print(table)
    else:
        # Compact list view
        for i, violation in enumerate(result["violations"], 1):
            matches_str = ", ".join(f"'{m}'" for m in violation["matches"])
            console.print(f"  {i}. Pattern '{violation['pattern']}' matched: {matches_str}")
            if violation["notes"]:
                console.print(f"     [dim]{violation['notes']}[/dim]")

    console.print()
    console.print(
        "[yellow]Recommendation:[/yellow] Remove or replace these terms before using this content."
    )
