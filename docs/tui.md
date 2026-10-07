# TUI

```bash
litert-agent tui          # full Textual TUI
litert-agent tui --rich   # lightweight Rich dashboard
```

## Screens
| Key | Screen |
|---|---|
| D | Dashboard (state, model, queue) |
| T | Tasks (recent DB tasks) |
| S | Scheduler (persisted jobs + live queue/worker status) |
| A | Approvals (pending high-risk operations) |
| L | Logs (live event stream from the shared event bus) |
| P | Pause (stops worker and heartbeat) |
| R | Resume (restarts worker and heartbeat) |
| Q | Quit |

## Approval decisions
While approvals are pending, decide the first one directly from the TUI:

| Key | Decision |
|---|---|
| O | Allow once |
| Y | Allow session (tool:action approved for this session) |
| X | Deny |

The logs screen subscribes to the shared runtime event bus (`task_started`,
`task_resumed`, `task_completed`, `task_failed`, `tool_started`,
`tool_completed`, `health`, `scheduler_event`), so tool and task events
appear live while a task runs from any interface.

Pause/Resume control the shared runtime's worker and heartbeat: after pause,
the current step finishes and then the runtime halts; resume restarts both
supervisors. The model backend stays LiteRT-LM only in every state.
