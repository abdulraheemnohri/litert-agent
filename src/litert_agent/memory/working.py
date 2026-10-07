"""Working memory in-memory buffer."""

class WorkingMemory:
    def __init__(self, max_items: int = 50):
        self.max_items = max_items
        self.buffer: list[dict] = []

    def add(self, role: str, content: str):
        self.buffer.append({"role": role, "content": content})
        if len(self.buffer) > self.max_items:
            self.buffer.pop(0)

    def get_recent(self, n: int = 10) -> list[dict]:
        return self.buffer[-n:]

    def clear(self):
        self.buffer.clear()
