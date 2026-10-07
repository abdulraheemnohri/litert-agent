# Architecture

## Layers

1. **Presentation** — CLI (Typer/Rich), TUI (Rich), Web UI (FastAPI + HTML/JS)
2. **Application** — Orchestrator, AutonomousLoop, EventBus, Scheduler
3. **Cognition** — Planner → DecisionEngine → Executor → Verifier → Critic → Reflector → Replanner
4. **Intelligence** — `LiteRTLMProvider` wrapping the LiteRT-LM CLI (only inference backend)
5. **Tools** — terminal, filesystem, git, python, browser, http, search, archive, scheduler
6. **State** — SQLite memory (working, episodic, semantic, lessons, tasks), checkpoints
7. **Security** — `SecurityPolicy` with ALLOW/ASK/BLOCK permission levels

## Loop

```
OBSERVE → THINK (LiteRT-LM) → DECIDE → POLICY CHECK → EXECUTE TOOL
   → VERIFY → REFLECT → MEMORY → REPLAN or COMPLETE
```

## Events

`EventBus` publishes `task_started`, `tool_started`, `tool_completed`, `task_completed`, `approval_required`, `health`, `log`. The WebSocket manager forwards these to all connected Web UI clients, so CLI, TUI and Web always see the same state.

## Model rule

The provider discovers the LiteRT-LM executable at runtime (`LiteRTCLIDiscovery`), inspects its `--help` output, and never invents command syntax. If the CLI is missing the loop returns an error message — there is no fallback provider by design.
