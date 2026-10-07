"""Base Tool abstract class."""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field
from litert_agent.security.permissions import PermissionLevel

class ToolResult(BaseModel):
    success: bool
    output: str
    error: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)

class BaseTool(ABC):
    name: str
    description: str
    permission_level: PermissionLevel = PermissionLevel.ALLOW

    @abstractmethod
    async def execute(self, action: str, **kwargs) -> ToolResult:
        pass

    def validate_args(self, action: str, kwargs: dict) -> bool:
        return True
