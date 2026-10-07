"""FastAPI application exposing the local agent API and Web UI."""

import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.environment.resources import ResourceManager
from litert_agent.memory.sqlite import DatabaseManager
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.security.policy import SecurityPolicy
from litert_agent.skills.registry import SkillRegistry
from litert_agent.api.websocket import manager as ws_manager
from litert_agent.api.schemas import TaskCreate, ApprovalDecision, SettingsUpdate
from litert_agent.web.pages import render_page

STATIC_DIR = Path(__file__).parent.parent / "web" / "static"

app = FastAPI(title="LiteRT Agent API", version="0.1.0")

# --- shared runtime services (lazy singletons) ---
_config = Config()
_db = DatabaseManager(_config.agent.home_dir / "agent.db")
_db.init_db()
_checkpoints = CheckpointManager(_db)
_skills = SkillRegistry(_db)
_resources = ResourceManager()
_policy = SecurityPolicy(safe_mode=_config.agent.safe_mode)

APPROVALS: list[dict] = []


@app.on_event("startup")
async def startup():
    import asyncio
    asyncio.get_event_loop()  # ensure loop exists


# ---------- HTML pages ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    return render_page("dashboard")


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page():
    return render_page("tasks")


@app.get("/memory", response_class=HTMLResponse)
async def memory_page():
    return render_page("memory")


@app.get("/skills", response_class=HTMLResponse)
async def skills_page():
    return render_page("skills")


@app.get("/tools", response_class=HTMLResponse)
async def tools_page():
    return render_page("tools")


@app.get("/approvals", response_class=HTMLResponse)
async def approvals_page():
    return render_page("approvals")


@app.get("/checkpoints", response_class=HTMLResponse)
async def checkpoints_page():
    return render_page("checkpoints")


@app.get("/system", response_class=HTMLResponse)
async def system_page():
    return render_page("system")


@app.get("/settings", response_class=HTMLResponse)
async def settings_page():
    return render_page("settings")


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
    resources = _resources.snapshot()
    return {
        "healthy": True,
        "model_detected": getattr(caps, "has_litert_lm", None) is not False,
        "resources": resources,
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
    import uuid
    from datetime import datetime
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
            approval["status"] = "ALLOW" if decision.decision != "deny" else "DENY"
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
    return {"resources": _resources.snapshot(), "capabilities": Capabilities.discover().model_dump()}


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
