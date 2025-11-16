"""Main CLI entry point for Bloginator."""

import click

from bloginator import __version__


@click.group()
@click.version_option(version=__version__, prog_name="bloginator")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Bloginator: Authentic content generation from your own writing corpus.

    Bloginator helps you create high-quality documents by leveraging your
    historical writing to maintain your authentic voice.
    """
    ctx.ensure_object(dict)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"Bloginator version {__version__}")
    click.echo("Copyright (c) 2025 Matt Bordenet")


if __name__ == "__main__":
    cli()
