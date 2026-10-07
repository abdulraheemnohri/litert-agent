"""Command-Line Interface (Typer)."""

import asyncio
import typer
from rich.console import Console
from rich.table import Table

from litert_agent.runtime.orchestrator import Orchestrator
from litert_agent.environment.detector import EnvironmentDetector
from litert_agent.environment.capabilities import Capabilities

app = typer.Typer(name="litert-agent", help="LiteRT Autonomous Agent CLI")
console = Console()

@app.command()
def run(goal: str = typer.Argument(..., help="Goal or prompt for the autonomous agent"),
    safe: bool = typer.Option(False, "--safe", help="Safe mode: block destructive ops"),
    offline: bool = typer.Option(False, "--offline", help="Disable network access"),
    profile: str = typer.Option("normal", "--profile", help="low-memory | normal | performance"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory")):
    """Run an autonomous task."""
    console.print(f"[bold green]Starting LiteRT Agent task:[/bold green] {goal}")

    async def _run():
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        result = await orchestrator.run_task(goal)
        console.print(f"\n[bold blue]Result:[/bold blue]\n{result}")

    asyncio.run(_run())

@app.command()
def doctor():
    """Run system diagnostics (self-diagnostics)."""
    console.print("[bold yellow]Running LiteRT Agent Self-Diagnostics...[/bold yellow]\n")
    env = EnvironmentDetector.detect_all()

    table = Table(title="System Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Status / Value", style="magenta")

    table.add_row("OS", str(env["os"]))
    table.add_row("Python Version", str(env["python_version"]))
    table.add_row("Git Installed", "YES" if env["has_git"] else "NO")
    table.add_row("LiteRT-LM CLI Installed", "YES" if env["has_litert_lm"] else "NO")
    table.add_row("Playwright Installed", "YES" if env["has_playwright"] else "NO")
    table.add_row("CPU Percent", f"{env['resources']['cpu_percent']}%")
    table.add_row("RAM Available", f"{env['resources']['memory']['available_gb']} GB")

    console.print(table)

@app.command()
def capabilities():
    """List agent capabilities."""
    caps = Capabilities.discover()
    console.print(caps.model_dump_json(indent=2))

@app.command()
def version():
    """Show application version."""
    console.print(f"litert-agent {__version__}")


if __name__ == "__main__":
    app()
