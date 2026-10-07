# LiteRT Agent

A **fully local-first autonomous AI agent** powered by the **LiteRT-LM CLI** as its *only* AI inference backend. No cloud LLMs, no fallback providers — ever.

## Interfaces

| Interface | Command |
|---|---|
| CLI | `litert-agent run "goal"` |
| Chat | `litert-agent chat` |
| TUI Dashboard | `litert-agent tui` |
| Web UI + API | `litert-agent web` (http://127.0.0.1:8765) |

All interfaces share one agent runtime, SQLite memory and event bus.

## Architecture

```
CLI / TUI / Web UI
        │
   Agent API Core
        │
  ┌─────┼─────┐
Cognition Memory Security
  └─────┼─────┘
  LiteRT-LM Provider
        │
   LiteRT-LM CLI   ← the only model backend
        │
  Tools (terminal, filesystem, git, python, browser, http)
```

## Subsystems

- **Cognition** — planner, decision engine, executor, verifier, critic, reflector, replanner, prioritizer
- **Model** — LiteRT-LM CLI discovery, provider, protocol parser (never invents CLI commands; probes `--help` at runtime)
- **Memory** — SQLite-backed working / episodic / semantic / lessons / tasks
- **Security** — policy engine (ALLOW / ASK / BLOCK), safe mode, protected paths
- **Recovery** — checkpoints, rollback, self-healing, crash recovery
- **Skills** — 10 built-in skills with validator + usage tracking registry
- **Scheduler** — job queue, background worker, delegation to role workers
- **API/Web** — FastAPI + WebSocket live events, modern dark responsive Web UI

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
litert-agent run "Create a Python app that monitors my system"
litert-agent doctor          # self-diagnostics
litert-agent status --json   # scripting-friendly output
litert-agent task list
litert-agent memory search "lesson"
litert-agent checkpoint list
litert-agent self-test
litert-agent web             # full console UI
```

## Tests

```bash
pytest
```

## Non-negotiable rule

If LiteRT-LM is unavailable the agent reports an error — it never silently switches to another provider. See the [master specification](docs/architecture.md).

## License

MIT
