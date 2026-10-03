"""Base class + context for visualizers."""
from gui.theme import COLORS


class VisualizerContext:
    def __init__(self, trace_model, step_index):
        self.trace = trace_model
        self.step_index = step_index
        self.src_lines = trace_model.source_lines

    @property
    def event(self):
        return self.trace.event(self.step_index)

    @property
    def locals(self):
        return self.event["locals"] if self.event else {}

    @property
    def line_number(self):
        return self.event["line_number"] if self.event else None

    @property
    def function(self):
        return self.event["function"] if self.event else None


class BaseVisualizer:
    display_name = "Visualization"

    def render(self, surface, rect, ctx):
        from gui.theme import draw_text
        draw_text(surface, "(visualizer stub)", (rect.x + 16, rect.y + 16), COLORS["text"])
