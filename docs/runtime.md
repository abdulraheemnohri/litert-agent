# Shared Runtime

## AgentRuntime (runtime/service.py)
A process-wide singleton that owns:
- the `Orchestrator` (tools, policy, approvals, audit, memory, checkpoints)
- the `EventBus` — one stream for CLI, TUI and Web UI
- a `JobQueue` + `JobWorker` for background jobs
- a `Supervisor` and `Heartbeat` publishing health events every 30s
- graceful `ShutdownManager` stop (the CLI `litert-agent stop` kill switch)

## Why shared
All interfaces call `AgentRuntime.get()`, so a task started from the Web UI appears in the CLI `task list`, and events published by the loop stream to every WebSocket client. The API (`api/runtime.py`) binds the runtime event bus to `/ws/events`.

## Offline / safe modes
- offline: `HTTPTool.offline = True` blocks network calls
- safe: `SecurityPolicy(safe_mode=True)` blocks filesystem/terminal writes and destructive commands
