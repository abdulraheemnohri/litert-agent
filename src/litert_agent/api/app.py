"""FastAPI application exposing the local agent API and Web UI."""

import json
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.resources import ResourceMonitor
from litert_agent.memory.sqlite import DatabaseManager, SCHEMA
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.security.policy import SecurityPolicy
from litert_agent.skills.registry import SkillRegistry
from litert_agent.api.websocket import manager as ws_manager
from litert_agent.api.schemas import TaskCreate, ApprovalDecision, SettingsUpdate
from litert_agent.web.pages import render_page
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="LiteRT Agent API", version="0.1.0")
_STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# --- shared runtime services (singletons) ---
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


# ---------- HTML pages ----------
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
    return {
        "agent": _config.agent.name,
        "status": "IDLE",
        "autonomy_level": _config.agent.autonomy_level,
        "safe_mode": _config.agent.safe_mode,
        "offline_mode": _config.agent.offline_mode,
    }


@app.get("/api/health")
async def health():
    caps = Capabilities.discover()
    return {
        "healthy": True,
        "model_detected": caps.has_litert_lm,
        "resources": _resource_snapshot(),
    }


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
    task_id = str(uuid.uuid4())
    _db.execute_write(
        "INSERT INTO tasks (id, title, description, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (task_id, "User Task", payload.goal, "PENDING", datetime.utcnow().isoformat()),
    )
    await ws_manager.broadcast({"type": "task_started", "payload": {"id": task_id, "goal": payload.goal}})
    return {"id": task_id, "status": "PENDING"}


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
    from litert_agent.tools.registry import ToolRegistry
    from litert_agent.tools.terminal import TerminalTool
    from litert_agent.tools.filesystem import FilesystemTool
    from litert_agent.tools.python import PythonTool
    from litert_agent.tools.git import GitTool
    registry = ToolRegistry()
    for tool in (TerminalTool(), FilesystemTool(), PythonTool(), GitTool()):
        registry.register(tool)
    return {"tools": registry.list_tools()}


@app.get("/api/approvals")
async def list_approvals():
    return {"approvals": APPROVALS}


@app.post("/api/approvals/{approval_id}/approve")
async def approve(approval_id: str, decision: ApprovalDecision):
    for approval in APPROVALS:
        if approval["id"] == approval_id:
            approval["status"] = "DENY" if decision.decision == "deny" else "ALLOW"
            return approval
    return {"error": "not found"}


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
