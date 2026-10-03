"""Auto-generated stub visualizer for Stack."""
from gui.theme import COLORS, draw_text
from visualization.base import BaseVisualizer


class StackVisualizer(BaseVisualizer):
    display_name = "Stack"

    def render(self, surface, rect, ctx):
        draw_text(surface, "Stack", (rect.x + 16, rect.y + 16),
                  COLORS["accent"], size=14, bold=True)
        draw_text(surface, "(stub — replace with full implementation)",
                  (rect.x + 16, rect.y + 44), COLORS["dim"], size=12)
        if ctx.event is not None:
            draw_text(surface, f"line {ctx.line_number}  in  {ctx.function}()",
                      (rect.x + 16, rect.y + 72), COLORS["text"], size=13, mono=True)
