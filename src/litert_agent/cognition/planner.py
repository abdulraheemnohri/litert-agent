"""Structured planning V2 for bounded autonomous execution.

The planner records concise action metadata for orchestration and policy.
It does not store or expose model chain-of-thought.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Risk = Literal["low", "medium", "high", "critical"]


class PlanStep(BaseModel):
    id: str
    description: str
    capability: str = "terminal"
    depends_on: list[str] = Field(default_factory=list)
    risk: Risk = "low"
    estimated_cost: float = 1.0
    estimated_seconds: float = 1.0
    requires_approval: bool = False

    @field_validator("id", "description")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class PlanProposal(BaseModel):
    goal: str
    steps: list[PlanStep] = Field(default_factory=list)
    overall_risk: Risk = "low"
    estimated_cost: float = 0.0
    estimated_seconds: float = 0.0
    requires_approval: bool = False
    blockers: list[str] = Field(default_factory=list)

    @field_validator("goal")
    @classmethod
    def valid_goal(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("goal must not be empty")
        return value


class PlanValidationError(ValueError):
    pass


class DependencyResolver:
    """Validate dependencies and return deterministic topological order."""

    @staticmethod
    def order(steps: list[PlanStep]) -> list[PlanStep]:
        by_id = {step.id: step for step in steps}
        if len(by_id) != len(steps):
            raise PlanValidationError("plan contains duplicate step IDs")

        missing = {
            dep for step in steps for dep in step.depends_on if dep not in by_id
        }
        if missing:
            raise PlanValidationError(
                f"plan contains missing dependencies: {sorted(missing)}"
            )

        state: dict[str, int] = {}
        ordered: list[PlanStep] = []

        def visit(step_id: str) -> None:
            mark = state.get(step_id, 0)
            if mark == 1:
                raise PlanValidationError("plan contains a dependency cycle")
            if mark == 2:
                return
            state[step_id] = 1
            for dep in by_id[step_id].depends_on:
                visit(dep)
            state[step_id] = 2
            ordered.append(by_id[step_id])

        for step in steps:
            visit(step.id)
        return ordered


class RiskEstimator:
    """Conservative pre-policy risk estimate."""

    HIGH_RISK = re.compile(
        r"\b(?:sudo|shutdown|reboot|poweroff|mkfs|fdisk|parted|push|delete|remove|credential|secret)\b",
        re.IGNORECASE,
    )
    MEDIUM_RISK = re.compile(
        r"\b(?:write|create|install|update|modify|execute|run|download|network|http|git)\b",
        re.IGNORECASE,
    )

    @classmethod
    def estimate(cls, description: str, capability: str) -> Risk:
        text = f"{capability} {description}"
        if cls.HIGH_RISK.search(text):
            return "high"
        if cls.MEDIUM_RISK.search(text):
            return "medium"
        return "low"


class Planner:
    """Creates deterministic baseline plans and validates structured proposals."""

    def analyze_goal(self, goal: str) -> dict:
        words = goal.split()
        return {
            "goal": goal,
            "complexity": "low" if len(words) < 8 else ("medium" if len(words) < 20 else "high"),
            "requirements": self.identify_requirements(goal),
        }

    def identify_requirements(self, goal: str) -> list[str]:
        requirements: list[str] = []
        lowered = goal.lower()
        if any(k in lowered for k in ("file", "create", "write", "app", "project")):
            requirements.append("filesystem")
        if any(k in lowered for k in ("run", "test", "execute", "build", "install")):
            requirements.append("terminal")
        if any(k in lowered for k in ("git", "commit", "push", "branch")):
            requirements.append("git")
        if any(k in lowered for k in ("http", "url", "web", "download", "fetch")):
            requirements.append("http")
        return requirements or ["terminal"]

    def create_plan(self, goal: str) -> list[str]:
        return [step.description for step in self.create_plan_proposal(goal).steps]

    def create_plan_proposal(self, goal: str) -> PlanProposal:
        if not goal.strip():
            raise ValueError("goal must not be empty")

        requirements = self.identify_requirements(goal)
        steps = [
            PlanStep(
                id="inspect",
                description=f"Inspect environment for goal: {goal}",
                capability="terminal",
            )
        ]
        previous = "inspect"
        for index, requirement in enumerate(requirements, start=1):
            description = f"Use '{requirement}' capability to progress the goal"
            risk = RiskEstimator.estimate(description, requirement)
            steps.append(
                PlanStep(
                    id=f"capability-{index}",
                    description=description,
                    capability=requirement,
                    depends_on=[previous],
                    risk=risk,
                    requires_approval=risk in {"high", "critical"},
                )
            )
            previous = f"capability-{index}"

        steps.append(
            PlanStep(
                id="verify",
                description="Verify the outcome matches the goal",
                capability="verification",
                depends_on=[previous],
            )
        )
        return self.validate_plan(PlanProposal(goal=goal, steps=steps))

    def validate_plan(self, proposal: PlanProposal) -> PlanProposal:
        ordered = DependencyResolver.order(proposal.steps)
        overall: Risk = "low"
        for step in ordered:
            if step.risk == "critical":
                overall = "critical"
                break
            if step.risk == "high":
                overall = "high"
            elif step.risk == "medium" and overall == "low":
                overall = "medium"

        return proposal.model_copy(
            update={
                "steps": ordered,
                "overall_risk": overall,
                "estimated_cost": sum(max(0.0, s.estimated_cost) for s in ordered),
                "estimated_seconds": sum(max(0.0, s.estimated_seconds) for s in ordered),
                "requires_approval": any(s.requires_approval for s in ordered),
            }
        )

    def replan(self, proposal: PlanProposal, failed_step: str, reason: str) -> PlanProposal:
        """Create bounded recovery work; this never changes security policy."""
        recovery = PlanStep(
            id=f"recovery-{len(proposal.steps) + 1}",
            description=f"Recover from failed step '{failed_step}': {reason}",
            capability="recovery",
            risk="medium",
        )
        return self.validate_plan(
            proposal.model_copy(update={"steps": [*proposal.steps, recovery]})
        )

    def prioritize_steps(self, steps: list[str]) -> list[str]:
        return steps

    def plan_message(self, goal: str):
        from litert_agent.model.protocol import ProtocolMessage

        return ProtocolMessage(
            type="plan",
            content=f"Plan for: {goal}",
            plan_steps=self.create_plan(goal),
        )
