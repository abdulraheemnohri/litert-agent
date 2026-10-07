"""Scheduler models and job definitions."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    task_description: str
    cron_or_interval: str = ""
    status: str = "PENDING"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
