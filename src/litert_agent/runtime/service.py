"""Shared agent runtime service used by CLI, TUI and Web UI."""


from litert_agent.config import Config
from litert_agent.runtime.heartbeat import Heartbeat, Supervisor
from litert_agent.runtime.shutdown import ShutdownManager
from litert_agent.scheduler.queue import JobQueue
from litert_agent.scheduler.worker import JobWorker


class AgentRuntime:
    """One shared runtime: orchestrator + heartbeat + scheduler, addressable by every interface."""

    _instance: "AgentRuntime | None" = None

    def __init__(self, config: Config | None = None):
        from litert_agent.runtime.orchestrator import Orchestrator
        self.config = config or Config()
        self.orchestrator = Orchestrator(self.config)
        self.event_bus = self.orchestrator.event_bus
        self.queue = JobQueue()
        self.worker = JobWorker(self.queue, handler=self._handle_job)
        self.supervisor = Supervisor(self.orchestrator.model_provider, self.queue)
        self.heartbeat = Heartbeat(30.0, self.event_bus)
        self.started = False

    @classmethod
    def get(cls, config: Config | None = None) -> "AgentRuntime":
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    async def start(self):
        if self.started:
            return
        await self.orchestrator.initialize()
        self.started = True

    async def run_task(self, goal: str) -> str:
        await self.start()
        return await self.orchestrator.run_task(goal)

    async def _handle_job(self, job):
        await self.start()
        return await self.orchestrator.run_task(job.task_description)

    def status(self) -> dict:
        return {
            "agent": self.config.agent.name,
            "started": self.started,
            "autonomy_level": self.config.agent.autonomy_level,
            "safe_mode": self.config.agent.safe_mode,
            "offline_mode": self.config.agent.offline_mode,
            "model_provider": "litert-cli",
            "queue_size": self.queue.size(),
            "self": self.orchestrator.self_manager.snapshot(),
        }

    def health(self) -> dict:
        return self.supervisor.check_health()

    async def shutdown(self) -> dict:
        self.worker.stop()
        self.heartbeat.stop()
        result = ShutdownManager.shutdown(self.worker, self.heartbeat)
        self.started = False
        return result
