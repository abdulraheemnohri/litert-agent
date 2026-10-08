"""Strict-ish parser for LiteRT-LM agent protocol output.

Model output is untrusted data. Unknown/malformed structures become a thought
message and are never executed. The parser does not expose chain-of-thought.
"""

import json
import re
from typing import Any

from litert_agent.model.protocol import ProtocolMessage


class ProtocolParser:
    @staticmethod
    def _extract_json(raw: str) -> str:
        match = re.search(r"\`\`\`(?:json)?\s*(\{.*?\})\s*\`\`\`", raw, re.DOTALL)
        return match.group(1) if match else raw

    @staticmethod
    def _normalize(data: dict[str, Any]) -> ProtocolMessage | None:
        if "type" not in data:
            intent = str(data.get("intent", "")).lower()
            if intent in {"execute_task", "execute_tool", "tool_call"}:
                data["type"] = "tool_call" if data.get("tool") else "plan"
            elif intent in {"complete", "final", "answer"}:
                data["type"] = "final"
            elif intent in {"error", "fail"}:
                data["type"] = "error"
            elif intent in {"plan", "planning"}:
                data["type"] = "plan"
            else:
                return None

        if data["type"] == "tool_call" and not data.get("tool"):
            return None
        return ProtocolMessage.model_validate(data)

    @staticmethod
    def parse(raw_output: str) -> ProtocolMessage:
        cleaned = raw_output.strip()
        if not cleaned:
            return ProtocolMessage(type="error", content="Empty model output", reason="empty_output")

        candidate = ProtocolParser._extract_json(cleaned)
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                parsed = ProtocolParser._normalize(data)
                if parsed is not None:
                    return parsed
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        match = re.search(r"TOOL:\s*([A-Za-z0-9_.-]+)\s+ARGS:\s*(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                args = json.loads(match.group(2))
                if isinstance(args, dict):
                    return ProtocolMessage(
                        type="tool_call", tool=match.group(1), arguments=args,
                    )
            except json.JSONDecodeError:
                pass

        if re.search(r"^FINAL:\s*", cleaned, re.IGNORECASE):
            return ProtocolMessage(
                type="final", content=re.sub(r"^FINAL:\s*", "", cleaned, count=1, flags=re.I).strip(),
            )

        # Plain text is non-executable. The loop must not interpret it as completion.
        return ProtocolMessage(type="thought", content=cleaned[:12000], reason="unstructured_output")
