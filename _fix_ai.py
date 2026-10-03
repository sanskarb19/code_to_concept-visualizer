# _fix_ai.py — run from the project root to regenerate the entire ai package
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
AI   = os.path.join(ROOT, "ai")
os.makedirs(AI, exist_ok=True)

FILES = {}

FILES["__init__.py"] = '''from ai.gemini_client import GeminiExplainer

__all__ = ["GeminiExplainer"]
'''

FILES["prompts.py"] = '''SYSTEM_PROMPT = """You are a patient Python programming tutor.
Explain the provided execution step to a beginner.
Do not invent program behavior - use only the provided source code and execution state.
Explain what changed and why.
If the trace information is insufficient, explicitly say so.
Do not rewrite the entire program unless requested.
Keep explanations short (3-5 sentences) and beginner-friendly."""


def build_step_prompt(ctx: dict) -> str:
    src = ctx.get("source", "")
    line_no = ctx.get("line_number")
    line_text = ctx.get("line_text", "")
    locs = ctx.get("locals", {})
    fn = ctx.get("function", "<module>")
    event = ctx.get("event", "line")
    concept = ctx.get("concept", "Variables & Assignment")
    prev = ctx.get("prev_locals", {})

    loc_lines = "\\n".join(f"  {k} = {v}" for k, v in locs.items()) or "  (none)"
    prev_lines = "\\n".join(f"  {k} = {v}" for k, v in prev.items()) or "  (none)"

    return f"""Execution step context:

Source program:
{src}
Currently executing line #{line_no}:  {line_text}
Function/frame: {fn}
Event type: {event}
Selected concept: {concept}

Variables before this step:
{prev_lines}

Variables after this step:
{loc_lines}

Please explain in 3-5 beginner-friendly sentences:
1. What this line does.
2. Why it is executing now.
3. Which variables changed (if any), and to what.
4. A small conceptual tie-in."""


def build_error_prompt(ctx: dict) -> str:
    return f"""A beginner ran this Python program and got an error.

Source:
{ctx.get('source', '')}
Error type: {ctx.get('error_type')}
Error message: {ctx.get('error_message')}
Failing line: {ctx.get('error_line')}
Variables right before the failure:
{ctx.get('var_lines', '  (unknown)')}

Explain the error to a beginner in 2-4 sentences:
1. What this error means in plain English.
2. Why it happened (based on the failing line and state).
3. How to fix it."""
'''

FILES["gemini_client.py"] = '''import os
import threading

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from ai.prompts import SYSTEM_PROMPT, build_step_prompt, build_error_prompt


class GeminiExplainer:
    """Optional. Fails loudly but harmlessly if not configured."""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.available = bool(api_key) and HAS_GEMINI
        self._model = None
        self._error = None
        if not HAS_GEMINI:
            self._error = "google-generativeai not installed (pip install google-generativeai)."
        elif not api_key:
            self._error = "GEMINI_API_KEY not set. Set it in your environment to enable AI."
        else:
            try:
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=SYSTEM_PROMPT,
                )
            except Exception as e:
                self.available = False
                self._error = f"Failed to init Gemini: {e}"

    def status(self):
        return "ready" if self.available else self._error

    def explain_step_async(self, ctx, on_done):
        """Run in a background thread, call on_done(text, ok) when finished."""
        if not self.available:
            on_done(f"AI explanation unavailable: {self._error}", False)
            return

        def worker():
            try:
                prompt = build_step_prompt(ctx)
                resp = self._model.generate_content(prompt)
                text = getattr(resp, "text", None) or str(resp)
                on_done(text.strip(), True)
            except Exception as e:
                on_done(f"AI request failed: {e}", False)

        threading.Thread(target=worker, daemon=True).start()

    def explain_error_async(self, ctx, on_done):
        if not self.available:
            on_done(f"AI explanation unavailable: {self._error}", False)
            return

        def worker():
            try:
                resp = self._model.generate_content(build_error_prompt(ctx))
                text = getattr(resp, "text", None) or str(resp)
                on_done(text.strip(), True)
            except Exception as e:
                on_done(f"AI request failed: {e}", False)

        threading.Thread(target=worker, daemon=True).start()
'''

for name, content in FILES.items():
    path = os.path.join(AI, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote   ai/{name}  ({len(content)} bytes)")

print("\nVerifying (fresh interpreter)...")
sys.stdout.flush()

r = subprocess.run(
    [sys.executable, "-c",
     "from ai import GeminiExplainer; "
     "g = GeminiExplainer(); "
     "print('ai ok  available =', g.available); "
     "print('status:', g.status())"],
    cwd=ROOT, capture_output=True, text=True,
)
print(r.stdout, r.stderr)
