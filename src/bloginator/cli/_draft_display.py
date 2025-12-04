"""Display formatting and results output for draft generation."""

from rich.console import Console
from rich.table import Table

from bloginator.generation import VoiceScorer
from bloginator.models.draft import Draft
from bloginator.search import CorpusSearcher


def display_results(
    draft: Draft,
    searcher: CorpusSearcher,
    score_voice: bool,
    validate_safety: bool,
    console: Console,
) -> None:
    """Display draft generation results and statistics.

    Args:
        draft: Generated draft object
        searcher: CorpusSearcher instance
        score_voice: Whether voice scoring was performed
        validate_safety: Whether safety validation was performed
        console: Rich console for output
    """
    console.print()
    console.print("[green]✓[/green] Draft generation complete")
    console.print()

    # Statistics table
    stats_table = Table(show_header=False, box=None, padding=(0, 2))
    stats_table.add_row("Total Sections:", str(len(draft.get_all_sections())))
    stats_table.add_row("Total Words:", str(draft.total_words))
    stats_table.add_row("Total Citations:", str(draft.total_citations))

    if score_voice:
        voice_color = (
            "green" if draft.voice_score >= 0.7 else "yellow" if draft.voice_score >= 0.5 else "red"
        )
        stats_table.add_row(
            "Voice Score:",
            f"[{voice_color}]{draft.voice_score:.2f}[/{voice_color}]",
        )

    if validate_safety:
        safety_status = (
            "[red]⚠ Violations found[/red]"
            if draft.has_blocklist_violations
            else "[green]✓ Clean[/green]"
        )
        stats_table.add_row("Safety Status:", safety_status)

    console.print(stats_table)
    console.print()

    # Safety warnings
    if validate_safety and draft.has_blocklist_violations:
        _display_safety_violations(draft, console)

    # Voice insights
    if score_voice:
        _display_voice_insights(draft, searcher, console)

    # Final recommendations
    if draft.has_blocklist_violations:
        console.print()
        console.print(
            "[yellow]⚠️[/yellow] Remember to address blocklist violations before publishing"
        )

    if score_voice and draft.voice_score < 0.6:
        console.print()
        console.print("[yellow]⚠️[/yellow] Voice score is low - consider refining weak sections")


def _display_safety_violations(draft: Draft, console: Console) -> None:
    """Display blocklist violations found in draft.

    Args:
        draft: Generated draft object
        console: Rich console for output
    """
    console.print("[red]⚠️ Blocklist Violations Detected[/red]")
    console.print()

    violations = (
        draft.blocklist_validation_result.get("violations", [])
        if draft.blocklist_validation_result
        else []
    )
    for violation in violations:
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


def _display_voice_insights(draft: Draft, searcher: CorpusSearcher, console: Console) -> None:
    """Display voice similarity insights for draft.

    Args:
        draft: Generated draft object
        searcher: CorpusSearcher instance
        console: Rich console for output
    """
    scorer = VoiceScorer(searcher=searcher)
    insights = scorer.get_voice_insights(draft, threshold=0.7)

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
