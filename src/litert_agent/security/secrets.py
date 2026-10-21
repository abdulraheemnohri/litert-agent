"""Secret masking utilities for logs, memory, and user-visible diagnostics."""

import re

# Match credential labels in environment variables, Python-like assignments,
# and JSON/YAML-style key/value text. Allow prefixed names such as
# OPENAI_API_KEY and DATABASE_PASSWORD.
_SECRET_ASSIGNMENT = re.compile(
    r"""(?ix)
    (?P<prefix>
        (?:\b|_)
        (?:api[-_]?key|access[-_]?token|refresh[-_]?token|auth[-_]?token|
        client[-_]?secret|password|passwd|secret|credential)
        \b["']?\s*[:=]\s*["']?
    )
    (?P<value>[^"'\x60\s,;}\]]+)
    """
)

_BEARER_CREDENTIAL = re.compile(
    r"(?i)(?P<prefix>\bBearer\s+)(?P<value>[A-Za-z0-9\-._~+/]+=*)"
)


class SecretSanitizer:
    """Redact credential values without changing unrelated text."""

    @staticmethod
    def sanitize(text: str) -> str:
        if not text:
            return text

        sanitized = _SECRET_ASSIGNMENT.sub(
            lambda match: f"{match.group('prefix')}[REDACTED_SECRET]", text
        )
        return _BEARER_CREDENTIAL.sub(
            lambda match: f"{match.group('prefix')}[REDACTED_SECRET]", sanitized
        )
