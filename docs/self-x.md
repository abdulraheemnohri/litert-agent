# Self-X: Goals, Curiosity, Learning

The Self-X subsystem gives the agent direction and improvement without ever
touching its own safety boundaries.

> Self-X tables are namespaced with a `self_x_` prefix (e.g.
> `self_x_goals`, `self_x_curiosity`, `self_x_lessons`) so they never
> collide with the canonical tables created by `memory/sqlite.py` in the
> same shared database.

## Goal manager

Goals persist in the `self_x_goals` SQLite table with the full state machine:

```
IDEA → PENDING → READY → ACTIVE → VERIFYING → COMPLETED
                ↘ WAITING_APPROVAL (high risk, needs human approval)
                ↘ PAUSED / BLOCKED / FAILED / CANCELLED
```

- High-risk goals (`medium`/`high`/`critical`) are created in
  `WAITING_APPROVAL` and cannot run until approved.
- Dependencies block execution until the parent goals are completed.
- `SelfManager` wires goals to real autonomous execution through
  `GoalExecutionController`.

CLI (via `litert-agent-self`):

```bash
litert-agent-self goal create "Add dark mode" --priority HIGH
litert-agent-self goal list
litert-agent-self goal approve <id>
litert-agent-self goal execute-next
litert-agent-self goal pause <id>
```

## Curiosity engine

Generates candidate future goals from observed signals (repeated failures,
tool limitations, research gaps...). Items are scored, deduplicated, ranked
and only become goals when explicitly promoted — promoted goals always start
as `WAITING_APPROVAL`.

```bash
litert-agent-self curiosity
litert-agent-self curiosity-add "Why does inference time vary?" --origin research_gap
```

## Self-learning

Learning is memory-only (never model-weight modification):

```
Experience → Evaluation → Lesson → Confidence → Memory
                     ↓
        Pattern detection → Skill proposal (needs human approval)
```

- A failure pattern repeated 3+ times proposes a diagnostic skill.
- Proposals stay `PROPOSED` — `skill_auto_activation` is false by default;
  a human explicitly accepts or rejects each proposal.

```bash
litert-agent-self learn
litert-agent-self report
```

## Safety contract

Self-improvement may never modify security policy, permissions, approvals,
audit, or the LiteRT-LM-only model rule (A-to-Z spec section 19).
