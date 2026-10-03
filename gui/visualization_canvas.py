"""Right-top panel: hosts concept-specific visualizers."""
import pygame
from gui.theme import COLORS, draw_panel, draw_text, font as get_font


class VisualizationCanvas:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.visualizer = None

    def set_visualizer(self, visualizer):
        self.visualizer = visualizer

    def render(self, surface, context):
        draw_panel(surface, self.rect)
        header = pygame.Rect(self.rect.x + 1, self.rect.y + 1, self.rect.w - 2, 30)
        pygame.draw.rect(surface, COLORS["panel_alt"], header,
                         border_top_left_radius=6, border_top_right_radius=6)
        name = getattr(self.visualizer, "display_name", "Visualization")
        draw_text(surface, name, (header.x + 12, header.y + 8),
                  COLORS["accent"], size=14, bold=True)
        body = pygame.Rect(self.rect.x + 1, self.rect.y + 32,
                           self.rect.w - 2, self.rect.h - 33)
        prev = surface.get_clip()
        surface.set_clip(body)
        if self.visualizer is None:
            draw_text(surface, "No visualizer selected.", (body.x + 12, body.y + 12),
                      COLORS["dim"])
        else:
            try:
                self.visualizer.render(surface, body, context)
            except Exception as e:
                draw_text(surface, f"Visualization error: {e}",
                          (body.x + 12, body.y + 12), COLORS["error"])
        surface.set_clip(prev)
