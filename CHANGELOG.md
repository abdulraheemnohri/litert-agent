# Changelog

## Unreleased

### Added
- Persisted scheduler jobs (`scheduler_jobs` SQLite table) shared by CLI and Web API
- Real `litert-agent schedule list / add / remove / run` CLI commands
- API: `POST /api/chat`, `GET /api/scheduler`, `POST /api/scheduler`, `POST /api/scheduler/{id}/run`,
  `GET /api/workers`, `GET /api/diagnostics`
- Web UI pages: Chat, Agent, Scheduler, Workers, Diagnostics; task creation and
  checkpoint restore actions
- Tests for scheduler queue registry and job worker lifecycle
- TUI: scheduler view (S), approval decisions (O/Y/X), real pause/resume of worker and heartbeat
- Approvals: Web UI Allow Once / Allow Session / Deny actions with decision history;
  CLI `security decide <id> <allow_once|allow|deny>`
- Tests for the approval manager decision lifecycle
- Crash recovery integrated into the autonomous loop: snapshots keyed by goal,
  resumed automatically after a restart, cleared on completion or hard failure
- CI: GitHub Actions workflow (ruff lint + pytest + wheel build), `.gitignore`, ruff config
- Examples: quickstart, chat via Web API, scheduler and approvals demos
- Community/ops files: SECURITY.md, CODE_OF_CONDUCT.md, Makefile,
  issue templates and pull request template
- Scripts: dev setup and CI-equivalent check scripts
- Docs: autonomy, memory, tools, scheduler and development guides

### Fixed
- Broken `th,td` CSS rule (newline inside `solid`) in the Web UI stylesheet
- Scheduler worker: re-queuing released jobs no longer leaves an un-awaited coroutine
- Committed `__pycache__` bytecode artifacts removed from the repository

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
