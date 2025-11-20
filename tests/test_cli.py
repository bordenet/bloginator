"""Test CLI functionality."""

from click.testing import CliRunner

from bloginator.cli.main import cli


def test_cli_help() -> None:
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Bloginator" in result.output
    # Ensure the help output includes the concise CLI description
    assert "bloginator command-line interface" in result.output.lower()


def test_cli_version_option() -> None:
    """Test CLI version option."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "bloginator" in result.output.lower()
    assert "1.0.0" in result.output


def test_version_command() -> None:
    """Test version command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "Bloginator version 1.0.0" in result.output
    assert "Matt Bordenet" in result.output
