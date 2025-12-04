"""Initialize Bloginator by pre-downloading required models."""

import logging

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from bloginator.search._embedding import _get_embedding_model


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--model",
    default="all-MiniLM-L6-v2",
    help="Embedding model to download (default: all-MiniLM-L6-v2)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def init(model: str, verbose: bool) -> None:
    """Initialize Bloginator by pre-downloading required models.

    This command downloads the embedding model used for semantic search.
    Running this before your first use of bloginator will make subsequent
    commands faster.

    The default model (all-MiniLM-L6-v2) is ~80MB and typically takes
    10-60 seconds to download depending on your internet connection.

    Examples:
        # Download default model
        bloginator init

        # Download with verbose logging
        bloginator init --verbose

        # Download specific model
        bloginator init --model sentence-transformers/all-mpnet-base-v2
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    console.print("\n[bold cyan]Bloginator Initialization[/bold cyan]")
    console.print(f"Downloading embedding model: [yellow]{model}[/yellow]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Downloading model '{model}' (this may take 10-60 seconds)...",
            total=None,
        )

        try:
            # This will download and cache the model
            _get_embedding_model(model)
            progress.update(task, description=f"✓ Model '{model}' downloaded successfully")
        except Exception as e:
            progress.update(task, description=f"✗ Failed to download model '{model}'")
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            console.print(
                "\n[yellow]Troubleshooting:[/yellow]\n"
                "  • Check your internet connection\n"
                "  • Verify the model name is correct\n"
                "  • Try again in a few minutes\n"
            )
            raise click.Abort()

    console.print("\n[bold green]✓ Initialization complete![/bold green]")
    console.print(
        "\nYou can now use bloginator commands without waiting for model downloads.\n"
        "Next steps:\n"
        "  1. Extract documents: [cyan]bloginator extract <source> -o output/extracted[/cyan]\n"
        "  2. Create index: [cyan]bloginator index output/extracted -o output/index[/cyan]\n"
        "  3. Generate outline: [cyan]bloginator outline --index output/index --keywords 'topic'[/cyan]\n"
    )
