"""Export CLI command for converting drafts and outlines to various formats."""

import json
from pathlib import Path

import click

from bloginator.export import ExportFormat, create_exporter
from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection


def _load_draft_from_markdown(file_path: Path) -> Draft:
    """Load a draft from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Draft object parsed from markdown
    """
    content = file_path.read_text()
    lines = content.split("\n")

    title = "Untitled"
    sections: list[DraftSection] = []
    current_section: DraftSection | None = None
    current_content: list[str] = []

    for line in lines:
        if line.startswith("# ") and title == "Untitled":
            title = line[2:].strip()
        elif line.startswith("## "):
            # Save previous section
            if current_section is not None:
                current_section.content = "\n".join(current_content).strip()
                sections.append(current_section)
            # Start new section
            current_section = DraftSection(
                title=line[3:].strip(),
                content="",
            )
            current_content = []
        elif current_section is not None:
            current_content.append(line)
        elif not line.startswith("#"):
            # Content before any section (intro)
            if not sections and current_section is None:
                current_section = DraftSection(
                    title="Introduction",
                    content="",
                )
            if current_section:
                current_content.append(line)

    # Save last section
    if current_section is not None:
        current_section.content = "\n".join(current_content).strip()
        sections.append(current_section)

    return Draft(
        title=title,
        sections=sections,
    )


def _load_outline_from_json(file_path: Path) -> Outline:
    """Load an outline from a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Outline object parsed from JSON
    """
    data = json.loads(file_path.read_text())

    sections = []
    for section_data in data.get("sections", []):
        section = OutlineSection(
            title=section_data.get("title", ""),
            key_points=section_data.get("key_points", []),
            subsections=[
                OutlineSection(
                    title=sub.get("title", ""),
                    key_points=sub.get("key_points", []),
                    subsections=[],
                )
                for sub in section_data.get("subsections", [])
            ],
        )
        sections.append(section)

    return Outline(
        title=data.get("title", "Untitled"),
        thesis=data.get("thesis", ""),
        keywords=data.get("keywords", []),
        sections=sections,
    )


def _detect_input_type(file_path: Path) -> str:
    """Detect whether input is a draft (markdown) or outline (json).

    Args:
        file_path: Path to input file

    Returns:
        'draft' or 'outline'
    """
    suffix = file_path.suffix.lower()
    if suffix in (".md", ".markdown"):
        return "draft"
    if suffix == ".json":
        return "outline"
    # Try to detect by content
    content = file_path.read_text()
    if content.strip().startswith("{"):
        return "outline"
    return "draft"


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file path",
)
@click.option(
    "-f",
    "--format",
    "export_format",
    type=click.Choice(["markdown", "pdf", "docx", "html", "text"], case_sensitive=False),
    default=None,
    help="Export format (inferred from output extension if not specified)",
)
def export(input_file: Path, output: Path, export_format: str | None) -> None:
    """Export a draft or outline to various formats.

    Converts markdown drafts or JSON outlines to PDF, DOCX, HTML, or other formats.

    INPUT_FILE is the path to a markdown (.md) draft or JSON (.json) outline.

    Examples:
        Export draft to PDF:
            bloginator export draft.md --format pdf -o draft.pdf

        Export outline to HTML:
            bloginator export outline.json -o outline.html

        Format inferred from output extension:
            bloginator export draft.md -o draft.docx
    """
    # Determine format
    if export_format is None:
        try:
            fmt = ExportFormat.from_extension(output.suffix)
        except ValueError as e:
            raise click.ClickException(str(e))
    else:
        try:
            fmt = ExportFormat(export_format.lower())
        except ValueError:
            raise click.ClickException(f"Unsupported format: {export_format}")

    # Load input document
    input_type = _detect_input_type(input_file)
    try:
        if input_type == "outline":
            document = _load_outline_from_json(input_file)
        else:
            document = _load_draft_from_markdown(input_file)
    except Exception as e:
        raise click.ClickException(f"Failed to load input file: {e}")

    # Create exporter and export
    try:
        exporter = create_exporter(fmt)
        output.parent.mkdir(parents=True, exist_ok=True)
        exporter.export(document, output)
        click.echo(f"Exported to {output}")
    except Exception as e:
        raise click.ClickException(f"Export failed: {e}")
