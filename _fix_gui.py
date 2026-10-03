# _fix_gui.py — writes every file in gui/ with correct content, then verifies.
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
GUI  = os.path.join(ROOT, "gui")
os.makedirs(GUI, exist_ok=True)

FILES = {}

FILES["__init__.py"] = "# gui package marker\n"

FILES["theme.py"] = '''import pygame

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
'''

FILES["code_editor.py"] = r'''"""Pygame-based code editor with a tiny syntax highlighter."""
import re
import pygame
from gui.theme import COLORS, font as get_font

KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
}

TOKEN_RE = re.compile(
    r'("""[^"]*?"""|\'\'\'[^\']*?\'\'\'|"[^"\n]*"|\'[^\'\n]*\'|#[^\n]*'
    r'|\b\d+\.?\d*\b|\b[A-Za-z_]\w*\b|\s+|[^\s])'
)


def tokenize(line):
    toks = []
    for m in TOKEN_RE.finditer(line):
        t = m.group(0)
        if t.startswith("#"):
            c = COLORS["comment"]
        elif t.startswith('"') or t.startswith("'"):
            c = COLORS["string"]
        elif t in KEYWORDS:
            c = COLORS["keyword"]
        elif t and t[0].isdigit():
            c = COLORS["number"]
        else:
            c = COLORS["text"]
        toks.append((t, c))
    return toks


class CodeEditor:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.lines = ["# Write or paste Python here, then click Run & Visualize."]
        self.cursor_line = 0
        self.cursor_col = len(self.lines[0])
        self.scroll = 0
        self.focus = True
        self.highlight_line = None
        self.error_line = None
        self.font = get_font(15, mono=True)
        self.line_h = self.font.get_linesize() + 2
        self.char_w = self.font.size("M")[0]
        self.gutter_w = 48
        self.blink = 0.0
        self.blink_on = True
        self._cursor_visible_time = 0.0

    def get_text(self):
        return "\n".join(self.lines)

    def set_text(self, text):
        self.lines = text.split("\n") or [""]
        self.cursor_line = 0
        self.cursor_col = 0
        self.scroll = 0

    def set_highlight(self, line_number):
        self.highlight_line = line_number

    def set_error(self, line_number):
        self.error_line = line_number

    def _clamp_cursor(self):
        self.cursor_line = max(0, min(self.cursor_line, len(self.lines) - 1))
        maxc = len(self.lines[self.cursor_line])
        self.cursor_col = max(0, min(self.cursor_col, maxc))

    def handle_text(self, text):
        if not self.focus:
            return
        line = self.lines[self.cursor_line]
        for ch in text:
            if ch == "\r":
                continue
            self.lines[self.cursor_line] = line[:self.cursor_col] + ch + line[self.cursor_col:]
            self.cursor_col += 1
            line = self.lines[self.cursor_line]

    def handle_key(self, key, mods):
        if not self.focus:
            return
        ctrl = mods & pygame.KMOD_CTRL
        if key == pygame.K_BACKSPACE:
            if self.cursor_col > 0:
                line = self.lines[self.cursor_line]
                self.lines[self.cursor_line] = line[:self.cursor_col - 1] + line[self.cursor_col:]
                self.cursor_col -= 1
            elif self.cursor_line > 0:
                prev = self.lines[self.cursor_line - 1]
                self.cursor_col = len(prev)
                self.lines[self.cursor_line - 1] = prev + self.lines[self.cursor_line]
                del self.lines[self.cursor_line]
                self.cursor_line -= 1
        elif key == pygame.K_DELETE:
            line = self.lines[self.cursor_line]
            if self.cursor_col < len(line):
                self.lines[self.cursor_line] = line[:self.cursor_col] + line[self.cursor_col + 1:]
            elif self.cursor_line < len(self.lines) - 1:
                self.lines[self.cursor_line] = line + self.lines[self.cursor_line + 1]
                del self.lines[self.cursor_line + 1]
        elif key == pygame.K_RETURN:
            line = self.lines[self.cursor_line]
            indent = re.match(r"^(\s*)", line).group(1)
            if line.rstrip().endswith(":"):
                indent += "    "
            before = line[:self.cursor_col]
            after = line[self.cursor_col:]
            self.lines[self.cursor_line] = before
            self.lines.insert(self.cursor_line + 1, indent + after)
            self.cursor_line += 1
            self.cursor_col = len(indent)
        elif key == pygame.K_TAB:
            self.handle_text("    ")
        elif key == pygame.K_LEFT:
            if ctrl:
                self.cursor_col = self._word_left()
            elif self.cursor_col > 0:
                self.cursor_col -= 1
            else:
                if self.cursor_line > 0:
                    self.cursor_line -= 1
                    self.cursor_col = len(self.lines[self.cursor_line])
        elif key == pygame.K_RIGHT:
            if self.cursor_col < len(self.lines[self.cursor_line]):
                self.cursor_col += 1
            elif self.cursor_line < len(self.lines) - 1:
                self.cursor_line += 1
                self.cursor_col = 0
        elif key == pygame.K_UP:
            self.cursor_line = max(0, self.cursor_line - 1)
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
        elif key == pygame.K_DOWN:
            self.cursor_line = min(len(self.lines) - 1, self.cursor_line + 1)
            self.cursor_col = min(self.cursor_col, len(self.lines[self.cursor_line]))
        elif key == pygame.K_HOME:
            self.cursor_col = 0
        elif key == pygame.K_END:
            self.cursor_col = len(self.lines[self.cursor_line])
        self._clamp_cursor()

    def _word_left(self):
        line = self.lines[self.cursor_line]
        i = self.cursor_col
        while i > 0 and line[i - 1].isspace():
            i -= 1
        while i > 0 and not line[i - 1].isspace():
            i -= 1
        return i

    def handle_click(self, pos):
        x, y = pos
        if not self.rect.collidepoint(pos):
            self.focus = False
            return
        self.focus = True
        rel_y = y - self.rect.y - 4
        line_idx = self.scroll + rel_y // self.line_h
        line_idx = max(0, min(line_idx, len(self.lines) - 1))
        self.cursor_line = line_idx
        rel_x = max(0, x - self.rect.x - self.gutter_w - 4)
        self.cursor_col = min(len(self.lines[line_idx]), rel_x // self.char_w)
        self._clamp_cursor()

    def update(self, dt):
        self._cursor_visible_time += dt
        if self._cursor_visible_time > 0.5:
            self._cursor_visible_time = 0
            self.blink_on = not self.blink_on
        visible = (self.rect.h - 8) // self.line_h
        if self.cursor_line < self.scroll:
            self.scroll = self.cursor_line
        elif self.cursor_line >= self.scroll + visible:
            self.scroll = self.cursor_line - visible + 1

    def render(self, surface):
        r = self.rect
        pygame.draw.rect(surface, COLORS["editor_bg"], r, border_radius=6)
        gutter = pygame.Rect(r.x, r.y, self.gutter_w, r.h)
        pygame.draw.rect(surface, COLORS["gutter_bg"], gutter,
                         border_top_left_radius=6, border_bottom_left_radius=6)
        pygame.draw.rect(surface, COLORS["border"], r, 1, border_radius=6)

        clip = pygame.Rect(r.x + 1, r.y + 1, r.w - 2, r.h - 2)
        prev_clip = surface.get_clip()
        surface.set_clip(clip)

        visible = (r.h - 8) // self.line_h
        start = self.scroll
        end = min(len(self.lines), start + visible)

        for i in range(start, end):
            y = r.y + 4 + (i - start) * self.line_h
            line_no = i + 1

            if self.highlight_line == line_no:
                pygame.draw.rect(surface, COLORS["highlight_cur"],
                                 (r.x + 1, y - 1, r.w - 2, self.line_h))
            if self.error_line == line_no:
                pygame.draw.rect(surface, (110, 40, 40),
                                 (r.x + 1, y - 1, r.w - 2, self.line_h))

            num_s = self.font.render(str(line_no), True, COLORS["faint"])
            surface.blit(num_s, (r.x + self.gutter_w - 8 - num_s.get_width(), y))

            x = r.x + self.gutter_w + 4
            for tok, color in tokenize(self.lines[i]):
                surf = self.font.render(tok, True, color)
                surface.blit(surf, (x, y))
                x += surf.get_width()

            if i == self.cursor_line and self.focus and self.blink_on:
                cx = r.x + self.gutter_w + 4 + self.cursor_col * self.char_w
                pygame.draw.line(surface, COLORS["accent"], (cx, y), (cx, y + self.line_h - 2), 2)

        surface.set_clip(prev_clip)
'''

FILES["visualization_canvas.py"] = '''"""Right-top panel: hosts concept-specific visualizers."""
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
'''

FILES["variable_panel.py"] = '''import pygame
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
'''

FILES["control_bar.py"] = '''import pygame
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
'''

FILES["ai_panel.py"] = '''import pygame
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
        for para in text.split("\\n"):
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
'''

FILES["error_panel.py"] = '''import pygame
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
            lines = self.stdout.split("\\n")
            for line in lines[self.scroll:]:
                if y + lh > body.bottom:
                    break
                draw_text(surface, line.rstrip(), (body.x, y), COLORS["text"], size=14)
                y += lh
        if not self.stdout and not self.error:
            draw_text(surface, "(program output appears here)", (body.x, body.y),
                      COLORS["dim"], size=13)
'''

for name, content in FILES.items():
    path = os.path.join(GUI, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote   gui/{name}  ({len(content)} bytes)")

print("\nVerifying (fresh interpreter)...")
sys.stdout.flush()

r = subprocess.run(
    [sys.executable, "-c",
     "import gui.theme, gui.code_editor, gui.variable_panel, gui.control_bar, "
     "gui.ai_panel, gui.error_panel, gui.visualization_canvas; "
     "from gui.code_editor import CodeEditor; "
     "from gui.visualization_canvas import VisualizationCanvas; "
     "print('gui ok:', CodeEditor, VisualizationCanvas)"],
    cwd=ROOT, capture_output=True, text=True,
)
print(r.stdout, r.stderr)