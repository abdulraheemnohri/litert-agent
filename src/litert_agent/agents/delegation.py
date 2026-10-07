"""Agent delegation manager."""

from litert_agent.agents.roles import AgentRole
from litert_agent.agents.worker import WorkerAgent
from litert_agent.model.provider import ModelProvider
from litert_agent.tools.registry import ToolRegistry

class DelegationManager:
    def __init__(self, model_provider: ModelProvider, tool_registry: ToolRegistry):
        self.model_provider = model_provider
        self.tool_registry = tool_registry

    async def delegate(self, role: AgentRole, task_description: str) -> dict:
        worker = WorkerAgent(role, self.model_provider, self.tool_registry)
        return await worker.run_task(task_description)
