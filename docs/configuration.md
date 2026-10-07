# Configuration

Default file: `~/.litert-agent/config.toml` (created manually; missing file = defaults).

```toml
[agent]
name = "litert-agent"
autonomy_level = 3
safe_mode = false
offline_mode = false
profile = "normal"   # low-memory | normal | performance

[model]
cli_path = "litert-lm"
model_path = ""
timeout_seconds = 120.0
temperature = 0.7
max_tokens = 4096

[loop]
max_iterations = 50
max_retries = 3
max_tool_calls = 100

[memory]
enabled = true
working_max_items = 50

[scheduler]
enabled = true
heartbeat_seconds = 30.0
workers = 1

[web]
host = "127.0.0.1"
port = 8765
```

## Profiles
| Profile | Workers | Heartbeat | Working memory | Max iterations |
|---|---|---|---|---|
| low-memory | 1 | 60s | 20 items | 25 |
| normal | 1 | 30s | 50 items | 50 |
| performance | 4 | 15s | 100 items | 50 |

## CLI overrides
```bash
litert-agent run --safe --profile low-memory "goal"
litert-agent run --offline "goal"
litert-agent run --workspace ./project "goal"
litert-agent chat --safe
```
