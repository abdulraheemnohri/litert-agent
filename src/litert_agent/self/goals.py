"""Persistent self-goal primitives; execution remains policy-controlled."""
from dataclasses import dataclass, field
from time import time

@dataclass
class SelfGoal:
    id: str
    title: str
    reason: str
    priority: int=50
    status: str="PROPOSED"
    metrics: dict=field(default_factory=dict)
    created_at: float=field(default_factory=time)

class SelfGoalManager:
    def __init__(self): self.goals={}
    def create(self,id,title,reason,priority=50,metrics=None):
        g=SelfGoal(id,title,reason,priority,metrics=metrics or {}); self.goals[id]=g; return g
    def list(self,status=None): return [g for g in self.goals.values() if status is None or g.status==status]
    def activate(self,id): self.goals[id].status="ACTIVE"; return self.goals[id]
    def complete(self,id): self.goals[id].status="COMPLETED"; return self.goals[id]
    def pause(self,id): self.goals[id].status="PAUSED"; return self.goals[id]
    def next_goal(self):
        active=[g for g in self.goals.values() if g.status in {"PROPOSED","ACTIVE"}]
        return sorted(active,key=lambda g:g.priority,reverse=True)[0] if active else None
