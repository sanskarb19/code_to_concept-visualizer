# _fix_visualization.py — run from the project root
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VIS = os.path.join(ROOT, "visualization")
os.makedirs(VIS, exist_ok=True)

# ---- (filename, class name, display label) ----
VISUALIZERS = [
    ("variables.py",  "VariableVisualizer",   "Variables & Assignment"),
    ("loops.py",      "LoopVisualizer",       "Loops"),
    ("functions.py",  "FunctionVisualizer",   "Functions / Call Stack"),
    ("recursion.py",  "RecursionVisualizer",  "Recursion"),
    ("lists.py",      "ListVisualizer",       "Lists / Arrays"),
    ("stack.py",      "StackVisualizer",      "Stack"),
    ("queue.py",      "QueueVisualizer",      "Queue"),
    ("linked_list.py","LinkedListVisualizer", "Linked List (limited)"),
    ("tree.py",       "TreeVisualizer",       "Tree (limited)"),
    ("graph.py",      "GraphVisualizer",      "Graph (limited)"),
]

STUB = '''"""Auto-generated stub visualizer for {disp}."""
from gui.theme import COLORS, draw_text
from visualization.base import BaseVisualizer


class {cls}(BaseVisualizer):
    display_name = "{disp}"

    def render(self, surface, rect, ctx):
        draw_text(surface, "{disp}", (rect.x + 16, rect.y + 16),
                  COLORS["accent"], size=14, bold=True)
        draw_text(surface, "(stub — replace with full implementation)",
                  (rect.x + 16, rect.y + 44), COLORS["dim"], size=12)
        if ctx.event is not None:
            draw_text(surface, f"line {{ctx.line_number}}  in  {{ctx.function}}()",
                      (rect.x + 16, rect.y + 72), COLORS["text"], size=13, mono=True)
'''

BASE = '''"""Base class + context for visualizers."""
from gui.theme import COLORS


class VisualizerContext:
    def __init__(self, trace_model, step_index):
        self.trace = trace_model
        self.step_index = step_index
        self.src_lines = trace_model.source_lines

    @property
    def event(self):
        return self.trace.event(self.step_index)

    @property
    def locals(self):
        return self.event["locals"] if self.event else {}

    @property
    def line_number(self):
        return self.event["line_number"] if self.event else None

    @property
    def function(self):
        return self.event["function"] if self.event else None


class BaseVisualizer:
    display_name = "Visualization"

    def render(self, surface, rect, ctx):
        from gui.theme import draw_text
        draw_text(surface, "(visualizer stub)", (rect.x + 16, rect.y + 16), COLORS["text"])
'''

REGISTRY = '''from visualization.variables import VariableVisualizer
from visualization.loops import LoopVisualizer
from visualization.functions import FunctionVisualizer
from visualization.recursion import RecursionVisualizer
from visualization.lists import ListVisualizer
from visualization.stack import StackVisualizer
from visualization.queue import QueueVisualizer
from visualization.linked_list import LinkedListVisualizer
from visualization.tree import TreeVisualizer
from visualization.graph import GraphVisualizer

CONCEPTS = [
    "Variables & Assignment", "If / Else",
    "For Loop", "While Loop", "Nested Loops",
    "Functions", "Recursion",
    "Lists", "Strings", "Dictionary",
    "Stack", "Queue", "Searching", "Sorting",
    "Linked List", "Tree", "Graph",
]


def get_visualizer(concept):
    if concept in ("Variables & Assignment", "If / Else", "Dictionary",
                   "Strings", "Searching", "Sorting"):
        return VariableVisualizer()
    if concept in ("For Loop", "While Loop", "Nested Loops"):
        return LoopVisualizer()
    if concept == "Functions":
        return FunctionVisualizer()
    if concept == "Recursion":
        return RecursionVisualizer()
    if concept == "Lists":
        return ListVisualizer()
    if concept == "Stack":
        return StackVisualizer()
    if concept == "Queue":
        return QueueVisualizer()
    if concept == "Linked List":
        return LinkedListVisualizer()
    if concept == "Tree":
        return TreeVisualizer()
    if concept == "Graph":
        return GraphVisualizer()
    return VariableVisualizer()
'''

INIT = '''from visualization.registry import CONCEPTS, get_visualizer

__all__ = ["CONCEPTS", "get_visualizer"]
'''


def needs_stub(path, cls):
    if not os.path.exists(path) or os.path.getsize(path) < 200:
        return True
    try:
        return f"class {cls}" not in open(path, encoding="utf-8").read()
    except Exception:
        return True


# 1) base.py — always available
with open(os.path.join(VIS, "base.py"), "w", encoding="utf-8") as f:
    f.write(BASE)
print("wrote     visualization/base.py")

# 2) each visualizer — stub only when missing/broken
for fname, cls, disp in VISUALIZERS:
    path = os.path.join(VIS, fname)
    if needs_stub(path, cls):
        with open(path, "w", encoding="utf-8") as f:
            f.write(STUB.format(cls=cls, disp=disp))
        print(f"stubbed   visualization/{fname}")
    else:
        print(f"kept      visualization/{fname}")

# 3) __init__.py — always correct
with open(os.path.join(VIS, "__init__.py"), "w", encoding="utf-8") as f:
    f.write(INIT)
print("wrote     visualization/__init__.py")

# 4) registry.py — always correct
with open(os.path.join(VIS, "registry.py"), "w", encoding="utf-8") as f:
    f.write(REGISTRY)
print("wrote     visualization/registry.py")

print("\nDone. Verifying...")
sys.stdout.flush()

# fresh interpreter avoids stale module cache
import subprocess
r = subprocess.run(
    [sys.executable, "-c",
     "from visualization import CONCEPTS, get_visualizer; "
     "print('CONCEPTS:', len(CONCEPTS)); "
     "print('get_visualizer ok:', callable(get_visualizer))"],
    cwd=ROOT, capture_output=True, text=True,
)
print(r.stdout, r.stderr)