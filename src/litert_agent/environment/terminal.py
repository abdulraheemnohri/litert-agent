"""Cross-platform terminal environment abstraction.

This module only describes the host shell/runtime; command execution remains
owned by the policy-controlled terminal tool.
"""
import os
import platform
import shutil


class TerminalEnvironment:
    @staticmethod
    def detect() -> dict:
        system = platform.system().lower()
        shell = os.environ.get("SHELL") or os.environ.get("COMSPEC") or ""
        if system == "windows":
            family = "powershell" if "powershell" in shell.lower() else "cmd"
        elif "android" in platform.platform().lower() or os.environ.get("TERMUX_VERSION"):
            family = "termux"
        else:
            family = "posix"
        return {
            "platform": system,
            "family": family,
            "shell": shell,
            "python": shutil.which("python") or shutil.which("python3"),
            "git": shutil.which("git"),
            "cwd": os.getcwd(),
        }
