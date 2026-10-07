"""Capabilities representation."""

from pydantic import BaseModel

from litert_agent.environment.detector import EnvironmentDetector


class Capabilities(BaseModel):
    os: str
    python_version: str
    has_git: bool
    has_litert_lm: bool
    has_playwright: bool
    cpu_percent: float
    memory_gb: float
    disk_free_gb: float

    @classmethod
    def discover(cls) -> "Capabilities":
        env = EnvironmentDetector.detect_all()
        return cls(
            os=env["os"],
            python_version=env["python_version"],
            has_git=env["has_git"],
            has_litert_lm=env["has_litert_lm"],
            has_playwright=env["has_playwright"],
            cpu_percent=env["resources"]["cpu_percent"],
            memory_gb=env["resources"]["memory"]["total_gb"],
            disk_free_gb=env["resources"]["disk"]["free_gb"],
        )
