"""Unit tests for tools subsystem."""


import pytest

from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.tools.python import PythonTool
from litert_agent.tools.registry import ToolRegistry
from litert_agent.tools.terminal import TerminalTool


@pytest.mark.asyncio
async def test_tool_registry():
    registry = ToolRegistry()
    term = TerminalTool()
    fs = FilesystemTool()
    registry.register(term)
    registry.register(fs)

    tools = registry.list_tools()
    assert len(tools) == 2

    res = await registry.execute_tool("terminal", "execute", {"command": "echo hello"})
    assert res.success is True
    assert "hello" in res.output

@pytest.mark.asyncio
async def test_filesystem_tool(tmp_path):
    fs = FilesystemTool()
    test_file = tmp_path / "hello.txt"

    write_res = await fs.execute("write", str(test_file), content="world")
    assert write_res.success is True

    read_res = await fs.execute("read", str(test_file))
    assert read_res.success is True
    assert read_res.output == "world"

@pytest.mark.asyncio
async def test_python_tool():
    py = PythonTool()
    res = await py.execute("run", code="print(2 + 3)")
    assert res.success is True
    assert "5" in res.output.strip()
