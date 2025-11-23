"""Main CLI entry point for Bloginator."""

import click

from bloginator import __version__
from bloginator.cli.blocklist import blocklist
from bloginator.cli.diff import diff
from bloginator.cli.draft import draft
from bloginator.cli.extract import extract
from bloginator.cli.history import history
from bloginator.cli.index import index
from bloginator.cli.init import init
from bloginator.cli.metrics import metrics
from bloginator.cli.outline import outline
from bloginator.cli.refine import refine
from bloginator.cli.revert import revert
from bloginator.cli.search import search
from bloginator.cli.serve import serve
from bloginator.cli.template import template


@click.group()
@click.version_option(version=__version__, prog_name="bloginator")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Bloginator command-line interface.

    Use this tool to extract, index, search, outline, draft, refine,
    and review documents based on your existing writing corpus.

    First-time setup:
      bloginator init  # Pre-download models (recommended for first use)

    Workflow:
      1. bloginator extract <source> -o output/extracted
      2. bloginator index output/extracted -o output/index
      3. bloginator search output/index "your query"
      4. bloginator outline --index output/index --keywords "topic,theme"
      5. bloginator draft --outline outline.json -o draft.md
      6. bloginator refine -d draft.md -f "make more engaging"
      7. bloginator diff my-draft --list-versions
      8. bloginator revert my-draft 2 -o draft.md

    Examples:
      First-time setup:
        bloginator init

      Extract and index:
        bloginator extract ~/my-writing -o output/extracted
        bloginator index output/extracted -o output/index

      Search and generate:
        bloginator search output/index "agile transformation"
        bloginator outline --index output/index --keywords "agile,transformation"
        bloginator draft --index output/index --outline outline.json -o draft.md

      Refine and iterate:
        bloginator refine -i output/index -d draft.json -f "more optimistic tone"
        bloginator diff my-draft -v1 1 -v2 2
        bloginator revert my-draft 1 -o draft.json

      Web UI:
        bloginator serve --port 8000

    For more help on a command:
      bloginator <command> --help
    """
    ctx.ensure_object(dict)


# Register commands
cli.add_command(blocklist)
cli.add_command(diff)
cli.add_command(draft)
cli.add_command(extract)
cli.add_command(history)
cli.add_command(index)
cli.add_command(init)
cli.add_command(metrics)
cli.add_command(outline)
cli.add_command(refine)
cli.add_command(revert)
cli.add_command(search)
cli.add_command(serve)
cli.add_command(template)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"Bloginator version {__version__}")
    click.echo("Copyright (c) 2025 Matt Bordenet")


if __name__ == "__main__":
    cli()
