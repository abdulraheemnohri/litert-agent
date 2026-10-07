"""Decision engine: converts a ProtocolMessage into a loop decision."""

from litert_agent.model.protocol import ProtocolMessage


class DecisionEngine:
    """Maps parsed model messages to loop decisions."""

    def decide(self, msg: ProtocolMessage) -> str:
        if msg.type == "final":
            return "COMPLETE_TASK"
        if msg.type == "tool_call" and msg.tool:
            return "EXECUTE_TOOL"
        if msg.type == "error":
            return "HANDLE_ERROR"
        if msg.type == "thought" and msg.content:
            # Treat plain reasoning without tool usage as completion attempt
            return "COMPLETE_TASK"
        return "HANDLE_ERROR"
