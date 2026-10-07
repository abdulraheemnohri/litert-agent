"""Secret masking utility."""

import re

SECRET_PATTERNS = [
    re.compile(r"api[-_]?key\s*=\s*['\"]?([^'\"\s]+)['\"]?", re.IGNORECASE),
    re.compile(r"password\s*=\s*['\"]?([^'\"\s]+)['\"]?", re.IGNORECASE),
    re.compile(r"secret\s*=\s*['\"]?([^'\"\s]+)['\"]?", re.IGNORECASE),
    re.compile(r"bearer\s+([a-zA-Z0-9\-\._~\+\/]+=*)", re.IGNORECASE),
]

class SecretSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        sanitized = text
        for pattern in SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
        return sanitized
