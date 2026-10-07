# Autonomy

The autonomous loop is the heart of litert-agent. All three interfaces
(CLI, TUI, Web UI) drive the same runtime, so a task started anywhere is
visible everywhere.

## The loop

```
OBSERVE → UNDERSTAND → PLAN → POLICY CHECK → EXECUTE
   ↑                                         │
   └── REPLAN ← REFLECT ← VERIFY ← OBSERVE ──┘
```

Per iteration the loop:

1. **Observes** the environment and previous results.
2. **Plans** the next concrete action (planner).
3. **Checks policy** — every tool call passes the security policy and,
   if required, the human approval gate (allow-once / allow-session / deny).
4. **Executes** exactly one validated tool call (executor).
5. **Verifies** the result against the task's verification criteria (verifier).
6. **Reflects** — the critic checks correctness, completeness, side effects
   and stores lessons (critic, reflector).
7. **Replans** on failure with mandatory retry limits (replanner).

A task is only marked complete when verification succeeds.

## Limits (mandatory)

- `loop.max_iterations` — hard cap per run
- `loop.max_runtime_minutes` — wall-clock cap
- `loop.max_tool_calls` — tool budget
- `loop.max_retries` — per-step retry limit before escalation

When limits are exhausted the loop stops, snapshots are kept, and the
failure is reported honestly — never silently "completed".

## Modes

| Mode | Flag | Behavior |
| --- | --- | --- |
| Safe | `--safe` | destructive commands, network and credentials BLOCKED |
| Offline | `--offline` | external network disabled; local tools remain |
| Autonomous | `--autonomous` | agent plans/executes/retries on its own, still obeying policy, approvals, limits and the kill switch |

## Profiles

`--profile low-memory` shrinks workers, buffers and concurrency.
`normal` is balanced. `performance` raises concurrency within safety limits.

## Kill switch

Ctrl+C (CLI/TUI) or the Web UI Stop button cancels active work safely and
persists state for later crash-resume.
