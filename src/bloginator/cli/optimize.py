"""CLI command for prompt optimization."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from bloginator.generation.llm_factory import create_llm_from_config
from bloginator.optimization.prompt_tuner import PromptTuner
from bloginator.search import CorpusSearcher


console = Console()
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--corpus-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Corpus directory (overrides config)",
)
@click.option(
    "--index-dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Index directory (overrides config)",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default="./prompt_tuning_results",
    help="Output directory for results",
)
@click.option(
    "--num-test-cases",
    type=int,
    default=2,
    help="Number of test cases to generate",
)
@click.option(
    "--num-iterations",
    type=int,
    default=3,
    help="Number of optimization iterations",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def optimize(
    corpus_dir: Path | None,
    index_dir: Path | None,
    output_dir: Path,
    num_test_cases: int,
    num_iterations: int,
    verbose: bool,
) -> None:
    """Optimize LLM prompts through iterative testing and scoring.

    This command:
    1. Generates test cases from your corpus
    2. Runs baseline generation with current prompts
    3. Scores results using voice matching and AI slop detection
    4. Iteratively improves prompts to better match your voice
    5. Saves results and updated prompts

    Example:
        bloginator optimize --num-test-cases 5 --num-iterations 3
    """
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Get corpus and index directories
    corpus_path = corpus_dir or Path("./corpus")
    index_path = index_dir or Path("./.bloginator/index")

    # Validate paths
    if not corpus_path.exists():
        console.print(f"[red]Error: Corpus directory not found: {corpus_path}[/red]")
        raise click.Abort()

    if not index_path.exists():
        console.print(
            f"[yellow]Warning: Index not found at {index_path}. Run 'bloginator index' first.[/yellow]"
        )
        raise click.Abort()

    console.print("[bold]🚀 Prompt Optimization Framework[/bold]")
    console.print("=" * 50)

    # Initialize LLM client
    console.print("🔧 Initializing LLM client...")
    llm_client = create_llm_from_config(verbose=verbose)

    # Initialize searcher
    console.print(f"📚 Loading corpus index from {index_path}...")
    searcher = CorpusSearcher(index_dir=index_path)

    # Initialize prompt tuner
    console.print("🎯 Initializing prompt tuner...")
    tuner = PromptTuner(
        llm_client=llm_client,
        searcher=searcher,
        output_dir=output_dir,
    )

    # Run optimization
    console.print(
        f"\n🧬 Running optimization with {num_test_cases} test cases, {num_iterations} iterations..."
    )
    results = tuner.optimize(
        num_iterations=num_iterations,
        num_test_cases=num_test_cases,
    )

    # Display results
    console.print("\n[bold green]✅ Optimization Complete![/bold green]\n")

    table = Table(title="Optimization Results")
    table.add_column("Test Case", style="cyan")
    table.add_column("Baseline Score", justify="right")
    table.add_column("Improved Score", justify="right")
    table.add_column("Improvement", justify="right", style="green")
    table.add_column("Slop Before", justify="right")
    table.add_column("Slop After", justify="right")

    for result in results:
        improvement_str = f"+{result.improvement:.2f}" if result.improvement >= 0 else f"{result.improvement:.2f}"
        table.add_row(
            result.test_case_id,
            f"{result.baseline_score:.2f}",
            f"{result.improved_score:.2f}",
            improvement_str,
            str(result.slop_violations_before),
            str(result.slop_violations_after),
        )

    console.print(table)

    # Summary
    avg_baseline = sum(r.baseline_score for r in results) / len(results)
    avg_improved = sum(r.improved_score for r in results) / len(results)
    avg_improvement = avg_improved - avg_baseline

    console.print(f"\n📊 Average baseline score: {avg_baseline:.2f}/5.0")
    console.print(f"📈 Average improved score: {avg_improved:.2f}/5.0")
    console.print(f"🎯 Average improvement: {avg_improvement:+.2f}")
    console.print(f"\n📁 Results saved to: {output_dir}")

