"""HTTP client tool with offline-mode enforcement."""

import httpx
from litert_agent.tools.base import BaseTool, ToolResult


class HTTPTool(BaseTool):
    name = "http"
    description = "Make HTTP requests (GET/POST); blocked in offline mode"

    offline: bool = False

    async def execute(self, action: str = "get", url: str = "", headers: dict | None = None, json_data: dict | None = None, **kwargs) -> ToolResult:
        if not url:
            return ToolResult(success=False, output="", error="URL required")

        if self.offline:
            return ToolResult(success=False, output="", error="Network access disabled: offline mode is active")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if action.lower() == "get":
                    resp = await client.get(url, headers=headers)
                elif action.lower() == "post":
                    resp = await client.post(url, headers=headers, json=json_data)
                else:
                    return ToolResult(success=False, output="", error=f"Unsupported HTTP method: {action}")

                return ToolResult(
                    success=resp.status_code < 400,
                    output=resp.text,
                    error=None if resp.status_code < 400 else f"HTTP {resp.status_code}"
                )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
