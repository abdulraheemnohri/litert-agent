"""Decision engine: converts validated protocol messages into safe loop decisions."""

from litert_agent.model.protocol import ProtocolMessage


class DecisionEngine:
    """Maps parsed model messages to deterministic execution states."""

    def decide(self, msg: ProtocolMessage) -> str:
        if msg.type == "final":
            return "COMPLETE_TASK"
        if msg.type == "tool_call" and msg.tool:
            return "EXECUTE_TOOL"
        if msg.type == "plan":
            return "UPDATE_PLAN"
        if msg.type == "observation_request":
            return "OBSERVE"
        if msg.type == "approval_required":
            return "WAIT_APPROVAL"
        if msg.type == "error":
            return "HANDLE_ERROR"
        if msg.type in {"thought", "reflection"}:
            # Non-actionable model text must never be treated as task completion.
            return "CONTINUE"
        return "HANDLE_ERROR"
