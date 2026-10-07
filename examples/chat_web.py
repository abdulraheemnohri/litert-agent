"""Example: chat with the local Web API.

Start the server first:
    litert-agent web

Usage:
    python examples/chat_web.py "What tools do you have?"
"""

import sys

import httpx

BASE = "http://127.0.0.1:8000"


def main() -> None:
    message = " ".join(sys.argv[1:]) or "Hello!"
    response = httpx.post(f"{BASE}/api/chat", json={"message": message}, timeout=120)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
