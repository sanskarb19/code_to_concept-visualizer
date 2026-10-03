"""Pygame-based code editor with a tiny syntax highlighter."""
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
