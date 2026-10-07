"""FastAPI application exposing the local agent API and Web UI."""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.resources import ResourceMonitor
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.security.policy import SecurityPolicy
from litert_agent.skills.registry import SkillRegistry
from litert_agent.api.websocket import manager as ws_manager
from litert_agent.api.schemas import TaskCreate, ApprovalDecision, SettingsUpdate
from litert_agent.api.runtime import get_runtime
from litert_agent.web.pages import render_page

app = FastAPI(title="LiteRT Agent API", version="0.1.0")

_STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# --- shared runtime services ---
_config = Config()
_db = DatabaseManager(_config.agent.home_dir / "agent.db")
with sqlite3.connect(_db.db_path) as conn:
    conn.executescript(SCHEMA)
    conn.commit()
_checkpoints = CheckpointManager(_db)
_skills = SkillRegistry(_db)
_policy = SecurityPolicy(safe_mode=_config.agent.safe_mode)

APPROVALS: list[dict] = []


def _resource_snapshot() -> dict:
    return {
        "cpu_percent": ResourceMonitor.get_cpu_usage(),
        "memory": ResourceMonitor.get_memory_info(),
        "disk": ResourceMonitor.get_disk_info(),
    }


PAGES = ("dashboard", "tasks", "memory", "skills", "tools",
         "approvals", "checkpoints", "system", "settings", "logs")


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
    return {"healthy": runtime.health().get("status") != "DEGRADED",
            "model": runtime.health(), "resources": _resource_snapshot()}


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
    # run the task on the shared runtime (background)
    import asyncio
    asyncio.ensure_future(runtime.run_task(payload.goal))
    return {"id": task_id, "status": "RUNNING"}


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
