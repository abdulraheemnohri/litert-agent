"""Planner: goal analysis and step planning."""

from litert_agent.model.protocol import ProtocolMessage


class Planner:
    """Analyzes a goal and produces an ordered plan."""

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
        """Create simple deterministic plan steps from a goal."""
        reqs = self.identify_requirements(goal)
        steps = [f"Inspect environment for goal: {goal}"]
        for req in reqs:
            steps.append(f"Use '{req}' capability to progress the goal")
        steps.append("Verify the outcome matches the goal")
        return self.prioritize_steps(steps)

    def prioritize_steps(self, steps: list[str]) -> list[str]:
        return steps

    def plan_message(self, goal: str) -> ProtocolMessage:
        return ProtocolMessage(
            type="plan",
            content=f"Plan for: {goal}",
            plan_steps=self.create_plan(goal),
        )
