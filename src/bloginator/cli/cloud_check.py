"""CLI command for checking cloud file status in corpus sources.

This command scans corpus sources and identifies files that are cloud-only
placeholders (OneDrive/iCloud Files-On-Demand) that need to be downloaded
before extraction can work.
"""

import contextlib
import subprocess
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bloginator.cli.extract_utils import get_supported_extensions
from bloginator.corpus_config import CorpusConfig
from bloginator.utils.cloud_files import (
    CloudFileStatus,
    get_cloud_file_status,
    scan_for_cloud_only_files,
)


@click.command("cloud-check")
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    default="corpus/corpus.yaml",
    help="Path to corpus.yaml configuration file",
)
@click.option(
    "--source",
    type=str,
    help="Check only a specific source by name",
)
@click.option(
    "--open-finder/--no-open-finder",
    default=True,
    help="Open Finder at directories with cloud-only files (default: yes)",
)
def cloud_check(config: Path, source: str | None, open_finder: bool) -> None:
    """Check corpus sources for cloud-only placeholder files.

    Scans all configured corpus sources and identifies files that are
    OneDrive/iCloud placeholders needing download.

    If cloud-only files are found, opens Finder at the affected directories
    so you can right-click and select "Always Keep on This Device".

    Examples:
        bloginator cloud-check
        bloginator cloud-check --config corpus/corpus.yaml
        bloginator cloud-check --no-open-finder
    """
    console = Console()

    # Load corpus config
    try:
        corpus_cfg = CorpusConfig.load_from_file(config)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise click.Abort()

    extensions = get_supported_extensions()

    # Scan each source
    total_cloud_only = 0
    total_local = 0
    results: list[tuple[str, Path, int, int]] = []

    for src in corpus_cfg.sources:
        if not src.enabled:
            continue

        if source and src.name != source:
            continue

        src_path = Path(src.path).expanduser()

        if not src_path.exists():
            console.print(f"[yellow]⚠ Source not found: {src.name}[/yellow]")
            continue

        if src_path.is_file():
            # Single file
            status = get_cloud_file_status(src_path)
            if status == CloudFileStatus.CLOUD_ONLY:
                total_cloud_only += 1
                results.append((src.name, src_path, 0, 1))
            else:
                total_local += 1
                results.append((src.name, src_path, 1, 0))
        else:
            # Directory - scan for cloud-only files
            cloud_files = scan_for_cloud_only_files(src_path, extensions)
            local_count = 0

            # Count local files
            for f in src_path.rglob("*"):
                is_supported = f.is_file() and f.suffix.lower() in extensions
                if is_supported and get_cloud_file_status(f) == CloudFileStatus.LOCAL:
                    local_count += 1

            cloud_count = len(cloud_files)
            total_cloud_only += cloud_count
            total_local += local_count
            results.append((src.name, src_path, local_count, cloud_count))

    # Display results table
    table = Table(title="Cloud File Status by Source")
    table.add_column("Source", style="cyan")
    table.add_column("Local", justify="right", style="green")
    table.add_column("Cloud-Only", justify="right", style="red")
    table.add_column("Status")

    # Track directories with cloud-only files
    cloud_only_dirs: list[Path] = []

    for name, path, local, cloud in results:
        if cloud == 0:
            status = "[green]✓ Ready[/green]"
        elif local == 0:
            status = "[red]✗ All cloud-only[/red]"
            cloud_only_dirs.append(path)
        else:
            status = f"[yellow]⚠ {cloud} need download[/yellow]"
            cloud_only_dirs.append(path)

        table.add_row(name, str(local), str(cloud), status)

    console.print(table)

    # Summary
    console.print()
    console.print(f"[bold]Total:[/bold] {total_local} local, {total_cloud_only} cloud-only")

    if total_cloud_only > 0:
        # Ensure we only list directories (get parent if path is a file)
        normalized_dirs = [p if p.is_dir() else p.parent for p in cloud_only_dirs]
        dirs_to_open = list(dict.fromkeys(normalized_dirs))[:5]  # Dedupe, limit to 5

        # Show clear instructions
        console.print()
        console.print(
            Panel(
                "[bold yellow]📥 ACTION REQUIRED: Download Cloud Files[/bold yellow]\n\n"
                "[white]In Finder, right-click on each folder and select:[/white]\n\n"
                '[bold cyan]   "Always Keep on This Device"[/bold cyan]\n\n'
                "[dim]This will download all files in the folder.[/dim]\n"
                "[dim]Wait for the cloud icons to disappear, then re-run extraction.[/dim]",
                title="☁️  OneDrive Files Need Download",
                border_style="yellow",
            )
        )

        # Show which directories
        console.print()
        console.print("[bold]Directories with cloud-only files:[/bold]")
        for d in dirs_to_open:
            console.print(f"  📁 {d}")

        # Open Finder if requested
        if open_finder and dirs_to_open:
            console.print()
            console.print("[dim]Opening Finder at affected directories...[/dim]")
            for d in dirs_to_open:
                _open_in_finder(d)

    else:
        console.print()
        console.print("[bold green]✅ All files are downloaded and ready![/bold green]")


def _open_in_finder(path: Path) -> None:
    """Open a directory in Finder."""
    with contextlib.suppress(subprocess.TimeoutExpired, subprocess.SubprocessError):
        subprocess.run(
            ["open", str(path)],
            capture_output=True,
            timeout=5.0,
        )
