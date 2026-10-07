"""Main execution loop: OBSERVE -> THINK -> PLAN -> POLICY -> EXECUTE -> VERIFY -> REFLECT -> MEMORY -> REPLAN/COMPLETE."""

import asyncio
import hashlib

from litert_agent.cognition.critic import Critic
from litert_agent.cognition.decision import DecisionEngine
from litert_agent.cognition.executor import Executor
from litert_agent.cognition.planner import Planner
from litert_agent.cognition.reflector import Reflector
from litert_agent.cognition.replanner import Replanner
from litert_agent.cognition.verifier import Verifier
from litert_agent.memory.manager import MemoryManager
from litert_agent.model.protocol import ProtocolMessage
from litert_agent.model.provider import ModelProvider
from litert_agent.runtime.events import AgentEvent, EventBus
from litert_agent.runtime.state import AgentState
from litert_agent.tools.base import ToolResult


class AutonomousLoop:
    """Cognition-integrated autonomous task loop with crash-resume support."""

    def __init__(
        self,
        model_provider: ModelProvider,
        executor: Executor,
        memory_manager: MemoryManager,
        event_bus: EventBus | None = None,
        checkpoint_manager=None,
        audit_logger=None,
        crash_recovery=None,
        max_retries: int = 3,
    ):
        self.model_provider = model_provider
        self.executor = executor
        self.memory = memory_manager
        self.planner = Planner()
        self.decision_engine = DecisionEngine()
        self.verifier = Verifier()
        self.critic = Critic()
        self.reflector = Reflector()
        self.replanner = Replanner(max_retries=max_retries)
        self.event_bus = event_bus or EventBus()
        self.checkpoint_manager = checkpoint_manager
        self.audit_logger = audit_logger
        self.crash_recovery = crash_recovery
        self.self_manager = None
        self.state = AgentState()

    def attach_self_manager(self, manager) -> None:
        self.self_manager = manager

    def orchestrator_self_diagnostics(self):
        if self.self_manager is None:
            return None
        return self.self_manager.diagnose()

    def _audit(self, event_type: str, tool: str, args: dict, result: str, permission: str = "ALLOW"):
        if self.audit_logger is not None:
            try:
                self.audit_logger.log(event_type, tool, args, result, permission)
            except Exception:
                pass

    @staticmethod
    def goal_key(goal: str) -> str:
        """Stable snapshot key so a crashed run can be resumed by goal."""
        return hashlib.sha1(goal.encode("utf-8")).hexdigest()[:16]

    def _persist_progress(self, goal_key: str, observation: str, plan_steps: list[str]):
        if self.crash_recovery is not None:
            try:
                self.crash_recovery.persist_state(
                    goal_key, observation[:200], plan_steps, self.state.iteration_count
                )
            except Exception:
                pass

    def _clear_progress(self, goal_key: str):
        if self.crash_recovery is not None:
            try:
                self.crash_recovery.clear_state(goal_key)
            except Exception:
                pass

    async def run_task(self, goal: str) -> str:
        self.state.status = "RUNNING"
        self_report = self.orchestrator_self_diagnostics()
        self.event_bus.publish(AgentEvent(event_type="task_started", payload={"goal": goal}))

        self.memory.working.add("user", goal)

        goal_key = self.goal_key(goal)
        resumed = None
        if self.crash_recovery is not None:
            try:
                resumed = self.crash_recovery.load_state(goal_key)
            except Exception:
                resumed = None

        if resumed:
            # --- RESUME from crash snapshot ---
            plan_steps = resumed.get("plan") or []
            observation = "Resuming after restart: " + str(resumed.get("current_step") or goal)
            self.state.iteration_count = int(resumed.get("iteration") or 0)
            self.event_bus.publish(AgentEvent(event_type="task_resumed", payload={
                "goal_key": goal_key, "iteration": self.state.iteration_count}))
            self._audit("resume", "crash_recovery", {"goal": goal},
                        f"resumed at iteration {self.state.iteration_count}", "ALLOW")
        else:
            # --- PLAN ---
            plan_msg = self.planner.plan_message(goal)
            plan_steps = plan_msg.plan_steps
            observation = "Goal: " + goal

        self.event_bus.publish(AgentEvent(event_type="plan_created", payload={"steps": plan_steps}))
        self._audit("plan", "planner", {"goal": goal}, " | ".join(plan_steps), "ALLOW")

        task_id = await self.memory.tasks.create_task("Autonomous Goal", goal)
        self.state.current_task_id = task_id
        if self.checkpoint_manager is not None:
            self.checkpoint_manager.create_checkpoint(task_id, "task-start", {"goal": goal, "plan": plan_steps})

        exec_results: list[ToolResult] = []
        failures = 0

        while self.state.is_running and self.state.iteration_count < self.state.max_iterations:
            self.state.iteration_count += 1
            if self.self_manager is not None:
                resources = self.self_manager.resources()
                if resources["memory_percent"] >= 95 or resources["disk_percent"] >= 99:
                    observation = f"Resource guard triggered: {resources}"
                    self._persist_progress(goal_key, observation, plan_steps)
                    self.state.status = "PAUSED"
                    return "Task paused by resource safety guard; free resources and resume."

            prompt = f"Observation: {observation}\nTask: {goal}\nRemaining plan: {plan_steps}"
            msg: ProtocolMessage = await self.model_provider.generate(prompt)

            if msg.type == "error" and "LiteRT-LM" in msg.content:
                await self.memory.tasks.update_task_status(task_id, "FAILED", msg.content)
                self._audit("model_error", "litert-cli", {}, msg.content, "BLOCK")
                self._persist_progress(goal_key, msg.content, plan_steps)
                self.state.status = "IDLE"
                return f"Task failed: {msg.content}"

            decision = self.decision_engine.decide(msg)

            if decision == "COMPLETE_TASK":
                review = self.critic.review(goal, exec_results)
                if review["verdict"] == "FAIL" and self.state.iteration_count < self.state.max_iterations:
                    observation = "Critic rejected completion: requirements not met. Continue."
                    continue
                lesson = self.reflector.reflect(
                    goal,
                    [{"success": r.success, "tool": "tool", "output": r.output, "error": r.error} for r in exec_results],
                    review["verdict"] == "PASS",
                )
                await self.memory.lessons.add_lesson("task_outcome", lesson)
                if self.self_manager is not None:
                    self.self_manager.reflect(task_id, True, msg.content or "completed", lesson)
                await self.memory.tasks.update_task_status(task_id, "COMPLETED", msg.content)
                self.event_bus.publish(AgentEvent(event_type="task_completed", payload={"task_id": task_id, "result": msg.content}))
                self._audit("task_completed", "loop", {"goal": goal}, msg.content or "", "ALLOW")
                self._clear_progress(goal_key)
                self.state.status = "IDLE"
                return msg.content or "Task completed successfully."

            elif decision == "EXECUTE_TOOL":
                tool_name = msg.tool or "terminal"
                action = msg.action or "execute"
                args = msg.arguments or {}

                self.event_bus.publish(AgentEvent(event_type="tool_started", payload={"tool": tool_name, "action": action}))
                self._audit("tool_call", tool_name, args, "requested", "ASK")

                if self.checkpoint_manager is not None and tool_name in ("filesystem", "terminal", "git"):
                    self.checkpoint_manager.create_checkpoint(task_id, f"before:{tool_name}.{action}", {"step": action})

                tool_res = await self.executor.execute_action(tool_name, action, args)
                exec_results.append(tool_res)

                self.event_bus.publish(AgentEvent(event_type="tool_completed", payload={
                    "tool": tool_name, "action": action, "success": tool_res.success}))
                self._audit("tool_result", tool_name, args, tool_res.output[:200], "ALLOW" if tool_res.success else "BLOCK")

                is_valid = self.verifier.verify_action(tool_res)
                if is_valid:
                    observation = tool_res.output
                    await self.memory.episodic.record_episode("execution", f"Tool {tool_name} output: {tool_res.output[:100]}")
                    plan_steps = [s for s in plan_steps if tool_name not in s.lower()] or plan_steps
                else:
                    failures += 1
                    observation = f"Tool error: {tool_res.error}"
                    await self.memory.lessons.add_lesson("tool_failure", f"Tool {tool_name} failed with {tool_res.error}")
                    outcome = self.replanner.retry_or_escalate(f"{tool_name}.{action}", tool_res.error or "")
                    if outcome == "ESCALATE":
                        await self.memory.tasks.update_task_status(task_id, "FAILED", f"Escalated after retries: {tool_res.error}")
                        self.event_bus.publish(AgentEvent(event_type="task_failed", payload={"task_id": task_id, "error": tool_res.error}))
                        self._clear_progress(goal_key)
                        self.state.status = "IDLE"
                        return f"Task failed: {tool_res.error}"
                    plan_steps = self.replanner.update_plan(plan_steps, f"{tool_name}.{action}")

            elif decision == "HANDLE_ERROR":
                observation = f"Error encountered: {msg.content}"

            self._persist_progress(goal_key, observation, plan_steps)
            await asyncio.sleep(0.01)

        # max iterations reached: keep the snapshot so a later run can resume
        self._persist_progress(goal_key, observation, plan_steps)
        await self.memory.tasks.update_task_status(task_id, "FAILED", "Max iterations reached")
        if self.self_manager is not None:
            self.self_manager.reflect(task_id, False, "Max iterations reached", "Bound iteration limits before escalating.")
        self.event_bus.publish(AgentEvent(event_type="task_failed", payload={"task_id": task_id, "error": "max_iterations"}))
        self.state.status = "IDLE"
        return "Task stopped: Max iterations reached."
