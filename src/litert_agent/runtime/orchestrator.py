"""Central orchestrator for the Litert-Agent runtime."""

from pathlib import Path
from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.model.litert_cli import LiteRTLMProvider
from litert_agent.tools.registry import ToolRegistry
from litert_agent.tools.terminal import TerminalTool
from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.tools.python import PythonTool
from litert_agent.tools.git import GitTool
from litert_agent.security.policy import SecurityPolicy
from litert_agent.cognition.executor import Executor
from litert_agent.memory.manager import MemoryManager
from litert_agent.runtime.loop import AutonomousLoop
from litert_agent.runtime.events import EventBus

class Orchestrator:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.capabilities = Capabilities.discover()
        self.model_provider = LiteRTLMProvider(
            cli_path=self.config.model.cli_path,
            model_path=self.config.model.model_path,
            timeout=self.config.model.timeout_seconds
        )
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

        self.policy = SecurityPolicy(safe_mode=self.config.agent.safe_mode)
        self.executor = Executor(self.tool_registry, self.policy)
        self.memory = MemoryManager(self.config.agent.home_dir / "agent.db")
        self.event_bus = EventBus()

    def _register_default_tools(self):
        self.tool_registry.register(TerminalTool())
        self.tool_registry.register(FilesystemTool())
        self.tool_registry.register(PythonTool())
        self.tool_registry.register(GitTool())

    async def initialize(self):
        await self.model_provider.initialize()
        await self.memory.initialize()

    async def run_task(self, goal: str) -> str:
        loop = AutonomousLoop(self.model_provider, self.executor, self.memory, self.event_bus)
        return await loop.run_task(goal)
