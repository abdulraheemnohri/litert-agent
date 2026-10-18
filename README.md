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
- **Automatic setup** — Windows PowerShell, Linux/macOS/WSL and Termux launchers create an isolated virtual environment and install Python dependencies from requirements manifests.
- **On-demand runtimes** — services and browser binaries are started/installed only when requested; no blanket installation or boot-time startup of unused runtimes.

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

**Windows (PowerShell):**
```powershell
git clone https://github.com/abdulraheemnohri/litert-agent.git
cd litert-agent
.\scripts\install.ps1
```

**Linux, macOS, WSL, or Termux:**
```sh
git clone https://github.com/abdulraheemnohri/litert-agent.git
cd litert-agent
sh scripts/install.sh
```

Add `--dev` to install test/lint/build dependencies, or `--browser` to install Playwright Chromium. LiteRT-LM CLI must be installed separately for model inference; the installer checks for it but deliberately does not run an unverified OS-specific installer. See [docs/installation.md](docs/installation.md).

## Usage

### CLI

```bash
litert-agent run "Summarize the notes in ./workspace" --profile normal
litert-agent run "..." --safe
litert-agent run "..." --offline
litert-agent chat
litert-agent status
litert-agent health
litert-agent doctor
litert-agent schedule list
litert-agent schedule add "Daily report" --cron "0 9 * * *"
litert-agent security list
litert-agent task list
litert-agent memory show
litert-agent skill list
litert-agent tool list
litert-agent web
litert-agent tui
litert-agent self-test
litert-agent self status
litert-agent version
```

### Web UI

```bash
litert-agent web
```

Starts the FastAPI server with the web UI. It is not automatically started during installation.

### TUI

```bash
litert-agent tui
litert-agent tui --rich
```

## Crash Recovery

Every autonomous run is keyed by a goal hash. Progress is checkpointed per iteration; if the process crashes, the next run with the same goal resumes from the last checkpoint and publishes a `task_resumed` event.

## Configuration

Configuration lives in `~/.litert-agent/config.toml`. See `docs/configuration.md` for profiles and options.

## Documentation

See `docs/` for architecture, installation, CLI, TUI, web UI, autonomy, memory, tools, skills, scheduler, security, recovery, runtime, configuration, and troubleshooting.

## Testing

```bash
python scripts/bootstrap.py --dev
pytest -q
ruff check src tests
```

## Contributing

See `CONTRIBUTING.md` and `SECURITY.md`. Conventional commits are required.

## License

MIT — see `LICENSE`.

## Project Status

Work in progress; see `CHANGELOG.md`.

## Self-X

The bounded self-management subsystem covers diagnostics, learning, research provenance, persistent goals, curiosity and safe skill lifecycle. See [docs/self-x.md](docs/self-x.md).
