"""Worker agent implementation."""

from litert_agent.agents.roles import AgentRole
from litert_agent.model.provider import ModelProvider
from litert_agent.tools.registry import ToolRegistry


class WorkerAgent:
    def __init__(self, role: AgentRole, model_provider: ModelProvider, tool_registry: ToolRegistry):
        self.role = role
        self.model_provider = model_provider
        self.tool_registry = tool_registry

    async def run_task(self, task_description: str) -> dict:
        prompt = f"Role: {self.role.value}\nTask: {task_description}"
        response = await self.model_provider.generate(prompt)
        return {
            "role": self.role.value,
            "status": "COMPLETED",
            "result": response.content or str(response)
        }
