"""Output formatting and file writing for outline generation."""

import logging
from pathlib import Path

from rich.console import Console
from rich.table import Table

from bloginator.models.history import GenerationHistoryEntry, GenerationType
from bloginator.models.outline import Outline, OutlineSection
from bloginator.services.history_manager import HistoryManager


def display_outline_results(
    console: Console,
    outline_obj: Outline,
    classification: str,
    audience: str,
    min_coverage: int,
    logger: logging.Logger,
) -> None:
    """Display outline generation results in console.

    Args:
        console: Rich console instance
        outline_obj: Generated outline object
        classification: Content classification
        audience: Target audience
        min_coverage: Minimum coverage threshold
        logger: Logger instance
    """
    # Display title and metadata
    console.print()
    console.print(f"[bold cyan]Outline: {outline_obj.title}[/bold cyan]")

    # Display classification and audience as subtitle
    classification_label = classification.replace("-", " ").title()
    audience_label = audience.replace("-", " ").title()
    console.print(f"[dim italic]{classification_label} • For {audience_label}[/dim italic]")

    if outline_obj.thesis:
        console.print(f"[dim]Thesis: {outline_obj.thesis}[/dim]")
    console.print()

    # Statistics table
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row("Total Sections:", str(len(outline_obj.get_all_sections())))
    stats_table.add_row("Avg Coverage:", f"{outline_obj.avg_coverage:.0f}%")
    stats_table.add_row("Low Coverage Sections:", str(outline_obj.low_coverage_sections))
    console.print(stats_table)
    console.print()

    # Coverage analysis
    console.print("[bold]Coverage Analysis:[/bold]")
    _display_section_coverage(console, outline_obj.sections, level=0)
    console.print()

    # Warnings for low coverage
    if outline_obj.low_coverage_sections > 0:
        console.print()
        console.print(
            f"[yellow]⚠️[/yellow] {outline_obj.low_coverage_sections} section(s) have low corpus coverage"
        )
        console.print("[dim]Consider revising these sections or adding more source material[/dim]")


def save_outline_files(
    outline_obj: Outline,
    output_file: Path,
    output_format: str,
    title: str,
    classification: str,
    audience: str,
    keyword_list: list[str],
    thesis: str,
    num_sections: int,
    temperature: float,
    min_coverage: int,
    logger: logging.Logger,
    console: Console,
) -> None:
    """Save outline to files and history.

    Args:
        outline_obj: Generated outline object
        output_file: Output file path
        output_format: Format to save (json, markdown, both)
        title: Document title
        classification: Content classification
        audience: Target audience
        keyword_list: Keywords used
        thesis: Thesis statement
        num_sections: Number of sections
        temperature: LLM temperature
        min_coverage: Minimum coverage sources
        logger: Logger instance
        console: Rich console instance

    Raises:
        SystemExit: If file save fails
    """
    try:
        if output_format in ["json", "both"]:
            json_path = output_file.with_suffix(".json") if output_format == "both" else output_file
            json_path.write_text(outline_obj.model_dump_json(indent=2))
            logger.info(f"Saved JSON to {json_path}")
            console.print(f"[green]✓[/green] Saved JSON to {json_path}")

        if output_format in ["markdown", "both"]:
            md_path = output_file.with_suffix(".md") if output_format == "both" else output_file
            md_path.write_text(outline_obj.to_markdown())
            logger.info(f"Saved markdown to {md_path}")
            console.print(f"[green]✓[/green] Saved markdown to {md_path}")

        # Save to history
        try:
            history_manager = HistoryManager()
            history_entry = GenerationHistoryEntry(
                generation_type=GenerationType.OUTLINE,
                title=title,
                classification=classification,
                audience=audience,
                input_params={
                    "keywords": keyword_list,
                    "thesis": thesis,
                    "num_sections": num_sections,
                    "temperature": temperature,
                },
                output_path=str(output_file),
                output_format=output_format,
                metadata={
                    "total_sections": len(outline_obj.get_all_sections()),
                    "avg_coverage": outline_obj.avg_coverage,
                    "low_coverage_sections": outline_obj.low_coverage_sections,
                    "total_sources": outline_obj.total_sources,
                    "min_coverage": min_coverage,
                },
            )
            history_manager.save_entry(history_entry)
            logger.info(f"Saved to history: {history_entry.id}")
        except Exception as e:
            # Don't fail the command if history save fails
            logger.warning(f"Failed to save to history: {e}")

    except Exception as e:
        logger.error(f"Failed to save outline: {e}")
        console.print(f"[red]✗[/red] Failed to save outline: {e}")
        raise SystemExit(1) from e


def display_markdown_preview(console: Console, outline_obj: Outline) -> None:
    """Display markdown preview of outline in console.

    Args:
        console: Rich console instance
        outline_obj: Generated outline object
    """
    console.print("[bold]Markdown Preview:[/bold]")
    console.print(outline_obj.to_markdown())


def _display_section_coverage(
    console: Console, sections: list[OutlineSection], level: int = 0
) -> None:
    """Display section coverage recursively.

    Args:
        console: Rich console instance
        sections: Outline sections
        level: Current recursion level
    """
    indent = "  " * level
    for section in sections:
        # Coverage color coding
        if section.coverage_pct >= 75:
            coverage_color = "green"
            icon = "✓"
        elif section.coverage_pct >= 50:
            coverage_color = "yellow"
            icon = "○"
        else:
            coverage_color = "red"
            icon = "⚠"

        # Display section
        console.print(
            f"{indent}[{coverage_color}]{icon}[/{coverage_color}] {section.title} "
            f"[dim]({section.coverage_pct:.0f}% coverage, {section.source_count} sources)[/dim]"
        )

        if section.notes:
            console.print(f"{indent}  [dim]{section.notes}[/dim]")

        # Recursively display subsections
        if section.subsections:
            _display_section_coverage(console, section.subsections, level + 1)
