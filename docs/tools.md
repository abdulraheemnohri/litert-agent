# Tools

Tools are the agent's hands. Every tool call goes through:

```
Model output → Parser → Validator → Policy → Permission → Approval → Tool
```

Malformed model output or an unapproved call never executes.

## Built-in tools

| Tool | Module | Notes |
| --- | --- | --- |
| Terminal | `tools/terminal.py` | cross-platform shell; structured stdout/stderr/exit_code/duration |
| Filesystem | `tools/filesystem.py` | list/read/write/copy/move/delete; protected paths are policy-controlled |
| Python | `tools/python.py` | run scripts, modules, tests |
| Git | `tools/git.py` | status/diff/log/branch/commit; checkpoints before major changes |
| Browser | `tools/browser.py` | Playwright-driven; no browser AI provider |
| HTTP | `tools/http.py` | network access is permission-controlled |
| Search | `tools/search.py` | real grep-based local search |
| Archive | `tools/archive.py` | zip/tar helpers |
| Scheduler | `tools/scheduler.py` | schedule tool calls |

Process management is covered by the terminal tool; no separate process
tool is registered.

## Inspecting tools

```bash
litert-agent tool list
litert-agent tool inspect terminal
```
