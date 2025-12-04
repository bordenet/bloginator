"""Draft generation, output saving, and history management."""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from bloginator.generation import DraftGenerator
from bloginator.models.draft import Draft
from bloginator.models.history import GenerationHistoryEntry, GenerationType
from bloginator.models.outline import Outline
from bloginator.services.history_manager import HistoryManager


def generate_draft_with_progress(
    generator: DraftGenerator,
    outline: Outline,
    temperature: float,
    max_section_words: int,
    progress: Progress,
    logger: logging.Logger,
    console: Console,
) -> Draft:
    """Generate draft with progress tracking.

    Args:
        generator: DraftGenerator instance
        outline: Outline to generate from
        temperature: LLM sampling temperature
        max_section_words: Target words per section
        progress: Rich progress bar
        logger: Logger instance
        console: Rich console for output

    Returns:
        Generated draft object

    Raises:
        SystemExit: If generation fails
    """
    total_sections = len(outline.get_all_sections())
    task = progress.add_task(
        f"Generating content (0/{total_sections} sections)...",
        total=total_sections,
    )

    def update_progress(message: str, current: int, total: int) -> None:
        """Update progress bar with current section."""
        progress.update(
            task,
            description=f"{message} ({current + 1}/{total})",
            completed=current + 1,
        )

    try:
        logger.info(
            f"Generating draft with {len(outline.sections)} top-level sections, "
            f"{total_sections} total sections (including subsections), temperature={temperature}"
        )
        draft_obj = generator.generate(
            outline=outline,
            temperature=temperature,
            max_section_words=max_section_words,
            progress_callback=update_progress,
        )
        logger.info(
            f"Draft generated: {draft_obj.total_words} words, {draft_obj.total_citations} citations"
        )
        progress.update(task, completed=total_sections)
        return draft_obj
    except Exception as e:
        logger.error(f"Failed to generate draft: {e}", exc_info=True)
        console.print(f"[red]✗[/red] Failed to generate draft: {e}")
        sys.exit(1)


def save_draft_output(
    draft: Draft,
    output_file: Path,
    output_format: str,
    logger: logging.Logger,
    console: Console,
) -> None:
    """Save draft to markdown and/or JSON.

    Args:
        draft: Generated draft object
        output_file: Path to output file
        output_format: Format(s) to save ("markdown", "json", or "both")
        logger: Logger instance
        console: Rich console for output

    Raises:
        SystemExit: If save fails
    """
    try:
        if output_format in ["markdown", "both"]:
            md_path = output_file.with_suffix(".md") if output_format == "both" else output_file
            md_path.write_text(draft.to_markdown(include_citations=True))
            logger.info(f"Saved markdown to {md_path}")
            console.print(f"[green]✓[/green] Saved markdown to {md_path}")

        if output_format in ["json", "both"]:
            json_path = output_file.with_suffix(".json") if output_format == "both" else output_file
            json_path.write_text(draft.model_dump_json(indent=2))
            logger.info(f"Saved JSON to {json_path}")
            console.print(f"[green]✓[/green] Saved JSON to {json_path}")

    except Exception as e:
        logger.error(f"Failed to save draft: {e}")
        console.print(f"[red]✗[/red] Failed to save draft: {e}")
        sys.exit(1)


def save_to_history(
    draft: Draft,
    outline: Outline,
    outline_file: Path,
    output_file: Path,
    output_format: str,
    temperature: float,
    sources_per_section: int,
    max_section_words: int,
    validate_safety: bool,
    score_voice: bool,
    logger: logging.Logger,
) -> None:
    """Save generation entry to history.

    Args:
        draft: Generated draft object
        outline: Original outline
        outline_file: Path to outline file
        output_file: Path to output file
        output_format: Output format used
        temperature: Temperature used
        sources_per_section: Sources per section parameter
        max_section_words: Max section words parameter
        validate_safety: Whether safety validation was used
        score_voice: Whether voice scoring was used
        logger: Logger instance
    """
    try:
        history_manager = HistoryManager()
        history_entry = GenerationHistoryEntry(
            generation_type=GenerationType.DRAFT,
            title=outline.title,
            classification=outline.classification,
            audience=outline.audience,
            input_params={
                "outline_file": str(outline_file),
                "temperature": temperature,
                "sources_per_section": sources_per_section,
                "max_section_words": max_section_words,
            },
            output_path=str(output_file),
            output_format=output_format,
            metadata={
                "total_sections": len(draft.get_all_sections()),
                "total_words": draft.total_words,
                "total_citations": draft.total_citations,
                "voice_score": draft.voice_score if score_voice else 0.0,
                "has_blocklist_violations": draft.has_blocklist_violations,
                "validate_safety": validate_safety,
                "score_voice": score_voice,
            },
        )
        history_manager.save_entry(history_entry)
        logger.info(f"Saved to history: {history_entry.id}")
    except Exception as e:
        logger.warning(f"Failed to save to history: {e}")
