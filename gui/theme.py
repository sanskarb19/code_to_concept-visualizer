import pygame

COLORS = {
    "bg":         (24, 26, 33),
    "panel":      (34, 37, 46),
    "panel_alt":  (40, 44, 54),
    "border":     (60, 66, 82),
    "border_hi":  (95, 130, 200),
    "text":       (225, 228, 235),
    "dim":        (150, 158, 175),
    "faint":      (95, 102, 118),
    "accent":     (88, 166, 255),
    "accent2":    (180, 130, 255),
    "ok":         (80, 200, 120),
    "warn":       (240, 180, 60),
    "error":      (240, 90, 90),
    "keyword":    (255, 121, 198),
    "string":     (241, 250, 140),
    "comment":    (120, 130, 150),
    "number":     (189, 147, 249),
    "funcname":   (110, 220, 180),
    "highlight":  (50, 70, 115),
    "highlight_cur": (65, 90, 150),
    "editor_bg":  (28, 30, 38),
    "gutter_bg":  (22, 24, 30),
    "step":       (250, 210, 90),
}

_font_cache = {}


def font(size=14, bold=False, mono=False):
    key = (size, bold, mono)
    if key not in _font_cache:
        if mono:
            name = "consolas,couriernew,monospace"
        else:
            name = "segoeui,helvetica,arial"
        f = pygame.font.SysFont(name, size, bold=bold)
        _font_cache[key] = f
    return _font_cache[key]


def draw_panel(surface, rect, fill=None, border=None, radius=6):
    fill = fill or COLORS["panel"]
    border = border or COLORS["border"]
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, 1, border_radius=radius)


def draw_text(surface, text, pos, color=None, size=14, bold=False, mono=False, clip=None):
    color = color or COLORS["text"]
    f = font(size, bold, mono)
    surf = f.render(text, True, color)
    if clip:
        prev = surface.get_clip()
        surface.set_clip(clip)
    surface.blit(surf, pos)
    if clip:
        surface.set_clip(prev)
    return surf.get_width()
