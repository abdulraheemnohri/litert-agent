# Troubleshooting

**LiteRT-LM CLI missing** — `litert-agent doctor` shows MISSING. Install LiteRT-LM and ensure `litert-lm` is on PATH. The agent will not fall back to another provider by design.

**Web UI not loading data** — check the browser console; the API must be reachable at the same host/port; WebSocket needs ws:// support.

**Database locked** — only one agent runtime should use `~/.litert-agent/agent.db` at a time.

**Tests failing on imports** — reinstall with `pip install -e ".[dev]"` so the `src/` layout is on the path.

**Permission denied for tool** — check `docs/security.md`; ASK/BLOCK operations require approval or policy changes.
