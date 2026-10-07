"""Full Textual TUI for LiteRT Agent."""

from __future__ import annotations

import sqlite3

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Log, Static

from litert_agent.config import Config
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.runtime.service import AgentRuntime

SCHEDULER_TABLE = """
CREATE TABLE IF NOT EXISTS scheduler_jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    task_description TEXT NOT NULL,
    cron_or_interval TEXT DEFAULT '',
    status TEXT DEFAULT 'PENDING',
    created_at TEXT NOT NULL
)
"""


def _db() -> DatabaseManager:
    cfg = Config.load()
    db = DatabaseManager(cfg.agent.home_dir / "agent.db")
    with sqlite3.connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.executescript(SCHEDULER_TABLE)
        conn.commit()
    return db


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
            f"  [i]T tasks · S scheduler · A approvals · L logs · P pause · R resume · Q quit[/i]"
        )


class TasksView(Static):
    def on_mount(self) -> None:
        self.update(self.render_tasks())

    def render_tasks(self) -> str:
        db = _db()
        rows = db.execute_read(
            "SELECT id, description, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 20"
        )
        if not rows:
            return "[i]No tasks yet. Start one from the Web UI or CLI.[/i]"
        lines = ["[b]ID         Status      Description[/b]"]
        for r in rows:
            lines.append(f"{r[0][:10]}  {r[2]:<10}  {str(r[1])[:60]}")
        return "\n".join(lines)


class SchedulerView(Static):
    def on_mount(self) -> None:
        self.update(self.render_scheduler())

    def render_scheduler(self) -> str:
        db = _db()
        rows = db.execute_read(
            "SELECT id, name, task_description, cron_or_interval, status, created_at "
            "FROM scheduler_jobs ORDER BY created_at DESC LIMIT 20"
        )
        runtime = AgentRuntime.get()
        header = (
            f"[b]Live queue[/b]: {runtime.status()['queue_size']} pending · "
            f"worker {'running' if runtime.worker.running else 'idle'}\n\n"
        )
        if not rows:
            return header + "[i]No scheduled jobs yet. Add one via CLI or Web UI.[/i]"
        lines = [header + "[b]ID         Status      Interval  Name / Task[/b]"]
        for r in rows:
            lines.append(f"{r[0][:10]}  {r[4]:<10}  {str(r[3] or '-'):<8}  {str(r[1])[:20]} — {str(r[2])[:40]}")
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
                f"[yellow]{a['risk']} RISK[/yellow] {a['tool']}.{a['action']}\n"
                f"  ID: {a['id'][:10]}\n"
                f"  Args: {a['args']}\n"
                f"  Reason: {a['reason']}\n"
                f"  [b]O[/b]=Allow once  [b]Y[/b]=Allow session  [b]X[/b]=Deny (first pending)\n"
            )
        return "\n".join(lines)


class LogsView(Log):
    def on_mount(self) -> None:
        runtime = AgentRuntime.get()
        for event_type in ("task_started", "task_resumed", "task_completed", "task_failed",
                           "tool_started", "tool_completed", "health", "scheduler_event"):
            runtime.event_bus.subscribe(event_type, self._on_event)

    def _on_event(self, event) -> None:
        self.write_line(f"{event.event_type}: {event.payload}")



class SelfXView(Static):
    def on_mount(self) -> None:
        self.update(self.render_self())

    def render_self(self) -> str:
        manager = AgentRuntime.get().orchestrator.self_manager
        manager.initialize_learning()
        d = manager.diagnose()
        goals = manager.goals.list(limit=8)
        missions = manager.research.list_missions(limit=8)
        sources = manager.research.list_sources(limit=8)
        lines = [
            "[b]SELF-X CONTROL CENTER[/b]",
            f"Health: {'OK' if d['ok'] else 'WARN'}",
            f"CPU: {d['resources']['cpu_percent']}%  RAM: {d['resources']['memory_percent']}%  Disk: {d['resources']['disk_percent']}%",
            "",
            "[b]Goals[/b]",
        ]
        lines += [f"  {g['priority']:<10} {g['status']:<10} {g['progress']*100:>5.1f}%  {g['title'][:60]}" for g in goals] or ["  none"]
        lines += ["", "[b]Research Missions[/b]"]
        lines += [f"  {m['status']:<10} {m['topic'][:55]}" for m in missions] or ["  none"]
        lines += ["", f"[b]Sources[/b] {len(sources)} indexed"]
        lines += ["[dim]Self-X never changes model weights, provider identity, or security policy automatically.[/dim]"]
        return "\n".join(lines)

class LiteRTTUIApp(App):
    """LiteRT Agent terminal application."""

    TITLE = "LiteRT Agent"
    CSS = """
    Screen { layout: horizontal; }
    #sidebar { width: 26; border-right: solid $primary; padding: 1; }
    #main { padding: 1 2; }
    """

    BINDINGS = [
        ("d", "view_dashboard", "Dashboard"),
        ("t", "view_tasks", "Tasks"),
        ("s", "view_scheduler", "Scheduler"),
        ("a", "view_approvals", "Approvals"),
        ("l", "view_logs", "Logs"),
        ("e", "view_self", "Self-X"),
        ("o", "decide_allow_once", "Allow once"),
        ("y", "decide_allow_session", "Allow session"),
        ("x", "decide_deny", "Deny"),
        ("p", "pause", "Pause"),
        ("r", "resume", "Resume"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static(
                    "[b]LITERT AGENT[/b]\n\n"
                    " [b]D[/b] Dashboard\n [b]T[/b] Tasks\n [b]S[/b] Scheduler\n [b]A[/b] Approvals\n"
                    " [b]L[/b] Logs\n [b]E[/b] Self-X\n\n"
                    " [b]O/Y/X[/b] Decide approval\n\n"
                    " [b]P[/b] Pause agent\n [b]R[/b] Resume agent\n [b]Q[/b] Quit",
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

    def _notify(self, message: str) -> None:
        self.query_one("#content").mount(Static(message))

    def action_view_dashboard(self) -> None:
        self._set_content(DashboardView())

    def action_view_tasks(self) -> None:
        self._set_content(TasksView())

    def action_view_scheduler(self) -> None:
        self._set_content(SchedulerView())

    def action_view_approvals(self) -> None:
        self._set_content(ApprovalsView())

    def action_view_logs(self) -> None:
        logs = LogsView()
        self._set_content(logs)

    def _decide_first(self, decision: str) -> None:
        approvals = AgentRuntime.get().orchestrator.approval_manager
        pending = approvals.list_pending()
        if not pending:
            self._notify("[green]No pending approvals to decide.[/green]")
            return
        approval = pending[0]
        result = approvals.decide(approval["id"], decision)
        if result is None:
            self._notify(f"[red]Decision failed for {approval['id'][:8]}.[/red]")
        else:
            self._notify(f"[green]Recorded {result['status']} for {approval['tool']}.{approval['action']}.[/green]")
        self.action_view_approvals()

    def action_decide_allow_once(self) -> None:
        self._decide_first("allow_once")

    def action_decide_allow_session(self) -> None:
        self._decide_first("allow")

    def action_decide_deny(self) -> None:
        self._decide_first("deny")

    def action_pause(self) -> None:
        runtime = AgentRuntime.get()
        runtime.worker.stop()
        runtime.heartbeat.stop()
        self._notify("[yellow]Paused: worker and heartbeat stopped. Background job finishes its current step, then halts. Press R to resume.[/yellow]")

    def action_resume(self) -> None:
        runtime = AgentRuntime.get()
        runtime.worker.running = True
        runtime.heartbeat.start()
        self._notify("[green]Resumed: worker and heartbeat running again.[/green]")


class TUIApp:
    """Backward-compatible launcher."""

    def __init__(self):
        from rich.console import Console
        self.console = Console()

    def render_dashboard(self):
        """Rich fallback dashboard (used when Textual is unavailable)."""
        from rich.panel import Panel

        from litert_agent.environment.detector import EnvironmentDetector
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
