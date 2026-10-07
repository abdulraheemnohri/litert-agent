# Changelog

## 0.1.0 — 2026-10-07

### Added
- Cognition layer: planner, decision engine, executor, verifier, critic, reflector, replanner, prioritizer
- Recovery subsystem: checkpoints, rollback, healer, crash recovery
- Skills subsystem: loader, registry, validator, 10 built-in skills
- Scheduler background worker with claim/execute/release lifecycle
- Local FastAPI: status, health, tasks, memory, skills, tools, approvals, checkpoints, logs, system, settings
- WebSocket event stream (`/ws/events`)
- Modern dark responsive Web UI: dashboard, tasks, memory, skills, tools, approvals, checkpoints, logs, system, settings
- Expanded CLI: chat, task, memory, skill, tool, security, checkpoint, logs, web, tui, self-test with `--json` support
- Rich TUI dashboard
- Tests: cognition, recovery, skills, API integration

### Fixed
- Broken imports in `runtime/loop.py` (cognition modules were missing)
- Async `init_db` usage in recovery tests
- Resource monitor usage in the API layer
