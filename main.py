"""Python Code Visualizer — main Pygame application."""
import os
import sys
import time
import pygame

# Optional dotenv loading for GEMINI_API_KEY
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from execution.executor import execute_code
from execution.trace_model import TraceModel
from visualization import CONCEPTS, get_visualizer
from visualization.base import VisualizerContext
from ai import GeminiExplainer
from examples import get_example

from gui.theme import COLORS, draw_panel, draw_text, font as get_font
from gui.code_editor import CodeEditor
from gui.visualization_canvas import VisualizationCanvas
from gui.variable_panel import VariablePanel
from gui.control_bar import ControlBar, SPEEDS
from gui.ai_panel import AIPanel
from gui.error_panel import OutputPanel


WIDTH, HEIGHT = 1500, 950
FPS = 60


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Python Code Visualizer")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        # ---- Layout ----
        margin = 8
        top_h = 58
        bottom_h = 58
        main_top = top_h + margin
        main_bottom = HEIGHT - bottom_h - margin
        main_h = main_bottom - main_top
        left_w = 740
        right_x = margin + left_w + margin

        # Left: editor + output
        editor_h = int(main_h * 0.72)
        self.editor = CodeEditor((margin, main_top, left_w, editor_h))
        self.output_panel = OutputPanel(
            (margin, main_top + editor_h + 8, left_w, main_h - editor_h - 8))

        # Right: visualization + variables + AI
        vis_h = int(main_h * 0.60)
        vp_h = int(main_h * 0.22)
        self.vis_canvas = VisualizationCanvas((right_x, main_top, left_w, vis_h))
        self.var_panel = VariablePanel(
            (right_x, main_top + vis_h + 8, left_w, vp_h))
        self.ai_panel = AIPanel(
            (right_x, main_top + vis_h + vp_h + 16, left_w, main_h - vis_h - vp_h - 16))

        # Bottom controls
        self.control_bar = ControlBar((margin, HEIGHT - bottom_h - 4, WIDTH - 2 * margin, bottom_h))

        # Top bar
        self.top_rect = pygame.Rect(margin, margin, WIDTH - 2 * margin, top_h - 4)
        self.concept_dropdown_open = False
        self.concept_index = 0

        # ---- State ----
        self.trace = TraceModel({})
        self.step_index = -1
        self.playing = False
        self.speed_idx = 1  # 1x
        self.play_accum = 0.0
        self.editor.set_text(get_example(CONCEPTS[self.concept_index]))
        self.update_visualizer()

        self.ai = GeminiExplainer()
        if not self.ai.available:
            self.ai_panel.set_status(f"AI unavailable. {self.ai.status()}")
        else:
            self.ai_panel.set_status("Ready. Click 🤖 Explain to ask Gemini about this step.")

        self.ai_busy = False
        self.last_locals = {}

        self._build_dropdown_rects()

    # ------------- layout helpers -------------
    def _build_dropdown_rects(self):
        self.concept_box = pygame.Rect(
            self.top_rect.right - 340, self.top_rect.y + 10, 260, 30)
        self.run_button = pygame.Rect(
            self.top_rect.right - 70, self.top_rect.y + 10, 60, 30)
        self.clear_button = pygame.Rect(
            self.top_rect.right - 200, self.top_rect.y + 10, 60, 30)
        self.example_button = pygame.Rect(
            self.top_rect.right - 270, self.top_rect.y + 10, 66, 30)

        # Actually reorder (right to left): Run, Example, Clear, dropdown
        self.run_button = pygame.Rect(self.top_rect.right - 76, self.top_rect.y + 10, 66, 30)
        self.clear_button = pygame.Rect(self.run_button.left - 72, self.top_rect.y + 10, 66, 30)
        self.example_button = pygame.Rect(self.clear_button.left - 88, self.top_rect.y + 10, 82, 30)
        self.concept_box = pygame.Rect(self.example_button.left - 280, self.top_rect.y + 10, 270, 30)

        self.dropdown_items = []
        for i, c in enumerate(CONCEPTS):
            r = pygame.Rect(self.concept_box.x, self.concept_box.bottom + 2 + i * 26,
                            self.concept_box.w, 26)
            self.dropdown_items.append((c, r))

    # ------------- actions -------------
    def update_visualizer(self):
        concept = CONCEPTS[self.concept_index]
        self.vis_canvas.set_visualizer(get_visualizer(concept))

    def run_code(self):
        source = self.editor.get_text()
        self.editor.set_error(None)
        self.editor.set_highlight(None)
        self.output_panel.set_result("", None)
        self.ai_panel.set_explanation("")
        self.ai_panel.set_status("Running...")
        # Force redraw so user sees status change
        self._render()
        pygame.display.flip()

        trace_data = execute_code(source, timeout=5.0)
        self.trace = TraceModel(trace_data)

        if self.trace.error:
            err = self.trace.error
            self.output_panel.set_result(self.trace.stdout, err)
            self.editor.set_error(err.get("line"))
            self.ai_panel.set_status(
                "Program raised an error. AI can explain it; click 🤖 Explain.")
        else:
            self.output_panel.set_result(self.trace.stdout, None)

        self.step_index = 0 if self.trace.total_steps > 0 else -1
        self.playing = False
        self.play_accum = 0.0
        self._apply_step()

    def _apply_step(self):
        if self.trace.total_steps == 0:
            self.editor.set_highlight(None)
            self.var_panel.set_prev({})
            self.var_panel.render  # no-op
            return
        i = max(0, min(self.step_index, self.trace.total_steps - 1))
        self.step_index = i
        ev = self.trace.event(i)
        self.editor.set_highlight(ev["line_number"])
        if i > 0:
            self.var_panel.set_prev(self.trace.locals_at(i - 1))
        else:
            self.var_panel.set_prev({})

    def next_step(self):
        if self.trace.total_steps and self.step_index < self.trace.total_steps - 1:
            self.step_index += 1
            self._apply_step()

    def prev_step(self):
        if self.step_index > 0:
            self.step_index -= 1
            self._apply_step()

    def restart(self):
        if self.trace.total_steps:
            self.step_index = 0
            self.playing = False
            self._apply_step()

    def toggle_play(self):
        if self.trace.total_steps == 0:
            return
        self.playing = not self.playing

    def cycle_speed(self):
        self.speed_idx = (self.speed_idx + 1) % len(SPEEDS)

    def explain_step(self):
        if self.trace.total_steps == 0 or self.step_index < 0:
            self.ai_panel.set_status("Run the program and select a step first.")
            return
        if self.ai_busy:
            return
        ev = self.trace.event(self.step_index)
        locs = {k: self._display(k, v) for k, v in ev["locals"].items()}
        prev = {}
        if self.step_index > 0:
            prev_ev = self.trace.event(self.step_index - 1)
            prev = {k: self._display(k, v) for k, v in prev_ev["locals"].items()}
        ctx = {
            "source": self.trace.source_code,
            "line_number": ev["line_number"],
            "line_text": self.trace.source_lines[ev["line_number"] - 1]
                if 0 < ev["line_number"] <= len(self.trace.source_lines) else "",
            "function": ev["function"],
            "event": ev["event"],
            "concept": CONCEPTS[self.concept_index],
            "locals": locs,
            "prev_locals": prev,
        }
        if self.trace.error and self.trace.timed_out is False:
            # If there's an error, prefer error explanation
            pass
        self.ai_busy = True
        self.ai_panel.set_status("Querying Gemini…")

        def done(text, ok):
            self.ai_busy = False
            self.ai_panel.set_explanation(text)

        self.ai.explain_step_async(ctx, done)

    def _display(self, name, serialized):
        from execution.serializer import display
        return display(serialized)

    # ------------- events -------------
    def handle_event(self, ev):
        if ev.type == pygame.QUIT:
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self._on_click(ev)
        elif ev.type == pygame.KEYDOWN:
            if self.editor.focus:
                self.editor.handle_key(ev.key, ev.mod)
        elif ev.type == pygame.TEXTINPUT:
            if self.editor.focus:
                self.editor.handle_text(ev.text)
        elif ev.type == pygame.MOUSEWHEEL:
            if self.output_panel.rect.collidepoint(pygame.mouse.get_pos()):
                self.output_panel.handle_wheel(-ev.y)
        return True

    def _on_click(self, ev):
        pos = ev.pos
        # Dropdown first
        if self.concept_dropdown_open:
            for name, r in self.dropdown_items:
                if r.collidepoint(pos):
                    self.concept_index = CONCEPTS.index(name)
                    self.concept_dropdown_open = False
                    self.update_visualizer()
                    return
            self.concept_dropdown_open = False

        if self.concept_box.collidepoint(pos):
            self.concept_dropdown_open = True
            return
        if self.run_button.collidepoint(pos):
            self.run_code()
            return
        if self.clear_button.collidepoint(pos):
            self.editor.set_text("")
            self.editor.set_highlight(None)
            self.editor.set_error(None)
            self.trace = TraceModel({})
            self.step_index = -1
            self.output_panel.set_result("", None)
            self.ai_panel.set_explanation("")
            return
        if self.example_button.collidepoint(pos):
            self.editor.set_text(get_example(CONCEPTS[self.concept_index]))
            return

        # Control bar
        key = self.control_bar.handle_click(pos)
        if key == "prev":
            self.prev_step()
        elif key == "next":
            self.next_step()
        elif key == "play":
            self.playing = True
        elif key == "pause":
            self.playing = False
        elif key == "restart":
            self.restart()
        elif key == "speed":
            self.cycle_speed()
        elif key == "explain":
            self.explain_step()

        # Editor focus
        if self.editor.rect.collidepoint(pos):
            self.editor.handle_click(pos)
        else:
            self.editor.focus = False
            if self.editor.rect.collidepoint(pos):
                pass

    # ------------- render -------------
    def _render(self):
        self.screen.fill(COLORS["bg"])

        # Top bar
        draw_panel(self.screen, self.top_rect)
        draw_text(self.screen, "Python Code Visualizer",
                  (self.top_rect.x + 16, self.top_rect.y + 14),
                  COLORS["text"], size=22, bold=True)
        draw_text(self.screen,
                  "Write Python • Run & Visualize • Step through execution",
                  (self.top_rect.x + 260, self.top_rect.y + 20),
                  COLORS["dim"], size=13)

        # Concept dropdown
        self._draw_button(self.concept_box, f"{CONCEPTS[self.concept_index]}  ▼")
        self._draw_button(self.run_button, "Run & ▶", accent=True)
        self._draw_button(self.clear_button, "Clear")
        self._draw_button(self.example_button, "Example")

        # Panels
        self.editor.render(self.screen)
        self.output_panel.render(self.screen)

        # Visualization context
        ctx = VisualizerContext(self.trace, self.step_index)
        self.vis_canvas.render(self.screen, ctx)

        # Variables
        locals_ = ctx.locals if ctx.event else {}
        self.var_panel.render(self.screen, locals_)

        # AI panel
        self.ai_panel.render(self.screen)

        # Control bar
        self.control_bar.render(
            self.screen,
            step=self.step_index if self.step_index >= 0 else 0,
            total=self.trace.total_steps,
            playing=self.playing,
            speed=SPEEDS[self.speed_idx],
            explain_busy=self.ai_busy,
            explain_available=self.ai.available and self.trace.total_steps > 0,
        )

        # Dropdown open overlay
        if self.concept_dropdown_open:
            for name, r in self.dropdown_items:
                hover = r.collidepoint(pygame.mouse.get_pos())
                fill = COLORS["accent"] if hover else COLORS["panel_alt"]
                pygame.draw.rect(self.screen, fill, r, border_radius=3)
                pygame.draw.rect(self.screen, COLORS["border"], r, 1, border_radius=3)
                color = COLORS["text"]
                draw_text(self.screen, name, (r.x + 10, r.y + 5), color, size=13)

    def _draw_button(self, rect, label, accent=False):
        hover = rect.collidepoint(pygame.mouse.get_pos())
        fill = COLORS["accent"] if (accent or hover) else COLORS["panel_alt"]
        pygame.draw.rect(self.screen, fill, rect, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["border"], rect, 1, border_radius=5)
        f = get_font(13, bold=True)
        txt = f.render(label, True, COLORS["text"])
        self.screen.blit(txt, (rect.centerx - txt.get_width() // 2,
                               rect.centery - txt.get_height() // 2))

    # ------------- loop -------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self.editor.update(dt)

            for ev in pygame.event.get():
                if not self.handle_event(ev):
                    running = False
                    break

            # Playback
            if self.playing and self.trace.total_steps > 0:
                self.play_accum += dt * SPEEDS[self.speed_idx]
                step_time = 0.5  # seconds per step at 1x
                while self.play_accum >= step_time:
                    self.play_accum -= step_time
                    if self.step_index < self.trace.total_steps - 1:
                        self.next_step()
                    else:
                        self.playing = False
                        break

            self._render()
            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    App().run()