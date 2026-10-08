"""Defense-in-depth command guard for shell execution."""

import re


class CommandGuard:
    """Classify obviously dangerous shell commands before subprocess creation."""

    BLOCK_PATTERNS = (
        re.compile(r"(^|\s)sudo(\s|$)", re.I),
        re.compile(r"\brm\s+-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)[^\n]*\s+/(?:\s|$)", re.I),
        re.compile(r"\b(?:mkfs|fdisk|parted)\b", re.I),
        re.compile(r"\b(?:shutdown|reboot|poweroff|halt)\b", re.I),
        re.compile(r"\b(?:chmod|chown)\s+.*(?:777|/etc|/usr|/var|/root)", re.I),
        re.compile(r"\b(?:curl|wget)\b[^\n|;&]*\|\s*(?:sh|bash|zsh|powershell|pwsh)", re.I),
    )

    ASK_PATTERNS = (
        re.compile(r"\b(?:pip|pip3|apt|apt-get|dnf|yum|pacman|brew|npm|pnpm|yarn)\s+(?:install|uninstall|remove|update|upgrade)\b", re.I),
        re.compile(r"\b(?:git)\s+(?:push|reset|clean)\b", re.I),
        re.compile(r"(?:>|>>|2>|2>>|\|)"),
        re.compile(r"\b(?:kill|pkill|taskkill)\b", re.I),
    )

    @classmethod
    def classify(cls, command: str) -> str:
        if not command or not command.strip():
            return "BLOCK"
        if any(pattern.search(command) for pattern in cls.BLOCK_PATTERNS):
            return "BLOCK"
        if any(pattern.search(command) for pattern in cls.ASK_PATTERNS):
            return "ASK"
        return "ALLOW"
