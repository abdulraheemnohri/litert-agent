"""Compatibility shim: single error classifier shared by recovery modules."""


def classify_error(error: str) -> str:
    from litert_agent.recovery.healer import Healer
    return Healer().diagnose(error)
