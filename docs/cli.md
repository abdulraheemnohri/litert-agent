# CLI Reference

| Command | Purpose |
|---|---|
| `run "goal"` | Run an autonomous task |
| `chat` | Interactive loop |
| `status [--json]` | Agent status |
| `health [--json]` | Health + resources |
| `doctor` | Self-diagnostics table |
| `capabilities [--json]` | Environment capabilities |
| `task list / create` | Task management |
| `memory list / search / forget` | Memory management |
| `skill list` | Skills with usage stats |
| `tool list` | Registered tools + permissions |
| `security status` | Policy summary |
| `checkpoint list / create` | Checkpoint management |
| `logs [--limit N]` | Recent events |
| `web [--host --port]` | Web UI + API server |
| `tui` | Terminal dashboard |
| `self-test` | Subsystem pass/fail checks |

All list-style commands support `--json` for scripting.
