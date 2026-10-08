import pytest

from litert_agent.self.goal_execution import GoalExecutionController


class Goals:
    def __init__(self):
        self.items = {
            "g1": {"id": "g1", "title": "Test", "description": "do it", "priority": "NORMAL", "status": "PENDING", "progress": 0}
        }

    def list(self, status=None, limit=100):
        return [g for g in self.items.values() if status is None or g["status"] == status][:limit]

    def get(self, goal_id):
        return self.items.get(goal_id)

    def is_ready(self, goal_id):
        return True

    def update(self, goal_id, status=None, progress=None):
        g = self.items[goal_id]
        if status: g["status"] = status
        if progress is not None: g["progress"] = progress
        return g

    def pop_curiosity(self):
        return None


class Orchestrator:
    async def run_task(self, goal):
        return "completed"


class Manager:
    def __init__(self):
        self.goals = Goals()
        self.orchestrator = Orchestrator()


@pytest.mark.asyncio
async def test_execute_ready_goal():
    manager = Manager()
    controller = GoalExecutionController(manager)
    result = await controller.execute("g1")
    assert result["status"] == "COMPLETED"
    assert manager.goals.get("g1")["progress"] == 1.0


def test_ready_goals():
    controller = GoalExecutionController(Manager())
    assert controller.ready_goals(1)[0]["id"] == "g1"
