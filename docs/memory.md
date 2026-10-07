# Memory

litert-agent's memory is SQLite-backed (default `~/.litert-agent/agent.db`).
No external service is used.

## Memory types

| Type | Purpose |
| --- | --- |
| Working | current context, compressed when large |
| Task | task records and status |
| Episodic | what happened during runs (events, results) |
| Semantic | distilled facts the agent learned |
| Lesson | validated takeaways from reflection (self-learning) |
| Research | question, sources, findings, confidence |

## Self-learning pipeline

```
Task → Result → Reflection → Lesson → Validation → Memory → Future retrieval
```

Lessons are only stored after the critic validates them. The agent never
modifies model weights; learning is memory-only.

## Secrets

Passwords, tokens and private keys are never written to ordinary memory,
logs, the UI, or model context (see `docs/security.md`).
