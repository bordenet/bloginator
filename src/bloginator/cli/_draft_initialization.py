"""Component initialization for draft generation."""

import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from bloginator.generation.llm_base import LLMClient
from bloginator.generation.llm_factory import create_llm_from_config
from bloginator.models.outline import Outline
from bloginator.search import CorpusSearcher


def load_outline(outline_file: Path, logger: logging.Logger, console: Console) -> Outline:
    """Load and validate outline from file.

    Args:
        outline_file: Path to outline JSON file
        logger: Logger instance
        console: Rich console for output

    Returns:
        Loaded and validated Outline object

    Raises:
        SystemExit: If outline cannot be loaded
    """
    try:
        logger.info(f"Loading outline from {outline_file}")
        outline_data = json.loads(outline_file.read_text())
        outline_obj = Outline.model_validate(outline_data)
        logger.info(f"Outline loaded: {outline_obj.title}")
        return outline_obj
    except json.JSONDecodeError as e:
        logger.error(f"Failed to load outline: {e}")
        console.print(f"[red]✗[/red] Invalid JSON in outline file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load outline: {e}")
        console.print(f"[red]✗[/red] Failed to load outline: {e}")
        sys.exit(1)


def initialize_searcher(
    index_dir: Path, progress: Progress, logger: logging.Logger, console: Console
) -> CorpusSearcher:
    """Initialize corpus searcher with index.

    Args:
        index_dir: Path to index directory
        progress: Rich progress bar
        logger: Logger instance
        console: Rich console for output

    Returns:
        Initialized CorpusSearcher

    Raises:
        SystemExit: If index cannot be loaded
    """
    task = progress.add_task("Loading corpus index...", total=None)
    try:
        logger.info(f"Loading index from {index_dir}")
        searcher = CorpusSearcher(index_dir=index_dir)
        logger.info("Index loaded successfully")
        progress.update(task, completed=True)
        return searcher
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        console.print(f"[red]✗[/red] Failed to load index: {e}")
        sys.exit(1)


def initialize_llm(
    progress: Progress,
    verbose: bool,
    logger: logging.Logger,
    console: Console,
    batch_mode: bool = False,
    batch_timeout: int = 1800,
) -> LLMClient:
    """Initialize LLM client from configuration.

    Args:
        progress: Rich progress bar
        verbose: Whether to show verbose output
        logger: Logger instance
        console: Rich console for output
        batch_mode: If True, enable batch mode for AssistantLLMClient
        batch_timeout: Timeout in seconds for batch mode (default: 1800 = 30 min)

    Returns:
        Initialized LLM client

    Raises:
        SystemExit: If LLM cannot be initialized
    """
    task = progress.add_task("Connecting to LLM...", total=None)
    try:
        logger.info("Connecting to LLM from config")
        llm_client = create_llm_from_config(
            verbose=verbose, batch_mode=batch_mode, batch_timeout=batch_timeout
        )
        logger.info("LLM client connected")
        progress.update(task, completed=True)
        return llm_client
    except Exception as e:
        logger.error(f"Failed to connect to LLM: {e}")
        console.print(f"[red]✗[/red] Failed to connect to LLM: {e}")
        console.print("[dim]Make sure Ollama is running and check .env configuration[/dim]")
        sys.exit(1)
