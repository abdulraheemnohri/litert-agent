"""Agent state container."""

from pydantic import BaseModel


class AgentState(BaseModel):
    current_task_id: str | None = None
    status: str = "IDLE"
    autonomy_level: int = 3
    iteration_count: int = 0
    max_iterations: int = 50
    is_running: bool = True
