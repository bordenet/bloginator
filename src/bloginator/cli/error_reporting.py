"""Error reporting utilities for CLI commands with actionable guidance."""

from collections import defaultdict
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Re-export SkipCategory for backwards compatibility
from bloginator.cli._skip_tracking import SkipCategory


class ErrorCategory(str, Enum):
    """Categories of errors with actionable guidance."""

    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    CORRUPTED_FILE = "corrupted_file"
    UNSUPPORTED_FORMAT = "unsupported_format"
    ENCODING_ERROR = "encoding_error"
    NETWORK_ERROR = "network_error"
    CONFIG_ERROR = "config_error"
    DEPENDENCY_ERROR = "dependency_error"
    UNKNOWN = "unknown"


class ErrorTracker:
    """Track and report errors with actionable suggestions."""

    def __init__(self):
        """Initialize error tracker."""
        self.errors: dict[ErrorCategory, list[tuple[str, Exception]]] = defaultdict(list)
        self.total_errors = 0
        self.skipped: dict[SkipCategory, list[str]] = defaultdict(list)
        self.total_skipped = 0
        # File type tracking
        self.files_by_type: dict[str, int] = defaultdict(int)
        self.extracted_by_type: dict[str, int] = defaultdict(int)
        self.total_files_found = 0
        self.total_extracted = 0

    def record_file(self, file_path: Path, extracted: bool = True) -> None:
        """Record a file for type statistics.

        Args:
            file_path: Path to the file
            extracted: True if successfully extracted, False if just found
        """
        ext = file_path.suffix.lower() or "(no extension)"
        self.files_by_type[ext] += 1
        self.total_files_found += 1
        if extracted:
            self.extracted_by_type[ext] += 1
            self.total_extracted += 1

    def record_error(self, category: ErrorCategory, context: str, exception: Exception) -> None:
        """Record an error with its category and context.

        Args:
            category: Error category for grouping and reporting
            context: Contextual information (filename, operation, etc.)
            exception: The exception that was raised
        """
        self.errors[category].append((context, exception))
        self.total_errors += 1

    def record_skip(self, category: SkipCategory, context: str) -> None:
        """Record a skipped file with its category.

        Args:
            category: Skip category for grouping and reporting
            context: Contextual information (filename, path, etc.)
        """
        self.skipped[category].append(context)
        self.total_skipped += 1

    def categorize_exception(
        self, exception: Exception, file_path: Path | None = None
    ) -> ErrorCategory:
        """Categorize an exception based on its type and context.

        Args:
            exception: The exception to categorize
            file_path: Optional file path for additional context

        Returns:
            ErrorCategory for the exception
        """
        error_msg = str(exception).lower()

        # File not found errors
        if isinstance(exception, FileNotFoundError):
            return ErrorCategory.FILE_NOT_FOUND

        # Permission errors
        if isinstance(exception, PermissionError):
            return ErrorCategory.PERMISSION_DENIED

        # Encoding errors
        if isinstance(exception, UnicodeDecodeError | UnicodeEncodeError):
            return ErrorCategory.ENCODING_ERROR

        # Corrupted or invalid file content
        if any(
            keyword in error_msg
            for keyword in ["corrupted", "invalid", "malformed", "unexpected end", "decrypt"]
        ):
            return ErrorCategory.CORRUPTED_FILE

        # Network errors
        if any(
            keyword in error_msg for keyword in ["connection", "network", "timeout", "unreachable"]
        ):
            return ErrorCategory.NETWORK_ERROR

        # Configuration errors
        if any(keyword in error_msg for keyword in ["config", "yaml", "invalid syntax"]):
            return ErrorCategory.CONFIG_ERROR

        # Dependency errors
        if isinstance(exception, ImportError) or "module" in error_msg:
            return ErrorCategory.DEPENDENCY_ERROR

        # Check file extension for unsupported format hints
        if file_path and file_path.suffix.lower() not in {
            ".pdf",
            ".docx",
            ".md",
            ".markdown",
            ".txt",
        }:
            return ErrorCategory.UNSUPPORTED_FORMAT

        return ErrorCategory.UNKNOWN

    def get_actionable_advice(self, category: ErrorCategory) -> str:
        """Get actionable advice for an error category.

        Args:
            category: Error category

        Returns:
            Actionable advice string
        """
        advice = {
            ErrorCategory.FILE_NOT_FOUND: "Verify the file path exists and is accessible. Check for typos in the path.",
            ErrorCategory.PERMISSION_DENIED: "Check file permissions with 'ls -la' and ensure you have read access. Try running with sudo if appropriate, or change file ownership.",
            ErrorCategory.CORRUPTED_FILE: "The file may be corrupted or password-protected. Try opening it in the native application to verify. Remove or fix corrupted files.",
            ErrorCategory.UNSUPPORTED_FORMAT: "Supported formats: PDF (.pdf), Word (.docx), Markdown (.md), Text (.txt). Convert the file to a supported format or skip it.",
            ErrorCategory.ENCODING_ERROR: "File contains unsupported character encoding. Try converting to UTF-8 with: iconv -f ISO-8859-1 -t UTF-8 file.txt > file_utf8.txt",
            ErrorCategory.NETWORK_ERROR: "Check network connectivity and firewall settings. Verify the remote host is reachable.",
            ErrorCategory.CONFIG_ERROR: "Check YAML syntax in corpus.yaml. Verify all paths and settings are valid. Use a YAML validator or linter.",
            ErrorCategory.DEPENDENCY_ERROR: "Required Python package may be missing. Try: pip install -e '.[dev]' or check requirements.txt",
            ErrorCategory.UNKNOWN: "Review the error details below. Check file format, permissions, and content validity.",
        }
        return advice.get(category, "Review error details and check documentation.")

    def print_summary(self, console: Console) -> None:
        """Print a rich, actionable error summary.

        Args:
            console: Rich console for output
        """
        if self.total_errors == 0:
            return

        console.print()
        console.print(Panel("[bold red]Error Summary[/bold red]", expand=False))

        # Create summary table
        table = Table(title=f"{self.total_errors} Error(s) Encountered", show_header=True)
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Count", style="yellow", justify="right")
        table.add_column("Examples", style="dim")

        for category, error_list in sorted(
            self.errors.items(), key=lambda x: len(x[1]), reverse=True
        ):
            # Get first 2 examples
            examples = [ctx for ctx, _ in error_list[:2]]
            example_str = ", ".join(examples)
            if len(error_list) > 2:
                example_str += f" (+{len(error_list) - 2} more)"

            table.add_row(
                category.replace("_", " ").title(),
                str(len(error_list)),
                example_str[:60] + "..." if len(example_str) > 60 else example_str,
            )

        console.print(table)

        # Print actionable advice for each category
        console.print("\n[bold cyan]Actionable Advice:[/bold cyan]")
        for category in self.errors:
            advice = self.get_actionable_advice(category)
            console.print(
                f"\n[yellow]●[/yellow] [bold]{category.replace('_', ' ').title()}:[/bold]"
            )
            console.print(f"  {advice}")

        console.print()

    def print_detailed_errors(self, console: Console, max_per_category: int = 5) -> None:
        """Print detailed error information for debugging.

        Args:
            console: Rich console for output
            max_per_category: Maximum errors to show per category
        """
        if self.total_errors == 0:
            return

        console.print("\n[bold red]Detailed Error Log:[/bold red]")

        for category, error_list in self.errors.items():
            console.print(
                f"\n[cyan]━━━ {category.replace('_', ' ').title()} ({len(error_list)}) ━━━[/cyan]"
            )

            for context, exception in error_list[:max_per_category]:
                console.print(f"  [yellow]●[/yellow] {context}")
                console.print(f"    [dim]{type(exception).__name__}: {str(exception)}[/dim]")

            if len(error_list) > max_per_category:
                console.print(f"  [dim]... and {len(error_list) - max_per_category} more[/dim]")

    def save_to_file(self, output_dir: Path, prefix: str = "extraction") -> Path:
        """Save skip and error report to a JSON file.

        Args:
            output_dir: Directory to save the report
            prefix: Filename prefix (e.g., 'extraction', 'indexing')

        Returns:
            Path to the saved report file
        """
        from bloginator.cli._report_generation import save_report_to_json

        return save_report_to_json(self, output_dir, prefix)

    def generate_corpus_report(self, output_path: Path | None = None) -> Path:
        """Generate a comprehensive corpus extraction report to /tmp.

        Args:
            output_path: Optional output path. Defaults to /tmp/bloginator_corpus_report.md

        Returns:
            Path to the generated report file
        """
        from bloginator.cli._report_generation import generate_corpus_report

        return generate_corpus_report(self, output_path)

    def print_skip_summary(
        self, console: Console, max_display_lines: int = 32, show_file_path: Path | None = None
    ) -> None:
        """Print a summary of skipped files with scrollable-height constraint.

        Args:
            console: Rich console for output
            max_display_lines: Maximum lines to display (default 32)
            show_file_path: If provided, show path to full report file
        """
        from bloginator.cli._skip_tracking import print_skip_summary

        print_skip_summary(
            skipped=self.skipped,
            total_skipped=self.total_skipped,
            console=console,
            max_display_lines=max_display_lines,
            show_file_path=str(show_file_path) if show_file_path else None,
        )


def create_error_panel(title: str, message: str, suggestion: str | None = None) -> Panel:
    """Create a rich error panel with optional suggestion.

    Args:
        title: Panel title
        message: Error message
        suggestion: Optional actionable suggestion

    Returns:
        Rich Panel for display
    """
    content = f"[red]{message}[/red]"
    if suggestion:
        content += f"\n\n[yellow]💡 Suggestion:[/yellow]\n{suggestion}"

    return Panel(content, title=f"[bold red]{title}[/bold red]", border_style="red")
