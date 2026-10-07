"""Self-skill discovery, proposal, validation and promotion.

Self-generated skills are inert proposals until validated. Security policy is
never delegated to a generated skill.
"""
from dataclasses import dataclass, field
from time import time

@dataclass
class SkillProposal:
    name: str
    purpose: str
    trigger: str
    steps: list[str]
    evidence: list[str] = field(default_factory=list)
    risk: str = "MEDIUM"
    status: str = "PROPOSED"
    created_at: float = field(default_factory=time)

class SelfSkillEngine:
    FORBIDDEN_CAPABILITIES={"modify_security_policy","extract_secrets","disable_approval","modify_model_weights","replace_provider"}
    def __init__(self, registry=None):
        self.registry=registry
        self.proposals: dict[str,SkillProposal]={}

    def discover(self, task_history: list[dict]) -> list[SkillProposal]:
        proposals=[]
        for row in task_history:
            pattern=row.get("repeated_tool_sequence") or row.get("pattern")
            if not pattern: continue
            name=row.get("skill_name") or "learned_"+str(abs(hash(str(pattern))))[:10]
            if name not in self.proposals:
                proposals.append(self.propose(name,row.get("purpose","Automate a repeated validated workflow"),row.get("trigger","repeated pattern"),list(pattern),row.get("evidence",[])))
        return proposals

    def propose(self,name,purpose,trigger,steps,evidence=None,risk="MEDIUM"):
        text=" ".join(steps).lower()
        if any(x in text for x in self.FORBIDDEN_CAPABILITIES):
            raise ValueError("Generated skill contains a forbidden capability")
        p=SkillProposal(name=name,purpose=purpose,trigger=trigger,steps=steps,evidence=evidence or [],risk=risk)
        self.proposals[name]=p
        return p

    def validate(self,name,test_result: bool, evidence: str=""):
        p=self.proposals[name]
        if evidence: p.evidence.append(evidence)
        p.status="VALIDATED" if test_result else "REJECTED"
        return p

    def promote(self,name):
        p=self.proposals[name]
        if p.status!="VALIDATED": raise ValueError("Skill must be validated before promotion")
        p.status="PROMOTED"
        if self.registry is not None and hasattr(self.registry,"register"):
            self.registry.register(p.name,purpose=p.purpose)
        return p

    def list_proposals(self): return list(self.proposals.values())
