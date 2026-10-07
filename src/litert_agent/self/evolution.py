"""Safe self-evolution primitives.

Evolution is configuration/skill/documentation oriented only. It cannot modify
security policy, provider identity, or model weights automatically.
"""

from dataclasses import dataclass


@dataclass
class ImprovementProposal:
    area: str
    reason: str
    changes: list[str]
    risk: str = "MEDIUM"
    requires_approval: bool = True


class EvolutionManager:
    FORBIDDEN_AREAS = {"model_weights", "security_policy", "provider_backend"}

    def propose(self, area: str, reason: str, changes: list[str]) -> ImprovementProposal:
        if area in self.FORBIDDEN_AREAS:
            raise ValueError(f"Automatic evolution is forbidden for {area}")
        return ImprovementProposal(area=area, reason=reason, changes=changes)

    def validate(self, proposal: ImprovementProposal) -> bool:
        return bool(proposal.area and proposal.reason and proposal.changes)
