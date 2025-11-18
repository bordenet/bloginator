"""CLI commands for template management.

This module provides commands for managing custom prompt templates:
- List available templates (built-in and user-created)
- Show template details and preview
- Create new templates
- Delete user templates
- Test template rendering
"""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.models.template import TemplateType
from bloginator.services.template_manager import TemplateManager


@click.group()
def template() -> None:
    """Manage custom prompt templates.

    Templates allow you to customize the style and format of generated content.
    Built-in templates provide common styles (technical, blog, executive, tutorial).
    Create your own templates using Jinja2 syntax.

    Examples:
        bloginator template list
        bloginator template show builtin-blog
        bloginator template create --name "My Style" --type outline
    """
    pass


@template.command()
@click.option(
    "--type",
    "template_type",
    type=click.Choice(["outline", "draft", "section"]),
    help="Filter by template type",
)
@click.option(
    "--builtin-only",
    is_flag=True,
    help="Show only built-in templates",
)
def list(template_type: str | None, builtin_only: bool) -> None:
    """List available templates.

    Shows all templates (built-in and user-created) with their metadata.
    Use --type to filter by template type (outline, draft, section).
    Use --builtin-only to show only built-in templates.

    Examples:
        bloginator template list
        bloginator template list --type outline
        bloginator template list --builtin-only
    """
    console = Console()
    manager = TemplateManager()

    # Parse type filter
    type_filter = TemplateType(template_type) if template_type else None

    # Get templates
    templates = manager.list_templates(type=type_filter, include_builtin=True)

    if builtin_only:
        templates = [t for t in templates if t.is_builtin]

    if not templates:
        console.print("[yellow]No templates found[/yellow]")
        return

    # Create table
    table = Table(title="Prompt Templates", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="green")
    table.add_column("Type", style="blue")
    table.add_column("Built-in", style="magenta")
    table.add_column("Variables", style="yellow")
    table.add_column("Tags")

    for t in templates:
        table.add_row(
            t.id[:16] + "..." if len(t.id) > 16 else t.id,
            t.name,
            t.type.value,
            "✓" if t.is_builtin else "",
            ", ".join(t.variables) if t.variables else "",
            ", ".join(t.tags) if t.tags else "",
        )

    console.print(table)
    console.print(f"\n[cyan]Total: {len(templates)} templates[/cyan]")


@template.command()
@click.argument("template_id")
@click.option(
    "--preview",
    is_flag=True,
    help="Show template preview with example variables",
)
def show(template_id: str, preview: bool) -> None:
    """Show template details.

    Display full template information including description, variables,
    and template content. Use --preview to see rendered output with example values.

    Examples:
        bloginator template show builtin-blog
        bloginator template show abc123 --preview
    """
    console = Console()
    manager = TemplateManager()

    template_obj = manager.get_template(template_id)

    if template_obj is None:
        console.print(f"[red]Template not found: {template_id}[/red]")
        return

    # Display metadata
    console.print(f"\n[bold cyan]Template: {template_obj.name}[/bold cyan]")
    console.print(f"ID: {template_obj.id}")
    console.print(f"Type: {template_obj.type.value}")
    console.print(f"Built-in: {'Yes' if template_obj.is_builtin else 'No'}")
    console.print(f"Created: {template_obj.created_date.strftime('%Y-%m-%d')}")

    if template_obj.description:
        console.print(f"Description: {template_obj.description}")

    if template_obj.variables:
        console.print(f"Variables: {', '.join(template_obj.variables)}")

    if template_obj.tags:
        console.print(f"Tags: {', '.join(template_obj.tags)}")

    # Display template
    console.print("\n[bold yellow]Template:[/bold yellow]")
    console.print(template_obj.template)

    # Preview with example values
    if preview:
        console.print("\n[bold green]Preview (with example values):[/bold green]")
        example_vars = {
            "title": "Example Article Title",
            "keywords": "keyword1, keyword2, keyword3",
            "thesis": "This is the main argument or thesis",
            "num_sections": "5",
        }
        try:
            rendered = manager.render_template(template_id, **example_vars)
            console.print(rendered)
        except Exception as e:
            console.print(f"[red]Preview failed: {e}[/red]")


@template.command()
@click.option("--name", required=True, help="Template name")
@click.option(
    "--type",
    "template_type",
    required=True,
    type=click.Choice(["outline", "draft", "section"]),
    help="Template type",
)
@click.option("--description", default="", help="Template description")
@click.option("--tags", help="Comma-separated tags")
@click.option(
    "--file",
    "template_file",
    type=click.Path(exists=True, path_type=Path),
    help="Load template content from file",
)
@click.option(
    "--interactive",
    is_flag=True,
    help="Enter template interactively",
)
def create(
    name: str,
    template_type: str,
    description: str,
    tags: str | None,
    template_file: Path | None,
    interactive: bool,
) -> None:
    """Create a new template.

    Templates use Jinja2 syntax for variable substitution.
    Variables are automatically detected from template content.

    Provide template content via:
    - --file: Load from file
    - --interactive: Enter in editor
    - stdin: Pipe template content

    Examples:
        bloginator template create --name "My Style" --type outline --file template.txt
        bloginator template create --name "Custom" --type draft --interactive
        echo "{{ title }}" | bloginator template create --name "Simple" --type outline
    """
    console = Console()
    manager = TemplateManager()

    # Get template content
    if template_file:
        template_content = template_file.read_text()
    elif interactive:
        console.print("[cyan]Enter template content (Ctrl+D to finish):[/cyan]")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        template_content = "\n".join(lines)
    else:
        # Read from stdin
        import sys

        template_content = sys.stdin.read()

    if not template_content.strip():
        console.print("[red]Error: Template content is empty[/red]")
        return

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Create template
    try:
        template_obj = manager.create_template(
            name=name,
            type=TemplateType(template_type),
            template=template_content,
            description=description,
            tags=tag_list,
        )

        console.print(f"[green]✓ Template created: {template_obj.id}[/green]")
        console.print(f"Name: {template_obj.name}")
        console.print(f"Type: {template_obj.type.value}")
        console.print(f"Variables: {', '.join(template_obj.variables)}")

    except Exception as e:
        console.print(f"[red]Error creating template: {e}[/red]")


@template.command()
@click.argument("template_id")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
def delete(template_id: str, force: bool) -> None:
    """Delete a user template.

    Built-in templates cannot be deleted.

    Examples:
        bloginator template delete abc123
        bloginator template delete abc123 --force
    """
    console = Console()
    manager = TemplateManager()

    # Get template to confirm it exists
    template_obj = manager.get_template(template_id)

    if template_obj is None:
        console.print(f"[red]Template not found: {template_id}[/red]")
        return

    if template_obj.is_builtin:
        console.print("[red]Cannot delete built-in template[/red]")
        return

    # Confirm deletion
    if not force:
        console.print(f"Delete template '{template_obj.name}' ({template_id})? [y/N]: ", end="")
        response = input().strip().lower()
        if response not in ("y", "yes"):
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Delete
    success = manager.delete_template(template_id)

    if success:
        console.print(f"[green]✓ Template deleted: {template_id}[/green]")
    else:
        console.print(f"[red]Failed to delete template: {template_id}[/red]")


@template.command()
@click.argument("template_id")
@click.option("--var", "variables", multiple=True, help="Template variable (key=value)")
def render(template_id: str, variables: tuple[str, ...]) -> None:
    """Test template rendering with variables.

    Render a template with provided variable values to test output.
    Variables are provided as key=value pairs.

    Examples:
        bloginator template render builtin-blog --var title="My Post" --var keywords="test"
        bloginator template render abc123 --var num_sections=5
    """
    console = Console()
    manager = TemplateManager()

    # Parse variables
    var_dict = {}
    for var in variables:
        if "=" not in var:
            console.print(f"[red]Invalid variable format: {var} (expected key=value)[/red]")
            return
        key, value = var.split("=", 1)
        var_dict[key.strip()] = value.strip()

    # Render
    try:
        rendered = manager.render_template(template_id, **var_dict)
        console.print("\n[bold green]Rendered Template:[/bold green]")
        console.print(rendered)
    except ValueError as e:
        console.print(f"[red]Template not found: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Rendering failed: {e}[/red]")
