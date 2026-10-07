"""Terminal UI dashboard using Rich."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from litert_agent.environment.detector import EnvironmentDetector


class TUIApp:
    """Rich-based terminal dashboard."""

    def __init__(self):
        self.console = Console()

    def render_dashboard(self):
        env = EnvironmentDetector.detect_all()
        litert_ok = env["has_litert_lm"]

        status = Table.grid(padding=(0, 2))
        status.add_row("[bold]State[/bold]", "IDLE")
        status.add_row("[bold]Model[/bold]", "[green]LiteRT-LM[/green]" if litert_ok else "[red]LiteRT-LM not found[/red]")
        status.add_row("[bold]Autonomy[/bold]", "LEVEL 3")
        status.add_row("[bold]CPU[/bold]", f"{env['resources']['cpu_percent']}%")
        status.add_row("[bold]RAM[/bold]", f"{env['resources']['memory']['available_gb']} GB available")
        status.add_row("[bold]Disk[/bold]", f"{env['resources']['disk']['free_gb']} GB free")
        status.add_row("[bold]Git[/bold]", "OK" if env["has_git"] else "MISSING")

        nav = ("[cyan]Dashboard[/cyan]\nAgent\nTasks\nPlans\nMemory\nSkills\nTools\n"
               "Workers\nScheduler\nApprovals\nSecurity\nCheckpoints\nLogs\nSystem\nSettings")

        events = "[green]✓[/green] Environment inspected\n→ Awaiting mission"

        self.console.print(Panel(status, title="LITERT AGENT  ●  STATUS"))
        self.console.print(Panel(nav, title="NAVIGATION"))
        self.console.print(Panel(events, title="EVENTS"))
        self.console.print("[dim]Controls: Q quit · full TUI screens available via 'litert-agent web'[/dim]")
