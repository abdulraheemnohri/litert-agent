"""Platform and shell abstraction layer."""

import os
import platform
import shutil
from pathlib import Path


class PlatformInfo:
    @staticmethod
    def os_name() -> str:
        return platform.system()

    @staticmethod
    def is_windows() -> bool:
        return platform.system() == "Windows"

    @staticmethod
    def is_linux() -> bool:
        return platform.system() == "Linux"

    @staticmethod
    def is_macos() -> bool:
        return platform.system() == "Darwin"

    @staticmethod
    def is_termux() -> bool:
        return "TERMUX_VERSION" in os.environ or Path("/data/data/com.termux").exists()

    @staticmethod
    def default_shell() -> str:
        if PlatformInfo.is_windows():
            return os.getenv("COMSPEC", "cmd.exe")
        return os.getenv("SHELL", "/bin/sh")

    @staticmethod
    def which(cmd: str) -> str | None:
        return shutil.which(cmd)
