"""Reflector: extracts lessons from execution experience."""


class Reflector:
    """Turns task outcomes into reusable lessons."""

    def reflect(self, goal: str, results: list[dict], success: bool) -> str:
        if success:
            tool_counts: dict[str, int] = {}
            for r in results:
                tool_counts[r.get("tool", "unknown")] = tool_counts.get(r.get("tool", "unknown"), 0) + 1
            dominant = max(tool_counts, key=lambda k: tool_counts[k]) if tool_counts else "unknown"
            return f"Goal '{goal}' succeeded using mostly '{dominant}' tools; reuse this approach."
        errors = [r.get("error") or r.get("output", "") for r in results if not r.get("success")]
        first_error = errors[0] if errors else "unknown error"
        return f"Goal '{goal}' failed; primary cause: {first_error}. Avoid repeating this path."
