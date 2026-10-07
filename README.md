# litert-agent

A fully local-first autonomous AI agent built in Python. It plans, executes, verifies, and reflects on tasks using the **LiteRT-LM CLI** as its single and only model backend.

> **Non-negotiable rule:** LiteRT-LM CLI is the only model backend. There is no fallback provider, and none will ever be added. If the model reports an error, the agent stops and escalates — it never silently switches models.

## Highlights

- **Autonomous loop** — plan → audit → checkpoint → execute → verify → critic → reflect → replan, with escalation when stuck.
- **Local-first** — runs entirely on your machine. Memory, checkpoints, and job queues live in SQLite.
- **Rich interfaces** — Typer CLI, Textual TUI, and FastAPI web UI, all sharing one runtime.
- **Safety-first** — tool policies, human approval gates, audit log, checkpoints, and rollback.
- **Crash-resume** — goals are keyed and snapshotted; restart resumes an interrupted task automatically.
- **Skills system** — 10 built-in skills with validation and a registry, plus user-provided skills.
- **Self-X** — bounded self-awareness, diagnostics, resource guards, reflection/lesson capture, maintenance proposals, safe evolution proposals, local snapshots, and a dedicated Web/TUI/CLI self-control surface.

## Subsystems

| Subsystem | Purpose |
| --- | --- |
| `cognition` | Planner, decision, executor (policy + approvals), verifier, critic, reflector, replanner, prioritizer |
| `runtime` | Integrated loop, orchestrator (10 tools), shared `AgentRuntime`, heartbeat supervisor, graceful shutdown |
| `model` | LiteRT-LM provider, CLI adapter, discovery, parser, protocol, session |
| `recovery` | Checkpoints, rollback, healer, crash recovery, replanner compatibility |
| `skills` | Loader, registry, validator, 10 built-in skills |
| `scheduler` | SQLite-backed job queue and worker (claim / execute / release, re-queue on failure) |
| `security` | Tool policy, permissions, approvals, sandbox, secrets, audit |
| `memory` | Working, episodic, semantic, lessons, tasks — all SQLite-backed |
| `agents` | Worker, delegation, roles (logical workers, one LiteRT-LM backend) |
| `environment` | OS/platform detector, resources, capabilities |
| `api` | FastAPI app with shared runtime, `/api/chat`, WebSocket, scheduler and worker endpoints |
| `web` | 15-page web UI: chat, agent, tasks, approvals, scheduler, workers, diagnostics, checkpoints, and more |
| `tui` | Full Textual TUI with rich fallback; scheduler view, approval keys, real pause/resume |
| `tools` | Terminal, filesystem, python, git, browser (Playwright), http, search, archive, scheduler |

## Installation

Requires Python 3.12+.

```bash
git clone https://github.com/abdulraheemnohri/litert-agent.git
cd litert-agent
pip install -e ".[dev]"        # or: make install / scripts/dev_setup.sh
```

Make sure the LiteRT-LM CLI is installed and available on your `PATH`. litert-agent will not run without it — by design.

## Usage

### CLI

```bash
# Run an autonomous task
litert-agent run "Summarize the notes in ./workspace" --profile normal

# Safer, offline variants
litert-agent run "..." --safe
litert-agent run "..." --offline

# Interactive chat
litert-agent chat

# Status, health, doctor
litert-agent status
litert-agent health
litert-agent doctor

# Scheduler (SQLite-backed)
litert-agent schedule list
litert-agent schedule add "Daily report" --cron "0 9 * * *"
litert-agent schedule remove <job-id>
litert-agent schedule run <job-id>

# Approvals
litert-agent security list
litert-agent security decide <request-id> --allow once|session|deny

# Checkpoints and recovery
litert-agent checkpoint list
litert-agent checkpoint restore <checkpoint-id>

# Other commands
litert-agent task list
litert-agent memory show
litert-agent skill list
litert-agent tool list
litert-agent logs
litert-agent web
litert-agent tui --rich
litert-agent self-test
litert-agent self status
litert-agent self diagnose
litert-agent self maintenance
litert-agent self snapshot
litert-agent version
```

### Web UI

```bash
litert-agent web
```

Opens the FastAPI server with a 15-page UI including chat, agent monitoring, tasks, approvals (Allow Once / Allow Session / Deny), scheduler, workers, diagnostics, and checkpoints.

### TUI

```bash
litert-agent tui        # Textual interface
litert-agent tui --rich # Rich fallback
```

Key bindings: `D` dashboard, `T` tasks, `A` approvals (`O` allow once, `Y` allow session, `X` deny), `S` scheduler, `L` logs, `P` pause, `R` resume, `Q` quit.

## Crash Recovery

Every autonomous run is keyed by a goal hash. Progress is checkpointed per iteration; if the process crashes, the next run with the same goal resumes from the last checkpoint and publishes a `task_resumed` event. Snapshots are cleared on completion or hard failure and kept on max-iteration exhaustion.

## Configuration

Configuration lives in `~/.litert-agent/config.toml` with three built-in profiles:

- `low-memory` — constrained machines
- `normal` — balanced defaults
- `performance` — aggressive settings

See `docs/configuration.md` for all options (loop, memory, scheduler, web).

## Documentation

- `docs/architecture.md`
- `docs/installation.md`
- `docs/development.md`
- `docs/cli.md`
- `docs/tui.md`
- `docs/web-ui.md`
- `docs/autonomy.md`
- `docs/memory.md`
- `docs/tools.md`
- `docs/skills.md`
- `docs/scheduler.md`
- `docs/security.md`
- `docs/recovery.md`
- `docs/runtime.md`
- `docs/configuration.md`
- `docs/troubleshooting.md`

## Examples

See `examples/` — quickstart, chat via the Web API, scheduler and approvals demos.

## Testing

```bash
pytest -q        # or: make test / scripts/check.sh
ruff check src tests
```

Unit tests cover cognition, recovery, skills, config, runtime service, chat API, scheduler, approvals, and crash-recovery integration. Integration tests cover the API and the full loop with a scripted fake provider. CI runs lint, tests and a wheel build on every push.

## Contributing

See `CONTRIBUTING.md` and `SECURITY.md`. Conventional commits are required.

## License

MIT — see `LICENSE`.

## Project Status

Work in progress; see `CHANGELOG.md` for the latest changes.
