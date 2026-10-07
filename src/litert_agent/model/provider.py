"""Base abstract model provider."""

from abc import ABC, abstractmethod
from litert_agent.model.protocol import ProtocolMessage

class ModelProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str | None = None) -> ProtocolMessage:
        pass
