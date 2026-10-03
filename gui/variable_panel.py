import pygame
from gui.theme import COLORS, draw_panel, draw_text, font as get_font
from execution.serializer import display


class VariablePanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.scroll = 0
        self.prev_locals = {}

    def set_prev(self, locs):
        self.prev_locals = locs

    def render(self, surface, locals_):
        draw_panel(surface, self.rect)
        header = pygame.Rect(self.rect.x + 1, self.rect.y + 1, self.rect.w - 2, 26)
        pygame.draw.rect(surface, COLORS["panel_alt"], header,
                         border_top_left_radius=6, border_top_right_radius=6)
        draw_text(surface, "CURRENT VARIABLES", (header.x + 12, header.y + 6),
                  COLORS["accent"], size=13, bold=True)

        body = pygame.Rect(self.rect.x + 12, self.rect.y + 34, self.rect.w - 24, self.rect.h - 44)
        if not locals_:
            draw_text(surface, "(no variables yet)", (body.x, body.y + 4), COLORS["dim"])
            return

        f_key = get_font(15, mono=True)
        y = body.y
        line_h = 22
        for name in sorted(locals_.keys()):
            if y + line_h > body.bottom:
                break
            raw = locals_[name]
            val_str = display(raw)
            changed = self.prev_locals.get(name) != raw
            name_color = COLORS["step"] if changed else COLORS["text"]
            val_color = COLORS["ok"] if changed else COLORS["dim"]
            name_s = f_key.render(f"{name}", True, name_color)
            eq_s = f_key.render(" = ", True, COLORS["faint"])
            val_s = f_key.render(val_str, True, val_color)
            surface.blit(name_s, (body.x, y))
            x = body.x + max(70, name_s.get_width() + 8)
            surface.blit(eq_s, (x, y))
            surface.blit(val_s, (x + eq_s.get_width(), y))
            if changed:
                pygame.draw.circle(surface, COLORS["step"], (body.right - 10, y + 8), 4)
            y += line_h
