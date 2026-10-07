"""Parser for model output to ProtocolMessage."""

import json
import re

from litert_agent.model.protocol import ProtocolMessage


class ProtocolParser:
    @staticmethod
    def parse(raw_output: str) -> ProtocolMessage:
        cleaned = raw_output.strip()

        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(1)

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "type" in data:
                return ProtocolMessage(**data)
        except Exception:
            pass

        if "TOOL:" in cleaned:
            match = re.search(r"TOOL:\s*(\w+)\s+ARGS:\s*(\{.*\})", cleaned)
            if match:
                tool_name = match.group(1)
                try:
                    args = json.loads(match.group(2))
                except Exception:
                    args = {}
                return ProtocolMessage(type="tool_call", tool=tool_name, arguments=args)

        if "FINAL:" in cleaned:
            final_text = cleaned.split("FINAL:", 1)[1].strip()
            return ProtocolMessage(type="final", content=final_text)

        return ProtocolMessage(type="thought", content=cleaned)
