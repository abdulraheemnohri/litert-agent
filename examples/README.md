# Examples

Runnable examples for litert-agent.

| File | What it shows |
| --- | --- |
| `quickstart.py` | Run a fully autonomous task with the default profile |
| `chat_web.py` | Talk to the local Web API (`POST /api/chat`) |
| `scheduler_demo.py` | Add, list, and trigger scheduler jobs |
| `approvals_demo.py` | List pending approvals and decide via the API |

First install the package and make sure the LiteRT-LM CLI is on your PATH:

```bash
pip install -e .
```

All examples are local-only: the agent uses LiteRT-LM as its single model backend
and never falls back to any other provider.
