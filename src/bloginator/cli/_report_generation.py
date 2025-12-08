"""Report generation utilities for extraction and indexing operations.

This module handles generating markdown and JSON reports for corpus operations.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from bloginator.cli.error_reporting import ErrorTracker


def generate_corpus_report(tracker: "ErrorTracker", output_path: Path | None = None) -> Path:
    """Generate a comprehensive corpus extraction report to /tmp.

    Args:
        tracker: ErrorTracker with extraction statistics
        output_path: Optional output path. Defaults to /tmp/bloginator_corpus_report.md

    Returns:
        Path to the generated report file
    """
    if output_path is None:
        output_path = Path("/tmp/bloginator_corpus_report.md")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Bloginator Corpus Extraction Report",
        f"\nGenerated: {timestamp}",
        "",
        "## Summary",
        "",
        f"- **Total Files Found**: {tracker.total_files_found}",
        f"- **Successfully Extracted**: {tracker.total_extracted}",
        f"- **Skipped**: {tracker.total_skipped}",
        f"- **Errors**: {tracker.total_errors}",
        "",
        "## Files by Type",
        "",
        "| Extension | Found | Extracted | Skipped/Failed |",
        "|-----------|-------|-----------|----------------|",
    ]

    # Sort by count descending
    for ext, count in sorted(tracker.files_by_type.items(), key=lambda x: x[1], reverse=True):
        extracted = tracker.extracted_by_type.get(ext, 0)
        skipped_failed = count - extracted
        lines.append(f"| {ext} | {count} | {extracted} | {skipped_failed} |")

    lines.append("")
    lines.append("## Skipped Files")
    lines.append("")

    if tracker.total_skipped > 0:
        for category, skip_list in sorted(
            tracker.skipped.items(), key=lambda x: len(x[1]), reverse=True
        ):
            lines.append(f"### {category.value.replace('_', ' ').title()} ({len(skip_list)})")
            lines.append("")
            for item in skip_list[:20]:  # Limit to 20 per category
                lines.append(f"- {item}")
            if len(skip_list) > 20:
                lines.append(f"- ... and {len(skip_list) - 20} more")
            lines.append("")
    else:
        lines.append("*No files were skipped.*")
        lines.append("")

    lines.append("## Errors")
    lines.append("")

    if tracker.total_errors > 0:
        for category, error_list in sorted(
            tracker.errors.items(), key=lambda x: len(x[1]), reverse=True
        ):
            lines.append(f"### {category.value.replace('_', ' ').title()} ({len(error_list)})")
            lines.append("")
            for ctx, exc in error_list[:10]:  # Limit to 10 per category
                lines.append(f"- **{ctx}**: {type(exc).__name__}: {exc!s}")
            if len(error_list) > 10:
                lines.append(f"- ... and {len(error_list) - 10} more")
            lines.append("")
    else:
        lines.append("*No errors occurred.*")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def save_report_to_json(
    tracker: "ErrorTracker", output_dir: Path, prefix: str = "extraction"
) -> Path:
    """Save skip and error report to a JSON file.

    Args:
        tracker: ErrorTracker with extraction statistics
        output_dir: Directory to save the report
        prefix: Filename prefix (e.g., 'extraction', 'indexing')

    Returns:
        Path to the saved report file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"{prefix}_report_{timestamp}.json"

    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_skipped": tracker.total_skipped,
            "total_errors": tracker.total_errors,
        },
        "skipped": {category.value: items for category, items in tracker.skipped.items()},
        "errors": {
            category.value: [
                {"context": ctx, "error": str(exc), "type": type(exc).__name__}
                for ctx, exc in items
            ]
            for category, items in tracker.errors.items()
        },
    }

    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report_file
