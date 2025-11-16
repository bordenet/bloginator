"""Main CLI entry point for Bloginator."""

import click

from bloginator import __version__
from bloginator.cli.extract import extract
from bloginator.cli.index import index
from bloginator.cli.search import search


@click.group()
@click.version_option(version=__version__, prog_name="bloginator")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Bloginator: Authentic content generation from your own writing corpus.

    Bloginator helps you create high-quality documents by leveraging your
    historical writing to maintain your authentic voice.

    \b
    Workflow:
      1. bloginator extract <source> -o output/extracted
      2. bloginator index output/extracted -o output/index
      3. bloginator search output/index "your query"
      4. bloginator outline --index output/index --keywords "topic,theme"
      5. bloginator draft outline.json -o draft.md

    Examples:
      Extract documents:
        bloginator extract ~/my-writing -o output/extracted

      Index documents:
        bloginator index output/extracted -o output/index

      Search corpus:
        bloginator search output/index "agile transformation"

    For more help on a command:
      bloginator <command> --help
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(extract)
cli.add_command(index)
cli.add_command(search)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"Bloginator version {__version__}")
    click.echo("Copyright (c) 2025 Matt Bordenet")


if __name__ == "__main__":
    cli()
