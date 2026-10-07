"""Local search tool: real codebase/filesystem search via grep."""

import asyncio
import shutil
from pathlib import Path

from litert_agent.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    name = "search"
    description = "Search local files/codebase for a query (grep-based)"

    async def execute(self, action: str = "search", query: str = "", path: str = ".", max_results: int = 20, **kwargs) -> ToolResult:
        if action != "search":
            return ToolResult(success=False, output="", error=f"Unknown search action: {action}")
        if not query:
            return ToolResult(success=False, output="", error="No query provided")

        root = Path(path)
        if not root.exists():
            return ToolResult(success=False, output="", error=f"Search path does not exist: {path}")

        grep = shutil.which("grep")
        if grep is None:
            # Pure-python fallback (shallow walk)
            matches: list[str] = []
            for file in sorted(root.rglob("*"))[:2000]:
                if file.is_file() and file.suffix in (".py", ".md", ".txt", ".toml", ".json", ".js", ".ts"):
                    try:
                        for i, line in enumerate(file.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                            if query in line:
                                matches.append(f"{file}:{i}:{line.strip()}")
                                if len(matches) >= max_results:
                                    break
                    except Exception:
                        continue
                if len(matches) >= max_results:
                    break
            if not matches:
                return ToolResult(success=True, output=f"No matches for '{query}' in {root}")
            return ToolResult(success=True, output="\n".join(matches))

        try:
            proc = await asyncio.create_subprocess_exec(
                grep, "-rn", "--include", "*", "-m", str(max_results), query, str(root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            out = stdout.decode("utf-8", errors="replace").strip()
            lines = out.splitlines()[:max_results]
            if not lines:
                return ToolResult(success=True, output=f"No matches for '{query}' in {root}")
            return ToolResult(success=True, output="\n".join(lines))
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))
