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

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.resources import ResourceMonitor
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.skills.registry import SkillRegistry
from litert_agent.api.websocket import manager as ws_manager
from litert_agent.api.schemas import TaskCreate, ApprovalDecision, SettingsUpdate
from litert_agent.api.runtime import get_runtime
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
         "diagnostics", "settings")


def _resource_snapshot() -> dict:
    return {
        "cpu_percent": ResourceMonitor.get_cpu_usage(),
        "memory": ResourceMonitor.get_memory_info(),
        "disk": ResourceMonitor.get_disk_info(),
    }


@app.get("/", response_class=HTMLResponse)
async def index():
    return render_page("dashboard")


@app.get("/{page}", response_class=HTMLRespon
se)
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
        "SELECT id, category, content, importance, created_at FROM memories ORDER 
BY created_at DESC LIMIT 100"
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
    runtime = await get_runtime()
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
        model_state = (health.get("model") or {}).get("checks", {}).get("model", "UNKNOWN") \
            if isinstance(health.get("model"), dict) else health.get("model", "UNKNOWN")
        checks["model"] = "READY" if model_state in ("READY", "OK", "PASS") else f"WARN: {model_state}"
        checks["runtime"] = "PASS" if runtime.started else "WARN: not started"
        checks["queue"] = "PASS"
    except Exception as exc:
        checks["runtime"] = f"FAIL: {exc}"

    healthy = all(v == "PASS" or
 v == "READY" for v in checks.values())
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
