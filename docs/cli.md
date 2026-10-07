# CLI Reference

| Command | Purpose |
|---|---|
| `run "goal"` | Run an autonomous task (`--safe --offline --profile --workspace --autonomy`) |
| `chat` | Interactive loop |
| `status [--json]` | Agent status |
| `health [--json]` | Health + resources |
| `doctor` | Self-diagnostics table |
| `capabilities [--json]` | Environment capabilities |
| `version` | Show version |
| `stop` | Graceful shutdown (kill switch) |
| `task list / create` | Task management |
| `memory list / search / forget` | Memory management |
| `skill list` | Skills with usage stats |
| `tool list / test <name>` | Registered tools + smoke tests |
| `security status / approvals / decide` | Policy, pending approvals and decisions |
| `checkpoint list / create` | Checkpoint management |
| `schedule list / add / remove / run` | Persisted scheduler jobs |
| `logs [--limit N]` | Recent events |
| `web [--host --port]` | Web UI + API server |
| `tui [--full/--rich]` | Terminal UI |
| `self-test` | Subsystem pass/fail checks |

All list-style commands support `--json` for scripting.

## Scheduler

Scheduled jobs are persisted in the local SQLite database (`scheduler_jobs` table),
so the CLI and the Web UI show the same jobs.

```bash
litert-agent schedule add nightly-tests "Run the project test suite" --interval "daily"
litert-agent schedule list
litert-agent schedule run <job-id>
litert-agent schedule remove <job-id>
```

`schedule run` executes the job's task description immediately on the shared
runtime (LiteRT-LM only) and marks the job as completed.

## Approvals

When a tool call needs confirmation, it appears as a pending approval. Decide it via CLI or Web UI:

```bash
litert-agent security approvals
litert-agent security decide <approval-id> allow_once   # also: allow (session), deny
```
