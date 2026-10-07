"""Pydantic schemas for API requests/responses."""

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    goal: str


class TaskAction(BaseModel):
    reason: str = ""


class SettingsUpdate(BaseModel):
    section: str
    values: dict = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: str  # "allow_once" | "allow" | "deny"
