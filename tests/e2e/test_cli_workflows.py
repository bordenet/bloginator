"""End-to-end tests for CLI command workflows.

These tests invoke the actual CLI commands using CliRunner to verify
complete workflows function correctly from command invocation through
to output generation.

Part of Coder B's implementation (see docs/PARALLEL_VALIDATION_COVERAGE_PLAN.md).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from bloginator.cli.main import cli


if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_docs(tmp_path: Path) -> Path:
    """Create sample documents for extraction testing."""
    docs_dir = tmp_path / "sample_docs"
    docs_dir.mkdir()

    # Create markdown documents
    (docs_dir / "leadership.md").write_text(
        "# Leadership Principles\n\n"
        "Effective leadership requires clear communication and empathy.\n\n"
        "## Key Traits\n\n"
        "Leaders must demonstrate integrity, vision, and accountability.\n"
    )

    (docs_dir / "engineering.md").write_text(
        "# Engineering Excellence\n\n"
        "Building great software requires discipline and collaboration.\n\n"
        "## Best Practices\n\n"
        "Code reviews, testing, and documentation are essential.\n"
    )

    (docs_dir / "culture.md").write_text(
        "# Team Culture\n\n"
        "A healthy team culture promotes innovation and psychological safety.\n\n"
        "## Values\n\n"
        "Trust, respect, and continuous learning drive success.\n"
    )

    return docs_dir


@pytest.mark.e2e
class TestCLIBasicCommands:
    """Test basic CLI commands work correctly."""

    def test_help_command(self, runner: CliRunner) -> None:
        """Test --help shows usage information."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Bloginator" in result.output
        assert "extract" in result.output
        assert "index" in result.output
        assert "search" in result.output
        assert "outline" in result.output
        assert "draft" in result.output

    def test_version_command(self, runner: CliRunner) -> None:
        """Test version command shows version info."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Bloginator version" in result.output

    def test_init_command(self, runner: CliRunner) -> None:
        """Test init command runs successfully."""
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "Pre-download" in result.output or "model" in result.output.lower()


@pytest.mark.e2e
class TestTemplateCommands:
    """Test template CLI commands."""

    def test_template_list(self, runner: CliRunner) -> None:
        """Test template list shows available templates."""
        result = runner.invoke(cli, ["template", "list"])
        assert result.exit_code == 0
        assert "blog_post" in result.output or "templates" in result.output.lower()

    def test_template_show(self, runner: CliRunner) -> None:
        """Test template show displays template details or not found message."""
        result = runner.invoke(cli, ["template", "show", "builtin-blog"])
        assert result.exit_code == 0
        # Should show template structure or indicate template identity
        output_lower = result.output.lower()
        assert (
            "template" in output_lower
            or "title" in output_lower
            or "section" in output_lower
            or "not found" in output_lower
        )


@pytest.mark.e2e
class TestExtractCommand:
    """Test extract CLI command."""

    def test_extract_single_source(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path
    ) -> None:
        """Test extracting documents from a single source."""
        output_dir = tmp_path / "extracted"

        result = runner.invoke(
            cli,
            ["extract", str(sample_docs), "-o", str(output_dir)],
        )

        assert result.exit_code == 0
        assert output_dir.exists()
        # Should have extracted JSON files
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) >= 1

    def test_extract_with_quality_rating(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path
    ) -> None:
        """Test extracting with explicit quality rating."""
        output_dir = tmp_path / "extracted"

        result = runner.invoke(
            cli,
            [
                "extract",
                str(sample_docs),
                "-o",
                str(output_dir),
                "--quality",
                "preferred",
            ],
        )

        assert result.exit_code == 0


@pytest.mark.e2e
class TestIndexCommand:
    """Test index CLI command."""

    def test_index_extracted_documents(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path
    ) -> None:
        """Test indexing extracted documents."""
        extracted_dir = tmp_path / "extracted"
        index_dir = tmp_path / "index"

        # First extract
        runner.invoke(cli, ["extract", str(sample_docs), "-o", str(extracted_dir)])

        # Then index
        result = runner.invoke(
            cli,
            ["index", str(extracted_dir), "-o", str(index_dir)],
        )

        assert result.exit_code == 0
        assert index_dir.exists()


@pytest.mark.e2e
class TestSearchCommand:
    """Test search CLI command."""

    def test_search_requires_index(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test search fails gracefully without index."""
        fake_index = tmp_path / "nonexistent"
        result = runner.invoke(cli, ["search", str(fake_index), "query"])
        # Should fail because index doesn't exist
        assert result.exit_code != 0

    def test_search_with_real_index(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path
    ) -> None:
        """Test search works with a real index."""
        extracted_dir = tmp_path / "extracted"
        index_dir = tmp_path / "index"

        # Extract and index
        runner.invoke(cli, ["extract", str(sample_docs), "-o", str(extracted_dir)])
        runner.invoke(cli, ["index", str(extracted_dir), "-o", str(index_dir)])

        # Search
        result = runner.invoke(cli, ["search", str(index_dir), "leadership", "-n", "3"])

        assert result.exit_code == 0
        # Should have some output (results or message)
        assert len(result.output) > 0


@pytest.mark.e2e
class TestBlocklistCommands:
    """Test blocklist CLI commands."""

    def test_blocklist_list_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test blocklist list with no blocklist configured."""
        result = runner.invoke(
            cli, ["blocklist", "list", "--config-dir", str(tmp_path / "nonexistent")]
        )
        # Should handle missing config gracefully or show empty list
        assert result.exit_code == 0

    def test_blocklist_help(self, runner: CliRunner) -> None:
        """Test blocklist help shows subcommands."""
        result = runner.invoke(cli, ["blocklist", "--help"])
        assert result.exit_code == 0
        assert "add" in result.output
        assert "remove" in result.output
        assert "list" in result.output


@pytest.mark.e2e
class TestMetricsCommand:
    """Test metrics CLI command."""

    def test_metrics_help(self, runner: CliRunner) -> None:
        """Test metrics help shows options."""
        result = runner.invoke(cli, ["metrics", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
class TestDiffAndRevertCommands:
    """Test diff and revert CLI commands."""

    def test_diff_help(self, runner: CliRunner) -> None:
        """Test diff help shows options."""
        result = runner.invoke(cli, ["diff", "--help"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_revert_help(self, runner: CliRunner) -> None:
        """Test revert help shows options."""
        result = runner.invoke(cli, ["revert", "--help"])
        assert result.exit_code == 0


@pytest.mark.e2e
@pytest.mark.slow
class TestFullWorkflow:
    """Test complete extract → index → outline → draft workflow."""

    def test_extract_to_search_workflow(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path
    ) -> None:
        """Test complete workflow from extract through search."""
        extracted_dir = tmp_path / "extracted"
        index_dir = tmp_path / "index"

        # Step 1: Extract
        result = runner.invoke(cli, ["extract", str(sample_docs), "-o", str(extracted_dir)])
        assert result.exit_code == 0, f"Extract failed: {result.output}"
        assert extracted_dir.exists()

        # Step 2: Index
        result = runner.invoke(cli, ["index", str(extracted_dir), "-o", str(index_dir)])
        assert result.exit_code == 0, f"Index failed: {result.output}"
        assert index_dir.exists()

        # Step 3: Search
        result = runner.invoke(
            cli, ["search", str(index_dir), "engineering best practices", "-n", "5"]
        )
        assert result.exit_code == 0, f"Search failed: {result.output}"

    def test_outline_command_with_mock_llm(
        self, runner: CliRunner, sample_docs: Path, tmp_path: Path, monkeypatch
    ) -> None:
        """Test outline generation with mock LLM."""
        extracted_dir = tmp_path / "extracted"
        index_dir = tmp_path / "index"
        outline_path = tmp_path / "outline"

        # Set mock LLM mode (BLOGINATOR_LLM_MOCK=true enables MockLLMClient)
        monkeypatch.setenv("BLOGINATOR_LLM_MOCK", "true")

        # Extract and index first
        runner.invoke(cli, ["extract", str(sample_docs), "-o", str(extracted_dir)])
        runner.invoke(cli, ["index", str(extracted_dir), "-o", str(index_dir)])

        # Generate outline
        result = runner.invoke(
            cli,
            [
                "outline",
                "--index",
                str(index_dir),
                "--title",
                "Engineering Leadership",
                "--keywords",
                "leadership,engineering,culture",
                "--thesis",
                "Great engineering requires great leadership",
                "--sections",
                "3",
                "--output",
                str(outline_path),
                "--format",
                "both",
            ],
        )

        # With mock LLM, this should succeed
        assert result.exit_code == 0, f"Outline failed: {result.output}"
