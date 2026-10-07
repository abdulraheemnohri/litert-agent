"""Unit test for CLI."""

from typer.testing import CliRunner

from litert_agent.cli import app

runner = CliRunner()

def test_cli_doctor():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "System Diagnostics" in result.stdout

def test_cli_capabilities():
    result = runner.invoke(app, ["capabilities"])
    assert result.exit_code == 0
    assert "python_version" in result.stdout
