import pygame
from gui.theme import COLORS, draw_panel, draw_text, font as get_font


class AIPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.lines = []
        self.status = "Idle. Click Explain to ask about the current step."

    def set_status(self, s):
        self.status = s

    def set_explanation(self, text):
        self.lines = self._wrap(text or "")

    def _wrap(self, text):
        f = get_font(14)
        max_w = self.rect.w - 24
        out = []
        for para in text.split("\n"):
            if not para:
                out.append("")
                continue
            words = para.split(" ")
            cur = ""
            for w in words:
                t = (cur + " " + w).strip()
                if f.size(t)[0] > max_w and cur:
                    out.append(cur)
                    cur = w
                else:
                    cur = t
            out.append(cur)
        return out

    def render(self, surface):
        draw_panel(surface, self.rect)
        header = pygame.Rect(self.rect.x + 1, self.rect.y + 1, self.rect.w - 2, 26)
        pygame.draw.rect(surface, COLORS["panel_alt"], header,
                         border_top_left_radius=6, border_top_right_radius=6)
        draw_text(surface, "AI EXPLANATION", (header.x + 12, header.y + 6),
                  COLORS["accent2"], size=13, bold=True)
        body = pygame.Rect(self.rect.x + 12, self.rect.y + 34, self.rect.w - 24, self.rect.h - 44)
        y = body.y
        lh = 18
        if not self.lines:
            for line in self._wrap(self.status):
                if y + lh > body.bottom:
                    break
                draw_text(surface, line, (body.x, y), COLORS["dim"], size=13)
                y += lh
            return
        for line in self.lines:
            if y + lh > body.bottom:
                break
            draw_text(surface, line, (body.x, y), COLORS["text"], size=13)
            y += lh
