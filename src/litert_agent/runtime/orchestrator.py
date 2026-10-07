"""Central orchestrator for the Litert-Agent runtime."""

from litert_agent.cognition.executor import Executor
from litert_agent.config import Config
from litert_agent.environment.capabilities import Capabilities
from litert_agent.memory.manager import MemoryManager
from litert_agent.model.litert_cli import LiteRTLMProvider
from litert_agent.recovery.checkpoints import CheckpointManager
from litert_agent.recovery.crash_recovery import CrashRecovery
from litert_agent.runtime.events import EventBus
from litert_agent.runtime.loop import AutonomousLoop
from litert_agent.security.approvals import ApprovalManager
from litert_agent.security.audit import AuditLogger
from litert_agent.security.policy import SecurityPolicy
from litert_agent.self.manager import SelfManager
from litert_agent.tools.archive import ArchiveTool, ProcessTool
from litert_agent.tools.browser import BrowserTool
from litert_agent.tools.filesystem import FilesystemTool
from litert_agent.tools.git import GitTool
from litert_agent.tools.http import HTTPTool
from litert_agent.tools.python import PythonTool
from litert_agent.tools.registry import ToolRegistry
from litert_agent.tools.scheduler import SchedulerTool
from litert_agent.tools.search import SearchTool
from litert_agent.tools.terminal import TerminalTool


class Orchestrator:
    """Wires all subsystems together and owns the shared event bus."""

    def __init__(self, config: Config | None = None, auto_approve: bool = False):
        self.config = config or Config()
        self.capabilities = Capabilities.discover()
        self.model_provider = LiteRTLMProvider(
            cli_path=self.config.model.cli_path,
            model_path=self.config.model.model_path,
            timeout=self.config.model.timeout_seconds,
        )
        self.tool_registry = ToolRegistry()
        self._register_default_tools()

        self.policy = SecurityPolicy(safe_mode=self.config.agent.safe_mode)
        self.audit_logger = AuditLogger(self.config.agent.home_dir / "logs")
        self.approval_manager = ApprovalManager(auto_approve=auto_approve,
                                                 audit_logger=self.audit_logger)
        self.executor = Executor(self.tool_registry, self.policy, self.approval_manager)
        self.memory = MemoryManager(self.config.agent.home_dir / "agent.db")
        self.event_bus = EventBus()
        self.self_manager = SelfManager(self.config, self)

    def _register_default_tools(self):
        for tool in (
            TerminalTool(),
            FilesystemTool(),
            PythonTool(),
            GitTool(),
            HTTPTool(),
            BrowserTool(),
            SearchTool(),
            ArchiveTool(),
            ProcessTool(),
            SchedulerTool(),
        ):
            self.tool_registry.register(tool)

    async def initialize(self):
        await self.model_provider.initialize()
        await self.memory.initialize()
        self.checkpoint_manager = CheckpointManager(self.memory.db_manager)
        self.crash_recovery = CrashRecovery(self.memory.db_manager)

    async def run_task(self, goal: str) -> str:
        loop = AutonomousLoop(
            self.model_provider,
            self.executor,
            self.memory,
            self.event_bus,
            checkpoint_manager=getattr(self, "checkpoint_manager", None),
            audit_logger=self.audit_logger,
            crash_recovery=getattr(self, "crash_recovery", None),
        )
        return await loop.run_task(goal)
