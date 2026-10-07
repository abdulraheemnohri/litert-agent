"""Permission levels enum."""

from enum import Enum

class PermissionLevel(str, Enum):
    ALLOW = "ALLOW"
    ASK = "ASK"
    BLOCK = "BLOCK"
