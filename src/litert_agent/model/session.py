"""Model session state container."""

from litert_agent.model.protocol import ProtocolMessage

class ModelSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict[str, str]] = []

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, message: ProtocolMessage):
        self.history.append({"role": "assistant", "content": message.model_dump_json()})

    def get_context_prompt(self) -> str:
        return "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in self.history)
