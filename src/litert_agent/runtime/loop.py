"""Main execution loop: OBSERVE -> THINK -> PLAN -> POLICY -> EXECUTE -> VERIFY -> REFLECT -> MEMORY -> REPLAN/COMPLETE."""

import asyncio
from litert_agent.runtime.state import AgentState
from litert_agent.model.provider import ModelProvider
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.cognition.planner import Planner
from litert_agent.cognition.decision import DecisionEngine
from litert_agent.cognition.executor import Executor
from litert_agent.cognition.verifier import Verifier
from litert_agent.cognition.reflector import Reflector
from litert_agent.memory.manager import MemoryManager
from litert_agent.runtime.events import EventBus, AgentEvent

class AutonomousLoop:
    def __init__(
        self,
        model_provider: ModelProvider,
        executor: Executor,
        memory_manager: MemoryManager,
        event_bus: EventBus | None = None
    ):
        self.model_provider = model_provider
        self.executor = executor
        self.memory = memory_manager
        self.planner = Planner()
        self.decision_engine = DecisionEngine()
        self.verifier = Verifier()
        self.reflector = Reflector()
        self.event_bus = event_bus or EventBus()
        self.state = AgentState()

    async def run_task(self, goal: str) -> str:
        self.state.status = "RUNNING"
        self.event_bus.publish(AgentEvent(event_type="task_started", payload={"goal": goal}))

        self.memory.working.add("user", goal)

        task_id = await self.memory.tasks.create_task("Autonomous Goal", goal)
        self.state.current_task_id = task_id

        observation = f"Goal: {goal}"
        exec_results = []

        while self.state.is_running and self.state.iteration_count < self.state.max_iterations:
            self.state.iteration_count += 1

            prompt = f"Observation: {observation}\nTask: {goal}"
            msg: ProtocolMessage = await self.model_provider.generate(prompt)

            decision = self.decision_engine.decide(msg)

            if decision == "COMPLETE_TASK":
                await self.memory.tasks.update_task_status(task_id, "COMPLETED", msg.content)
                self.event_bus.publish(AgentEvent(event_type="task_completed", payload={"task_id": task_id, "result": msg.content}))
                return msg.content or "Task completed successfully."

            elif decision == "EXECUTE_TOOL":
                tool_name = msg.tool or "terminal"
                action = msg.action or "execute"
                args = msg.arguments

                self.event_bus.publish(AgentEvent(event_type="tool_started", payload={"tool": tool_name, "action": action}))
                tool_res = await self.executor.execute_action(tool_name, action, args)

                is_valid = self.verifier.verify_action(tool_res)
                observation = tool_res.output if is_valid else f"Tool error: {tool_res.error}"
                exec_results.append(observation)

                if is_valid:
                    await self.memory.episodic.record_episode("execution", f"Tool {tool_name} output: {tool_res.output[:100]}")
                else:
                    await self.memory.lessons.add_lesson("tool_failure", f"Tool {tool_name} failed with {tool_res.error}")

            elif decision == "HANDLE_ERROR":
                observation = f"Error encountered: {msg.content}"

            await asyncio.sleep(0.01)

        await self.memory.tasks.update_task_status(task_id, "FAILED", "Max iterations reached")
        return "Task stopped: Max iterations reached."
