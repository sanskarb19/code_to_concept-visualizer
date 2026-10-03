"""Convenience wrapper around the raw trace dict."""
from execution.serializer import display


class TraceModel:
    def __init__(self, data: dict):
        self.data = data or {}
        self.source_code = self.data.get("source_code", "")
        self.source_lines = self.source_code.split("\n")
        self.events = self.data.get("events", [])
        self.error = self.data.get("error")
        self.stdout = self.data.get("stdout", "")
        self.stderr = self.data.get("stderr", "")
        self.timed_out = self.data.get("timed_out", False)

    @property
    def total_steps(self):
        return len(self.events)

    def event(self, index):
        if 0 <= index < len(self.events):
            return self.events[index]
        return None

    def locals_at(self, index):
        ev = self.event(index)
        return ev["locals"] if ev else {}

    def line_at(self, index):
        ev = self.event(index)
        return ev["line_number"] if ev else None

    def function_at(self, index):
        ev = self.event(index)
        return ev["function"] if ev else None

    def stack_at(self, index):
        """Reconstruct approximate call stack by walking back through events."""
        if index < 0 or index >= len(self.events):
            return []
        stack = []
        depth = self.events[index]["call_depth"]
        seen_depths = {}
        for i in range(index, -1, -1):
            ev = self.events[i]
            d = ev["call_depth"]
            if d not in seen_depths:
                seen_depths[d] = ev["function"]
        for d in sorted(seen_depths.keys()):
            if d <= depth:
                stack.append({"function": seen_depths[d], "depth": d})
        return stack

    def variables_display(self, index):
        locs = self.locals_at(index)
        return {k: display(v) for k, v in locs.items()}