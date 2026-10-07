"""Terminal UI application using Rich."""

from rich.console import Console
from rich.panel import Panel

class TUIApp:
    def __init__(self):
        self.console = Console()

    def render_dashboard(self):
        panel = Panel(
            "[bold cyan]LITERT AUTONOMOUS AGENT DASHBOARD[/bold cyan]\n"
            "Model: LOCAL / LiteRT-LM\n"
            "State: IDLE\n"
            "Autonomy: LEVEL 3",
            title="LiteRT Agent"
        )
        self.console.print(panel)
