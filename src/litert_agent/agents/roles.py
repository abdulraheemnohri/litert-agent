"""Agent roles definition."""

from enum import Enum


class AgentRole(str, Enum):
    MAIN = "main"
    RESEARCHER = "researcher"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DEVOPS = "devops"
    BROWSER = "browser"
