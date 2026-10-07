"""Environment detector."""

import sys
from litert_agent.environment.platform import PlatformInfo
from litert_agent.environment.resources import ResourceMonitor

class EnvironmentDetector:
    @staticmethod
    def detect_all() -> dict:
        return {
            "os": PlatformInfo.os_name(),
            "is_windows": PlatformInfo.is_windows(),
            "is_linux": PlatformInfo.is_linux(),
            "is_macos": PlatformInfo.is_macos(),
            "is_termux": PlatformInfo.is_termux(),
            "python_version": sys.version.split()[0],
            "default_shell": PlatformInfo.default_shell(),
            "has_git": PlatformInfo.which("git") is not None,
            "has_litert_lm": PlatformInfo.which("litert-lm") is not None,
            "has_playwright": PlatformInfo.which("playwright") is not None,
            "resources": {
                "cpu_percent": ResourceMonitor.get_cpu_usage(),
                "memory": ResourceMonitor.get_memory_info(),
                "disk": ResourceMonitor.get_disk_info(),
            }
        }
