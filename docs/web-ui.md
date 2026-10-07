# Web UI

Start with `litert-agent web` (default http://127.0.0.1:8765).

## Pages
Dashboard, Tasks, Memory, Skills, Tools, Approvals, Checkpoints, Logs, System, Settings — all rendered from one HTML template with live data from the API.

## Live events
A WebSocket connection to `/ws/events` streams `task_started`, `tool_started`, `tool_completed`, `task_completed`, `approval_required`, `health` and `log` events into the dashboard event panel in real time.

## API

```
GET  /api/status        GET  /api/health
GET  /api/capabilities  GET  /api/tasks      POST /api/tasks
GET  /api/memory        GET  /api/skills     GET  /api/tools
GET  /api/approvals     POST /api/approvals/{id}/approve
GET  /api/checkpoints   POST /api/checkpoints/{id}/restore
GET  /api/logs          GET  /api/system
GET  /api/settings      PUT  /api/settings
WS   /ws/events
```
