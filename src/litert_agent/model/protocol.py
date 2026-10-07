"""Agent action/message protocol objects."""

from typing import Any, Literal

from pydantic import BaseModel, Field

MessageType = Literal[
    "thought",
    "plan",
    "tool_call",
    "observation_request",
    "approval_required",
    "reflection",
    "final",
    "error",
]

class ProtocolMessage(BaseModel):
    type: MessageType
    content: str = ""
    tool: str | None = None
    action: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    plan_steps: list[str] = Field(default_factory=list)
    reason: str | None = None
