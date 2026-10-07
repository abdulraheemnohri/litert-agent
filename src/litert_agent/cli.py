"""Command-Line Interface (Typer + Rich)."""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from litert_agent.runtime.orchestrator import Orchestrator
from litert_agent.environment.detector import EnvironmentDetector
from litert_agent.environment.capabilities import Capabilities
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.skills.registry import SkillRegistry
from litert_agent.security.policy import SecurityPolicy
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.config import Config

app = typer.Typer(name="litert-agent", help="LiteRT Autonomous Agent CLI")
console = Console()


def _db() -> DatabaseManager:
    cfg = Config()
    db = DatabaseManager(cfg.agent.home_dir / "agent.db")
    with sqlite3.connect(db.db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    return db


def _print(data, as_json: bool):
    if as_json:
        console.print(json.dumps(data, indent=2, default=str))
    else:
        console.print(data)


@app.command()
def run(goal: str = typer.Argument(..., help="Goal or prompt for the autonomous agent")):
    """Run an autonomous task."""

    async def _run():
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        result = await orchestrator.run_task(goal)
        console.print(f"\n[bold blue]Result:[/bold blue]\n{result}")

    asyncio.run(_run())


@app.command()
def chat():
    """Interactive chat loop with the agent."""
    console.print("[bold]LiteRT Agent chat (type 'exit' to quit)[/bold]")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        async def _run():
            orchestrator = Orchestrator()
            await orchestrator.initialize()
            result = await orchestrator.run_task(user_input)
            console.print(f"Agent: {result}")

        asyncio.run(_run())


@app.command()
def status(json_out: bool = typer.Option(False, "--json", help="Output JSON")):
    """Show agent status."""
    cfg = Config()
    data = {
        "agent": cfg.agent.name,
        "status": "IDLE",
        "autonomy_level": cfg.agent.autonomy_level,
        "safe_mode": cfg.agent.safe_mode,
        "offline_mode": cfg.agent.offline_mode,
        "model_provider": "litert-cli",
    }
    if json_out:
        _print(data, True)
    else:
        console.print(Panel.fit(
            f"[bold]{data['agent']}[/bold]\n"
            f"Status: {data['status']}\n"
            f"Autonomy: {data['autonomy_level']}\n"
            f"Model: {data['model_provider']} (LiteRT-LM only)",
            title="Agent Status"))


@app.command()
def health(json_out: bool = typer.Option(False, "--json")):
    """Show runtime health and resources."""
    env = EnvironmentDetector.detect_all()
    data = {
        "os": env["os"],
        "python": env["python_version"],
        "git": env["has_git"],
        "litert_lm": env["has_litert_lm"],
        "playwright": env["has_playwright"],
        "cpu_percent": env["resources"]["cpu_percent"],
        "memory": env["resources"]["memory"],
        "disk": env["resources"]["disk"],
    }
    if json_out:
        _print(data, True)
    else:
        console.print(Panel.fit(
            f"LiteRT-LM: {'[green]OK[/green]' if data['litert_lm'] else '[red]MISSING[/red]'}\n"
            f"CPU: {data['cpu_percent']}%  RAM: {data['memory']['available_gb']}GB free  "
            f"Disk: {data['disk']['free_gb']}GB free",
            title="Health"))


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
def capabilities(json_out: bool = typer.Option(False, "--json")):
    """List agent capabilities."""
    caps = Capabilities.discover()
    if json_out:
        _print(caps.model_dump(), True)
    else:
        console.print(caps.model_dump_json(indent=2))


task_app = typer.Typer(help="Task management")
app.add_typer(task_app, name="task")


@task_app.command("list")
def task_list(json_out: bool = typer.Option(False, "--json")):
    """List tasks."""
    db = _db()
    rows = db.execute_read("SELECT id, description, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 50")
    tasks = [{"id": r[0], "description": r[1], "status": r[2], "created_at": r[3]} for r in rows]
    if json_out:
        _print({"tasks": tasks}, True)
        return
    table = Table(title="Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Description")
    table.add_column("Status")
    table.add_column("Created")
    for t in tasks:
        table.add_row(t["id"][:8], t["description"], t["status"], str(t["created_at"]))
    console.print(table)


@task_app.command("create")
def task_create(goal: str = typer.Argument(...)):
    """Create a pending task."""
    db = _db()
    task_id = str(uuid.uuid4())
    db.execute_write(
        "INSERT INTO tasks (id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (task_id, "User Task", goal, "PENDING", datetime.utcnow().isoformat()),
    )
    console.print(f"[green]Task created:[/green] {task_id}")


memory_app = typer.Typer(help="Memory management")
app.add_typer(memory_app, name="memory")


@memory_app.command("list")
def memory_list(json_out: bool = typer.Option(False, "--json")):
    """List recent memories."""
    db = _db()
    rows = db.execute_read("SELECT id, category, content, created_at FROM memories ORDER BY created_at DESC LIMIT 50")
    memories = [{"id": r[0], "category": r[1], "content": r[2], "created_at": r[3]} for r in rows]
    _print({"memories": memories} if json_out else memories, json_out)


@memory_app.command("search")
def memory_search(query: str = typer.Argument(...)):
    """Search memories."""
    db = _db()
    rows = db.execute_read(
        "SELECT id, category, content FROM memories WHERE content LIKE ? LIMIT 20",
        (f"%{query}%",),
    )
    if not rows:
        console.print("[yellow]No matches.[/yellow]")
        return
    for r in rows:
        console.print(f"[cyan]{r[0][:8]}[/cyan] ({r[1]}) {r[2]}")


@memory_app.command("forget")
def memory_forget(memory_id: str = typer.Argument(...)):
    """Delete a memory by id."""
    db = _db()
    db.execute_write("DELETE FROM memories WHERE id = ?", (memory_id,))
    console.print(f"[green]Forgotten:[/green] {memory_id}")


skill_app = typer.Typer(help="Skill management")
app.add_typer(skill_app, name="skill")


@skill_app.command("list")
def skill_list():
    """List skills."""
    registry = SkillRegistry(_db())
    table = Table(title="Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Enabled")
    table.add_column("Uses")
    for s in registry.list_skills():
        table.add_row(s["name"], s["description"], "yes" if s["enabled"] else "no", str(s["usage_count"]))
    console.print(table)


tool_app = typer.Typer(help="Tool inspection")
app.add_typer(tool_app, name="tool")


@tool_app.command("list")
def tool_list():
    """List registered tools."""
    from litert_agent.tools.registry import ToolRegistry
    from litert_agent.tools.terminal import TerminalTool
    from litert_agent.tools.filesystem import FilesystemTool
    from litert_agent.tools.python import PythonTool
    from litert_agent.tools.git import GitTool
    registry = ToolRegistry()
    for tool in (TerminalTool(), FilesystemTool(), PythonTool(), GitTool()):
        registry.register(tool)
    table = Table(title="Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Permission")
    table.add_column("Description")
    for t in registry.list_tools():
        table.add_row(t["name"], t["permission_level"], t["description"])
    console.print(table)


schedule_app = typer.Typer(help="Scheduler")
app.add_typer(schedule_app, name="schedule")


@schedule_app.command("list")
def schedule_list():
    """List scheduler jobs (in-memory queue of current session)."""
    console.print("[yellow]Scheduler jobs live in the running session; start via 'litert-agent web'.[/yellow]")


security_app = typer.Typer(help="Security")
app.add_typer(security_app, name="security")


@security_app.command("status")
def security_status():
    """Show security policy status."""
    policy = SecurityPolicy()
    console.print(Panel.fit(
        "[green]ALLOW[/green] read operations, safe terminal commands\n"
        "[yellow]ASK[/yellow] package installs, protected paths\n"
        "[red]BLOCK[/red] sudo, rm -rf /, safe-mode writes",
        title="Security Policy"))


checkpoint_app = typer.Typer(help="Checkpoints")
app.add_typer(checkpoint_app, name="checkpoint")


@checkpoint_app.command("list")
def checkpoint_list():
    """List checkpoints."""
    mgr = CheckpointManager(_db())
    cps = mgr.list_checkpoints()
    if not cps:
        console.print("[yellow]No checkpoints.[/yellow]")
        return
    for cp in cps:
        console.print(f"[cyan]{cp['id'][:8]}[/cyan] {cp['description']} ({cp['created_at']})")


@checkpoint_app.command("create")
def checkpoint_create(description: str = typer.Argument(...), task_id: str = typer.Argument("none")):
    """Create a checkpoint."""
    mgr = CheckpointManager(_db())
    cid = mgr.create_checkpoint(task_id, description, {"created_by": "cli"})
    console.print(f"[green]Checkpoint created:[/green] {cid}")


@app.command()
def logs(limit: int = typer.Option(20, help="Number of log entries")):
    """Show recent events log."""
    db = _db()
    rows = db.execute_read(
        "SELECT id, event_type, payload, created_at FROM events ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    if not rows:
        console.print("[yellow]No logs yet.[/yellow]")
        return
    for r in rows:
        console.print(f"[dim]{r[3]}[/dim] [cyan]{r[1]}[/cyan] {r[2]}")


@app.command()
def web(host: str = typer.Option("127.0.0.1"), port: int = typer.Option(8765)):
    """Start the Web UI + API server."""
    import uvicorn
    from litert_agent.api.app import app as api_app
    console.print(f"[bold green]LiteRT Agent Web UI →[/bold green] http://{host}:{port}")
    uvicorn.run(api_app, host=host, port=port, log_level="warning")


@app.command()
def tui():
    """Launch the terminal dashboard UI."""
    from litert_agent.tui.app import TUIApp
    TUIApp().render_dashboard()


@app.command()
def self_test():
    """Run self-tests over core subsystems."""
    results = {}
    db = _db()
    results["database"] = bool(db.execute_read("SELECT name FROM sqlite_master WHERE type='table'"))
    results["memory"] = bool(db.execute_read("SELECT * FROM memories LIMIT 1") is not None)
    results["checkpoints"] = isinstance(CheckpointManager(db).list_checkpoints(), list)
    results["skills"] = len(SkillRegistry(db).list_skills()) > 0
    results["litert_lm"] = EnvironmentDetector.detect_all()["has_litert_lm"]
    for name, ok in results.items():
        console.print(f"[{'green' if ok else 'red'}]{'PASS' if ok else 'FAIL'}[/] {name}")


if __name__ == "__main__":
    app()
