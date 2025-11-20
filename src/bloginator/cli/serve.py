"""CLI command to run the web server."""

import click


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to",
)
@click.option(
    "--port",
    "-p",
    default=8000,
    type=int,
    help="Port to bind to",
)
@click.option(
    "--reload/--no-reload",
    default=False,
    help="Enable auto-reload on code changes",
)
def serve(host: str, port: int, reload: bool) -> None:
    """Run the Bloginator web server.

    This starts a uvicorn server hosting the Bloginator web UI.
    Access the UI at http://localhost:8000 (or specified host/port).

    Examples:
        # Run on default host and port
        bloginator serve

        # Run on custom port with auto-reload
        bloginator serve --port 3000 --reload

        # Bind to all interfaces
        bloginator serve --host 0.0.0.0 --port 8080
    """
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn is not installed.")
        click.echo("Install with: pip install bloginator[web]")
        raise click.Abort()

    click.echo(f"Starting Bloginator web server on http://{host}:{port}")
    click.echo("Press CTRL+C to stop")

    if reload:
        click.echo("Auto-reload enabled")

    uvicorn.run(
        "bloginator.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )
