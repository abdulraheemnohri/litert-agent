# Development

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

The LiteRT-LM CLI must be on your PATH — litert-agent has no other model
backend by design.

## Everyday commands

```bash
make install    # pip install -e ".[dev]"
make test       # pytest -q
make lint       # ruff check src tests
make format     # ruff format src tests
make build      # python -m build --wheel
make clean
```

Or run the tools directly:

```bash
pytest -q
ruff check src tests
```

## Layout

```
src/litert_agent/
├── cognition/   planner, decision, executor, verifier, critic, reflector, replanner, prioritizer
├── runtime/     loop, orchestrator, events, heartbeat, service, shutdown
├── model/       LiteRT-LM provider, CLI adapter, discovery, parser, protocol, session
├── tools/       terminal, filesystem, python, git, browser, http, search, archive, scheduler
├── memory/      working, episodic, semantic, lessons, tasks, manager (SQLite)
├── security/    policy, permissions, approvals, sandbox, secrets, audit
├── recovery/    checkpoints, rollback, healer, crash_recovery
├── scheduler/   queue, worker, jobs, scheduler
├── skills/      loader, registry, validator, builtin
├── agents/      worker, delegation, roles (logical workers, one LiteRT-LM backend)
├── environment/ detector, platform, resources, capabilities
├── api/         FastAPI app, schemas, websocket
├── tui/         Textual app (rich fallback)
└── web/         pages, static assets
```

## Conventions

- Python 3.12+, typed code, docstrings on public APIs.
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- New features need backend → CLI → TUI → Web → tests coverage where applicable.
- Never add a fallback model provider. LiteRT-LM CLI is the only backend.

## CI

GitHub Actions runs `ruff check`, `pytest` and a wheel build on every push
and pull request (see `.github/workflows/ci.yml`).
