"""FastAPI application exposing the local agent API and Web UI."""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from litert_agent.api.runtime import get_runtime
from litert_agent.api.schemas import ApprovalDecision, SettingsUpdate, TaskCreate
from litert_agent.api.websocket import manager as ws_manager
from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.resources import ResourceMonitor
from litert_agent.memory.sqlite import SCHEMA, DatabaseManager
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.skills.registry import SkillRegistry
from litert_agent.web.pages import render_page

app = FastAPI(title="LiteRT Agent API", version="0.1.0")

_STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# --- shared runtime services ---
_config = Config.load()
_db = DatabaseManager(_config.agent.home_dir / "agent.db")

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

with sqlite3.connect(_db.db_path) as conn:
    conn.executescript(SCHEMA)
    conn.executescript(SCHEDULER_TABLE)
    conn.commit()
_checkpoints = CheckpointManager(_db)
_skills = SkillRegistry(_db)

PAGES = ("dashboard", "chat", "agent", "tasks", "scheduler", "workers", "memory",
         "skills", "tools", "approvals", "checkpoints", "logs", "system",
         "diagnostics", "self", "settings")


def _resource_snapshot() -> dict:
    return {
        "cpu_percent": ResourceMonitor.get_cpu_usage(),
        "memory": ResourceMonitor.get_memory_info(),
        "disk": ResourceMonitor.get_disk_info(),
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    return render_page("dashboard")


@app.get("/{page}", response_class=HTMLResponse)
async def generic_page(page: str):
    if page in PAGES:
        return render_page(page)
    return HTMLResponse("<h1>404 - Page not found</h1>", status_code=404)


# ---------- API ----------
@app.get("/api/status")
async def status():
    runtime = await get_runtime()
    return runtime.status()


@app.get("/api/health")
async def health():
    runtime = await get_runtime()
    health = runtime.health()
    return {"healthy": health.get("status") != "DEGRADED",
            "model": health, "resources": _resource_snapshot()}


@app.get("/api/capabilities")
async def capabilities():
    return Capabilities.discover().model_dump()


@app.get("/api/tasks")
async def list_tasks():
    rows = _db.execute_read(
        "SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 100"
    )
    return {"tasks": [{"id": r[0], "title": r[1], "description": r[2], "status": r[3], "created_at": r[4]} for r in rows]}


@app.post("/api/tasks")
async def create_task(payload: TaskCreate):
    runtime = await get_runtime()
    task_id = str(uuid.uuid4())
    _db.execute_write(
        "INSERT INTO tasks (id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (task_id, "User Task", payload.goal, "PENDING", datetime.utcnow().isoformat()),
    )
    await ws_manager.broadcast({"type": "task_started", "payload": {"id": task_id, "goal": payload.goal}})
    import asyncio
    asyncio.ensure_future(runtime.run_task(payload.goal))
    return {"id": task_id, "status": "RUNNING"}


class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Send a chat message; runs it as a task on the shared runtime."""
    runtime = await get_runtime()
    result = await runtime.run_task(message.message)
    return {"reply": result}


@app.get("/api/memory")
async def list_memory():
    rows = _db.execute_read(
        "SELECT id, category, content, importance, created_at FROM memories ORDER BY created_at DESC LIMIT 100"
    )
    return {"memories": [{"id": r[0], "category": r[1], "content": r[2], "importance": r[3], "created_at": r[4]} for r in rows]}


@app.get("/api/skills")
async def list_skills():
    return {"skills": _skills.list_skills()}


@app.get("/api/tools")
async def list_tools():
    runtime = await get_runtime()
    return {"tools": runtime.orchestrator.tool_registry.list_tools()}


@app.get("/api/approvals")
async def list_approvals():
    runtime = await get_runtime()
    return {"approvals": runtime.orchestrator.approval_manager.list_pending(),
            "history": runtime.orchestrator.approval_manager.list_history()}


@app.post("/api/approvals/{approval_id}/approve")
async def approve(approval_id: str, decision: ApprovalDecision):
    runtime = await get_runtime()
    result = runtime.orchestrator.approval_manager.decide(approval_id, decision.decision)
    return result or {"error": "not found"}


# ---------- Scheduler ----------
@app.get("/api/scheduler")
async def scheduler_jobs():
    """Persisted scheduler jobs (shared with the CLI) plus live queue info."""
    runtime = await get_runtime()
    rows = _db.execute_read(
        "SELECT id, name, task_description, cron_or_interval, status, created_at "
        "FROM scheduler_jobs ORDER BY created_at DESC LIMIT 100"
    )
    jobs = [{"id": r[0], "name": r[1], "task_description": r[2],
             "cron_or_interval": r[3], "status": r[4], "created_at": r[5]} for r in rows]
    return {"jobs": jobs, "queue_size": runtime.queue.size(),
            "worker_running": runtime.worker.running}


class JobCreate(BaseModel):
    name: str
    task_description: str


@app.post("/api/scheduler")
async def scheduler_add(payload: JobCreate):
    job_id = str(uuid.uuid4())
    _db.execute_write(
        "INSERT INTO scheduler_jobs (id, name, task_description, cron_or_interval, status, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, payload.name, payload.task_description, "", "PENDING", datetime.utcnow().isoformat()),
    )
    await ws_manager.broadcast({"type": "scheduler_event",
                               "payload": {"job_id": job_id, "name": payload.name, "event": "added"}})
    return {"id": job_id, "name": payload.name, "status": "PENDING"}


@app.post("/api/scheduler/{job_id}/run")
async def scheduler_run(job_id: str):
    runtime = await get_runtime()
    rows = _db.execute_read("SELECT task_description FROM scheduler_jobs WHERE id = ?", (job_id,))
    if not rows:
        return {"error": "not found"}
    import asyncio
    _db.execute_write("UPDATE scheduler_jobs SET status = ? WHERE id = ?", ("RUNNING", job_id))
    asyncio.ensure_future(runtime.run_task(rows[0][0]))
    await ws_manager.broadcast({"type": "scheduler_event",
                               "payload": {"job_id": job_id, "event": "run_now"}})
    return {"id": job_id, "status": "RUNNING"}


# ---------- Workers ----------
@app.get("/api/workers")
async def workers():
    """Logical worker roles, all powered by the single LiteRT-LM backend."""
    runtime = await get_runtime()
    worker = runtime.worker
    roles = ["Main", "Researcher", "Coder", "Tester", "Reviewer", "DevOps", "Browser"]
    return {"workers": [
        {"role": role,
         "status": "RUNNING" if (worker.running or runtime.started) else "IDLE",
         "completed_jobs": len(worker.completed) if role == "Main" else 0,
         "queue_size": runtime.queue.size()}
        for role in roles
    ], "queue_size": runtime.queue.size()}


# ---------- Diagnostics ----------
@app.get("/api/diagnostics")
async def diagnostics():
    """Lightweight self-test: database, skills, runtime health."""
    checks = {}

    try:
        _db.execute_read("SELECT 1")
        checks["database"] = "PASS"
    except Exception as exc:
        checks["database"] = f"FAIL: {exc}"

    try:
        skills = _skills.list_skills()
        checks["skills"] = "PASS" if skills else "WARN: no skills registered"
    except Exception as exc:
        checks["skills"] = f"FAIL: {exc}"

    try:
        runtime = await get_runtime()
        health = runtime.health()
        model = health.get("model")
        if isinstance(model, dict):
            model_state = (model.get("checks") or {}).get("model", "UNKNOWN")
        else:
            model_state = str(model or "UNKNOWN")
        checks["model"] = "READY" if model_state in ("READY", "OK", "PASS") else f"WARN: {model_state}"
        checks["runtime"] = "PASS" if runtime.started else "WARN: not started"
        checks["queue"] = "PASS"
    except Exception as exc:
        checks["runtime"] = f"FAIL: {exc}"

    healthy = all(v in ("PASS", "READY") for v in checks.values())
    return {"checks": checks, "healthy": healthy}


@app.get("/api/checkpoints")
async def list_checkpoints():
    return {"checkpoints": _checkpoints.list_checkpoints()}


@app.post("/api/checkpoints/{checkpoint_id}/restore")
async def restore_checkpoint(checkpoint_id: str):
    state = _checkpoints.restore_checkpoint(checkpoint_id)
    return {"restored": state is not None, "state": state}


@app.get("/api/logs")
async def logs():
    rows = _db.execute_read(
        "SELECT id, event_type, payload, created_at FROM events ORDER BY created_at DESC LIMIT 200"
    )
    return {"logs": [{"id": r[0], "type": r[1], "payload": r[2], "created_at": r[3]} for r in rows]}




@app.get("/api/self")
async def self_state():
    """Self-awareness snapshot and bounded maintenance proposals."""
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    return manager.snapshot()

@app.get("/api/self/overview")
async def self_overview():
    runtime = await get_runtime()
    return runtime.orchestrator.self_manager.self_overview()

@app.get("/api/self/research")
async def self_research(topic: str = ""):
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    return {
        "missions": manager.research.list_missions(),
        "sources": manager.research.list_sources(),
        "findings": manager.research.list_findings(topic),
        "comparisons": manager.research.compare_claims(topic),
    }

class ResearchMissionCreate(BaseModel):
    topic: str
    goal: str
    urls: list[str] = []

@app.post("/api/self/research")
async def create_research_mission(payload: ResearchMissionCreate):
    runtime = await get_runtime()
    return runtime.orchestrator.self_manager.research_mission(payload.topic, payload.goal, payload.urls)

class ResearchClaimCreate(BaseModel):
    mission_id: str
    topic: str
    url: str
    claim: str
    evidence: str = ""
    confidence: float = 0.5

@app.post("/api/self/research/claim")
async def ingest_research_claim(payload: ResearchClaimCreate):
    runtime = await get_runtime()
    return await runtime.orchestrator.self_manager.research_source(
        payload.mission_id, payload.topic, payload.url, payload.claim, payload.evidence, payload.confidence
    )

@app.post("/api/self/research/{mission_id}/collect")
async def collect_self_research(mission_id: str):
    runtime = await get_runtime()
    return await runtime.orchestrator.self_manager.collect_research(mission_id)

@app.post("/api/self/research/{mission_id}/synthesize")
async def synthesize_self_research(mission_id: str, max_sources: int = 5):
    """Synthesize fetched research evidence using LiteRT-LM only."""
    from litert_agent.self.research_synthesis import ResearchSynthesizer
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    engine = ResearchSynthesizer(
        manager.research.db,
        runtime.orchestrator.model_provider,
        manager.research,
    )
    return await engine.synthesize(mission_id, max_sources)

@app.get("/api/self/research/{mission_id}/summaries")
async def self_research_summaries(mission_id: str):
    from litert_agent.self.research_synthesis import ResearchSynthesizer
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    engine = ResearchSynthesizer(
        manager.research.db,
        runtime.orchestrator.model_provider,
        manager.research,
    )
    return {"summaries": engine.list_summaries(mission_id)}

@app.get("/api/self/goals/{goal_id}/dependencies")
async def self_goal_dependencies(goal_id: str):
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    return {"goal_id": goal_id, "ready": manager.goals.is_ready(goal_id),
            "dependencies": manager.goals.dependencies(goal_id)}

@app.post("/api/self/goals/generate-curiosity")
async def generate_self_curiosity():
    runtime = await get_runtime()
    return {"created": runtime.orchestrator.self_manager.generate_curiosity()}

@app.get("/api/self/goals")
async def self_goals(status: str | None = None):
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    return {"goals": manager.goals.list(status), "curiosity": manager.goals.peek_curiosity()}

class GoalCreate(BaseModel):
    title: str
    description: str
    priority: str = "NORMAL"
    parent_id: str | None = None
    goal_type: str = "user"

@app.post("/api/self/goals")
async def create_self_goal(payload: GoalCreate):
    runtime = await get_runtime()
    return runtime.orchestrator.self_manager.create_goal(
        payload.title, payload.description, payload.priority, payload.parent_id, payload.goal_type
    )

@app.patch("/api/self/goals/{goal_id}")
async def update_self_goal(goal_id: str, status: str | None = None, progress: float | None = None):
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    return manager.goals.update(goal_id, status, progress)

@app.post("/api/self/curiosity")
async def add_curiosity(topic: str, reason: str, priority: str = "LOW"):
    runtime = await get_runtime()
    manager = runtime.orchestrator.self_manager
    manager.initialize_learning()
    return manager.goals.enqueue_curiosity(topic, reason, priority)

@app.get("/api/system")
async def system():
    return {"resources": _resource_snapshot(), "capabilities": Capabilities.discover().model_dump()}


@app.get("/api/settings")
async def get_settings():
    return {"config": _config.model_dump()}


@app.put("/api/settings")
async def update_settings(update: SettingsUpdate):
    section = getattr(_config, update.section, None)
    if section is None or not hasattr(section, "model_dump"):
        return {"error": f"Unknown settings section: {update.section}"}
    for key, value in update.values.items():
        if hasattr(section, key):
            setattr(section, key, value)
    return {"status": "updated"}


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
            except Exception:
                event = {"type": "client_message", "payload": data}
            await ws_manager.broadcast(event)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
