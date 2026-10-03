import pygame
from gui.theme import COLORS, draw_panel, draw_text, font as get_font


class OutputPanel:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.stdout = ""
        self.error = None
        self.scroll = 0

    def set_result(self, stdout, error):
        self.stdout = stdout or ""
        self.error = error

    def handle_wheel(self, y):
        self.scroll = max(0, self.scroll + y)

    def render(self, surface):
        draw_panel(surface, self.rect,
                   fill=(40, 26, 26) if self.error else COLORS["panel"])
        header = pygame.Rect(self.rect.x + 1, self.rect.y + 1, self.rect.w - 2, 24)
        pygame.draw.rect(surface, COLORS["panel_alt"], header,
                         border_top_left_radius=6, border_top_right_radius=6)
        title = "ERROR" if self.error else "OUTPUT"
        color = COLORS["error"] if self.error else COLORS["accent"]
        draw_text(surface, title, (header.x + 12, header.y + 5), color, size=13, bold=True)

        body = pygame.Rect(self.rect.x + 12, self.rect.y + 32, self.rect.w - 24, self.rect.h - 40)
        f = get_font(14, mono=True)
        lh = f.get_linesize() + 1
        y = body.y
        if self.error:
            draw_text(surface, f"Type:    {self.error.get('type','Error')}",
                      (body.x, y), COLORS["error"]); y += lh
            draw_text(surface, f"Line:    {self.error.get('line') or '?'}",
                      (body.x, y), COLORS["error"]); y += lh
            msg = str(self.error.get("message", ""))
            for i in range(0, len(msg), 90):
                if y > body.bottom: break
                draw_text(surface, msg[i:i + 90], (body.x, y), COLORS["text"], size=14)
                y += lh
            y += 4
        if self.stdout:
            lines = self.stdout.split("\n")
            for line in lines[self.scroll:]:
                if y + lh > body.bottom:
                    break
                draw_text(surface, line.rstrip(), (body.x, y), COLORS["text"], size=14)
                y += lh
        if not self.stdout and not self.error:
            draw_text(surface, "(program output appears here)", (body.x, body.y),
                      COLORS["dim"], size=13)
