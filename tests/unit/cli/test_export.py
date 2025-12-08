"""Tests for the export CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from bloginator.cli.export import export


class TestExportCLI:
    """Tests for bloginator export command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_draft_md(self, tmp_path: Path) -> Path:
        """Create a sample markdown draft file."""
        draft_file = tmp_path / "draft.md"
        draft_file.write_text(
            "# Test Draft\n\n"
            "This is a test draft for export testing.\n\n"
            "## Section 1\n\n"
            "Content for section 1.\n"
        )
        return draft_file

    @pytest.fixture
    def sample_outline_json(self, tmp_path: Path) -> Path:
        """Create a sample outline JSON file."""
        import json

        outline_file = tmp_path / "outline.json"
        outline_data = {
            "title": "Test Outline",
            "thesis": "This is a test thesis",
            "keywords": ["test", "outline"],
            "sections": [
                {
                    "title": "Introduction",
                    "key_points": ["Point 1", "Point 2"],
                    "subsections": [],
                }
            ],
        }
        outline_file.write_text(json.dumps(outline_data))
        return outline_file

    def test_export_markdown_to_html(
        self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path
    ) -> None:
        """Export markdown draft to HTML format."""
        output_file = tmp_path / "output.html"

        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "html", "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        content = output_file.read_text()
        assert "<html" in content.lower() or "<!doctype" in content.lower()
        assert "Test Draft" in content

    def test_export_markdown_to_pdf(
        self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path
    ) -> None:
        """Export markdown draft to PDF format."""
        pytest.importorskip("reportlab", reason="PDF export requires reportlab")
        output_file = tmp_path / "output.pdf"

        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "pdf", "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        # PDF files start with %PDF
        content = output_file.read_bytes()
        assert content.startswith(b"%PDF")

    def test_export_markdown_to_docx(
        self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path
    ) -> None:
        """Export markdown draft to DOCX format."""
        output_file = tmp_path / "output.docx"

        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "docx", "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        # DOCX files are ZIP archives starting with PK
        content = output_file.read_bytes()
        assert content.startswith(b"PK")

    def test_export_infers_format_from_output_extension(
        self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path
    ) -> None:
        """Format is inferred from output file extension when not specified."""
        output_file = tmp_path / "output.html"

        result = runner.invoke(
            export,
            [str(sample_draft_md), "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        content = output_file.read_text()
        assert "<html" in content.lower() or "<!doctype" in content.lower()

    def test_export_outline_to_html(
        self, runner: CliRunner, sample_outline_json: Path, tmp_path: Path
    ) -> None:
        """Export outline JSON to HTML format."""
        output_file = tmp_path / "output.html"

        result = runner.invoke(
            export,
            [str(sample_outline_json), "--format", "html", "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Outline" in content

    def test_export_to_text(self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path) -> None:
        """Export markdown draft to plain text format."""
        output_file = tmp_path / "output.txt"

        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "text", "-o", str(output_file)],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Draft" in content

    def test_export_missing_input_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Error when input file doesn't exist."""
        result = runner.invoke(
            export,
            [str(tmp_path / "nonexistent.md"), "-o", str(tmp_path / "out.html")],
        )

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower()

    def test_export_unsupported_format(
        self, runner: CliRunner, sample_draft_md: Path, tmp_path: Path
    ) -> None:
        """Error when unsupported format is specified."""
        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "xyz", "-o", str(tmp_path / "out.xyz")],
        )

        assert result.exit_code != 0
        assert "unsupported" in result.output.lower() or "invalid" in result.output.lower()

    def test_export_requires_output(self, runner: CliRunner, sample_draft_md: Path) -> None:
        """Error when output path is not specified."""
        result = runner.invoke(
            export,
            [str(sample_draft_md), "--format", "html"],
        )

        assert result.exit_code != 0

    def test_export_help(self, runner: CliRunner) -> None:
        """Help text shows usage information."""
        result = runner.invoke(export, ["--help"])

        assert result.exit_code == 0
        assert "export" in result.output.lower()
        assert "--format" in result.output
        assert "--output" in result.output or "-o" in result.output
