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
| A | Approvals (pending high-risk operations) |
| L | Logs (live event stream from the shared event bus) |
| P | Pause |
| Q | Quit |

The logs screen subscribes to the shared runtime event bus, so tool and task events appear live while a task runs from any interface.
