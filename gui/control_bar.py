import pygame
from gui.theme import COLORS, draw_panel, draw_text, font as get_font

SPEEDS = [0.5, 1.0, 2.0, 4.0]


class ControlBar:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.buttons = {}
        self._layout()

    def _layout(self):
        r = self.rect
        x = r.x + 12
        y = r.y + 8
        h = r.h - 16
        def mk(key, label, w):
            nonlocal x
            self.buttons[key] = {"rect": pygame.Rect(x, y, w, h), "label": label}
            x += w + 6
        mk("prev", "Prev", 72)
        mk("play", "Play", 72)
        mk("pause", "Pause", 82)
        mk("next", "Next", 72)
        mk("restart", "Restart", 82)
        mk("speed", "Speed 1x", 96)
        mk("explain", "Explain", 96)

    def handle_click(self, pos):
        for key, b in self.buttons.items():
            if b["rect"].collidepoint(pos):
                return key
        return None

    def render(self, surface, *, step, total, playing, speed, explain_busy, explain_available):
        draw_panel(surface, self.rect)
        mouse = pygame.mouse.get_pos()
        for key, b in self.buttons.items():
            label = b["label"]
            disabled = False
            if key == "play" and playing:
                disabled = True
            if key == "pause" and not playing:
                disabled = True
            if key == "explain" and not explain_available:
                disabled = True
            if key == "speed":
                label = f"Speed {speed:g}x"
            if key == "explain" and explain_busy:
                label = "..."
            hover = b["rect"].collidepoint(mouse) and not disabled
            fill = COLORS["accent"] if hover else COLORS["panel_alt"]
            if disabled:
                fill = COLORS["panel"]
            pygame.draw.rect(surface, fill, b["rect"], border_radius=4)
            pygame.draw.rect(surface, COLORS["border"], b["rect"], 1, border_radius=4)
            color = COLORS["text"] if not disabled else COLORS["faint"]
            txt = get_font(13).render(label, True, color)
            surface.blit(txt, (b["rect"].centerx - txt.get_width() // 2,
                               b["rect"].centery - txt.get_height() // 2))

        px = self.rect.right - 220
        py = self.rect.y + 12
        draw_text(surface, f"Step {step + 1 if total else 0} / {total}",
                  (px, py), COLORS["dim"], size=13)
        bar = pygame.Rect(px, py + 22, 200, 8)
        pygame.draw.rect(surface, COLORS["panel_alt"], bar, border_radius=4)
        if total > 0:
            frac = (step + 1) / total
            pygame.draw.rect(surface, COLORS["accent"],
                             (bar.x, bar.y, int(bar.w * frac), bar.h), border_radius=4)
