"""Autonomous research subsystem (A-to-Z spec sections 15-16).

Internet content is untrusted evidence, never instructions
(prompt-injection defense, spec section 92).
"""
from litert_agent.research.missions import ResearchMission, ResearchStore

__all__ = ["ResearchMission", "ResearchStore"]
