"""CLI command for generating drafts."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from bloginator.generation import DraftGenerator, SafetyValidator, VoiceScorer, create_llm_client
from bloginator.models.outline import Outline
from bloginator.search import CorpusSearcher


@click.command()
@click.option(
    "--index",
    "index_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to index directory",
)
@click.option(
    "--outline",
    "outline_file",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to outline JSON file",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file for draft (markdown or JSON)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="Output format (default: markdown)",
)
@click.option(
    "--temperature",
    type=float,
    default=0.7,
    help="LLM sampling temperature 0.0-1.0 (default: 0.7)",
)
@click.option(
    "--model",
    default="llama3",
    help="LLM model to use (default: llama3)",
)
@click.option(
    "--sources-per-section",
    type=int,
    default=5,
    help="Number of sources to retrieve per section (default: 5)",
)
@click.option(
    "--max-section-words",
    type=int,
    default=300,
    help="Target words per section (default: 300)",
)
@click.option(
    "--validate-safety",
    is_flag=True,
    help="Validate against blocklist (blocks generation if violations found)",
)
@click.option(
    "--score-voice",
    is_flag=True,
    help="Calculate voice similarity score",
)
@click.option(
    "--config-dir",
    type=click.Path(path_type=Path),
    default=Path(".bloginator"),
    help="Configuration directory for blocklist (default: .bloginator)",
)
def draft(
    index_dir: Path,
    outline_file: Path,
    output_file: Path,
    output_format: str,
    temperature: float,
    model: str,
    sources_per_section: int,
    max_section_words: int,
    validate_safety: bool,
    score_voice: bool,
    config_dir: Path,
) -> None:
    """Generate document draft from outline.

    Uses RAG to synthesize content for each section based on corpus sources.
    Optionally validates against blocklist and scores voice similarity.

    Examples:
      Generate draft:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md

      With safety validation:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md \\
          --validate-safety

      With voice scoring:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.md \\
          --score-voice

      Save as JSON:
        bloginator draft --index output/index \\
          --outline outline.json \\
          -o draft.json \\
          --format json
    """
    console = Console()

    # Load outline
    try:
        outline_data = json.loads(outline_file.read_text())
        outline_obj = Outline.model_validate(outline_data)
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load outline: {e}")
        return

    console.print(f"[bold cyan]Generating draft: {outline_obj.title}[/bold cyan]")
    console.print()

    # Initialize components
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Load searcher
        task = progress.add_task("Loading corpus index...", total=None)
        try:
            searcher = CorpusSearcher(index_dir=index_dir)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load index: {e}")
            return
        progress.update(task, completed=True)

        # Initialize LLM client
        task = progress.add_task("Connecting to LLM...", total=None)
        try:
            llm_client = create_llm_client(model=model)
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to connect to LLM: {e}")
            console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
            return
        progress.update(task, completed=True)

        # Pre-validate inputs if safety validation enabled
        if validate_safety:
            task = progress.add_task("Pre-validating inputs...", total=None)
            validator = SafetyValidator(config_dir / "blocklist.json")

            validation_result = validator.validate_before_generation(
                title=outline_obj.title,
                keywords=outline_obj.keywords,
                thesis=outline_obj.thesis,
            )

            if not validation_result["is_valid"]:
                progress.update(task, completed=True)
                console.print()
                console.print(
                    f"[red]✗[/red] Input validation failed: {len(validation_result['violations'])} violation(s) found"
                )
                for v in validation_result["violations"]:
                    console.print(
                        f"  • Pattern '{v['pattern']}' matched: {', '.join(v['matches'])}"
                    )
                console.print()
                console.print("[dim]Fix these violations before generating content[/dim]")
                return

            progress.update(task, completed=True)

        # Initialize generator
        generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
            sources_per_section=sources_per_section,
        )

        # Generate draft
        task = progress.add_task(
            f"Generating content ({len(outline_obj.sections)} sections)...",
            total=None,
        )
        try:
            draft_obj = generator.generate(
                outline=outline_obj,
                temperature=temperature,
                max_section_words=max_section_words,
            )
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to generate draft: {e}")
            return
        progress.update(task, completed=True)

        # Validate safety if requested
        if validate_safety:
            task = progress.add_task("Validating against blocklist...", total=None)
            validator = SafetyValidator(config_dir / "blocklist.json", auto_reject=False)
            try:
                validator.validate_draft(draft_obj)
            except Exception as e:
                console.print(f"[red]✗[/red] Safety validation failed: {e}")
                return
            progress.update(task, completed=True)

        # Score voice if requested
        if score_voice:
            task = progress.add_task("Calculating voice similarity...", total=None)
            scorer = VoiceScorer(searcher=searcher)
            try:
                scorer.score_draft(draft_obj)
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Voice scoring failed: {e}")
            progress.update(task, completed=True)

    # Display results
    console.print()
    console.print("[green]✓[/green] Draft generation complete")
    console.print()

    # Statistics table
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row("Total Sections:", str(len(draft_obj.get_all_sections())))
    stats_table.add_row("Total Words:", str(draft_obj.total_words))
    stats_table.add_row("Total Citations:", str(draft_obj.total_citations))

    if score_voice:
        voice_color = (
            "green"
            if draft_obj.voice_score >= 0.7
            else "yellow"
            if draft_obj.voice_score >= 0.5
            else "red"
        )
        stats_table.add_row(
            "Voice Score:",
            f"[{voice_color}]{draft_obj.voice_score:.2f}[/{voice_color}]",
        )

    if validate_safety:
        safety_status = (
            "[red]⚠ Violations found[/red]"
            if draft_obj.has_blocklist_violations
            else "[green]✓ Clean[/green]"
        )
        stats_table.add_row("Safety Status:", safety_status)

    console.print(stats_table)
    console.print()

    # Safety warnings
    if validate_safety and draft_obj.has_blocklist_violations:
        console.print("[red]⚠️ Blocklist Violations Detected[/red]")
        console.print()

        for violation in draft_obj.blocklist_validation_result.get("violations", []):
            console.print(
                f"  • Pattern '{violation['pattern']}' in '{violation.get('section_title', 'Unknown')}'"
            )
            matches_str = ", ".join(f"'{m}'" for m in violation["matches"][:3])
            console.print(f"    Matched: {matches_str}")
            if violation.get("notes"):
                console.print(f"    [dim]{violation['notes']}[/dim]")

        console.print()
        console.print("[yellow]Review and remove violations before publishing[/yellow]")
        console.print()

    # Voice insights
    if score_voice:
        scorer = VoiceScorer(searcher=searcher)
        insights = scorer.get_voice_insights(draft_obj, threshold=0.7)

        console.print("[bold]Voice Similarity Insights:[/bold]")
        console.print(f"  Overall Score: {insights['overall_score']:.2f}")
        console.print(
            f"  Authentic Sections: {insights['authentic_sections']}/{insights['total_sections']}"
        )

        if insights["weak_sections"] > 0:
            console.print(f"  [yellow]Weak Sections ({insights['weak_sections']}):[/yellow]")
            for title, score in insights["weak_section_details"][:5]:
                console.print(f"    • {title} ({score:.2f})")

        console.print()

    # Save output
    try:
        if output_format in ["markdown", "both"]:
            md_path = output_file.with_suffix(".md") if output_format == "both" else output_file
            md_path.write_text(draft_obj.to_markdown(include_citations=True))
            console.print(f"[green]✓[/green] Saved markdown to {md_path}")

        if output_format in ["json", "both"]:
            json_path = output_file.with_suffix(".json") if output_format == "both" else output_file
            json_path.write_text(draft_obj.model_dump_json(indent=2))
            console.print(f"[green]✓[/green] Saved JSON to {json_path}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save draft: {e}")
        return

    # Final recommendations
    if draft_obj.has_blocklist_violations:
        console.print()
        console.print(
            "[yellow]⚠️[/yellow] Remember to address blocklist violations before publishing"
        )

    if score_voice and draft_obj.voice_score < 0.6:
        console.print()
        console.print("[yellow]⚠️[/yellow] Voice score is low - consider refining weak sections")
