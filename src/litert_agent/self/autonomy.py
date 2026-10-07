"""Bounded autonomous self-management controller."""
from dataclasses import dataclass
from time import time

@dataclass
class AutonomousPolicy:
    enabled: bool=False
    max_actions_per_cycle: int=5
    max_runtime_seconds: int=300
    allow_skill_learning: bool=True
    allow_memory_learning: bool=True
    allow_maintenance: bool=False
    require_approval_for_promote: bool=True

class SelfAutonomyController:
    def __init__(self, manager, learning, skills, policy=None):
        self.manager,self.learning,self.skills=manager,learning,skills
        self.policy=policy or AutonomousPolicy()
        self.running=False

    def start(self): self.running=True; return self.status()
    def stop(self): self.running=False; return self.status()
    def status(self): return {"running":self.running,"policy":self.policy.__dict__}

    def cycle(self, observations: list[dict]) -> list[dict]:
        if not self.running or not self.policy.enabled: return []
        started=time(); actions=[]
        diagnostics=self.manager.diagnose()
        actions.append({"action":"diagnostics","ok":diagnostics["ok"]})
        if len(actions)<self.policy.max_actions_per_cycle and self.policy.allow_skill_learning:
            proposals=self.skills.discover(observations)
            actions.append({"action":"skill_discovery","count":len(proposals)})
        if len(actions)<self.policy.max_actions_per_cycle and time()-started < self.policy.max_runtime_seconds:
            actions.append({"action":"maintenance_review","proposals":self.manager.maintenance_plan()})
        return actions[:self.policy.max_actions_per_cycle]
