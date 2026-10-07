# Web UI

Start with `litert-agent web` (default http://127.0.0.1:8765).

## Pages
Dashboard, Chat, Agent, Tasks, Scheduler, Workers, Memory, Skills, Tools,
Approvals, Checkpoints, Logs, System, Diagnostics, Settings — all rendered
from one HTML template with live data from the API.

- **Chat**: conversation with the agent on the shared runtime (LiteRT-LM only).
- **Tasks**: create a task and follow its status.
- **Scheduler**: add persisted jobs and run them now.
- **Workers**: logical worker roles (Main, Researcher, Coder, Tester, Reviewer,
  DevOps, Browser) — all powered by the single local LiteRT-LM backend.
- **Diagnostics**: run the built-in self-diagnostics (database, skills, model,
  runtime) and see pass/fail per check.
- **Checkpoints**: inspect and restore checkpoints.

## Live events
A WebSocket connection to `/ws/events` streams `task_started`, `tool_started`,
`tool_completed`, `task_completed`, `approval_required`, `scheduler_event`,
`health` and `log` events into the dashboard event panel in real time.

## API

```
GET  /api/status          GET  /api/health
GET  /api/capabilities    GET  /api/tasks        POST /api/tasks
POST /api/chat
GET  /api/scheduler       POST /api/scheduler    POST /api/scheduler/{id}/run
GET  /api/workers         GET  /api/diagnostics
GET  /api/memory          GET  /api/skills       GET  /api/tools
GET  /api/approvals       POST /api/approvals/{id}/approve
GET  /api/checkpoints     POST /api/checkpoints/{id}/restore
GET  /api/logs            GET  /api/system
GET  /api/settings        PUT  /api/settings
WebSocket /ws/events
```

The UI is dark-first, responsive (sidebar collapses on mobile) and every control
is wired to a real backend endpoint — no fake buttons.
