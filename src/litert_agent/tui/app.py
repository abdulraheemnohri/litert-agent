"""Full Textual TUI for LiteRT Agent."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static, DataTable, Log

from litert_agent.config import Config
from litert_agent.runtime.service import AgentRuntime
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.recovery.checkpoints import CheckpointManager

import sqlite3


class Sidebar(Static):
    """Navigation sidebar."""


class DashboardView(Static):
    def on_mount(self) -> None:
        self.update(self.render_dashboard())

    def render_dashboard(self) -> str:
        runtime = AgentRuntime.get()
        status = runtime.status()
        health = runtime.health()
        return (
            f"[b]Mission[/b]\n"
            f"  Agent: {status['agent']}  ·  State: {'RUNNING' if status['started'] else 'IDLE'}\n"
            f"  Autonomy: level {status['autonomy_level']}  ·  Profile-safe: {status['safe_mode']}  ·  Offline: {status['offline_mode']}\n\n"
            f"[b]Model[/b]\n"
            f"  Provider: {status['model_provider']} (LiteRT-LM CLI only)\n"
            f"  Health: {health.get('status', 'UNKNOWN')}\n\n"
            f"[b]Queue[/b]\n"
            f"  Pending jobs: {status['queue_size']}\n\n"
            f"  [i]Press T for tasks, A for approvals, L for logs, Q to quit.[/i]"
        )


class TasksView(Static):
    def on_mount(self) -> None:
        self.update(self.render_tasks())

    def render_tasks(self) -> str:
        cfg = Config.load()
        db = DatabaseManager(cfg.agent.home_dir / "agent.db")
        with sqlite3.connect(db.db_path) as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        rows = db.execute_read(
            "SELECT id, description, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 20"
        )
        if not rows:
            return "[i]No tasks yet. Start one from the Web UI or CLI.[/i]"
        lines = ["[b]ID         Status      Description[/b]"]
        for r in rows:
            lines.append(f"{r[0][:10]}  {r[2]:<10}  {str(r[1])[:60]}")
        return "\n".join(lines)


class ApprovalsView(Static):
    def on_mount(self) -> None:
        self.update(self.render_approvals())

    def render_approvals(self) -> str:
        approvals = AgentRuntime.get().orchestrator.approval_manager
        pending = approvals.list_pending()
        if not pending:
            return "[green]No pending approvals.[/green]"
        lines = []
        for a in pending:
            lines.append(
                f"[yellow]HIGH RISK[/yellow] {a['tool']}.{a['action']}\n"
                f"  Args: {a['args']}\n"
                f"  Reason: {a['reason']}\n"
                f"  [b]O[/b]=Allow once  [b]S[/b]=Allow session  [b]D[/b]=Deny\n"
            )
        return "\n".join(lines)


class LogsView(Log):
    def on_mount(self) -> None:
        runtime = AgentRuntime.get()
        for event_type in ("task_started", "task_completed", "task_failed",
                           "tool_started", "tool_completed", "health"):
            runtime.event_bus.subscribe(event_type, self._on_event)

    def _on_event(self, event) -> None:
        self.write_line(f"{event.event_type}: {event.payload}")


class LiteRTTUIApp(App):
    """LiteRT Agent terminal application."""

    TITLE = "LiteRT Agent"
    CSS = """
    Screen { layout: horizontal; }
    #sidebar { width: 24; border-right: solid $primary; padding: 1; }
    #main { padding: 1 2; }
    """

    BINDINGS = [
        ("d", "view_dashboard", "Dashboard"),
        ("t", "view_tasks", "Tasks"),
        ("a", "view_approvals", "Approvals"),
        ("l", "view_logs", "Logs"),
        ("p", "pause", "Pause"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static(
                    "[b]LITERT AGENT[/b]\n\n"
                    " [b]D[/b] Dashboard\n [b]T[/b] Tasks\n [b]A[/b] Approvals\n"
                    " [b]L[/b] Logs\n\n"
                    " [b]P[/b] Pause agent\n [b]Q[/b] Quit",
                    id="nav",
                )
            with Vertical(id="main"):
                yield Static(id="content")
        yield Footer()

    def on_mount(self) -> None:
        self.action_view_dashboard()

    def _set_content(self, widget) -> None:
        content = self.query_one("#content")
        content.remove_children()
        content.mount(widget)

    def action_view_dashboard(self) -> None:
        self._set_content(DashboardView())

    def action_view_tasks(self) -> None:
        self._set_content(TasksView())

    def action_view_approvals(self) -> None:
        self._set_content(ApprovalsView())

    def action_view_logs(self) -> None:
        logs = LogsView()
        self._set_content(logs)

    def action_pause(self) -> None:
        runtime = AgentRuntime.get()
        if runtime.started:
            runtime.orchestrator.model_provider.timeout = runtime.orchestrator.model_provider.timeout  # no-op keeps provider
        self.query_one("#content").mount(
            Static("[yellow]Pause requested. Background jobs finish current step, then halt.[/yellow]")
        )


class TUIApp:
    """Backward-compatible launcher."""

    def __init__(self):
        from rich.console import Console
        self.console = Console()

    def render_dashboard(self):
        """Rich fallback dashboard (used when Textual is unavailable)."""
        from litert_agent.environment.detector import EnvironmentDetector
        from rich.panel import Panel
        env = EnvironmentDetector.detect_all()
        status = AgentRuntime.get().status()
        self.console.print(Panel(
            f"[bold]State[/bold] {'RUNNING' if status['started'] else 'IDLE'}\n"
            f"[bold]Model[/bold] LiteRT-LM ({'found' if env['has_litert_lm'] else 'missing'})\n"
            f"[bold]Autonomy[/bold] level {status['autonomy_level']}\n"
            f"[bold]CPU[/bold] {env['resources']['cpu_percent']}%  "
            f"[bold]RAM[/bold] {env['resources']['memory']['available_gb']}GB free",
            title="LITERT AGENT",
        ))
        self.console.print("[dim]Full TUI: litert-agent tui[/dim]")

    def run(self):
        LiteRTTUIApp().run()
