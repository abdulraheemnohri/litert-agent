"""Command-Line Interface (Typer + Rich)."""

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.detector import EnvironmentDetector
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.self.doctor import SelfDoctor
from litert_agent.runtime.service import AgentRuntime
from litert_agent.skills.registry import SkillRegistry
from litert_agent.version import __version__

app = typer.Typer(name="litert-agent", help="LiteRT Autonomous Agent CLI")
console = Console()

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


def _print(data, as_json: bool):
    if as_json:
        console.print(json.dumps(data, indent=2, default=str))
    else:
        console.print(data)


@app.command()
def run(
    goal: str = typer.Argument(..., help="Goal or prompt for the autonomous agent"),
    safe: bool = typer.Option(False, "--safe", help="Safe mode: block destructive operations"),
    offline: bool = typer.Option(False, "--offline", help="Disable network access"),
    profile: str = typer.Option("normal", "--profile", help="low-memory | normal | performance"),
    workspace: str = typer.Option(None, "--workspace", help="Working directory"),
    autonomy: int = typer.Option(None, "--autonomy", help="Autonomy level 1-5"),
):
    """Run an autonomous task on the shared runtime."""

    async def _run():
        cfg = Config.load(overrides={
            "safe_mode": safe, "offline_mode": offline,
            "profile": profile, "workspace": workspace, "autonomy_level": autonomy,
        })
        runtime = AgentRuntime.get(cfg)
        result = await runtime.run_task(goal)
        console.print(f"\n[bold blue]Result:[/bold blue]\n{result}")

    asyncio.run(_run())


@app.command()
def chat(
    safe: bool = typer.Option(False, "--safe"),
    offline: bool = typer.Option(False, "--offline"),
    profile: str = typer.Option("normal", "--profile"),
):
    """Interactive chat loop with the agent."""
    console.print("[bold]LiteRT Agent chat (type 'exit' to quit)[/bold]")

    async def _send(user_input: str) -> str:
        cfg = Config.load(overrides={
            "safe_mode": safe, "offline_mode": offline, "profile": profile,
        })
        runtime = AgentRuntime.get(cfg)
        return await runtime.run_task(user_input)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        result = asyncio.run(_send(user_input))
        console.print(f"Agent: {result}")


@app.command()
def status(json_out: bool = typer.Option(False, "--json", help="Output JSON")):
    """Show agent status (shared runtime state)."""
    runtime = AgentRuntime.get()
    data = runtime.status()
    if json_out:
        _print(data, True)
    else:
        console.print(Panel.fit(
            f"[bold]{data['agent']}[/bold]\n"
            f"Status: {'RUNNING' if data['started'] else 'IDLE'}\n"
            f"Autonomy: {data['autonomy_level']}\n"
            f"Model: {data['model_provider']} (LiteRT-LM only)\n"
            f"Queue: {data['queue_size']}",
            title="Agent Status"))


@app.command()
def health(json_out: bool = typer.Option(False, "--json")):
    """Show runtime health and resources."""
    runtime = AgentRuntime.get()
    health = runtime.health()
    env = EnvironmentDetector.detect_all()
    data = {
        "agent_health": health,
        "os": env["os"],
        "python": env["python_version"],
        "litert_lm": env["has_litert_lm"],
        "cpu_percent": env["resources"]["cpu_percent"],
        "memory": env["resources"]["memory"],
        "disk": env["resources"]["disk"],
    }
    if json_out:
        _print(data, True)
    else:
        console.print(Panel.fit(
            f"Agent: {health['status']}\n"
            f"LiteRT-LM: {'[green]OK[/green]' if data['litert_lm'] else '[red]MISSING[/red]'}\n"
            f"CPU: {data['cpu_percent']}%  RAM: {data['memory']['available_gb']}GB free",
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


@app.command()
def version():
    """Show application version."""
    console.print(f"litert-agent {__version__}")


@app.command()
def stop():
    """Gracefully stop the shared runtime (kill switch)."""

    async def _stop():
        runtime = AgentRuntime.get()
        result = await runtime.shutdown()
        console.print_json(json.dumps(result, indent=2))

    asyncio.run(_stop())
    console.print("[green]Runtime stopped.[/green]")


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
    runtime = AgentRuntime.get()
    table = Table(title="Tools")
    table.add_column("Name", style="cyan")
    table.add_column("Permission")
    table.add_column("Description")
    for t in runtime.orchestrator.tool_registry.list_tools():
        table.add_row(t["name"], t["permission_level"], t["description"])
    console.print(table)


@tool_app.command("test")
def tool_test(name: str = typer.Argument(...)):
    """Run a harmless smoke test against a tool."""

    async def _test():
        registry = AgentRuntime.get().orchestrator.tool_registry
        smoke = {
            "terminal": ("execute", {"command": "echo ok"}),
            "filesystem": ("write", {"path": str(Config.load().agent.home_dir / "tool_test.txt"), "content": "ok"}),
            "python": ("run", {"code": "print('ok')"}),
        }
        if name not in smoke:
            console.print(f"[red]No smoke test defined for '{name}'[/red]")
            return
        action, args = smoke[name]
        result = await registry.execute_tool(name, action, args)
        console.print(f"[{'green' if result.success else 'red'}]{'PASS' if result.success else 'FAIL'}[/] {name}: {result.output or result.error}")

    asyncio.run(_test())


security_app = typer.Typer(help="Security")
app.add_typer(security_app, name="security")


@security_app.command("status")
def security_status():
    """Show security policy status."""
    console.print(Panel.fit(
        "[green]ALLOW[/green] read operations, safe terminal commands\n"
        "[yellow]ASK[/yellow] package installs, protected paths\n"
        "[red]BLOCK[/red] sudo, rm -rf /, safe-mode writes",
        title="Security Policy"))


@security_app.command("approvals")
def security_approvals():
    """Show pending approvals and history."""
    approvals = AgentRuntime.get().orchestrator.approval_manager
    pending = approvals.list_pending()
    if not pending:
        console.print("[green]No pending approvals.[/green]")
        return
    for a in pending:
        console.print(f"[yellow]{a['id'][:8]}[/yellow] {a['tool']}.{a['action']} risk={a['risk']}: {a['reason']}")


@security_app.command("decide")
def security_decide(approval_id: str = typer.Argument(...), decision: str = typer.Argument(...)):
    """Decide a pending approval (allow_once | allow | deny)."""
    valid = {"allow_once", "allow", "deny"}
    if decision not in valid:
        console.print(f"[red]Invalid decision '{decision}'. Use one of: {', '.join(sorted(valid))}[/red]")
        raise typer.Exit(1)
    approvals = AgentRuntime.get().orchestrator.approval_manager
    result = approvals.decide(approval_id, decision)
    if result is None:
        console.print(f"[red]Approval not found: {approval_id}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]Decision recorded:[/green] {approval_id[:8]} → {result['status']}")


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


schedule_app = typer.Typer(help="Scheduler jobs")
app.add_typer(schedule_app, name="schedule")


def _list_scheduler_jobs() -> list[dict]:
    db = _db()
    rows = db.execute_read(
        "SELECT id, name, task_description, cron_or_interval, status, created_at "
        "FROM scheduler_jobs ORDER BY created_at DESC LIMIT 100"
    )
    return [{"id": r[0], "name": r[1], "task_description": r[2],
             "cron_or_interval": r[3], "status": r[4], "created_at": r[5]} for r in rows]


@schedule_app.command("list")
def schedule_list(json_out: bool = typer.Option(False, "--json")):
    """List scheduled jobs."""
    jobs = _list_scheduler_jobs()
    if json_out:
        _print({"jobs": jobs}, True)
        return
    if not jobs:
        console.print("[yellow]No scheduled jobs yet.[/yellow]")
        return
    table = Table(title="Scheduled Jobs")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Task")
    table.add_column("Interval")
    table.add_column("Status")
    table.add_column("Created")
    for j in jobs:
        table.add_row(j["id"][:8], j["name"], j["task_description"],
                      j["cron_or_interval"] or "-", j["status"], str(j["created_at"]))
    console.print(table)


@schedule_app.command("add")
def schedule_add(
    name: str = typer.Argument(..., help="Job name"),
    task: str = typer.Argument(..., help="Task description for the agent"),
    interval: str = typer.Option("", "--interval", help="Cron-like or interval description"),
):
    """Add a scheduled job (persisted in the local database)."""
    db = _db()
    job_id = str(uuid.uuid4())
    db.execute_write(
        "INSERT INTO scheduler_jobs (id, name, task_description, cron_or_interval, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, name, task, interval, "PENDING", datetime.utcnow().isoformat()),
    )
    console.print(f"[green]Job added:[/green] {job_id}")


@schedule_app.command("remove")
def schedule_remove(job_id: str = typer.Argument(...)):
    """Remove a scheduled job."""
    db = _db()
    db.execute_write("DELETE FROM scheduler_jobs WHERE id = ?", (job_id,))
    console.print(f"[green]Job removed:[/green] {job_id}")


@schedule_app.command("run")
def schedule_run(job_id: str = typer.Argument(...)):
    """Run a scheduled job now on the shared runtime."""

    async def _run():
        db = _db()
        rows = db.execute_read("SELECT task_description FROM scheduler_jobs WHERE id = ?", (job_id,))
        if not rows:
            console.print(f"[red]Job not found: {job_id}[/red]")
            return
        db.execute_write("UPDATE scheduler_jobs SET status = ? WHERE id = ?", ("RUNNING", job_id))
        result = await AgentRuntime.get().run_task(rows[0][0])
        db.execute_write("UPDATE scheduler_jobs SET status = ? WHERE id = ?", ("COMPLETED", job_id))
        console.print(f"\n[bold blue]Result:[/bold blue]\n{result}")

    asyncio.run(_run())


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
def web(host: str = typer.Option(None, "--host"), port: int = typer.Option(None, "--port")):
    """Start the Web UI + API server (shared runtime)."""
    import uvicorn

    from litert_agent.api.app import app as api_app

    cfg = Config.load()
    host = host or cfg.web.host
    port = port or cfg.web.port

    async def _boot():
        await AgentRuntime.get(cfg).start()

    asyncio.run(_boot())
    console.print(f"[bold green]LiteRT Agent Web UI →[/bold green] http://{host}:{port}")
    uvicorn.run(api_app, host=host, port=port, log_level="warning")


@app.command()
def tui(full: bool = typer.Option(True, "--full/--rich", help="Full Textual TUI or Rich dashboard")):
    """Launch the terminal UI."""
    from litert_agent.tui.app import TUIApp
    tui_app = TUIApp()
    if full:
        tui_app.run()
    else:
        tui_app.render_dashboard()


self_app = typer.Typer(help="Self-awareness, diagnostics and bounded self-management")
app.add_typer(self_app, name="self")


@self_app.command("status")
def self_status(json_out: bool = typer.Option(False, "--json")):
    """Show the agent's self-awareness snapshot."""
    data = AgentRuntime.get().orchestrator.self_manager.snapshot()
    _print(data, json_out)


@self_app.command("diagnose")
def self_diagnose(json_out: bool = typer.Option(False, "--json")):
    """Run bounded self-diagnostics without modifying the system."""
    data = AgentRuntime.get().orchestrator.self_manager.diagnose()
    _print(data, json_out)


@self_app.command("learn-web")
def self_learn_web(url: str, lesson: str = typer.Option(..., "--lesson"), json_out: bool = typer.Option(False, "--json")):
    """Fetch a web source and store a user-specified lesson as untrusted-source knowledge."""
    runtime = AgentRuntime.get()
    data = asyncio.run(runtime.orchestrator.self_manager.learn_from_web(url, lesson))
    _print(data, json_out)


@self_app.command("cycle")
def self_cycle(json_out: bool = typer.Option(False, "--json")):
    """Run one bounded self-maintenance planning cycle; no destructive action is auto-executed."""
    data = AgentRuntime.get().orchestrator.self_manager.self_cycle()
    _print(data, json_out)


@self_app.command("maintenance")
def self_maintenance(json_out: bool = typer.Option(False, "--json")):
    """Show safe maintenance proposals; no action is executed automatically."""
    data = AgentRuntime.get().orchestrator.self_manager.maintenance_plan()
    _print({"actions": data}, json_out)


@self_app.command("snapshot")
def self_snapshot(path: str = typer.Option(None, "--path"), json_out: bool = typer.Option(False, "--json")):
    """Export a diagnostic/self-awareness snapshot to local storage."""
    manager = AgentRuntime.get().orchestrator.self_manager
    target = manager.export_snapshot(
        Config.load().agent.home_dir / "self" / "snapshot.json" if path is None else __import__("pathlib").Path(path)
    )
    _print({"path": str(target)}, json_out)



research_app = typer.Typer(help="Self-research and provenance")
app.add_typer(research_app, name="research")

@research_app.command("mission")
def research_mission(topic: str, goal: str, url: list[str] = typer.Option(None, "--url")):
    """Create a bounded research mission."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(manager.research_mission(topic, goal, url or []), False)

@research_app.command("collect")
def research_collect(mission_id: str, json_out: bool = typer.Option(False, "--json")):
    """Fetch all sources attached to a research mission; never execute source content."""
    manager = AgentRuntime.get().orchestrator.self_manager
    data = asyncio.run(manager.collect_research(mission_id))
    _print(data, json_out)

@research_app.command("sources")
def research_sources(json_out: bool = typer.Option(False, "--json")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print({"sources": manager.research.list_sources()}, json_out)

@research_app.command("findings")
def research_findings(topic: str = typer.Option("", "--topic"), json_out: bool = typer.Option(False, "--json")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print({"findings": manager.research.list_findings(topic)}, json_out)

@research_app.command("synthesize")
def research_synthesize(mission_id: str, max_sources: int = typer.Option(5, "--max-sources"), json_out: bool = typer.Option(False, "--json")):
    """Synthesize fetched research evidence using LiteRT-LM only."""
    from litert_agent.self.research_synthesis import ResearchSynthesizer
    runtime = AgentRuntime.get()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    engine = ResearchSynthesizer(
        manager.research.db,
        runtime.orchestrator.model_provider,
        manager.research,
    )
    data = asyncio.run(engine.synthesize(mission_id, max_sources))
    _print(data, json_out)

@research_app.command("compare")
def research_compare(topic: str = typer.Option("", "--topic"), json_out: bool = typer.Option(False, "--json")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print({"comparisons": manager.research.compare_claims(topic)}, json_out)

goal_app = typer.Typer(help="Persistent Self-X goals and curiosity")
app.add_typer(goal_app, name="goal")

@goal_app.command("create")
def goal_create(title: str, description: str, priority: str = typer.Option("NORMAL", "--priority"),
                parent: str = typer.Option(None, "--parent"), goal_type: str = typer.Option("user", "--type")):
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(manager.create_goal(title, description, priority, parent, goal_type), False)

@goal_app.command("ready")
def goal_ready(limit: int = typer.Option(3, "--limit")):
    """List pending goals whose dependencies are complete."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(manager.ready_goals(limit), False)

@goal_app.command("execute")
def goal_execute(goal_id: str):
    """Execute one ready Self-X goal through the normal policy-controlled loop."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(asyncio.run(manager.execute_goal(goal_id)), False)

@goal_app.command("execute-next")
def goal_execute_next():
    """Execute the highest-priority ready Self-X goal."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(asyncio.run(manager.execute_next_goal()), False)

@goal_app.command("promote-curiosity")
def goal_promote_curiosity():
    """Promote one curiosity item into a persistent goal."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(manager.promote_curiosity_goal(), False)

@goal_app.command("dependency")
def goal_dependency(goal_id: str, depends_on: str):
    """Add a prerequisite goal dependency."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print(manager.add_goal_dependency(goal_id, depends_on), False)

@goal_app.command("generate-curiosity")
def goal_generate_curiosity(json_out: bool = typer.Option(False, "--json")):
    """Create bounded curiosity items for stale knowledge."""
    manager = AgentRuntime.get().orchestrator.self_manager
    _print({"created": manager.generate_curiosity()}, json_out)

@goal_app.command("list")
def goal_list(status: str = typer.Option(None, "--status"), json_out: bool = typer.Option(False, "--json")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print({"goals": manager.goals.list(status)}, json_out)

@goal_app.command("curiosity")
def goal_curiosity(topic: str, reason: str, priority: str = typer.Option("LOW", "--priority")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print(manager.goals.enqueue_curiosity(topic, reason, priority), False)

@goal_app.command("next-curiosity")
def goal_next_curiosity(json_out: bool = typer.Option(False, "--json")):
    manager = AgentRuntime.get().orchestrator.self_manager
    manager.initialize_learning()
    _print(manager.goals.pop_curiosity(), json_out)

@self_app.command("overview")
def self_overview(json_out: bool = typer.Option(False, "--json")):
    """Show the complete Self-X overview."""
    _print(AgentRuntime.get().orchestrator.self_manager.self_overview(), json_out)

@app.command()
def self_test():
    """Run self-tests over core subsystems."""
    results = {}
    db = _db()
    required = {"research_sources","research_missions","research_mission_urls","research_findings","self_goals","goal_dependencies","curiosity_queue","knowledge_expiry","self_skill_versions","self_skill_quarantine"}
    tables = {r[0] for r in db.execute_read("SELECT name FROM sqlite_master WHERE type='table'")}
    results["database"] = required.issubset(tables)
    results["checkpoints"] = isinstance(CheckpointManager(db).list_checkpoints(), list)
    results["skills"] = len(SkillRegistry(db).list_skills()) > 0
    results["scheduler"] = isinstance(_list_scheduler_jobs(), list)
    results["litert_lm"] = EnvironmentDetector.detect_all()["has_litert_lm"]
    self_report = asyncio.run(SelfDoctor(Config.load(), AgentRuntime.get().orchestrator).run())
    results["self_diagnostics"] = self_report["ok"]
    results["runtime"] = AgentRuntime.get().status()["model_provider"] == "litert-cli"
    for name, ok in results.items():
        console.print(f"[{'green' if ok else 'red'}]{'PASS' if ok else 'FAIL'}[/] {name}")


if __name__ == "__main__":
    app()
