"""Quickstart: run one fully autonomous task.

Requires the LiteRT-LM CLI on PATH (litert-agent never falls back to
another model provider).

Usage:
    python examples/quickstart.py "Summarize the files in ./workspace"
"""

import asyncio
import sys

from litert_agent.config import load_config
from litert_agent.runtime.orchestrator import Orchestrator


async def main() -> None:
    goal = " ".join(sys.argv[1:]) or "Say hello and describe your capabilities."
    config = load_config("normal")
    orchestrator = Orchestrator(config)
    result = await orchestrator.run(goal)
    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
