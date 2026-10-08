"""Durable runtime state for bounded autonomous task execution."""

from typing import Literal

from pydantic import BaseModel, Field

TaskStatus = Literal[
    "IDLE", "RUNNING", "WAITING_APPROVAL", "PAUSED",
    "VERIFYING", "COMPLETED", "FAILED", "CANCELLED",
]


class StepState(BaseModel):
    step_id: str
    status: Literal["PENDING", "ACTIVE", "WAITING_APPROVAL", "VERIFYING", "COMPLETED", "FAILED", "SKIPPED"] = "PENDING"
    attempts: int = 0
    last_error: str | None = None
    verification_failures: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    current_task_id: str | None = None
    status: TaskStatus = "IDLE"
    autonomy_level: int = 3
    iteration_count: int = 0
    max_iterations: int = 50
    is_running: bool = True
    active_step_id: str | None = None
    waiting_reason: str | None = None
    steps: list[StepState] = Field(default_factory=list)

    def step(self, step_id: str) -> StepState:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        step = StepState(step_id=step_id)
        self.steps.append(step)
        return step

    def snapshot(self) -> dict:
        return self.model_dump(mode="json")
